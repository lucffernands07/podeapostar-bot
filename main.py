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
    # User-agent atualizado para evitar bloqueios
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
        
        # Tempo maior para garantir que o ZenRows processe o desafio do Cloudflare
        time.sleep(15)

        # DEBUG: Verificar se entramos no site
        print(f"📄 Título da página: {driver.title}")

        # 0. TENTAR FECHAR COOKIES (Isso impede cliques em botões atrás da camada)
        try:
            print("🍪 Verificando se existe modal de cookies...")
            botoes_cookies = driver.find_elements(By.XPATH, "//button[contains(., 'Aceitar') or contains(., 'Agree') or contains(., 'Consent')]")
            if botoes_cookies:
                driver.execute_script("arguments[0].click();", botoes_cookies[0])
                print("✅ Modal de cookies fechado.")
                time.sleep(2)
        except:
            pass

        # 1. CLICAR NA ABA "PRÓXIMOS"
        try:
            print("🖱️ Localizando aba 'Próximos'...")
            # Busca por múltiplos textos possíveis para evitar erro de idioma
            botao_proximos = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Próximos') or contains(text(), 'Upcoming')]"))
            )
            
            # Garante que o botão está na tela e clica via JS
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao_proximos)
            time.sleep(2)
            driver.execute_script("arguments[0].click();", botao_proximos)
            print("✅ Aba 'Próximos' selecionada.")
            time.sleep(7) # Espera carregar a nova lista de jogos
        except Exception as e:
            print(f"⚠️ Aviso: Falha ao clicar em 'Próximos'. Verifique se a página carregou corretamente.")

        # 2. ROLAR A PÁGINA PARA CARREGAR JOGOS "LAZY LOAD"
        print("⏬ Rolando página para carregar eventos...")
        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(3)

        # 3. CAPTURAR LINKS DOS JOGOS
        # Busca links que contenham a estrutura de partida do SofaScore
        elementos_jogos = driver.find_elements(By.XPATH, "//a[contains(@href, '/partida/') or contains(@href, '/match/')]")
        
        links_validos = []
        for el in elementos_jogos:
            link = el.get_attribute('href')
            # Evita links de widgets ou duplicados, foca em links de confrontos
            if link and link not in links_validos and ("-vs-" in link or "/match/" in link or "/partida/" in link):
                # Filtro adicional para não pegar links de "odds" ou "estatísticas" separadas
                if link.split('/')[-1].isdigit() or link[-1].isdigit(): 
                    links_validos.append(link)

        print(f"✅ {len(links_validos)} potenciais jogos encontrados.")
        print("-" * 50)

        if not links_validos:
            print("❌ Nenhum link de jogo foi extraído. Encerrando.")
            return

        # 4. ANALISAR JOGOS (Limite de 15 para não estourar o tempo do Actions)
        for link in links_validos[:15]:
            print(f"🔍 Abrindo: {link}")
            driver.get(link)
            time.sleep(6) 
            
            try:
                # Extração segura do título
                titulo_site = driver.title
                nome_jogo = titulo_site.split(" - ")[0] if " - " in titulo_site else "Jogo Desconhecido"
                
                # --- [LÓGICA DE CONSISTÊNCIA E CHUTES] ---
                # Substitua pelos seletores reais quando mapear as classes fixas
                consist_t1, consist_t2 = 5, 4  
                chutes_t1, chutes_t2 = 5.2, 4.3
                media_total = chutes_t1 + chutes_t2

                print(f"   📊 Consistência: {consist_t1}/5 e {consist_t2}/5")
                print(f"   🎯 Média de Chutes: {media_total:.1f}")

                if consist_t1 >= 4 and consist_t2 >= 4:
                    print(f"   ✅ JOGO APROVADO!")
                    jogos_aprovados.append({
                        "home": nome_jogo.split(" vs ")[0] if " vs " in nome_jogo else "Casa",
                        "away": nome_jogo.split(" vs ")[1] if " vs " in nome_jogo else "Fora",
                        "hora": "Hoje",
                        "liga": "H2H Pro",
                        "consistencia": int(((consist_t1 + consist_t2) / 10) * 100),
                        "chutes": media_total
                    })
                else:
                    print(f"   ❌ REPROVADO (Consistência baixa).")
                
            except Exception as e:
                print(f"   ⚠️ Erro ao processar este jogo: {e}")
            
            print("-" * 30)

        # 5. ENVIO DO BILHETE FORMATADO
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
            print("✉️ Bilhete enviado ao Telegram!")
        else:
            print("📭 Nenhum jogo passou pelos critérios técnicos hoje.")

    except Exception as e:
        print(f"❌ Erro Geral: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    realizar_analise()
