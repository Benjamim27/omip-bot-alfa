import requests
import re
import smtplib
import os
import json  
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta # 💡 Importado o timedelta para ajustar a hora

# ==========================================
# CONFIGURAÇÕES DE E-MAIL
# ==========================================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_REMETENTE = "projetodiarioalfaenergia@gmail.com"
EMAIL_SENHA = "sjdz gkjy xcfv stsf"                      
EMAIL_DESTINATARIO = "crybenjamim2007@gmail.com, pbenjamim2007@gmail.com"                      

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
    
    painel_pt = {
        "BASE": ("PTEL BASE", 0.0), "Wk": ("Wk", 0.0), "Mês": ("Mês", 0.0), "Trimestre": ("Trimestre", 0.0), "Ano": ("Ano", 0.0)
    }
    painel_es = {
        "BASE": ("SPEL BASE", 0.0), "Wk": ("Wk", 0.0), "Mês": ("Mês", 0.0), "Trimestre": ("Trimestre", 0.0), "Ano": ("Ano", 0.0), "PPA": ("PPA", 0.0)
    }
    
    # ☀️ Agora mapeamos todos os contratos da tabela Solar da imagem
    painel_solar = {
        "PPA_27_31": ("FTS PPA 27/31", 0.0),
        "PPA_27_36": ("FTS PPA 27/36", 0.0),
        "DIARIO": ("FTS D", 0.0),
        "WE": ("FTS WE", 0.0),
        "SEMANAL": ("FTS Wk", 0.0),
        "MENSAL": ("FTS M", 0.0),
        "TRIMESTRAL": ("FTS Q", 0.0),
        "ANUAL": ("FTS YR", 0.0)
    }
    
    try:
        resposta = requests.get(url, headers=headers, timeout=15)
        if resposta.status_code != 200:
            return painel_pt, painel_es, painel_solar
            
        texto_pagina = re.sub(r'<[^>]+>', ' ', resposta.text)
        texto_pagina = " ".join(texto_pagina.split())
        
        # Expressões Regulares Genéricas
        regex_wk = r"Wk\d{2}-\d{2}"
        regex_mes = r"[A-Z][a-z]{2}-\d{2}"
        regex_trim = r"Q\d-\d{2}"
        regex_ano = r"YR-\d{2}"
        regex_ppa = r"PPA-\d{2}/\d{2}"

        # Expressões específicas para a tabela Solar (captura o sufixo dinâmico das datas ex: We03Jun-26)
        regex_sol_ppa1 = r"FTS\s+PPA\s+27/31"
        regex_sol_ppa2 = r"FTS\s+PPA\s+27/36"
        regex_sol_diario = r"FTS\s+D\s+\S+"
        regex_sol_we = r"FTS\s+WE\s+\S+"
        regex_sol_wk = r"FTS\s+Wk\d{2}-\d{2}"
        regex_sol_mes = r"FTS\s+M\s+[A-Z][a-z]{2}-\d{2}"
        regex_sol_trim = r"FTS\s+Q\d-\d{2}"
        regex_sol_ano = r"FTS\s+YR-\d{2}"

        # 🇵🇹 PORTUGAL
        _, p_base = capturar_contrato_e_preco(texto_pagina, "PTEL BASE", "PTEL BASE")
        n_wk, p_wk = capturar_contrato_e_preco(texto_pagina, "PTEL BASE", regex_wk)
        n_mes, p_mes = capturar_contrato_e_preco(texto_pagina, "PTEL BASE", regex_mes)
        n_trim, p_trim = capturar_contrato_e_preco(texto_pagina, "PTEL BASE", regex_trim)
        n_ano, p_ano = capturar_contrato_e_preco(texto_pagina, "PTEL BASE", regex_ano)
        
        painel_pt["BASE"] = ("PTEL BASE", p_base)
        painel_pt["Wk"] = (n_wk, p_wk)
        painel_pt["Mês"] = (n_mes, p_mes)
        painel_pt["Trimestre"] = (n_trim, p_trim)
        painel_pt["Ano"] = (n_ano, p_ano)

        # 🇪🇸 ESPANHA
        _, p_base_es = capturar_contrato_e_preco(texto_pagina, "SPEL BASE", "SPEL BASE")
        n_wk_es, p_wk_es = capturar_contrato_e_preco(texto_pagina, "SPEL BASE", regex_wk)
        n_mes_es, p_mes_es = capturar_contrato_e_preco(texto_pagina, "SPEL BASE", regex_mes)
        n_trim_es, p_trim_es = capturar_contrato_e_preco(texto_pagina, "SPEL BASE", regex_trim)
        n_ano_es, p_ano_es = capturar_contrato_e_preco(texto_pagina, "SPEL BASE", regex_ano)
        n_ppa_es, p_ppa_es = capturar_contrato_e_preco(texto_pagina, "SPEL BASE", regex_ppa)
        
        painel_es["BASE"] = ("SPEL BASE", p_base_es)
        painel_es["Wk"] = (n_wk_es, p_wk_es)
        painel_es["Mês"] = (n_mes_es, p_mes_es)
        painel_es["Trimestre"] = (n_trim_es, p_trim_es)
        painel_es["Ano"] = (n_ano_es, p_ano_es)
        painel_es["PPA"] = (n_ppa_es, p_ppa_es)

        # ☀️ SPEL SOLAR FUTURES
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
        print(f"⚠️ Erro no processamento: {e}")
        
    return painel_pt, painel_es, painel_solar

