FROM python:3.11-slim-bookworm

# Atualiza os pacotes do sistema e instala o wkhtmltopdf
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    wkhtmltopdf \
    build-essential \
    libssl-dev \
    libffi-dev \
    libxrender1 \
    libxext6 \
    libx11-6 \
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
