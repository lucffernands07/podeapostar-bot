import os
import time
import re
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import telebot

# 🟢 NOVOS IMPORTS PARA O SEU DRIVER
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

try:
    import ligas
except ModuleNotFoundError:
    print("❌ Arquivo ligas.py não encontrado. Certifique-se de que ele está na raiz.")
    raise

# --- CONFIGURAÇÃO DO AMBIENTE ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

bot = telebot.TeleBot(TELEGRAM_TOKEN) if TELEGRAM_TOKEN else None
usuario_odds_teste = {}

LIGAS_SUREBET_ELITE = [
    #"Brasileirão Série A", 
    #"Copa do Brasil", 
    #"Libertadores", 
    #"Sul-Americana",
    #"Argentina - Liga Profesional", 
    "Mundo - Copa do Mundo"
    #"Europa - Champions League",
    #"Inglaterra - Premier League", 
    #"Espanha - LaLiga", 
    #"Alemanha - Bundesliga",
    #"Italia - Serie A", 
    #"França - Ligue 1", 
    #"Inglaterra - FA Cup",
    #"Espanha - Copa del Rey", 
    #"Alemanha - DFB Pokal",
    #"Argentina - Copa"
]

# =====================================================================
# 🌐 CONFIGURAÇÃO DO SEU DRIVER PADRÃO
# =====================================================================
def configurar_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(30) 
    driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "UTC"})
    return driver

# =====================================================================
# 📊 RASPAGEM APENAS DE CHUTES NO GOL (FASE 2)
# =====================================================================

