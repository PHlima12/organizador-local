import json
from pathlib import Path

import msal


PASTA_APP = Path(__file__).resolve().parent
ARQUIVO_CONFIGURACAO = PASTA_APP / "microsoft_app.json"
ARQUIVO_USUARIO = PASTA_APP / "microsoft_user.json"


def carregar_usuario_microsoft():
    try:
        with ARQUIVO_USUARIO.open(encoding="utf-8") as arquivo:
            perfil = json.load(arquivo)
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError) as erro:
        raise RuntimeError(f"Não foi possível ler {ARQUIVO_USUARIO.name}: {erro}") from erro

    if not isinstance(perfil, dict) or not isinstance(perfil.get("usuario"), str):
        raise RuntimeError(f"O conteúdo de {ARQUIVO_USUARIO.name} é inválido.")
    return perfil["usuario"]


def salvar_usuario_microsoft(usuario):
    try:
        with ARQUIVO_USUARIO.open("w", encoding="utf-8") as arquivo:
            json.dump({"usuario": usuario}, arquivo, ensure_ascii=False, indent=2)
            arquivo.write("\n")
    except OSError as erro:
        raise RuntimeError(f"Não foi possível salvar {ARQUIVO_USUARIO.name}: {erro}") from erro


def autenticar_com_microsoft():
    try:
        with ARQUIVO_CONFIGURACAO.open(encoding="utf-8") as arquivo:
            configuracao = json.load(arquivo)
    except FileNotFoundError as erro:
        raise RuntimeError(
            "Falta configurar microsoft_app.json. Siga as instruções da seção "
            "'Login Microsoft' no README.md."
        ) from erro
    except (OSError, json.JSONDecodeError) as erro:
        raise RuntimeError(
            f"Não foi possível ler {ARQUIVO_CONFIGURACAO.name}: {erro}"
        ) from erro

    if not isinstance(configuracao, dict):
        raise RuntimeError(f"O conteúdo de {ARQUIVO_CONFIGURACAO.name} deve ser um objeto.")

    client_id = configuracao.get("client_id")
    tenant_id = configuracao.get("tenant_id")
    if not isinstance(client_id, str) or not client_id.strip():
        raise RuntimeError("Preencha client_id em microsoft_app.json.")
    if not isinstance(tenant_id, str) or not tenant_id.strip():
        raise RuntimeError("Preencha tenant_id em microsoft_app.json.")

    aplicativo = msal.PublicClientApplication(
        client_id.strip(),
        authority=f"https://login.microsoftonline.com/{tenant_id.strip()}",
    )
    resultado = aplicativo.acquire_token_interactive(
        scopes=["User.Read"],
        prompt="select_account",
    )
    if "error" in resultado:
        detalhe = resultado.get("error_description") or resultado["error"]
        raise RuntimeError(f"A Microsoft não concluiu o login: {detalhe}")

    claims = resultado.get("id_token_claims")
    if not isinstance(claims, dict):
        raise RuntimeError("A resposta de login da Microsoft não incluiu os dados da conta.")

    nome = claims.get("name")
    conta = claims.get("preferred_username") or claims.get("email")
    if isinstance(nome, str) and isinstance(conta, str):
        return f"{nome} ({conta})"
    if isinstance(conta, str):
        return conta
    if isinstance(nome, str):
        return nome
    raise RuntimeError("A Microsoft não retornou nome nem e-mail para identificar a conta.")
