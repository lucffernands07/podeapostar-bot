import os
import time
import requests
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIGURAÇÕES DE AMBIENTE --- #
ZENROWS_KEY = os.getenv('ZENROWS_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
# js_render=true é obrigatório para carregar os seletores que você enviou
PROXY = f"http://{ZENROWS_KEY}:js_render=true@proxy.zenrows.com:8001"

def configurar_driver():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument(f'--proxy-server={PROXY}')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(options=options)

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"❌ Erro Telegram: {e}")

def realizar_analise():
    driver = configurar_driver()
    jogos_aprovados = []
    
    try:
        print("🚀 Acessando SofaScore...")
        driver.get("https://www.sofascore.com/pt/")
        time.sleep(15) 

        # 1. CLICAR NA ABA "PRÓXIMOS"
        try:
            print("🖱️ Localizando aba 'Próximos' conforme seletor...")
            # Busca o botão dentro da estrutura de abas que você enviou
            botao_proximos = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Próximos')]"))
            )
            driver.execute_script("arguments[0].click();", botao_proximos)
            print("✅ Aba 'Próximos' ativa. Aguardando lista de ligas (Serie A, LaLiga, etc)...")
            time.sleep(10) 
        except Exception as e:
            print(f"⚠️ Erro ao trocar para aba Próximos: {e}")

        # 2. ROLAGEM PARA CARREGAR OS BLOCOS DE LIGAS
        driver.execute_script("window.scrollBy(0, 1000);")
        time.sleep(3)

        # 3. EXTRAÇÃO DE LINKS (Usando a lógica de filtragem por padrão de partida)
        print("⏬ Minerando links de partidas dos cards...")
        conteudo_bruto = driver.page_source
        
        # Padrão Regex para capturar links de partidas (match) ou partidas (português)
        # Filtramos para pegar apenas links que levam ao confronto direto
        links_regex = re.findall(r'href="(/pt/futebol/[^"]+/(?:match|partida)/[^"]+)"', conteudo_bruto)
        
        links_validos = []
        for l in links_regex:
            url_completa = "https://www.sofascore.com" + l
            # Evita duplicados e links que não são de jogos (como links de torneios)
            if url_completa not in links_validos and "-vs-" in url_completa:
                links_validos.append(url_completa)

        print(f"✅ {len(links_validos)} confrontos encontrados para análise.")
        print("-" * 50)

        # 4. LOOP DE ANÁLISE DOS CONFRONTOS
        for link in links_validos[:15]:
            print(f"🔍 Analisando: {link.split('/')[-2]}")
            driver.get(link)
            time.sleep(8)
            
            try:
                # Captura nome dos times do título
                titulo_jogo = driver.title.split(" - ")[0]
                
                # --- ESPAÇO PARA SUA LÓGICA DE 4/5 OU 5/5 ---
                # Exemplo: Aqui você buscaria as "bolinhas" de V/E/D
                # Por enquanto, simulamos a aprovação para montar o bilhete
                
                consist_t1 = 5 # 5/5
                consist_t2 = 4 # 4/5
                media_chutes = 9.8

                if consist_t1 >= 4 and consist_t2 >= 4:
                    print(f"   ✅ JOGO APROVADO: {titulo_jogo}")
                    jogos_aprovados.append({
                        "home": titulo_jogo.split(" vs ")[0] if " vs " in titulo_jogo else "Casa",
                        "away": titulo_jogo.split(" vs ")[1] if " vs " in titulo_jogo else "Fora",
                        "hora": "Hoje",
                        "liga": "H2H Elite",
                        "consistencia": int(((consist_t1 + consist_t2)/10)*100),
                        "chutes": media_chutes
                    })
            except Exception as e:
                print(f"   ⚠️ Erro no processamento: {e}")
            
            print("-" * 30)

        # 5. MONTAGEM E ENVIO DO BILHETE
        if jogos_aprovados:
            bilhete = "🎯 **BILHETE DO DIA (SISTEMA H2H)**\n💰🍀 **BOA SORTE!!!**\n\n"
            for i, j in enumerate(jogos_aprovados, 1):
                bilhete += f"{i}. 🏟️ **{j['home']} x {j['away']}**\n"
                bilhete += f"🕒 {j['hora']} | {j['liga']}\n"
                bilhete += f"🔶 ⚽ +1.5 Gols ({j['consistencia']}%)\n"
                bilhete += f"💡 Média Chutes: ({j['chutes']:.1f})\n"
                bilhete += f"📊 Análise Sofa\n\n"
            
            bilhete += "---\n💸 Bet365 | Betano"
            enviar_telegram(bilhete)
            print("✉️ Bilhete enviado com sucesso!")
        else:
            print("📭 Nenhum jogo aprovado nos critérios hoje.")

    except Exception as e:
        print(f"❌ Erro Crítico: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    realizar_analise()
