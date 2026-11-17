# Organizador de mensagens e tarefas

Protótipo local para organizar mensagens e tarefas. A interface em Python funciona sem conectar contas. Há também um agente experimental em TypeScript para receber mensagens diretas do Teams e gravá-las para importação no organizador.

## Estrutura

- `app.py`: interface gráfica, validação dos dados, filtros e persistência local.
- `itens.json`: exemplos fictícios carregados na abertura; novos cadastros são salvos neste arquivo.
- `teams-task-organizer/`: agente em TypeScript baseado no Teams SDK.
- `teams_inbox.jsonl`: caixa de entrada local criada pelo agente quando recebe mensagens.

## Requisitos

- Python 3 instalado no Windows. O Tkinter já vem com a instalação padrão do Python.
- Para usar o login Microsoft, instale as dependências com `py -m pip install -r requirements.txt`.

## Executar

1. Abra o PowerShell ou o Prompt de Comando.
2. Acesse a pasta do protótipo: `cd $HOME\organizador_local`
3. Crie um ambiente isolado e instale as dependências:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```
4. Execute: `.\.venv\Scripts\python.exe app.py`

## Login Microsoft

O botão **Entrar com Microsoft** identifica a conta corporativa no organizador usando a autenticação oficial da Microsoft. A senha é digitada apenas na página da Microsoft; o organizador não a solicita nem a salva. Depois do login, apenas o nome/e-mail mostrado na tela é salvo localmente em `microsoft_user.json` para continuar visível ao reabrir o organizador; nenhum token nem senha são gravados nesse arquivo. A identificação salva representa a última conta que concluiu o login, não uma sessão Microsoft ativa. Este login não concede ao bot acesso às mensagens do Teams nem substitui a instalação do bot e a permissão de apps personalizados.

Para ativar o botão:

1. Peça ao administrador de TI da empresa para registrar um aplicativo de desktop no Microsoft Entra ID e habilitar autenticação de cliente público. A conta também pode fazer esse registro se a empresa permitir registros de aplicativos por usuários.
2. No registro, abra **Authentication (Preview)**, adicione a plataforma **Aplicativos móveis e desktop** e habilite o URI `http://localhost` para autenticação interativa.
3. Em **Permissões de APIs**, adicione a permissão delegada do Microsoft Graph `User.Read`. O consentimento do administrador pode ser exigido pela política da empresa.
4. Copie `microsoft_app.example.json` para `microsoft_app.json` e preencha os valores `client_id` (ID do aplicativo) e `tenant_id` (ID do tenant/diretório da empresa), mostrados na página de visão geral do registro. Se o assistente criou os identificadores automaticamente, use esses valores.
5. Instale a biblioteca e abra o organizador:

   ```powershell
   cd $HOME\organizador_local
   py -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe app.py
   ```

6. Clique em **Entrar com Microsoft** e conclua o login na janela oficial que será aberta.

Sem o registro do aplicativo e esses IDs, não é possível concluir um login Microsoft real; não use sua senha em arquivos de configuração.

## Como testar

1. Ao abrir, confira os três exemplos fictícios.
2. Use a visão **Hoje** e **Esta semana**. A semana começa na segunda-feira e as visões consideram a data do prazo.
3. Combine os filtros de prioridade e status; escolha **Todos** para remover cada filtro.
4. Selecione uma linha para consultar sua descrição.
5. Cadastre um item com assunto e descrição, datas no formato `AAAA-MM-DD`, origem, prioridade e status. Ele deve aparecer na lista e continuar lá após fechar e reabrir o programa.
6. Experimente deixar assunto ou descrição vazios e informe uma data inválida: a tela deve explicar o que precisa ser corrigido.

## Etapas do protótipo

1. **Dados:** `itens.json` representa cada item como um objeto com origem, assunto, descrição, data de recebimento, prazo, prioridade e status.
2. **Cadastro:** o formulário valida os campos e datas antes de acrescentar um item.
3. **Consulta:** a tabela mostra os campos principais; selecionar uma linha revela a descrição.
4. **Visões e filtros:** as visões de hoje e da semana usam o prazo; prioridade e status podem ser combinados.
5. **Persistência:** os cadastros são gravados localmente em `itens.json`.

## Receber mensagens diretas do Teams

O agente registra o texto da mensagem como tarefa **Pendente**, com prioridade **Média** e prazo inicial igual à data de recebimento. Esses valores podem ser ajustados no organizador. O agente evita registrar novamente o mesmo identificador de mensagem.

1. Instale as dependências do agente uma vez:

   ```powershell
   cd $HOME\organizador_local\teams-task-organizer
   npm install
   ```
2. Inicie o agente:

   ```powershell
   npm run dev
   ```
3. Inicie o organizador com `py $HOME\organizador_local\app.py`.
4. Depois que o agente estiver conectado a um app do Teams, envie uma mensagem direta para ele. Clique em **Atualizar Teams** no organizador para importar a mensagem.

O serviço e os dados ficam neste computador; a conexão real com o Teams ainda precisa ser configurada. Para testar no Teams, a documentação oficial pede uma conta corporativa/escolar em um tenant que permita instalar apps personalizados. O quickstart de execução local não exige uma assinatura Azure. Se o envio de apps estiver bloqueado, será necessário pedir liberação ao administrador do Microsoft 365.

O agente grava em `teams_inbox.jsonl`, um arquivo separado de `itens.json`, para evitar que a interface sobrescreva mensagens recebidas enquanto salva tarefas locais. É possível escolher outro caminho definindo `ORGANIZER_INBOX_PATH` antes de iniciar o agente.

Consulte o [quickstart oficial do Teams SDK para TypeScript](https://learn.microsoft.com/en-us/microsoftteams/platform/agents-in-teams/quickstart-create-agent-teams-sdk) para autenticar e instalar/testar um agente no Teams.
