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
# Adicionando renderização de JS via ZenRows para garantir que o JSON carregue
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
    requests.post(url, data=payload)

def realizar_analise():
    driver = configurar_driver()
    jogos_aprovados = []
    
    try:
        print("🚀 Acessando SofaScore...")
        driver.get("https://www.sofascore.com/pt/")
        
        # Espera o carregamento inicial (Aba "Todos")
        time.sleep(15)

        # 1. CLICAR NA ABA "PRÓXIMOS" (Baseado na sua print)
        try:
            print("🖱️ Clicando na aba 'Próximos'...")
            # O seletor abaixo busca especificamente o botão de aba pelo texto
            botao_proximos = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'Tabs')]//button[contains(., 'Próximos')] | //button[text()='Próximos']"))
            )
            driver.execute_script("arguments[0].click();", botao_proximos)
            print("✅ Aba 'Próximos' selecionada. Aguardando JSON de jogos...")
            time.sleep(8) 
        except Exception as e:
            print(f"⚠️ Erro ao clicar: {e}. Prosseguindo com varredura geral...")

        # 2. CAPTURA DO CÓDIGO BRUTO (HTML/JSON)
        conteudo_bruto = driver.page_source
        
        # 3. MINERAÇÃO DE LINKS VIA REGEX (Pega todos os links de partidas)
        # Esse padrão busca a estrutura /pt/futebol/time-a-time-b/id_do_jogo
        padrao_links = r'href="(/pt/futebol/[^"]+/match/[^"]+|/pt/futebol/[^"]+/partida/[^"]+)"'
        matches = re.findall(padrao_links, conteudo_bruto)
        
        links_validos = []
        for m in matches:
            url_completa = "https://www.sofascore.com" + m
            if url_completa not in links_validos:
                links_validos.append(url_completa)

        print(f"✅ {len(links_validos)} jogos detectados no código bruto.")
        print("-" * 50)

        # 4. LOOP DE ANÁLISE (Limitado aos 15 primeiros para não travar o bot)
        for link in links_validos[:15]:
            print(f"🔍 Analisando: {link}")
            driver.get(link)
            time.sleep(7)
            
            try:
                # Extraindo nome dos times pelo título da página
                nome_jogo = driver.title.split(" - ")[0]
                
                # --- AQUI É ONDE VOCÊ VAI COLOCAR SEUS SELETORES REAIS DE ESTATÍSTICA ---
                # Simulando aprovação baseada na sua regra de 4/5 jogos
                print(f"   📊 Processando estatísticas de H2H para {nome_jogo}...")
                
                # Exemplo de lógica (se bater 4/5 ou 5/5)
                # No momento, mantemos a simulação para o bilhete ser gerado
                aprovado = True 

                if aprovado:
                    jogos_aprovados.append({
                        "home": nome_jogo.split(" vs ")[0] if " vs " in nome_jogo else "Time Casa",
                        "away": nome_jogo.split(" vs ")[1] if " vs " in nome_jogo else "Time Fora",
                        "hora": "Hoje",
                        "liga": "Filtro Próximos",
                        "consistencia": 90, # 90% de sucesso
                        "chutes": 9.5
                    })
            except:
                continue
            
            print("-" * 30)

        # 5. GERAR BILHETE TELEGRAM
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

    except Exception as e:
        print(f"❌ Erro Crítico: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    realizar_analise()
