import json
import tkinter as tk
from datetime import date, timedelta
from pathlib import Path
from threading import Thread
from tkinter import messagebox, ttk

from microsoft_auth import (
    autenticar_com_microsoft,
    carregar_usuario_microsoft,
    salvar_usuario_microsoft,
)


PASTA_APP = Path(__file__).resolve().parent
ARQUIVO_DADOS = PASTA_APP / "itens.json"
ARQUIVO_ENTRADA_TEAMS = PASTA_APP / "teams_inbox.jsonl"

ORIGENS = ("Teams", "E-mail")
PRIORIDADES = ("Alta", "Média", "Baixa")
STATUS = ("Pendente", "Em andamento", "Concluído")
VISOES = ("Todos", "Hoje", "Esta semana")


def carregar_itens():
    try:
        with ARQUIVO_DADOS.open(encoding="utf-8") as arquivo:
            itens = json.load(arquivo)
    except (OSError, json.JSONDecodeError) as erro:
        raise RuntimeError(f"Não foi possível ler {ARQUIVO_DADOS.name}: {erro}") from erro

    if not isinstance(itens, list):
        raise RuntimeError(f"O conteúdo de {ARQUIVO_DADOS.name} deve ser uma lista.")
    return itens


def salvar_itens(itens):
    try:
        with ARQUIVO_DADOS.open("w", encoding="utf-8") as arquivo:
            json.dump(itens, arquivo, ensure_ascii=False, indent=2)
            arquivo.write("\n")
    except OSError as erro:
        raise RuntimeError(f"Não foi possível salvar {ARQUIVO_DADOS.name}: {erro}") from erro


def carregar_mensagens_teams():
    try:
        with ARQUIVO_ENTRADA_TEAMS.open(encoding="utf-8") as arquivo:
            linhas = arquivo.readlines()
    except FileNotFoundError:
        return []
    except OSError as erro:
        raise RuntimeError(
            f"Não foi possível ler {ARQUIVO_ENTRADA_TEAMS.name}: {erro}"
        ) from erro

    if linhas and not linhas[-1].endswith("\n"):
        raise RuntimeError(
            f"A última mensagem em {ARQUIVO_ENTRADA_TEAMS.name} está incompleta. "
            "Tente atualizar novamente."
        )

    mensagens = []
    for numero, linha in enumerate(linhas, start=1):
        if not linha.strip():
            continue
        try:
            item = json.loads(linha)
        except json.JSONDecodeError as erro:
            raise RuntimeError(
                f"Mensagem inválida na linha {numero} de {ARQUIVO_ENTRADA_TEAMS.name}: {erro}"
            ) from erro
        if not isinstance(item, dict):
            raise RuntimeError(
                f"A linha {numero} de {ARQUIVO_ENTRADA_TEAMS.name} deve conter um objeto."
            )
        campos_obrigatorios = (
            "origem",
            "assunto",
            "descricao",
            "data_recebimento",
            "prazo",
            "prioridade",
            "status",
        )
        if any(not isinstance(item.get(campo), str) for campo in campos_obrigatorios):
            raise RuntimeError(
                f"A linha {numero} de {ARQUIVO_ENTRADA_TEAMS.name} não contém os campos esperados."
            )
        try:
            date.fromisoformat(item["data_recebimento"])
            date.fromisoformat(item["prazo"])
        except ValueError as erro:
            raise RuntimeError(
                f"As datas da linha {numero} de {ARQUIVO_ENTRADA_TEAMS.name} são inválidas."
            ) from erro
        mensagens.append(item)
    return mensagens


