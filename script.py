import requests
import re
import smtplib
import os
import json  
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import pytz  # 🌍 Biblioteca para controlar o fuso horário de Portugal

# ==========================================
# CONFIGURAÇÕES DE E-MAIL E PARÂMETROS
# ==========================================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_REMETENTE = "projetodiarioalfaenergia@gmail.com"
EMAIL_SENHA = "sjdz gkjy xcfv stsf"                      
EMAIL_DESTINATARIO = "crybenjamim2007@gmail.com, pbenjamim2007@gmail.com"                      

# 🧪 MODO DE TESTE (True = ignora o bloqueio matemático e envia e-mail/atualiza JSON sempre)
MODO_TESTE = True  

# 🎯 CORREÇÃO DE CAMINHO: Garante que encontra o JSON na pasta correta do GitHub
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
FICHEIRO_HISTORICO = os.path.join(DIRETORIO_ATUAL, "historico_omip.json")

def capturar_contrato_e_preco(texto, bloco_mercado, padrao_contrato):
    """Procura o nome exato do contrato e o seu respetivo preço no bloco do mercado"""
    match_bloco = re.search(rf"{bloco_mercado}.*?(?=Próximos Contratos|\Z)", texto, re.DOTALL | re.IGNORECASE)
    if not match_bloco:
        return "N/A", 0.0
        
    texto_bloco = match_bloco.group(0)
    padrao = rf"({padrao_contrato}).*?€\s*([\d.,]+)"
    match = re.search(padrao, texto_bloco, re.IGNORECASE)
    
    if match:
        nome_exato = match.group(1).strip()
        try:
            preco = float(match.group(2).replace(',', '.'))
            return nome_exato, preco
        except:
            return nome_exato, 0.0
            
    return "N/A", 0.0

def obter_dados_omip_validados():
    """Faz a leitura do texto corrido do site e organiza os blocos de Portugal, Espanha e os Futuros Solar"""
    url = "https://www.omip.pt/pt"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    painel_pt = {"BASE": ("PTEL BASE", 0.0), "Wk": ("Wk", 0.0), "Mês": ("Mês", 0.0), "Trimestre": ("Trimestre", 0.0), "Ano": ("Ano", 0.0)}
    painel_es = {"BASE": ("SPEL BASE", 0.0), "Wk": ("Wk", 0.0), "Mês": ("Mês", 0.0), "Trimestre": ("Trimestre", 0.0), "Ano": ("Ano", 0.0), "PPA": ("PPA", 0.0)}
    painel_solar = {"PPA_27_31": ("FTS PPA 27/31", 0.0), "PPA_27_36": ("FTS PPA 27/36", 0.0), "DIARIO": ("FTS D", 0.0), "WE": ("FTS WE", 0.0), "SEMANAL": ("FTS Wk", 0.0), "MENSAL": ("FTS M", 0.0), "TRIMESTRAL": ("FTS Q", 0.0), "ANUAL": ("FTS YR", 0.0)}
    
    try:
        resposta = requests.get(url, headers=headers, timeout=15)
        print(f"ℹ️ [HTTP STATUS] Código de resposta do OMIP: {resposta.status_code}")
        if resposta.status_code != 200:
            return painel_pt, painel_es, painel_solar
            
        texto_pagina = re.sub(r'<[^>]+>', ' ', resposta.text)
        texto_pagina = " ".join(texto_pagina.split())
        
        regex_wk, regex_mes, regex_trim, regex_ano, regex_ppa = r"Wk\d{2}-\d{2}", r"[A-Z][a-z]{2}-\d{2}", r"Q\d-\d{2}", r"YR-\d{2}", r"PPA-\d{2}/\d{2}"
        regex_sol_ppa1, regex_sol_ppa2, regex_sol_diario, regex_sol_we, regex_sol_wk, regex_sol_mes, regex_sol_trim, regex_sol_ano = r"FTS\s+PPA\s+27/31", r"FTS\s+PPA\s+27/36", r"FTS\s+D\s+\S+", r"FTS\s+WE\s+\S+", r"FTS\s+Wk\d{2}-\d{2}", r"FTS\s+M\s+[A-Z][a-z]{2}-\d{2}", r"FTS\s+Q\d-\d{2}", r"FTS\s+YR-\d{2}"

        _, p_base = capturar_contrato_e_preco(texto_pagina, "PTEL BASE", "PTEL BASE")
        n_wk, p_wk = capturar_contrato_e_preco(texto_pagina, "PTEL BASE", regex_wk)
        n_mes, p_mes = capturar_contrato_e_preco(texto_pagina, "PTEL BASE", regex_mes)
        n_trim, p_trim = capturar_contrato_e_preco(texto_pagina, "PTEL BASE", regex_trim)
        n_ano, p_ano = capturar_contrato_e_preco(texto_pagina, "PTEL BASE", regex_ano)
        painel_pt.update({"BASE": ("PTEL BASE", p_base), "Wk": (n_wk, p_wk), "Mês": (n_mes, p_mes), "Trimestre": (n_trim, p_trim), "Ano": (n_ano, p_ano)})

        _, p_base_es = capturar_contrato_e_preco(texto_pagina, "SPEL BASE", "SPEL BASE")
        n_wk_es, p_wk_es = capturar_contrato_e_preco(texto_pagina, "SPEL BASE", regex_wk)
        n_mes_es, p_mes_es = capturar_contrato_e_preco(texto_pagina, "SPEL BASE", regex_mes)
        n_trim_es, p_trim_es = capturar_contrato_e_preco(texto_pagina, "SPEL BASE", regex_trim)
        n_ano_es, p_ano_es = capturar_contrato_e_preco(texto_pagina, "SPEL BASE", regex_ano)
        n_ppa_es, p_ppa_es = capturar_contrato_e_preco(texto_pagina, "SPEL BASE", regex_ppa)
        painel_es.update({"BASE": ("SPEL BASE", p_base_es), "Wk": (n_wk_es, p_wk_es), "Mês": (n_mes_es, p_mes_es), "Trimestre": (n_trim_es, p_trim_es), "Ano": (n_ano_es, p_ano_es), "PPA": (n_ppa_es, p_ppa_es)})

        bloco_solar = "SPEL Solar Futures"
        painel_solar["PPA_27_31"] = capturar_contrato_e_preco(texto_pagina, bloco_solar, regex_sol_ppa1)
        painel_solar["PPA_27_36"] = capturar_contrato_e_preco(texto_pagina, bloco_solar, regex_sol_ppa2)
        painel_solar["DIARIO"] = capturar_contrato_e_preco(texto_pagina, bloco_solar, regex_sol_diario)
        painel_solar["WE"] = capturar_contrato_e_preco(texto_pagina, bloco_solar, regex_sol_we)
        painel_solar["SEMANAL"] = capturar_contrato_e_preco(texto_pagina, bloco_solar, regex_sol_wk)
        painel_solar["MENSAL"] = capturar_contrato_e_preco(texto_pagina, bloco_solar, regex_sol_mes)
        painel_solar["TRIMESTRAL"] = capturar_contrato_e_preco(texto_pagina, bloco_solar, regex_sol_trim)
        painel_solar["ANUAL"] = capturar_contrato_e_preco(texto_pagina, bloco_solar, regex_sol_ano)

    except Exception as e:
        print(f"⚠️ Erro crítico na requisição ao OMIP: {e}")
        
    return painel_pt, painel_es, painel_solar

