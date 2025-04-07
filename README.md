# Classroom Autograder 🎓

Uma ferramenta CLI para correção automática de submissões do Google Classroom usando LLMs (Large Language Models). Automatize a avaliação de trabalhos, gere feedbacks personalizados e atribua notas de forma eficiente.

## ✨ Funcionalidades

- 📝 Correção automática de submissões usando LLM
- 📊 Geração de notas baseadas em critérios personalizáveis
- 📧 Envio automático de feedbacks por email
- 🔄 Integração com Google Classroom e Google Drive
- 📋 Suporte a diferentes formatos de submissão (Python, Jupyter Notebooks, arquivos de texto, etc.)
- 💡 Geração automática de critérios de avaliação

## 📋 Formatos de Submissão Suportados

- 🐍 Arquivos Python (.py)
- 📓 Jupyter Notebooks (.ipynb)
- 📝 Arquivos de texto (.txt)
- 📑 Documentos PDF (.pdf)
- ~~📄 Documentos do Word (.docx)~~
- ~~📊 Planilhas do Excel (.xlsx)~~

## 🚀 Requisitos

- Python 3.10 ou superior
- Conta Google com acesso ao Google Classroom
- Chave de API da OpenAI
- Servidor SMTP (opcional, para envio de emails)

## ⚙️ Configuração

### 1. Configuração do Ambiente

É recomendado usar um ambiente virtual Python:

```bash
# Clone o repositório
git clone https://github.com/nes-collaborate/classroom-autograder
cd classroom-autograder

# Crie e ative um ambiente virtual (Linux/macOS)
python -m venv .venv
source .venv/bin/activate

# Ou no Windows
python -m venv .venv
.venv\Scripts\activate

# Instale as dependências (escolha uma opção):
pip install -r requirements.txt
# ou
uv sync
```

### 2. Variáveis de Ambiente

```bash
# Configure sua chave da API OpenAI (obrigatório)
export OPENAI_API_KEY=sk-sua-chave-aqui

# No Windows (PowerShell)
$env:OPENAI_API_KEY="sk-sua-chave-aqui"
```

### 3. Autenticação Google

1. Acesse o [Google Cloud Console](https://console.cloud.google.com)
2. Crie um projeto (ou selecione um existente)
3. Ative as APIs do Google Classroom e Google Drive
4. Configure as credenciais OAuth 2.0:
   - Em "OAuth consent screen", configure o app como "External" e adicione seu email como usuário de teste
   - Em "Credentials", crie uma credencial OAuth 2.0 do tipo "Desktop app"
   - Baixe o arquivo de credenciais e salve como `credentials.json` na raiz do projeto

## 🎯 Como Usar

1. Execute o programa:
```bash
python main.py
```

2. Na primeira execução:
   - Um navegador abrirá para autenticação com Google
   - Faça login com a conta que tem acesso às turmas do Google Classroom
   - Na tela de aviso "Google ainda não verificou este app", clique em "Continuar"
   - Autorize o acesso às suas turmas e arquivos

3. Selecione interativamente:
   - Curso
   - Atividade
   - Modo de avaliação
   - Opções de feedback

4. Os resultados serão salvos em:
   - `output/{curso_id}/{atividade_id}/`
   - Feedbacks individuais em Markdown
   - Log de erros (se houver)

## 📝 Critérios de Avaliação

Os critérios podem ser:
1. Definidos em arquivo markdown (veja `examples/criteria.md`)
2. Gerados automaticamente a partir do enunciado da atividade.

## ⚠️ Limitações Conhecidas

1. **Atribuição de Notas:**
   - A atribuição automática de notas só funciona quando você é o criador da atividade
   - Limitação da API do Google: professores não-criadores não podem modificar notas via API
   - Neste caso, as notas precisam ser inseridas manualmente via interface web

2. **Comentários Privados:**
   - Não é possível adicionar comentários privados via API
   - Todos os feedbacks são enviados por email ou salvos localmente

## 📧 Configuração de Email

- Se optar por enviar feedbacks por email, será solicitado:
  - Nome do professor
  - Número do WhatsApp
  - Email
  - Configurações SMTP
- As configurações são salvas em `teacher_profile.json` na raiz do projeto.
- A configuração só é necessária na primeira vez

## 🤝 Contribuindo

Contribuições são sempre bem-vindas! Siga estes passos:

1. Fork o projeto
2. Crie uma branch para sua feature: `git checkout -b feature/nome-da-feature`
3. Commit suas mudanças: `git commit -m 'Adiciona nova feature'`
4. Push para a branch: `git push origin feature/nome-da-feature`
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## ❓ Troubleshooting

### Erros Comuns

1. **Erro de autenticação Google:**
   - Verifique se o arquivo `credentials.json` está na raiz do projeto
   - Certifique-se de que as APIs necessárias estão ativas no Google Cloud Console
   - Delete a pasta `tokens/` e tente novamente

2. **Erro da API OpenAI:**
   - Confirme se a variável de ambiente `OPENAI_API_KEY` está configurada
   - Verifique se sua chave API é válida
   - Teste a chave em outro projeto OpenAI

3. **Erro ao enviar email:**
   - Verifique as configurações SMTP
   - Para Gmail, você precisa usar uma "Senha de App"
   - Tente excluir o arquivo `teacher_profile.json` e configurar novamente

4. **Erros de ambiente Python:**
   - Certifique-se de estar usando Python 3.10+
   - Verifique se o ambiente virtual está ativado
   - Tente reinstalar as dependências

Para outros problemas, consulte as [Issues do GitHub](https://github.com/nes-collaborate/classroom-autograder/issues).
