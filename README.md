# Projeto de Gestão de Sistemas

Este projeto é uma solução de gestão de sistemas que integra um chatbot inteligente utilizando **Pandas** como analista e LLM da Gemini como motor (IA). O backend é desenvolvido em **Python** com o framework **Django**, enquanto o frontend utiliza **HTML**, **CSS** e **JavaScript**. Este projeto foi desenvolvido para uma apresentação de Projeto de Conclusão de Curso para o titulo de Análise e Desenvolvimento de Sistemas. É uma breve demonstração de como uma IA pode ser treinada para facilitar e acelerar resultados de processos repentinos, trazendo insights, planos de ação e acelerando busca de resultados para crescimento do negócio (empresa).

## Funcionalidades

- Chatbot inteligente para análise de dados do sistema
- Integração com PandasAI para respostas analíticas
- Interface web moderna e responsiva

## Tecnologias Utilizadas

- **Backend:** Python, Django, PandasAI
- **Frontend:** HTML, CSS, JavaScript
- **LLM:** Google Gemini (gemini-2.0-flash)

## Como Executar o Projeto

1. **Clone o repositório:**
    ```bash
    git clone https://github.com/Jhowkley/tcc_gestao.git
    cd tcc_gestao
    ```

2. **Crie e ative o ambiente virtual:**
    ```bash
    python -m venv venv
    # No Windows
    venv\Scripts\activate
    # No Linux/Mac
    source venv/bin/activate
    ```
3. **Banco de Dados:**
    ```bash
    Ao clonar o repértorio aplique as migrations para gerar o arquivo `db.sqlite3`
    ```
3. **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4. **Execute o servidor Django:**
    ```bash
    python manage.py runserver
    ```

5. **Acesse o sistema:**
    Abra o navegador e acesse `http://localhost:8000`

## Users

Por padrão a aplicação tem um superuser.
user: admin
password: admin

## Contribuição

Sinta-se livre para abrir issues e enviar pull requests!

## Banco de Dados

Por padrão a aplicação usa SQLite3 (arquivo `db.sqlite3`) para facilitar a instalação e testes locais. Se preferir usar PostgreSQL em produção ou em um ambiente mais robusto, basta alterar a configuração `DATABASES` no `settings.py` para apontar ao PostgreSQL. 

Exemplo de configuração para PostgreSQL (substitua pelos seus valores):

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'nome_do_seu_banco', # Ex: 'mydjangodb'
        'USER': 'seu_usuario_postgres', # Ex: 'django_user'
        'PASSWORD': 'sua_senha_postgres',
        'HOST': 'localhost', # Ou o IP/nome do host do seu servidor Postgres
        'PORT': '', # Deixe vazio para a porta padrão (5432) ou especifique
    }
}
```

Passos rápidos após alterar a configuração:
- Instale o driver do Postgres: `pip install psycopg2-binary`
- Aplique migrações: `python manage.py migrate`
- Crie um superuser: `python manage.py createsuperuser`

Opcional: armazene credenciais sensíveis em variáveis de ambiente e atualize `requirements.txt` conforme necessário.
