from flask import Flask, render_template, request, send_file, redirect, url_for
import pdfkit
import io
import os
from validate_docbr import CPF, CNPJ

import sys # Importe sys globalmente

# Importações condicionais para travamento de arquivo
if sys.platform == 'win32':
    import msvcrt
else:
    import fcntl

    # ... outras importações ...

WKHTMLTOPDF_BIN = os.environ.get('WKHTMLTOPDF_BINARY_PATH', 'C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_BIN)

# ... restante do seu código ...
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
options = {
    'disable-external-links': None,
    'disable-javascript': None,
    'no-stop-slow-scripts': None,
    'load-error-handling': 'ignore',
    'image-dpi': '300',
    'enable-local-file-access': None,
    'encoding': 'UTF-8',
    'disable-smart-shrinking': None,
    'zoom': '1.0',
    'margin-top': '10mm',
    'margin-bottom': '10mm',
    'margin-left': '10mm',
    'margin-right': '10mm',
    'print-media-type': None,
    'page-width': '210mm',
    'page-height': '297mm'
}

cpf = CPF()
cnpj = CNPJ()

COUNTER_FILE = 'recibo_counter.txt'
def get_next_recibo_number():
    """
    Reads, increments, and writes the next sequential receipt number.
    Uses file locking to prevent race conditions in multi-threaded/multi-process environments.
    """
    # Use different locking mechanisms based on OS
    if sys.platform == 'win32':
        lock_method = msvcrt.locking
        LOCK_EX = msvcrt.LK_NBLCK # Non-blocking lock for Windows
        # Para msvcrt.locking, o terceiro argumento (nbytes) é o número de bytes a serem bloqueados.
        # Para bloquear todo o arquivo (ou a parte relevante), 0 geralmente funciona,
        # ou um número grande o suficiente. Vamos usar 0.
        LOCK_SIZE = 0 # Bloqueia do offset atual até o final do arquivo, ou todo o arquivo se offset 0
    else:
        lock_method = fcntl.flock
        LOCK_EX = fcntl.LOCK_EX | fcntl.LOCK_NB # Non-blocking lock for Unix

    while True: # Keep trying to acquire lock
        try:
            with open(COUNTER_FILE, 'r+') as f:
                # Acquire an exclusive lock on the file
                if sys.platform == 'win32':
                    lock_method(f.fileno(), LOCK_EX, LOCK_SIZE) # Adicionei LOCK_SIZE aqui
                else:
                    lock_method(f.fileno(), LOCK_EX) # Unix-like não precisa do 3º arg

                f.seek(0)
                content = f.read().strip()
                current_number = int(content) if content else 0
                next_number = current_number + 1
                f.seek(0)
                f.truncate() # Clear content before writing
                f.write(str(next_number))
            return next_number
        except (IOError, BlockingIOError) as e:
            # If lock fails, it means another process has the lock, retry
            # In a real-world scenario, you might want to add a small delay
            print(f"Waiting for file lock on {COUNTER_FILE}: {e}")
            import time
            time.sleep(0.05) # Wait a bit before retrying
def calcular_irpf(base):
    """
    Tabela IRPF 2025 vigente a partir de maio (com deduções fixas)
    """
    if base <= 2428.80:
        return 0.0
    elif base <= 2826.65:
        return round((base * 0.075) - 182.16, 2)
    elif base <= 3751.05:
        return round((base * 0.15) - 394.16, 2)
    elif base <= 4664.68:
        return round((base * 0.225) - 675.49, 2)
    else:
        return round((base * 0.275) - 908.73, 2)

def calcular_valores_finais(valor_liquido, forcar_irpf=False):
    base = valor_liquido / 0.87  # 1 - 0.11 - 0.02

    if not forcar_irpf and base <= 2428.80:
        return {
            'base': round(base, 2),
            'inss': round(base * 0.11, 2),
            'iss': round(base * 0.02, 2),
            'irpf': 0.0
        }

    # Iteração refinada com tolerância menor
    for _ in range(20):
        inss = base * 0.11
        iss = base * 0.02
        irpf = calcular_irpf(base)
        nova_base = valor_liquido + inss + iss + irpf
        if abs(nova_base - base) < 0.001:
            break
        base = nova_base

    return {
        'base': round(base, 2),
        'inss': round(base * 0.11, 2),
        'iss': round(base * 0.02, 2),
        'irpf': calcular_irpf(base)
    }

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        dados = request.form.to_dict()
        valor_liquido = float(dados['valor_liquido'])
        forcar_irpf = 'forcar_irpf' in dados and dados['forcar_irpf'] == 'on'

        resultados = calcular_valores_finais(valor_liquido, forcar_irpf)

        dados.update({
            'valor_bruto': f"{resultados['base']:.2f}",
            'inss': f"{resultados['inss']:.2f}",
            'iss': f"{resultados['iss']:.2f}",
            'irpf': f"{resultados['irpf']:.2f}",
            'recibo_num': get_next_recibo_number()
        })
        return redirect(url_for('preview', **dados))

    return render_template("formulario.html")

@app.route('/preview')
def preview():
    dados = request.args.to_dict()
    valor_liquido = float(dados['valor_liquido'])
    forcar_irpf = dados.get('forcar_irpf', 'off') == 'on'

    valores = calcular_valores_finais(valor_liquido, forcar_irpf)

    dados.update({
        'valor_bruto': f"{valores['base']:.2f}",
        'inss': f"{valores['inss']:.2f}",
        'iss': f"{valores['iss']:.2f}",
        'irpf': f"{valores['irpf']:.2f}",
        # Do NOT call get_next_recibo_number() here
        # The 'recibo_num' should already be in 'dados' from the index route
        'recibo_num': dados['recibo_num'] # Ensure we use the one already passed
    })
    return render_template("preview.html", **dados)


@app.route('/download/<recibo_num>')
def download(recibo_num):
    dados = request.args.to_dict()
    valor_liquido = float(dados['valor_liquido'])

    valores = calcular_valores_finais(valor_liquido, dados.get('forcar_irpf', 'off') == 'on')

    base = valores['base']
    inss = valores['inss']
    iss = valores['iss']
    irpf = valores['irpf']

    dados.update({
        'valor_bruto': f"{base:.2f}",
        'inss': f"{inss:.2f}",
        'iss': f"{iss:.2f}",
        'irpf': f"{irpf:.2f}",
        'recibo_num': recibo_num # Use the recibo_num from the URL
    })

    html = render_template("layout.html", **dados)

    with open('debug_html.html', 'w', encoding='utf-8') as f:
        f.write(html)

    pdf = pdfkit.from_string(html, False, configuration=config, options=options)

    return send_file(
        io.BytesIO(pdf),
        download_name=f"rpa_gerado_{recibo_num}.pdf",
        as_attachment=True
    )

@app.route('/teste/<valor>')
def teste_calculo(valor):
    valor_liquido = float(valor)
    resultados = calcular_valores_finais(valor_liquido, False)
    return {
        'valor_liquido': valor_liquido,
        'valor_bruto': f"R$ {resultados['base']:.2f}",
        'inss': f"R$ {resultados['inss']:.2f} ({(resultados['inss']/resultados['base']*100):.2f}%)",
        'iss': f"R$ {resultados['iss']:.2f} ({(resultados['iss']/resultados['base']*100):.2f}%)",
        'irpf': f"R$ {resultados['irpf']:.2f} ({(resultados['irpf']/resultados['base']*100):.2f}%)",
        'total_descontos': f"R$ {(resultados['inss'] + resultados['iss'] + resultados['irpf']):.2f}",
        'valor_liquido_calculado': f"R$ {(resultados['base'] - resultados['inss'] - resultados['iss'] - resultados['irpf']):.2f}"
    }

@app.template_filter('br_currency')
def br_currency(valor):
    try:
        return "{:,.2f}".format(float(valor)).replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return valor


# ... (restante do seu código) ...

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
