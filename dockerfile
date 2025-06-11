FROM python:3.10-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    libxrender1 \
    libfontconfig1 \
    libx11-dev \
    libjpeg62-turbo-dev \
    libxtst6 \
    fontconfig \
    xfonts-75dpi \
    xfonts-base \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar binário wkhtmltopdf
COPY bin/wkhtmltopdf /usr/local/bin/
RUN chmod +x /usr/local/bin/wkhtmltopdf

# Copiar aplicação
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000", "--workers", "4"]