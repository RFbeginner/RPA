# Imagem base com Python + dependências mínimas
FROM python:3.11-slim-bullseye

# Atualiza todos os pacotes do sistema e instala dependências do sistema e o wkhtmltopdf
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

# Expõe a porta do Flask
EXPOSE 8000

# Comando para rodar o app
CMD ["python", "app.py"]
