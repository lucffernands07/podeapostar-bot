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

# Ligas alvo
COMPETICOES = {
    "Champions League": "https://www.flashscore.com.br/futebol/europa/liga-dos-campeoes/",
    "Libertadores": "https://www.flashscore.com.br/futebol/america-do-sul/copa-libertadores/",
    "Sul-Americana": "https://www.flashscore.com.br/futebol/america-do-sul/copa-sul-americana/"
}

def enviar_telegram(mensagem):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    if not token or not chat_id: 
        print("Erro: TELEGRAM_TOKEN ou CHAT_ID não configurados.")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": mensagem, "parse_mode": "Markdown"})

def configurar_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def main():
    driver = configurar_driver()
    # Cabeçalho com a data de hoje (8 de Abril de 2026)
    lista_final = f"🏆 *Jogos de Hoje - {datetime.now().strftime('%d/%m/%Y')}*\n\n"
    
    try:
        for nome_comp, url in COMPETICOES.items():
            print(f"Buscando: {nome_comp}...")
            driver.get(url)
            time.sleep(8)

            # Força o clique na aba PRÓXIMOS via JavaScript
            try:
                driver.execute_script("""
                    var tabs = document.querySelectorAll('.tabs__tab');
                    for(var t of tabs){
                        if(t.innerText.includes('PRÓXIMOS')){ t.click(); }
                    }
                """)
                time.sleep(5)
            except:
                pass

            # Captura o texto bruto da página
            corpo_texto = driver.find_element(By.TAG_NAME, "body").text
            linhas = corpo_texto.split('\n')
            
            secao_adicionada = False
            for i in range(len(linhas)):
                # Busca padrão de horário (Ex: 16:00 ou 21:30)
                if re.match(r'^\d{2}:\d{2}$', linhas[i]):
                    try:
                        horario_utc = linhas[i]
                        time1 = linhas[i+1]
                        time2 = linhas[i+2]
                        
                        # Ignora lixo ou jogos que já têm placar/ao vivo
                        if any(x in time1.upper() for x in ['PREVIEW', 'LIVE', 'AO VIVO']): continue
                        if len(time1) < 3 or len(time2) < 3: continue

                        # Converte UTC para Brasília (UTC-3)
                        h_obj = datetime.strptime(horario_utc, "%H:%M")
                        h_br = (h_obj - timedelta(hours=3)).strftime("%H:%M")
                        
                        if not secao_adicionada:
                            lista_final += f"--- {nome_comp} ---\n"
                            secao_adicionada = True
                        
                        lista_final += f"🕒 `{h_br}` | *{time1} x {time2}*\n"
                    except:
                        continue

            if secao_adicionada:
                lista_final += "\n"

        # Verifica se algo foi encontrado antes de enviar
        if "🕒" in lista_final:
            enviar_telegram(lista_final)
            print("Lista enviada com sucesso!")
        else:
            enviar_telegram("⚠️ Nenhum jogo pendente encontrado para hoje nas ligas selecionadas.")

    except Exception as e:
        print(f"Erro geral: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
            