def extrair_chutes_no_gol_por_aba(driver, url_base, mid_param, dicionario_escudos, acumulador_scouts):
    url_final = f"{url_base}/resumo/estatisticas-jogadores/finalizacoes/?mid={mid_param}"
    try:
        driver.get(url_final)
        time.sleep(3.5)
        
        termos_busca = ["ALVO", "TARGET", "NO GOL"]
        
        cabecalhos = driver.find_elements(By.CSS_SELECTOR, "th, [data-testid='wcl-tableHeadCell'], .wcl-tableHeadCell_")
        indice_alvo = -1
        for idx, th in enumerate(cabecalhos):
            txt = th.text.strip().upper()
            if any(x in txt for x in termos_busca) and not any(x in txt for x in ["XG", "XGOT", "COMETIDAS"]):
                indice_alvo = idx
                break
        
        if indice_alvo == -1:
            indice_alvo = 5

        linhas = driver.find_elements(By.CSS_SELECTOR, "tr[class*='row'], tr, .wcl-table__row_, [data-testid='wcl-tableRow']")
        
        for linha in linhas:
            try:
                celula_jogador = linha.find_element(By.CSS_SELECTOR, "td[class*='isSticky'], td[class*='fitContent'], [data-testid='wcl-playerCell']")
                nome_jogador = celula_jogador.find_element(By.CSS_SELECTOR, "[class*='fp-playerName'], [class*='playerName']").text.strip()
                
                if not nome_jogador or nome_jogador == "TODOS": 
                    continue
                
                img_logo = celula_jogador.find_element(By.CSS_SELECTOR, "div[class*='wcl-teamLogo'] img, div.wcl-teamLogo_sFhMr img")
                src_linha = img_logo.get_attribute("src") or ""
                arquivo_linha = src_linha.split('/')[-1] if src_linha else ""
                
                time_real = dicionario_escudos.get(arquivo_linha, "DESCONHECIDO")
                if time_real == "DESCONHECIDO": 
                    continue
                
                celulas = linha.find_elements(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell'], .wcl-tableBodyCell_")
                if len(celulas) > indice_alvo:
                    valor_txt = celulas[indice_alvo].text.strip()
                    qtd = int(valor_txt) if valor_txt.isdigit() else 0
                    
                    if qtd > 0:
                        if nome_jogador not in acumulador_scouts:
                            acumulador_scouts[nome_jogador] = {"time": time_real, "chutes": 0, "c_jogos": 0}
                        
                        acumulador_scouts[nome_jogador]["chutes"] += qtd
                        acumulador_scouts[nome_jogador]["c_jogos"] += 1
            except:
                continue
    except:
        pass

def pegar_scouts_chutes_somente(driver, url_h2h_mae):
    driver.get(url_h2h_mae)
    time.sleep(4.0)
    
    dicionario_escudos = {}
    links_jogos_historico = set()
    acumulador_scouts = {}
    
    secoes_h2h = driver.find_elements(By.CSS_SELECTOR, ".h2h__section, [class*='h2h__section']")
    for bloco in secoes_h2h[:2]:
        linhas_jogos = bloco.find_elements(By.CSS_SELECTOR, "a.h2h__row, [class*='h2h__row']")
        for linha_jogo in linhas_jogos[:5]:
            href = linha_jogo.get_attribute("href")
            if href: 
                links_jogos_historico.add(href)
            
            participantes = linha_jogo.find_elements(By.CSS_SELECTOR, "[class*='wcl-matchRow-participant'], .h2h__participant")
            for p in participantes:
                try:
                    img_el = p.find_element(By.CSS_SELECTOR, "img")
                    src_img = img_el.get_attribute("src") or ""
                    nome_arquivo = src_img.split('/')[-1]
                    nome_time = p.text.strip().upper()
                    if nome_arquivo and nome_time and nome_arquivo not in dicionario_escudos:
                        dicionario_escudos[nome_arquivo] = nome_time
                except:
                    continue
        
    lista_final_links = list(links_jogos_historico)[:10]

    for url_jogo in lista_final_links:
        if "?mid=" in url_jogo:
            parts = url_jogo.split("?mid=")
            url_base = parts[0].rstrip('/')
            mid_param = parts[1]
        else:
            url_base = url_jogo.split("/#")[0].rstrip('/')
            mid_param = ""

        extrair_chutes_no_gol_por_aba(driver, url_base, mid_param, dicionario_escudos, acumulador_scouts)

    return acumulador_scouts

# =====================================================================
# ⚙️ MÉTODOS AUXILIARES E ENVIO
# =====================================================================

def pegar_odds_vitoria_topo(driver):
    try:
        wait = WebDriverWait(driver, 8)
        odds_elements = wait.until(EC.presence_of_all_elements_with_grid_cells(
            (By.CSS_SELECTOR, ".oddsValueInner, [class*='oddsValueInner']")
        ))
        if len(odds_elements) >= 3:
            odd_casa = float(odds_elements[0].text.strip().replace(",", "."))
            odd_fora = float(odds_elements[2].text.strip().replace(",", "."))
            return odd_casa, odd_fora
    except:
        pass
    return None, None

def enviar_telegram_surebet_nativo(mensagem, reply_markup_json=None):
    if not TELEGRAM_TOKEN or not CHANNEL_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": mensagem, "parse_mode": "Markdown", "disable_web_page_preview": True}
    if reply_markup_json:
        payload["reply_markup"] = reply_markup_json
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Erro Telegram: {e}")

def estruturar_e_enviar_bilhete(t1, t2, odd_c, odd_f, jogador_c, jogador_f):
    texto_mensagem = (
        "✅ **BILHETE SUREBET** ⚽\n\n"
        "🎟️ **Aposta 1**\n"
        f"🔶 Vitória: {t1}\n"
        f"🔶 Chutes no alvo: {jogador_c}\n\n"
        "🎟️ **Aposta 2**\n"
        f"🔶 Vitória: {t2}\n"
        f"🔶 Chutes no alvo: {jogador_f}\n"
        "---\n"
        "🌐 Betano\n\n"
        f"💡 *Odds Vitória Capturadas: {t1} ({odd_c:.2f}) | {t2} ({odd_f:.2f})*\n"
        "⚙️ *Ajuste os valores finais combinados abaixo para calcular as stakes:*"
    )
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("✏️ Odd Final Aposta 1", callback_data="def_odd1"),
        InlineKeyboardButton("✏️ Odd Final Aposta 2", callback_data="def_odd2"),
        InlineKeyboardButton("🧮 CALCULAR ENTRADAS", callback_data="calcular_stakes")
    )
    enviar_telegram_surebet_nativo(texto_mensagem, reply_markup_json=markup.to_json())

