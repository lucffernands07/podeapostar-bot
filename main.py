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

def salvar_log_debug(nome_comp, texto):
    """Salva o texto da página em um arquivo para o GitHub Actions fazer o upload"""
    filename = f"debug_{nome_comp.lower().replace(' ', '_')}.log"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"--- DEBUG LOG: {nome_comp} ---\n")
        f.write(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("-" * 50 + "\n")
        f.write(texto)
    print(f"Log salvo: {filename}")

def configurar_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def main():
    driver = configurar_driver()
    lista_final = "🏆 *Lista de Jogos (Verificação por Log)*\n\n"
    
    try:
        for nome_comp, url in COMPETICOES.items():
            driver.get(url)
            time.sleep(10)

            # Clique forçado na aba PRÓXIMOS
            try:
                driver.execute_script("""
                    var tabs = document.querySelectorAll('.tabs__tab');
                    for(var t of tabs){
                        if(t.innerText.includes('PRÓXIMOS')){ t.click(); }
                    }
                """)
                time.sleep(5)
            except Exception as e:
                print(f"Erro ao clicar na aba em {nome_comp}: {e}")

            # Captura o texto bruto para o LOG
            corpo_texto = driver.find_element(By.TAG_NAME, "body").text
            salvar_log_debug(nome_comp, corpo_texto)

            # Processamento básico para o Telegram não ir vazio
            linhas = corpo_texto.split('\n')
            secao_adicionada = False
            for i in range(len(linhas)):
                if re.match(r'^\d{2}:\d{2}$', linhas[i]):
                    try:
                        h_utc = linhas[i]
                        t1, t2 = linhas[i+1], linhas[i+2]
                        if "PREVIEW" in t1 or len(t1) < 3: continue
                        
                        h_br = (datetime.strptime(h_utc, "%H:%M") - timedelta(hours=3)).strftime("%H:%M")
                        if not secao_adicionada:
                            lista_final += f"--- {nome_comp} ---\n"
                            secao_adicionada = True
                        lista_final += f"🕒 `{h_br}` | *{t1} x {t2}*\n"
                    except: continue
            
            if secao_adicionada: lista_final += "\n"

        enviar_telegram(lista_final if "🕒" in lista_final else "⚠️ Nenhum jogo no texto bruto. Verifique os arquivos .log no Github.")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
            