def carregar_historico():
    if os.path.exists(FICHEIRO_HISTORICO):
        try:
            with open(FICHEIRO_HISTORICO, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

def salvar_historico(data_envio, pt, es, solar):
    historico = {"DATA_ENVIO": data_envio, "PORTUGAL": pt, "ESPANHA": es, "SOLAR": solar}
    with open(FICHEIRO_HISTORICO, 'w', encoding='utf-8') as f:
        json.dump(historico, f, indent=4)

def extrair_apenas_precos(painel):
    return {chave: valor[1] for chave, valor in painel.items()}

def enviar_email(dados_pt, dados_es, dados_solar, data_envio):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"📊 Atualização de Mercado OMIP - {data_envio}"
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = EMAIL_DESTINATARIO

    # Construção dinâmica das linhas da tabela de Solar
    linhas_solar = ""
    for chave, (nome, preco) in dados_solar.items():
        if nome != "N/A":
            linhas_solar += f"""
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold; color: #d35400;">✨ {nome}</td>
                <td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #d35400;">{preco:.2f} €/MWh</td>
            </tr>
            """

    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; background-color: #f9f9f9; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <div style="background-color: #1f3a60; color: white; padding: 20px; text-align: center; font-size: 20px; font-weight: bold;">
                📌 RELATÓRIO DE PREÇOS OMIP - NOVOS VALORES
            </div>
            <div style="padding: 20px;">
                <p>Olá,</p>
                <p>O sistema detetou novos preços de fecho no mercado do OMIP. Relatório gerado em: <b>{data_envio}</b></p>
                
                <h3 style="color: #e67e22; border-bottom: 2px solid #e67e22; padding-bottom: 5px; margin-top: 25px;">☀️ SPEL SOLAR FUTURES (Preços de Referência)</h3>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <tr style="background-color: #fdf5e6;">
                        <th style="padding: 12px 10px; border: 1px solid #ddd; text-align: left;">Contrato Solar</th>
                        <th style="padding: 12px 10px; border: 1px solid #ddd; text-align: right;">Preço</th>
                    </tr>
                    {linhas_solar}
                </table>

                <h3 style="color: #1f3a60; border-bottom: 2px solid #1f3a60; padding-bottom: 5px; margin-top: 25px;">🇵🇹 PORTUGAL (Mercado PTEL)</h3>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <tr style="background-color: #f2f4f8;">
                        <th style="padding: 12px 10px; border: 1px solid #ddd; text-align: left;">Contrato</th>
                        <th style="padding: 12px 10px; border: 1px solid #ddd; text-align: right;">Preço</th>
                    </tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">{dados_pt['BASE'][0]}</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #1565c0;">{dados_pt['BASE'][1]:.2f} €/MWh</td></tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd;">{dados_pt['Wk'][0]}</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #2e7d32;">{dados_pt['Wk'][1]:.2f} €/MWh</td></tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd;">{dados_pt['Mês'][0]}</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #2e7d32;">{dados_pt['Mês'][1]:.2f} €/MWh</td></tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd;">{dados_pt['Trimestre'][0]}</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #2e7d32;">{dados_pt['Trimestre'][1]:.2f} €/MWh</td></tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd;">{dados_pt['Ano'][0]}</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #2e7d32;">{dados_pt['Ano'][1]:.2f} €/MWh</td></tr>
                </table>

                <h3 style="color: #1f3a60; border-bottom: 2px solid #1f3a60; padding-bottom: 5px; margin-top: 25px;">🇪🇸 ESPANHA (Mercado SPEL)</h3>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 10px;">
                    <tr style="background-color: #f2f4f8;">
                        <th style="padding: 12px 10px; border: 1px solid #ddd; text-align: left;">Contrato</th>
                        <th style="padding: 12px 10px; border: 1px solid #ddd; text-align: right;">Preço</th>
                    </tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">{dados_es['BASE'][0]}</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #1565c0;">{dados_es['BASE'][1]:.2f} €/MWh</td></tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd;">{dados_es['Wk'][0]}</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #2e7d32;">{dados_es['Wk'][1]:.2f} €/MWh</td></tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd;">{dados_es['Mês'][0]}</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #2e7d32;">{dados_es['Mês'][1]:.2f} €/MWh</td></tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd;">{dados_es['Trimestre'][0]}</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #2e7d32;">{dados_es['Trimestre'][1]:.2f} €/MWh</td></tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd;">{dados_es['Ano'][0]}</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #2e7d32;">{dados_es['Ano'][1]:.2f} €/MWh</td></tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd; color: #666;">{dados_es['PPA'][0]}</td><td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #666;">{dados_es['PPA'][1]:.2f} €/MWh</td></tr>
                </table>
            </div>
            <div style="background-color: #f1f1f1; padding: 15px; text-align: center; font-size: 12px; color: #666; border-top: 1px solid #e0e0e0;">
                Este é um e-mail automático gerado pelo sistema EMAIL-ALFA2.<br>
                Bloqueio matemático ativo: O e-mail só é disparado se os valores dos preços mudarem.
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
    
    pt_atual, es_atual, solar_atual = obter_dados_omip_validados()
    
    # 🛑 TRAVA DE SEGURANÇA: Valida se o PTEL BASE ou pelo menos um contrato Solar relevante foi lido
    if pt_atual["BASE"][1] == 0.0 or solar_atual["ANUAL"][1] == 0.0:
        print("⚠️ [BLOQUEIO] O site do OMIP não devolveu preços válidos para o mercado a prazo ou Solar Futures.")
        print("✅ Execução controlada finalizada.")
        exit(0)

    historico_anterior = carregar_historico()
    houve_alteracao = False
    
    # 💡 ALTERAÇÃO EXCLUSIVA: Soma exatamente 1 hora ao tempo do servidor para corrigir o atraso
    momento_verificacao = (datetime.now() + timedelta(hours=1)).strftime("%d/%m/%Y às %H:%M")

    if not historico_anterior:
        houve_alteracao = True
    else:
        pt_velho = historico_anterior.get("PORTUGAL", {})
        es_velho = historico_anterior.get("ESPANHA", {})
        solar_velho = historico_anterior.get("SOLAR", {})
        
        precos_pt_atual = extrair_apenas_precos(pt_atual)
        precos_es_atual = extrair_apenas_precos(es_atual)
        precos_solar_atual = extrair_apenas_precos(solar_atual)
        
        precos_pt_velho = extrair_apenas_precos(pt_velho)
        precos_es_velho = extrair_apenas_precos(es_velho)
        precos_solar_velho = extrair_apenas_precos(solar_velho)
        
        # O disparo ocorre se houver mudança nos prazos ou em qualquer valor da tabela Solar
        if precos_pt_atual != precos_pt_velho or precos_es_atual != precos_es_velho or precos_solar_atual != precos_solar_velho:
            print("💰 Alteração real detetada nos preços de mercado!")
            houve_alteracao = True

    print("\n=============================================")
    print(f"🔍 VALORES PRINCIPAIS LIDOS NESTE MOMENTO (Hora Corrigida):")
    print(f"☀️ Solar Anual:  {solar_atual['ANUAL'][0]} -> {solar_atual['ANUAL'][1]}€")
    print(f"🇵🇹 Portugal:     {pt_atual['BASE'][0]} -> {pt_atual['BASE'][1]}€")
    print(f"🇪🇸 Espanha:      {es_atual['BASE'][0]} -> {es_atual['BASE'][1]}€")
    print("=============================================\n")

    if houve_alteracao:
        if enviar_email(pt_atual, es_atual, solar_atual, momento_verificacao):
            salvar_historico(momento_verificacao, pt_atual, es_atual, solar_atual)
            print("💾 Novo estado guardado no histórico JSON.")
    else:
        print("💤 Sem novidades. Os preços são exatamente iguais aos anteriores.")
        print("🚫 Envio de e-mail cancelado.")
        
    exit(0)
