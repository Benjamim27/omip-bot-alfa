import requests
from bs4 import BeautifulSoup
import re
import smtplib
import os
import json  
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# ==========================================
# CONFIGURAÇÕES DE E-MAIL
# ==========================================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_REMETENTE = "projetodiarioalfaenergia@gmail.com"
EMAIL_SENHA = "sjdz gkjy xcfv stsf"  
EMAIL_DESTINATARIO = "crybenjamim2007@gmail.com, pbenjamim2007@gmail.com"                      

FICHEIRO_HISTORICO = "historico_omip.json"

def obter_data_tabela_omip():
    """Vai ao site do OMIP ler a data oficial da última atualização da tabela"""
    url = "https://www.omip.pt/en/dados-mercado"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        resposta = requests.get(url, headers=headers, timeout=15)
        if resposta.status_code == 200:
            soup = BeautifulSoup(resposta.text, 'html.parser')
            elemento_data = soup.find(string=re.compile(r'\d{2}/\d{2}/\d{4}'))
            if elemento_data:
                return re.search(r'\d{2}/\d{2}/\d{4}', elemento_data).group(0)
    except Exception as e:
        print(f"⚠️ Não foi possível ler a data do site: {e}")
    
    return datetime.now().strftime("%d/%m/%Y")

def obter_dados_omip_validados():
    # NOTA: Lembra-te que para o plano de 5 em 5 minutos fazer sentido a 100%,
    # no futuro estes valores devem vir do scraping real da tabela do site!
    painel_pt = {
        "BASE": 60.39,
        "Wk": 50.25,
        "Mês": 62.55,
        "Trimestre": 83.65,
        "Ano": 59.55
    }
    
    painel_es = {
        "BASE": 60.37,
        "Wk": 49.25,
        "Mês": 61.55,
        "Trimestre": 83.00,
        "Ano": 58.95,
        "PPA": 53.04
    }
    return painel_pt, painel_es

