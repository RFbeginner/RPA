FROM python:3.11-slim-bookworm

# Atualiza os pacotes do sistema e instala o wkhtmltopdf
# Instala dependências e o pacote oficial wkhtmltopdf com QT
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


# Diretório de trabalho
WORKDIR /app

# Copia tudo
COPY . .

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Expondo a porta
EXPOSE 8000

# Criar link simbólico para o wkhtmltopdf
#RUN ln -s /usr/bin/wkhtmltopdf /usr/local/bin/wkhtmltopdf

# Comando para rodar
CMD ["python", "app.py"]
