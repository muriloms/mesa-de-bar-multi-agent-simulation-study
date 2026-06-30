# Estágio 1: Builder - Instala as dependências
FROM python:3.11-slim 

# Define o diretório de trabalho
WORKDIR /app

# Copia o arquivo de dependências e instala os pacotes
COPY requirements.txt .

RUN pip install --no-cache -r requirements.txt


# Copia o código da nossa aplicação
# O ponto '.' se refere a todo o conteúdo da pasta 'app' do nosso backend
COPY ./app .

# Expõe a porta em que a aplicação irá rodar dentro do contêiner
EXPOSE 8000

# Comando para iniciar a aplicação em modo de produção
# "app.main:app" -> informa ao uvicorn para rodar o objeto 'app' do arquivo 'main.py' dentro da pasta 'app'
# O host 0.0.0.0 é essencial para que a porta seja acessível de fora do contêiner.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]