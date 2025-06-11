FROM python:3.11-slim

# Instalar dependências do sistema para Ubuntu noble
RUN apt-get update && apt-get install -y \
    wget \
    xfonts-75dpi \
    xfonts-base \
    libxrender1 \
    libfontconfig1 \
    libx11-dev \
    libjpeg62-turbo-dev \
    libxtst6 \
    fontconfig \
    ca-certificates

# Baixar e instalar wkhtmltopdf
RUN wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.jammy_amd64.deb
RUN dpkg -i wkhtmltox_0.12.6.1-2.jammy_amd64.deb || apt-get install -yf
RUN ln -s /usr/local/bin/wkhtmltopdf /usr/bin/wkhtmltopdf

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000", "--workers", "4"]