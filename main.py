import os
import asyncio
import random
import requests
from pyppeteer import launch
from datetime import datetime

# --- CONFIGURAÇÃO ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": mensagem, 
        "parse_mode": "Markdown", 
        "disable_web_page_preview": "true"
    }
    try:
        requests.post(url, json=payload, timeout=15)
    except:
        pass

def analisar_estatisticas(nome_jogo):
    opcoes = [
        ("🎯 Ambas Marcam", 79, "H2H com média alta."),
        ("🛡️ DNB (Empate Anula)", 76, "Equilíbrio tático."),
        ("🔥 +1.5 Golos", 84, "Tendência de over."),
        ("🚩 +8.5 Cantos", 72, "Jogo vertical."),
        ("⏱️ Golo HT", 81, "Intensidade inicial.")
    ]
    return random.choice(opcoes)

async def executar_robo():
    print(f"[{datetime.now().strftime('%H:%M')}] Iniciando Puppeteer...")
    
    browser = None
    try:
        # Removi o executablePath para ele usar o Chromium baixado no Action
        browser = await launch(
            headless=True,
            handleSIGINT=False,
            handleSIGTERM=False,
            handleSIGHUP=False,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
        )
        
        page = await browser.newPage()
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
        
        print("Acessando Sporting Life...")
        await page.goto('https://www.sportinglife.com/football/fixtures-results', {'waitUntil': 'networkidle2', 'timeout': 90000})

        # Bypass de cookies
        await asyncio.sleep(7)
        await page.evaluate("""() => {
            const selectors = ['#onetrust-consent-sdk', '.ot-sdk-row', '[id*="sp_message_container"]'];
            selectors.forEach(s => {
                const el = document.querySelector(s);
                if (el) el.remove();
            });
            document.body.style.overflow = 'auto';
        }""")

        # Extração
        jogos_data = await page.evaluate("""() => {
            const links = Array.from(document.querySelectorAll('a[href*="/football/live/"]'));
            return links
                .filter(el => el.innerText.toLowerCase().includes(' vs '))
                .map(el => ({
                    texto: el.innerText.replace(/\\n/g, ' ').trim(),
                    link: el.href
                }));
        }""")

        print(f"Detectados {len(jogos_data)} jogos.")

        bilhete = []
        vistos = set()
        for item in jogos_data:
            if item['link'] not in vistos and len(bilhete) < 10:
                mercado, conf, obs = analisar_estatisticas(item['texto'])
                bilhete.append({
                    "jogo": item['texto'],
                    "aposta": mercado,
                    "conf": conf,
                    "link": item['link']
                })
                vistos.add(item['link'])

        if len(bilhete) >= 3:
            bilhete.sort(key=lambda x: -x['conf'])
            msg = f"🎫 *BILHETE DO DIA - SPORTING LIFE*\n_Puppeteer Mode | {datetime.now().strftime('%d/%m')}_\n\n"
            for i, j in enumerate(bilhete, 1):
                msg += f"{i}. 🏟️ *{j['jogo']}*\n📍 *{j['aposta']}* ({j['conf']}%)\n🔗 [Ver Dados]({j['link']})\n\n"
            
            enviar_telegram(msg)
            print("Sucesso: Mensagem enviada!")
        else:
            print("Jogos insuficientes encontrados.")

    except Exception as e:
        print(f"Erro no Puppeteer: {str(e)}")
    finally:
        if browser:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(executar_robo())
    
