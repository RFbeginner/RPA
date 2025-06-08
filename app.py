from flask import Flask, render_template, request, send_file, redirect, url_for
import pdfkit
import io
import os

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

COUNTER_FILE = 'recibo_counter.txt'

def get_next_recibo_number():
    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, 'r') as f:
            content = f.read().strip()
            if content:
                current_number = int(content)
            else:
                current_number = 0
    else:
        current_number = 0
    next_number = current_number + 1
    with open(COUNTER_FILE, 'w') as f:
        f.write(str(next_number))
    return next_number

def calcular_irpf(base):
    # Cálculo progressivo CORRETO do IRPF
    if base <= 1903.98:
        return 0.0
    elif base <= 2826.65:
        return base * 0.075 - 142.80
    elif base <= 3751.05:
        return base * 0.15 - 354.80
    elif base <= 4664.68:
        return base * 0.225 - 636.13
    else:
        return base * 0.275 - 869.36
    imposto = 0
    for faixa, aliquota in faixas:
        if base <= faixa:
            imposto += base * aliquota
            break
        else:
            imposto += faixa * aliquota
            base -= faixa
    return imposto

# Adicione esta função auxiliar para evitar duplicação
def calcular_valores_finais(valor_liquido, forcar_irpf=False):
    # Mesma lógica de cálculo da rota principal
    base = valor_liquido / (1 - 0.11 - 0.02)
    inss = base * 0.11
    iss = base * 0.02
    irpf = 0.0

    if forcar_irpf or base > 1903.98:
        for _ in range(3):
            irpf = calcular_irpf(base)
            base_nova = (valor_liquido + inss + iss + irpf) / (1 - 0.11 - 0.02)
            if abs(base_nova - base) < 0.01:
                break
            base = base_nova
            inss = base * 0.11
            iss = base * 0.02

    return {
        'base': base,
        'inss': inss,
        'iss': iss,
        'irpf': irpf
    }

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        dados = request.form.to_dict()
        valor_liquido = float(dados['valor_liquido'])
        forcar_irpf = 'forcar_irpf' in dados and dados['forcar_irpf'] == 'on'

        # Calcular valores finais usando a função auxiliar
        resultados = calcular_valores_finais(valor_liquido, forcar_irpf)

        # Atualizar dados
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
        'recibo_num': get_next_recibo_number()
    })
    return render_template("preview.html", **dados)

@app.route('/download/<recibo_num>')
def download(recibo_num):
    dados = request.args.to_dict()
    valor_liquido = float(dados['valor_liquido'])
    
    base = valor_liquido / (1 - 0.11 - 0.02)
    irpf = 0.0
    if float(dados.get('irpf', 0)) > 0 or ('forcar_irpf' in dados and dados['forcar_irpf'] == 'on'):
        base = valor_liquido / (1 - 0.11 - 0.02 - 0.075)
        irpf = calcular_irpf(base)
    
    inss = base * 0.11
    iss = base * 0.02
    
    valor_liquido_calculado = base - inss - iss - irpf
    tolerancia = 0.01
    if abs(valor_liquido_calculado - valor_liquido) > tolerancia:
        diferenca = valor_liquido - valor_liquido_calculado
        iss += diferenca * 0.3
        inss += diferenca * 0.7

    dados.update({
        'valor_bruto': f"{base:.2f}",
        'inss': f"{inss:.2f}",
        'iss': f"{iss:.2f}",
        'irpf': f"{irpf:.2f}",
        'recibo_num': recibo_num
    })

    html = render_template("layout.html", **dados)
    print("HTML gerado (primeiros 500 caracteres):", html[:500])

    with open('debug_html.html', 'w', encoding='utf-8') as f:
        f.write(html)

    pdf = pdfkit.from_string(html, False, configuration=config, options=options)

    return send_file(
        io.BytesIO(pdf),
        download_name=f"rpa_gerado_{recibo_num}.pdf",
        as_attachment=True
    )

if __name__ == '__main__':
    app.run(debug=True)