def carregar_historico():
    if os.path.exists(FICHEIRO_HISTORICO):
        try:
            with open(FICHEIRO_HISTORICO, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Erro ao ler JSON existente: {e}")
    return {}

def salvar_historico(data_envio, pt, es, solar):
    try:
        historico = {"DATA_ENVIO": data_envio, "PORTUGAL": pt, "ESPANHA": es, "SOLAR": solar}
        with open(FICHEIRO_HISTORICO, 'w', encoding='utf-8') as f:
            json.dump(historico, f, indent=4)
        print(f"💾 Sucesso: Ficheiro guardado em {FICHEIRO_HISTORICO}")
    except Exception as e:
        print(f"❌ Erro gravíssimo ao escrever no ficheiro JSON: {e}")

def extrair_apenas_precos(painel):
    return {chave: valor[1] for chave, valor in painel.items()}

def enviar_email(dados_pt, dados_es, dados_solar, data_envio):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"📊 Atualização de Mercado OMIP - {data_envio}"
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = EMAIL_DESTINATARIO

    linhas_solar = ""
    for chave, (nome, preco) in dados_solar.items():
        if nome != "N/A" and preco > 0.0:
            linhas_solar += f"<tr><td style='padding: 10px; border: 1px solid #ddd; font-weight: bold; color: #d35400;'>✨ {nome}</td><td style='padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #d35400;'>{preco:.2f} €/MWh</td></tr>"
    
    if not linhas_solar:
        linhas_solar = "<tr><td colspan='2' style='padding: 10px; text-align: center; color: #999;'>Nenhum contrato solar ativo no momento</td></tr>"

    html = f"<html><body><h2>📌 RELATÓRIO OMIP - {data_envio}</h2><table border='1'>{linhas_solar}</table></body></html>"
    msg.attach(MIMEText(html, 'html', 'utf-8'))

    try:
        print("🔌 A ligar ao servidor SMTP da Google...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15)
        server.starttls()
        print("🔑 A efetuar login com as credenciais...")
        server.login(EMAIL_REMETENTE, EMAIL_SENHA)
        lista_emails = [email.strip() for email in EMAIL_DESTINATARIO.split(",")]
        server.sendmail(EMAIL_REMETENTE, lista_emails, msg.as_string())
        server.quit()
        print("✅ E-mail enviado com sucesso absoluto para todos!")
        return True
    except Exception as e:
        print(f"❌ Falha crítica no envio do e-mail (SMTP): {e}")
        return False

if __name__ == "__main__":
    print("🔄 A iniciar diagnóstico do sistema...")
    pt_atual, es_atual, solar_atual = obter_dados_omip_validados()
    
    print(f"📊 Preço PT Base Lido: {pt_atual['BASE'][1]} €")
    print(f"📊 Preço ES Base Lido: {es_atual['BASE'][1]} €")

    if pt_atual["BASE"][1] == 0.0 and es_atual["BASE"][1] == 0.0:
        print("⚠️ [BLOQUEIO ATIVO] Paragem imediata: O script não conseguiu extrair os preços do site (valores vieram a zero).")
        exit(0)

    historico_anterior = carregar_historico()
    houve_alteracao = True if not historico_anterior else MODO_TESTE
    
    fuso_lisboa = pytz.timezone("Europe/Lisbon")
    momento_verificacao = datetime.now(fuso_lisboa).strftime("%d/%m/%Y às %H:%M")

    if houve_alteracao:
        email_ok = enviar_email(pt_atual, es_atual, solar_atual, momento_verificacao)
        if email_ok:
            salvar_historico(momento_verificacao, pt_atual, es_atual, solar_atual)
        else:
            print("❌ O JSON não foi atualizado porque o envio do e-mail falhou primeiro.")
            
    exit(0)
