# Classroom Autograder

Uma ferramenta CLI para correção automática de submissões do Google Classroom usando LLMs.

## Configuração

1. Configure as credenciais do Google Classroom:

```bash
# Baixe o arquivo credentials.json do Google Cloud Console
# Coloque o arquivo na raiz do projeto
```

2. Instale as dependências:


```bash
uv venv
source .venv/bin/activate  # Linux/macOS
# ou
.venv\Scripts\activate  # Windows

uv pip install -r requirements.txt
```

## Uso

1. Execute o comando:

```bash
python main.py
```

2. Selecione o curso e a atividade interativamente.

3. Os resultados serão salvos em:
   - `output/[student_id]_feedback.md`: Feedback individual
   - `output/errors.md`: Log de erros (se houver)

## Critérios de Avaliação

Os critérios de avaliação são definidos em arquivos markdown. Veja um exemplo em `examples/criteria.md`.

## Contribuição

1. Fork o repositório
2. Crie um branch para sua feature (`git checkout -b feature/nome`)
3. Commit suas mudanças (`git commit -am 'Adiciona feature'`)
4. Push para o branch (`git push origin feature/nome`)