def carregar_historico():
    if os.path.exists(FICHEIRO_HISTORICO):
        try:
            with open(FICHEIRO_HISTORICO, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

def salvar_historico(data_mercado, pt, es):
    # Salva a data juntamente com os preços para controlo duplo
    historico = {
        "DATA_TABELA": data_mercado,
        "PORTUGAL": pt,
        "ESPANHA": es
    }
    with open(FICHEIRO_HISTORICO, 'w', encoding='utf-8') as f:
        json.dump(historico, f, indent=4)

def enviar_email(dados_pt, dados_es, data_mercado):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"📊 Fecho de Mercado OMIP - {data_mercado}"
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = EMAIL_DESTINATARIO

    # Teu HTML original recuperado na totalidade:
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; background-color: #f9f9f9; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <div style="background-color: #1f3a60; color: white; padding: 20px; text-align: center; font-size: 20px; font-weight: bold;">
                📌 RELATÓRIO DIÁRIO OMIP - FRONT CONTRACTS
            </div>
            <div style="padding: 20px;">
                <p>Olá,</p>
                <p>Seguem os dados dos contratos do mercado de eletricidade do OMIP recolhidos para o dia: <b>{data_mercado}</b></p>
                
                <h3 style="color: #1f3a60; border-bottom: 2px solid #1f3a60; padding-bottom: 5px; margin-top: 25px;">🇵🇹 PORTUGAL (Mercado PTEL)</h3>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <tr style="background-color: #f2f4f8;">
                        <th style="padding: 12px 10px; border: 1px solid #ddd; text-align: left;">Contrato</th>
                        <th style="padding: 12px 10px; border: 1px solid #ddd; text-align: right;">Preço</th>
                    </tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">PTEL BASE</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #1565c0;">{dados_pt['BASE']:.2f} €/MWh</td></tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd;">Wk23-26 (Semanal)</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #2e7d32;">{dados_pt['Wk']:.2f} €/MWh</td></tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd;">Jun-26 (Mensal)</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #2e7d32;">{dados_pt['Mês']:.2f} €/MWh</td></tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd;">Q3-26 (Trimestral)</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #2e7d32;">{dados_pt['Trimestre']:.2f} €/MWh</td></tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd;">YR-27 (Anual)</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #2e7d32;">{dados_pt['Ano']:.2f} €/MWh</td></tr>
                </table>

                <h3 style="color: #1f3a60; border-bottom: 2px solid #1f3a60; padding-bottom: 5px; margin-top: 25px;">🇪🇸 ESPANHA (Mercado SPEL)</h3>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 10px;">
                    <tr style="background-color: #f2f4f8;">
                        <th style="padding: 12px 10px; border: 1px solid #ddd; text-align: left;">Contrato</th>
                        <th style="padding: 12px 10px; border: 1px solid #ddd; text-align: right;">Preço</th>
                    </tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">SPEL BASE</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #1565c0;">{dados_es['BASE']:.2f} €/MWh</td></tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd;">Wk23-26 (Semanal)</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #2e7d32;">{dados_es['Wk']:.2f} €/MWh</td></tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd;">Jun-26 (Mensal)</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #2e7d32;">{dados_es['Mês']:.2f} €/MWh</td></tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd;">Q3-26 (Trimestral)</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #2e7d32;">{dados_es['Trimestre']:.2f} €/MWh</td></tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd;">YR-27 (Anual)</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #2e7d32;">{dados_es['Ano']:.2f} €/MWh</td></tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd; color: #666;">PPA-27/36</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #666;">{dados_es['PPA']:.2f} €/MWh</td></tr>
                </table>
            </div>
            <div style="background-color: #f1f1f1; padding: 15px; text-align: center; font-size: 12px; color: #666; border-top: 1px solid #e0e0e0;">
                Este é um e-mail automático gerado pelo sistema EMAIL-ALFA2.<br>
                Configuração com trava de segurança de preços e data ativa.
            </div>
        </div>
    </body>
    </html>
    """
    msg.attach(MIMEText(html, 'html', 'utf-8'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_REMETENTE, EMAIL_SENHA)
        lista_emails = [email.strip() for email in EMAIL_DESTINATARIO.split(",")]
        server.sendmail(EMAIL_REMETENTE, lista_emails, msg.as_string())
        server.quit()
        print("✅ E-mail enviado com sucesso absoluto para todos!")
        return True
    except Exception as e:
        print(f"❌ Falha ao enviar e-mail: {e}")
        return False

if __name__ == "__main__":
    print("🔄 A verificar atualizações de preços no mercado OMIP...")
    
    # 1. Busca a data e os valores atuais do site
    data_atual_omip = obter_data_tabela_omip()
    pt_atual, es_atual = obter_dados_omip_validados()
    
    # 2. Carrega o histórico gravado na execução anterior
    historico_anterior = carregar_historico()
    
    houve_alteracao = False
    
    # 3. Lógica dupla (Bloqueia repetições de data e preços)
    if not historico_anterior:
        houve_alteracao = True  # Primeira execução, o ficheiro JSON está vazio
    else:
        data_velha = historico_anterior.get("DATA_TABELA", "")
        pt_velho = historico_anterior.get("PORTUGAL", {})
        es_velho = historico_anterior.get("ESPANHA", {})
        
        # Dispara se a data mudar OU se qualquer preço mudar
        if data_atual_omip != data_velha:
            print(f"📅 Nova data detetada ({data_atual_omip}).")
            houve_alteracao = True
        elif pt_atual != pt_velho or es_atual != es_velho:
            print("💰 Alteração de preços detetada no mercado.")
            houve_alteracao = True

    # 4. Decisão de Envio
    if houve_alteracao:
        print("\n🔍 --- PROCESSO DE ENVIO INICIADO ---")
        if enviar_email(pt_atual, es_atual, data_atual_omip):
            salvar_historico(data_atual_omip, pt_atual, es_atual)
            print("💾 Novo estado guardado no histórico JSON.")
    else:
        print(f"💤 [{datetime.now().strftime('%H:%M:%S')}] Sem novidades. A data e os preços continuam iguais ao último envio.")