# =====================================================================
# 🔄 LOOP PRINCIPAL
# =====================================================================

def executar_busca_surebet():
    driver = configurar_driver()
    
    hoje_ref = datetime.now()
    amanha_no_site = (hoje_ref + timedelta(days=1)).strftime("%d.%m.")
    
    print("🚀 Iniciando varredura clonada do main.py (F1: Vitória | F2: Chutes)...")
    
    for nome_comp, url in ligas.COMPETICOES.items():
        if nome_comp.strip() not in LIGAS_SUREBET_ELITE:
            continue
            
        print(f"\n--- Analisando: {nome_comp} ---")
        
        try:
            driver.get(url)
            time.sleep(6)
            
            elementos_jogos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
            if not elementos_jogos:
                elementos_jogos = driver.find_elements(By.CSS_SELECTOR, "div[id^='g_1_']")
            
            print(f"📊 Total de elementos encontrados na página: {len(elementos_jogos)}")
            
            ids_jogos = []
            for el in elementos_jogos:
                try:
                    _id = el.get_attribute("id")
                    if _id:
                        ids_jogos.append(_id.split('_')[-1])
                except:
                    continue
            
            ids_jogos = list(dict.fromkeys(ids_jogos))
            
        except Exception as e:
            if "invalid session id" in str(e).lower() or "session" in str(e).lower():
                print("⚠️ Sessão do Chrome caiu! Reiniciando o navegador...")
                try: driver.quit()
                except: pass
                driver = configurar_driver() 
                driver.get(url)
                time.sleep(6)
                elementos_jogos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
                ids_jogos = [el.get_attribute("id").split('_')[-1] for el in elementos_jogos if el.get_attribute("id")]
            else:
                print(f"⚠️ Erro ao carregar liga {nome_comp}: {e}")
                continue

        # Processamento dos jogos encontrados na liga
        for id_jogo in ids_jogos:
            try:
                url_jogo = f"https://www.flashscore.com.br/jogo/{id_jogo}/#/resumo-de-jogo"
                
                # 🟢 LOG DO LINK SOLICITADO
                print(f"   🔗 Acessando: {url_jogo}")
                
                driver.get(url_jogo)
                time.sleep(3)
                
                t1_bruto = driver.find_element(By.CSS_SELECTOR, ".duelParticipant__home").text.strip()
                t2_bruto = driver.find_element(By.CSS_SELECTOR, ".duelParticipant__away").text.strip()
                
                t1 = t1_bruto.split('\n')[0].strip()
                t2 = t2_bruto.split('\n')[0].strip()
                
                # 🛑 FILTRO DE SEGURANÇA: IGNORAR ESPORTS, LONG PRAZO OU RANKINGS
                termos_esport = ["FIFA", "ELECTRONIC", "ESPORTS", "SIMULATED", "VENCEDOR", "AVANÇA", "AVANCA"]
                if any(x in t1_bruto.upper() or x in t2_bruto.upper() for x in termos_esport):
                    print(f"   🚫 [{t1} x {t2}]: Ignorado (Detetado eSports, mercado de Longo Prazo ou Simulados)")
                    continue
                
                # 1️⃣ FASE 1: VALIDAÇÃO DAS ODDS DE VITÓRIA
                odd_casa, odd_fora = pegar_odds_vitoria_topo(driver)
                
                if not odd_casa or not odd_fora:
                    print(f"   🚫 [{t1} x {t2}]: Ignorado (Odds 1X2 não disponíveis no topo)")
                    continue
                    
                if odd_casa < 1.70 or odd_fora < 1.70:
                    print(f"   🚫 [{t1} x {t2}]: Ignorado (Odds fora do padrão -> H: {odd_casa} | A: {odd_fora})")
                    continue
                    
                print(f"   🎯 [ODDS VITÓRIA OK] {t1} ({odd_casa:.2f}) x {t2} ({odd_fora:.2f}) -> Buscando H2H...")
                
                # 2️⃣ FASE 2: SCOUTS DE CHUTES NO ALVO
                url_h2h_mae = f"https://www.flashscore.com.br/jogo/{id_jogo}/#/h2h/overall"
                acumulador_scouts = pegar_scouts_chutes_somente(driver, url_h2h_mae)
                
                melhor_jogador_casa = None
                melhor_jogador_fora = None
                
                for jogador, dados in acumulador_scouts.items():
                    if dados["c_jogos"] > 0:
                        media_chutes = dados["chutes"] / dados["c_jogos"]
                        
                        if dados["time"].upper() == t1.upper() and media_chutes >= 2.0 and not melhor_jogador_casa:
                            melhor_jogador_casa = f"{jogador} 1+"
                        if dados["time"].upper() == t2.upper() and media_chutes >= 2.0 and not melhor_jogador_fora:
                            melhor_jogador_fora = f"{jogador} 1+"
                
                # 3️⃣ SINALIZAÇÃO
                if melhor_jogador_casa and melhor_jogador_fora:
                    print(f"   ✅ Par Surebet qualificado!")
                    estruturar_e_enviar_bilhete(t1, t2, odd_casa, odd_fora, melhor_jogador_casa, melhor_jogador_fora)
                else:
                    print(f"   ❌ [{t1} x {t2}]: Sem jogadores com média de chutes >= 2.0")
                    
            except Exception as e:
                print(f"   ⚠️ Erro no processamento do jogo {id_jogo}: {e}")
                continue
                
    driver.quit()

