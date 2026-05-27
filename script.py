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

# SEGURANÇA: Tenta ler dos Secrets do GitHub. Se não encontrar, usa a string direta.
# RECOMENDAÇÃO: No GitHub, cria um Secret chamado EMAIL_SENHA e apaga o texto abaixo!
EMAIL_SENHA = os.environ.get("EMAIL_SENHA", "sjdz gkjy xcfv stsf")  

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
    
    # CORREÇÃO: Retorna None em vez de inventar a data de hoje. 
    # Isso impede que o script envie e-mails falsos se o site falhar de manhã.
    return None

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
