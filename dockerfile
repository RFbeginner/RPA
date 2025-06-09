# Imagem base com Python + dependências mínimas
FROM python:3.11-slim-bullseye

# Instala dependências do wkhtmltopdf
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    wkhtmltopdf \
    build-essential \
    libssl-dev \
    libffi-dev \
    libxrender1 \
    libxext6 \
    libx11-6 \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# Cria o link simbólico no caminho esperado
RUN ln -s /usr/bin/wkhtmltopdf /usr/local/bin/wkhtmltopdf

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["python", "app.py"]

