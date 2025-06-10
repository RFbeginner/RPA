# Use uma imagem base Python com as dependências mínimas necessárias para wkhtmltopdf
FROM python:3.9-slim-buster

# Instalar dependências essenciais do wkhtmltopdf (headless)
# wkhtmltopdf requer certas bibliotecas para funcionar em um ambiente sem display
RUN apt-get update && apt-get install -y \
    fontconfig \
    libxrender1 \
    libfontconfig1 \
    libjpeg-turbo8 \
    libxext6 \
    zlib1g \
    xfonts-base \
    xfonts-75dpi \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Baixar e instalar a versão estática do wkhtmltopdf (recomendado para evitar problemas de dependência)
# Verifique a URL mais recente e adequada em https://wkhtmltopdf.org/downloads.html
# Certifique-se de pegar a versão AMD64 (64-bit) para Linux (geralmente .deb para Debian/Ubuntu)
RUN WKHTMLTOPDF_VERSION="0.12.6-1" && \
    WKHTMLTOPDF_URL="https://github.com/wkhtmltopdf/packaging/releases/download/${WKHTMLTOPDF_VERSION}/wkhtmltox_${WKHTMLTOPDF_VERSION}.buster_amd64.deb" && \
    wget "${WKHTMLTOPDF_URL}" -O /tmp/wkhtmltox.deb && \
    dpkg -i /tmp/wkhtmltox.deb || apt-get install -fy && \
    dpkg -i /tmp/wkhtmltox.deb && \
    rm /tmp/wkhtmltox.deb

# Definir o caminho para o binário wkhtmltopdf
ENV WKHTMLTOPDF_BINARY_PATH=/usr/local/bin/wkhtmltopdf

# Definir o diretório de trabalho no contêiner
WORKDIR /app

# Copia os arquivos de requisitos e instala as dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o restante do código da aplicação para o contêiner
COPY . .

# Comando para iniciar a aplicação com Gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:$PORT"]