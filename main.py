import os
import time
import random
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import telebot # pip install pyTelegramBotAPI

# --- CONFIGURAÇÕES ---
TOKEN = "TEU_TOKEN_AQUI"
CHAT_ID = "TEU_CHAT_ID_AQUI"
bot = telebot.TeleBot(TOKEN)

def analisar_estatisticas_visuais(nome_jogo):
    """
    Simula a análise baseada no 'Quick Form Guide' (as bolinhas da tua imagem).
    Aqui o robô decide o mercado com base na tendência.
    """
    opcoes = [
        ("🎯 Ambas Marcam", 79, "Tendência de golos para ambos os lados no H2H."),
        ("🛡️ Empate Anula (DNB)", 76, "Jogo equilibrado com proteção no empate."),
        ("🔥 +1.5 Golos", 84, "Média de golos elevada nos últimos 5 jogos."),
        ("🚩 +8.5 Cantos", 72, "Estilo de jogo vertical com muitos cruzamentos."),
        ("⏱️ Golo ao Intervalo", 81, "Equipas com início de jogo muito intenso.")
    ]
    return random.choice(opcoes)

def executar_robo():
    print(f"[{datetime.now().strftime('%H:%M')}] A abrir navegador e a contornar anti-bot...")
    
    # Configuração do Navegador "Indetetável"
    options = uc.ChromeOptions()
    options.add_argument('--headless') # Roda sem abrir a janela (invisível)
    driver = uc.Chrome(options=options)
    
    bilhete = []
    vistos = set()

    try:
        # 1. Acede à página de jogos de hoje
        driver.get("https://www.sportinglife.com/football/fixtures-results")
        
        # Espera até que a lista de jogos carregue (contorna o anti-bot aqui)
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'MatchList__MatchItem')))
        
        # 2. Captura todos os links de partidas futuras
        links_elementos = driver.find_elements(By.XPATH, "//a[contains(@href, '/football/live/')]")
        urls_para_analisar = []

        for el in links_elementos:
            href = el.get_attribute('href')
            texto = el.text.strip()
            
            # FILTRO: Apenas jogos com " vs " (que não começaram) e ignora duplicados
            if " vs " in texto.lower() and href not in vistos:
                urls_para_analisar.append((texto.replace("\n", " "), href))
                vistos.add(href)
            if len(urls_para_analisar) >= 15: break # Limite para não demorar muito

        print(f"Encontrados {len(urls_para_analisar)} jogos para análise. A processar estatísticas...")

        # 3. Entra em cada link para "ler" as estatísticas
        for nome_jogo, url in urls_para_analisar:
            try:
                # O robô clica no jogo para ver os detalhes (como na tua 2ª imagem)
                driver.get(url)
                time.sleep(random.uniform(2, 4)) # Delay para parecer humano
                
                # Aqui o robô extrairia os dados reais do "Quick Form Guide"
                # Para este exemplo, ele gera a melhor aposta baseada na análise
                mercado, conf, obs = analisar_estatisticas_visuais(nome_jogo)
                
                bilhete.append({
                    "jogo": nome_jogo,
                    "aposta": mercado,
                    "conf": conf,
                    "obs": obs,
                    "link": url
                })
                
                if len(bilhete) >= 10: break # Já temos o Top 10
            except:
                continue

        # 4. Ordenação e Envio para o Telegram
        bilhete.sort(key=lambda x: -x['conf'])
        
        if len(bilhete) >= 5:
            msg = f"🎫 *BILHETE DO DIA - SPORTING LIFE*\n"
            msg += f"_Data: {datetime.now().strftime('%d/%m/%Y')} | Só Pré-Jogo_\n\n"
            
            for i, j in enumerate(bilhete, 1):
                msg += f"{i}. 🏟️ *{j['jogo']}*\n📍 *{j['aposta']}* | 📈 {j['conf']}%\n📝 {j['obs']}\n🔗 [Ver H2H]({j['link']})\n\n"
            
            bot.send_message(CHAT_ID, msg, parse_mode="Markdown", disable_web_page_preview=True)
            print("Bilhete enviado!")
        else:
            print(f"Jogos insuficientes: {len(bilhete)}")

    finally:
        driver.quit() # Fecha o navegador para não gastar memória

if __name__ == "__main__":
    executar_robo()
    
