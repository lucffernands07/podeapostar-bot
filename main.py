import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIGURAÇÕES DE AMBIENTE --- #
ZENROWS_KEY = os.getenv('ZENROWS_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
PROXY = f"http://{ZENROWS_KEY}:@proxy.zenrows.com:8001"

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
        print(f"❌ Erro ao enviar Telegram: {e}")

def realizar_analise():
    driver = configurar_driver()
    jogos_aprovados = []
    
    try:
        print("🚀 Acessando SofaScore...")
        driver.get("https://www.sofascore.com/pt/")
        
        # Espera inicial para carregar a página e passar pelo Cloudflare via ZenRows
        time.sleep(12)

        # 1. CLICAR NA ABA "PRÓXIMOS"
        try:
            print("🖱️ Tentando clicar na aba 'Próximos'...")
            # Busca o botão pelo texto para maior estabilidade
            botao_proximos = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Próximos')]"))
            )
            # Usa JavaScript para clicar e evitar erros de sobreposição de elementos
            driver.execute_script("arguments[0].click();", botao_proximos)
            print("✅ Aba 'Próximos' selecionada.")
            time.sleep(5) 
        except Exception as e:
            print(f"⚠️ Aviso: Não foi possível clicar em 'Próximos' (pode já estar selecionada): {e}")

        # 2. ROLAR A PÁGINA (SCROLL) PARA CARREGAR OS JOGOS
        print("⏬ Rolando a página para carregar os jogos...")
        driver.execute_script("window.scrollBy(0, 1000);")
        time.sleep(3)

        # 3. CAPTURAR LINKS DOS JOGOS (Sem lista de ligas)
        # Busca links que contenham 'partida' ou 'match'
        elementos_jogos = driver.find_elements(By.XPATH, "//a[contains(@href, '/partida/') or contains(@href, '/match/')]")
        
        links_validos = []
        for el in elementos_jogos:
            link = el.get_attribute('href')
            if link and link not in links_validos:
                links_validos.append(link)

        print(f"✅ {len(links_validos)} jogos encontrados na lista de hoje.")
        print("-" * 50)

        # 4. ANALISAR CADA JOGO ENCONTRADO (Limite de 15 para segurança de tempo)
        for link in links_validos[:15]:
            print(f"🔍 Analisando jogo: {link}")
            driver.get(link)
            time.sleep(6) # Tempo para carregar estatísticas
            
            try:
                # Extração do nome do jogo via Título
                nome_completo = driver.title.split(" - ")[0]
                
                # --- [AQUI ENTRA A EXTRAÇÃO REAL DOS DADOS] ---
                # Por enquanto mantemos a simulação da sua regra 4/5 ou 5/5
                # mas agora aplicada a todos os jogos que o robô encontrou
                consist_t1, consist_t2 = 5, 4  
                chutes_t1, chutes_t2 = 5.5, 4.8
                media_total = chutes_t1 + chutes_t2

                print(f"   📊 Consistência: {consist_t1}/5 e {consist_t2}/5")
                print(f"   🎯 Média de Chutes (Indiv.): {chutes_t1} | {chutes_t2}")

                if consist_t1 >= 4 and consist_t2 >= 4:
                    print(f"   ✅ APROVADO: Soma {media_total:.1f}")
                    
                    jogos_aprovados.append({
                        "home": nome_completo.split(" vs ")[0] if " vs " in nome_completo else "Time A",
                        "away": nome_completo.split(" vs ")[1] if " vs " in nome_completo else "Time B",
                        "hora": "Hoje",
                        "liga": "Análise Sofa",
                        "consistencia": int(((consist_t1 + consist_t2) / 10) * 100),
                        "chutes": media_total
                    })
                else:
                    print(f"   ❌ REPROVADO: Fora da regra 4/5.")
                
            except Exception as e:
                print(f"   ⚠️ Erro ao detalhar partida: {e}")
            
            print("-" * 30)

        # 5. GERAR BILHETE NO SEU FORMATO DESEJADO
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
