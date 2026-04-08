import os
import time
import requests
import re
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

COMPETICOES = {
    "Champions League": "https://www.flashscore.com.br/futebol/europa/liga-dos-campeoes/",
    "Libertadores": "https://www.flashscore.com.br/futebol/america-do-sul/copa-libertadores/",
    "Sul-Americana": "https://www.flashscore.com.br/futebol/america-do-sul/copa-sul-americana/"
}

def enviar_telegram(mensagem):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    if not token or not chat_id: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": mensagem, "parse_mode": "Markdown"})

def configurar_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,3000")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def main():
    driver = configurar_driver()
    lista_final = f"🏆 *JOGOS DE HOJE - {datetime.now().strftime('%d/%m')}*\n\n"
    
    # Datas para controle de fuso
    agora_utc = datetime.now()
    hoje_str = agora_utc.strftime("%d.%m.")
    amanha_str = (agora_utc + timedelta(days=1)).strftime("%d.%m.")

    try:
        for nome_comp, url in COMPETICOES.items():
            driver.get(url)
            time.sleep(8)

            # Força o clique na aba PRÓXIMOS
            try:
                driver.execute_script("""
                    var abas = document.querySelectorAll('.tabs__tab');
                    for(var a of abas){
                        if(a.innerText.includes('PRÓXIMOS')){ a.click(); }
                    }
                """)
                time.sleep(5)
            except: pass

            # Extração via Texto Bruto (Método que achou a Champions)
            corpo_texto = driver.find_element(By.TAG_NAME, "body").text
            linhas = corpo_texto.split('\n')
            
            secao_adicionada = False
            for i in range(len(linhas)):
                # Busca padrão de horário (00:00)
                if re.match(r'^\d{2}:\d{2}$', linhas[i]):
                    try:
                        h_utc_str = linhas[i]
                        time1 = linhas[i+1]
                        time2 = linhas[i+2]

                        if "PREVIEW" in time1 or len(time1) < 3: continue

                        # Captura a data que o site exibe (se houver, ex: 08.04. 21:00)
                        # Se não houver data na linha, assume que é hoje
                        data_jogo = hoje_str
                        for j in range(max(0, i-2), i):
                            if re.search(r'\d{2}\.\d{2}\.', linhas[j]):
                                data_jogo = re.search(r'(\d{2}\.\d{2}\.)', linhas[j]).group(1)

                        # --- LÓGICA DE CORREÇÃO DO FUSO (O AJUSTE QUE SE PERDEU) ---
                        h_vazia = int(h_utc_str.split(':')[0])
                        
                        # Se for data de amanhã e hora < 3h UTC, é jogo de HOJE à noite no BR
                        if data_jogo == amanha_str:
                            if h_vazia >= 3: continue # Realmente é amanhã
                        elif data_jogo != hoje_str:
                            continue # É de outro dia bem distante

                        # Conversão para Horário de Brasília
                        h_obj = datetime.strptime(h_utc_str, "%H:%M")
                        h_br = (h_obj - timedelta(hours=3)).strftime("%H:%M")
                        
                        if not secao_adicionada:
                            lista_final += f"--- {nome_comp} ---\n"
                            secao_adicionada = True
                        
                        lista_final += f"🕒 `{h_br}` | *{time1} x {time2}*\n"
                    except: continue
            
            if secao_adicionada: lista_final += "\n"

        enviar_telegram(lista_final if "🕒" in lista_final else "⚠️ Nenhum jogo capturado com os novos filtros.")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
