FROM python:3.11-slim-bookworm

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    wget \
    xfonts-75dpi \
    xfonts-base \
    libjpeg62-turbo \
    libxrender1 \
    libxtst6 \
    libxext6 \
    libfontconfig1 \
    && wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.6/wkhtmltox_0.12.6-1.buster_amd64.deb \
    && apt install -y ./wkhtmltox_0.12.6-1.buster_amd64.deb \
    && rm wkhtmltox_0.12.6-1.buster_amd64.deb \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos do projeto
COPY . .

# Instala as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Expondo a porta para o Railway
EXPOSE 8000

# Comando para iniciar a aplicação
CMD ["python", "app.py"]