class OrganizadorApp:
    def __init__(self, janela):
        self.janela = janela
        self.janela.title("Organizador local de mensagens e tarefas")
        self.janela.geometry("1120x760")
        self.janela.minsize(900, 620)
        self.itens = carregar_itens()
        self.itens_teams = carregar_mensagens_teams()
        ultimo_usuario = carregar_usuario_microsoft()
        identificacao = f"Última conta Microsoft conectada: {ultimo_usuario}" if ultimo_usuario else "Nenhuma conta Microsoft conectada"
        self.usuario_microsoft = tk.StringVar(value=identificacao)

        self._criar_interface()
        self._atualizar_lista()

    def _criar_interface(self):
        conteudo = ttk.Frame(self.janela, padding=16)
        conteudo.pack(fill="both", expand=True)

        cabecalho = ttk.Frame(conteudo)
        cabecalho.pack(fill="x")
        ttk.Label(
            cabecalho,
            text="Organizador de mensagens e tarefas",
            font=("Segoe UI", 19, "bold"),
        ).pack(side="left", anchor="w")
        ttk.Button(
            cabecalho,
            text="Entrar com Microsoft",
            command=self._iniciar_login_microsoft,
        ).pack(side="right")
        ttk.Label(
            conteudo,
            text="Conta Microsoft:",
        ).pack(anchor="w", pady=(2, 0))
        ttk.Label(
            conteudo,
            textvariable=self.usuario_microsoft,
        ).pack(anchor="w")
        ttk.Label(
            conteudo,
            text="Os dados do organizador ficam neste computador.",
        ).pack(anchor="w", pady=(2, 14))

        formulario = ttk.LabelFrame(conteudo, text="Cadastrar item", padding=12)
        formulario.pack(fill="x", pady=(0, 12))
        formulario.columnconfigure(1, weight=1)
        formulario.columnconfigure(3, weight=1)

        self.origem = tk.StringVar(value=ORIGENS[0])
        self.assunto = tk.StringVar()
        self.data_recebimento = tk.StringVar(value=date.today().isoformat())
        self.prazo = tk.StringVar(value=date.today().isoformat())
        self.prioridade = tk.StringVar(value=PRIORIDADES[1])
        self.status = tk.StringVar(value=STATUS[0])

        ttk.Label(formulario, text="Origem").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(
            formulario, textvariable=self.origem, values=ORIGENS, state="readonly", width=16
        ).grid(row=0, column=1, sticky="ew", padx=(0, 16), pady=4)
        ttk.Label(formulario, text="Assunto").grid(row=0, column=2, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(formulario, textvariable=self.assunto).grid(row=0, column=3, sticky="ew", pady=4)

        ttk.Label(formulario, text="Recebido em (AAAA-MM-DD)").grid(
            row=1, column=0, sticky="w", padx=(0, 8), pady=4
        )
        ttk.Entry(formulario, textvariable=self.data_recebimento).grid(
            row=1, column=1, sticky="ew", padx=(0, 16), pady=4
        )
        ttk.Label(formulario, text="Prazo (AAAA-MM-DD)").grid(
            row=1, column=2, sticky="w", padx=(0, 8), pady=4
        )
        ttk.Entry(formulario, textvariable=self.prazo).grid(
            row=1, column=3, sticky="ew", pady=4
        )

        ttk.Label(formulario, text="Prioridade").grid(
            row=2, column=0, sticky="w", padx=(0, 8), pady=4
        )
        ttk.Combobox(
            formulario,
            textvariable=self.prioridade,
            values=PRIORIDADES,
            state="readonly",
            width=16,
        ).grid(row=2, column=1, sticky="ew", padx=(0, 16), pady=4)
        ttk.Label(formulario, text="Status").grid(
            row=2, column=2, sticky="w", padx=(0, 8), pady=4
        )
        ttk.Combobox(
            formulario, textvariable=self.status, values=STATUS, state="readonly"
        ).grid(row=2, column=3, sticky="ew", pady=4)

        ttk.Label(formulario, text="Descrição").grid(
            row=3, column=0, sticky="nw", padx=(0, 8), pady=4
        )
        self.descricao = tk.Text(formulario, height=3, wrap="word")
        self.descricao.grid(row=3, column=1, columnspan=3, sticky="ew", pady=4)

        ttk.Button(formulario, text="Cadastrar item", command=self._cadastrar).grid(
            row=4, column=3, sticky="e", pady=(8, 0)
        )

        filtros = ttk.Frame(conteudo)
        filtros.pack(fill="x", pady=(0, 8))
        self.visao = tk.StringVar(value=VISOES[0])
        self.filtro_prioridade = tk.StringVar(value="Todas")
        self.filtro_status = tk.StringVar(value="Todos")

        ttk.Label(filtros, text="Visão").pack(side="left", padx=(0, 6))
        visao_box = ttk.Combobox(
            filtros, textvariable=self.visao, values=VISOES, state="readonly", width=14
        )
        visao_box.pack(side="left", padx=(0, 16))
        visao_box.bind("<<ComboboxSelected>>", lambda _evento: self._atualizar_lista())

        ttk.Label(filtros, text="Prioridade").pack(side="left", padx=(0, 6))
        prioridade_box = ttk.Combobox(
            filtros,
            textvariable=self.filtro_prioridade,
            values=("Todas",) + PRIORIDADES,
            state="readonly",
            width=12,
        )
        prioridade_box.pack(side="left", padx=(0, 16))
        prioridade_box.bind("<<ComboboxSelected>>", lambda _evento: self._atualizar_lista())

        ttk.Label(filtros, text="Status").pack(side="left", padx=(0, 6))
        status_box = ttk.Combobox(
            filtros,
            textvariable=self.filtro_status,
            values=("Todos",) + STATUS,
            state="readonly",
            width=16,
        )
        status_box.pack(side="left")
        status_box.bind("<<ComboboxSelected>>", lambda _evento: self._atualizar_lista())
        ttk.Button(
            filtros,
            text="Atualizar Teams",
            command=self._atualizar_mensagens_teams,
        ).pack(side="right")

        colunas = ("origem", "assunto", "recebido", "prazo", "prioridade", "status")
        self.tabela = ttk.Treeview(conteudo, columns=colunas, show="headings", height=12)
        titulos = {
            "origem": "Origem",
            "assunto": "Assunto",
            "recebido": "Recebido em",
            "prazo": "Prazo",
            "prioridade": "Prioridade",
            "status": "Status",
        }
        larguras = {"origem": 90, "assunto": 300, "recebido": 120, "prazo": 120,
                    "prioridade": 100, "status": 130}
        for coluna in colunas:
            self.tabela.heading(coluna, text=titulos[coluna])
            self.tabela.column(coluna, width=larguras[coluna], anchor="w")
        self.tabela.pack(fill="both", expand=True)
        self.tabela.bind("<<TreeviewSelect>>", self._mostrar_detalhes)

        self.detalhes = tk.StringVar(value="Selecione um item para consultar a descrição.")
        ttk.Label(
            conteudo,
            textvariable=self.detalhes,
            wraplength=1050,
            justify="left",
            padding=(4, 10),
        ).pack(fill="x")
        self.mensagem = tk.StringVar()
        ttk.Label(conteudo, textvariable=self.mensagem).pack(anchor="w")

    def _cadastrar(self):
        assunto = self.assunto.get().strip()
        descricao = self.descricao.get("1.0", "end").strip()
        if not assunto or not descricao:
            messagebox.showerror("Dados obrigatórios", "Preencha o assunto e a descrição.")
            return

        try:
            recebido = date.fromisoformat(self.data_recebimento.get().strip())
            prazo = date.fromisoformat(self.prazo.get().strip())
        except ValueError:
            messagebox.showerror(
                "Data inválida", "Informe as datas no formato AAAA-MM-DD, por exemplo 2026-10-05."
            )
            return

        item = {
            "origem": self.origem.get(),
            "assunto": assunto,
            "descricao": descricao,
            "data_recebimento": recebido.isoformat(),
            "prazo": prazo.isoformat(),
            "prioridade": self.prioridade.get(),
            "status": self.status.get(),
        }
        novos_itens = self.itens + [item]
        try:
            salvar_itens(novos_itens)
        except RuntimeError as erro:
            messagebox.showerror("Erro ao salvar", str(erro))
            return

        self.itens = novos_itens
        self.assunto.set("")
        self.descricao.delete("1.0", "end")
        self._atualizar_lista()
        self.mensagem.set(f"Item cadastrado: {assunto}")

    def _atualizar_lista(self):
        for linha in self.tabela.get_children():
            self.tabela.delete(linha)

        hoje = date.today()
        inicio_semana = hoje - timedelta(days=hoje.weekday())
        fim_semana = inicio_semana + timedelta(days=6)
        exibidos = []
        todos_itens = self.itens + self.itens_teams
        for indice, item in enumerate(todos_itens):
            prazo = date.fromisoformat(item["prazo"])
            if self.visao.get() == "Hoje" and prazo != hoje:
                continue
            if self.visao.get() == "Esta semana" and not inicio_semana <= prazo <= fim_semana:
                continue
            if self.filtro_prioridade.get() != "Todas" and item["prioridade"] != self.filtro_prioridade.get():
                continue
            if self.filtro_status.get() != "Todos" and item["status"] != self.filtro_status.get():
                continue
            exibidos.append((prazo, indice, item))

        for _prazo, indice, item in sorted(exibidos):
            self.tabela.insert(
                "",
                "end",
                iid=str(indice),
                values=(
                    item["origem"],
                    item["assunto"],
                    item["data_recebimento"],
                    item["prazo"],
                    item["prioridade"],
                    item["status"],
                ),
            )
        self.mensagem.set(f"{len(exibidos)} item(ns) nesta visão.")

    def _atualizar_mensagens_teams(self):
        try:
            self.itens_teams = carregar_mensagens_teams()
        except RuntimeError as erro:
            messagebox.showerror("Erro ao atualizar Teams", str(erro))
            return
        self._atualizar_lista()
        self.mensagem.set(
            f"Mensagens do Teams atualizadas: {len(self.itens_teams)} item(ns)."
        )

    def _iniciar_login_microsoft(self):
        self.mensagem.set("Aguardando autenticação segura da Microsoft...")
        Thread(target=self._autenticar_microsoft, daemon=True).start()

    def _autenticar_microsoft(self):
        try:
            usuario = autenticar_com_microsoft()
            salvar_usuario_microsoft(usuario)
        except Exception as erro:
            self.janela.after(
                0,
                lambda mensagem=str(erro): self._mostrar_erro_login_microsoft(mensagem),
            )
            return
        self.janela.after(
            0,
            lambda: self.usuario_microsoft.set(
                f"Última conta Microsoft conectada: {usuario}"
            ),
        )
        self.janela.after(0, lambda: self.mensagem.set("Login Microsoft concluído."))

    def _mostrar_erro_login_microsoft(self, mensagem):
        self.mensagem.set("Não foi possível entrar com a conta Microsoft.")
        messagebox.showerror("Login Microsoft", mensagem)

    def _mostrar_detalhes(self, _evento):
        selecionados = self.tabela.selection()
        if not selecionados:
            return
        todos_itens = self.itens + self.itens_teams
        item = todos_itens[int(selecionados[0])]
        self.detalhes.set(f"Descrição: {item['descricao']}")


def main():
    janela = tk.Tk()
    try:
        app = OrganizadorApp(janela)
    except RuntimeError as erro:
        messagebox.showerror("Erro ao abrir os dados", str(erro))
        janela.destroy()
        return
    janela.mainloop()


if __name__ == "__main__":
    main()
