import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import microsoft_auth


class MicrosoftAuthTests(unittest.TestCase):
    def test_saved_user_is_loaded_and_saved(self):
        with tempfile.TemporaryDirectory() as pasta:
            perfil = Path(pasta) / "microsoft_user.json"
            with patch.object(microsoft_auth, "ARQUIVO_USUARIO", perfil):
                self.assertIsNone(microsoft_auth.carregar_usuario_microsoft())
                microsoft_auth.salvar_usuario_microsoft(
                    "Ana Exemplo (ana@empresa.com)"
                )
                self.assertEqual(
                    microsoft_auth.carregar_usuario_microsoft(),
                    "Ana Exemplo (ana@empresa.com)",
                )

    def test_login_uses_microsoft_and_returns_account_identity(self):
        with tempfile.TemporaryDirectory() as pasta:
            configuracao = Path(pasta) / "microsoft_app.json"
            configuracao.write_text(
                json.dumps({"client_id": "client-id", "tenant_id": "tenant-id"}),
                encoding="utf-8",
            )
            cliente = Mock()
            cliente.acquire_token_interactive.return_value = {
                "id_token_claims": {
                    "name": "Ana Exemplo",
                    "preferred_username": "ana@empresa.com",
                }
            }
            with (
                patch.object(microsoft_auth, "ARQUIVO_CONFIGURACAO", configuracao),
                patch.object(microsoft_auth.msal, "PublicClientApplication", return_value=cliente) as criar_app,
            ):
                usuario = microsoft_auth.autenticar_com_microsoft()

        self.assertEqual(usuario, "Ana Exemplo (ana@empresa.com)")
        criar_app.assert_called_once_with(
            "client-id",
            authority="https://login.microsoftonline.com/tenant-id",
        )
        cliente.acquire_token_interactive.assert_called_once_with(
            scopes=["User.Read"],
            prompt="select_account",
        )

    def test_missing_registration_is_reported(self):
        with tempfile.TemporaryDirectory() as pasta:
            configuracao = Path(pasta) / "nao-existe.json"
            with patch.object(microsoft_auth, "ARQUIVO_CONFIGURACAO", configuracao):
                with self.assertRaisesRegex(RuntimeError, "Falta configurar"):
                    microsoft_auth.autenticar_com_microsoft()

    def test_microsoft_sign_in_error_is_reported(self):
        with tempfile.TemporaryDirectory() as pasta:
            configuracao = Path(pasta) / "microsoft_app.json"
            configuracao.write_text(
                json.dumps({"client_id": "client-id", "tenant_id": "tenant-id"}),
                encoding="utf-8",
            )
            cliente = Mock()
            cliente.acquire_token_interactive.return_value = {
                "error": "access_denied",
                "error_description": "Consentimento negado.",
            }
            with (
                patch.object(microsoft_auth, "ARQUIVO_CONFIGURACAO", configuracao),
                patch.object(microsoft_auth.msal, "PublicClientApplication", return_value=cliente),
            ):
                with self.assertRaisesRegex(RuntimeError, "Consentimento negado"):
                    microsoft_auth.autenticar_com_microsoft()


if __name__ == "__main__":
    unittest.main()