# =====================================================================
# 🤖 BOTÕES DO TELEGRAM (TELEBOT POLLING)
# =====================================================================
if bot:
    @bot.callback_query_handler(func=lambda call: True)
    def escutar_botoes_surebet(call):
        uid = call.from_user.id
        if uid not in usuario_odds_teste:
            usuario_odds_teste[uid] = {"odd1": 3.05, "odd2": 4.20}
            
        if call.data == "def_odd1":
            msg = bot.send_message(uid, "Digite a Odd Final Combinada da **Aposta 1**:")
            bot.register_next_step_handler(msg, lambda m: salvar_odd(m, "odd1"))
        elif call.data == "def_odd2":
            msg = bot.send_message(uid, "Digite a Odd Final Combinada da **Aposta 2**:")
            bot.register_next_step_handler(msg, lambda m: salvar_odd(m, "odd2"))
        elif call.data == "calcular_stakes":
            o1, o2 = usuario_odds_teste[uid]["odd1"], usuario_odds_teste[uid]["odd2"]
            banca_total = 90.00
            margem = (1 / o1) + (1 / o2)
            s1, s2 = banca_total / (margem * o1), banca_total / (margem * o2)
            
            texto_resultado = (
                "📊 **CÁLCULO DE STAKES**\n\n"
                f"💰 Investimento: R$ {banca_total:.2f}\n"
                "----------------------------\n"
                f"🔹 **Aposta 1 (Odd {o1:.2f}):** R$ {s1:.2f}\n"
                f"🔹 **Aposta 2 (Odd {o2:.2f}):** R$ {s2:.2f}\n"
                "----------------------------\n"
                f"🟢 **Lucro Garantido: +R$ {(s1*o1)-banca_total:.2f}**"
            )
            bot.send_message(call.message.chat.id, texto_resultado, parse_mode="Markdown")

    def salvar_odd(message, chave):
        try:
            usuario_odds_teste[message.from_user.id][chave] = float(message.text.replace(",", "."))
            bot.send_message(message.from_user.id, "✅ Odd salva!")
        except:
            bot.send_message(message.from_user.id, "❌ Valor inválido.")

if __name__ == "__main__":
    executar_busca_surebet()
    if bot and not os.getenv('GITHUB_ACTIONS'):
        print("🤖 Escutando interações locais do Telegram...")
        bot.infinity_polling()
    
