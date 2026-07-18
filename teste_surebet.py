import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import telebot

# --- SEUS IMPORTS EXISTENTES ---
import ligas          # Onde está o dicionário COMPETICOES
import scouts_avancado # Seu arquivo de scouts da Fase 2

# --- CONFIGURAÇÃO REAPROVEITADA DO SEU MAIN.PY ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')  # ID do Canal onde vão os bilhetes

# Inicializa o telebot apenas para ficar escutando e respondendo os botões (Polling)
bot = telebot.TeleBot(TELEGRAM_TOKEN) if TELEGRAM_TOKEN else None

# Dicionário temporário na memória para guardar as odds do cálculo das stakes
usuario_odds_teste = {}

# --- LISTA DE LIGAS ELITE SELECIONADAS ---
LIGAS_SUREBET_ELITE = [
    "Brasileirão Série A", "Copa do Brasil", "Libertadores", "Sul-Americana",
    "Argentina - Liga Profesional", "Mundo - Copa do Mundo", "Europa - Champions League",
    "Inglaterra - Premier League", "Espanha - LaLiga", "Alemanha - Bundesliga",
    "Italia - Serie A", "França - Ligue 1", "Europa - League", "Inglaterra - FA Cup",
    "Espanha - Copa del Rey", "Alemanha - DFB Pokal", "Arábia Saudita - King Cup",
    "EUA - MLS", "Argentina - Copa"
]

def enviar_telegram_surebet_nativo(mensagem, reply_markup_json=None):
    """ Envia o bilhete usando o mesmo método do seu main.py (requests) """
    if not TELEGRAM_TOKEN or not CHANNEL_ID:
        print("⚠️ Erro: TELEGRAM_TOKEN ou CHANNEL_ID não configurados nas variáveis de ambiente.")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID, 
        "text": mensagem,                 
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    # Adiciona os botões se eles forem passados
    if reply_markup_json:
        payload["reply_markup"] = reply_markup_json

    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Erro Telegram Surebet: {e}")

def pegar_odds_vitoria_topo(driver):
    """ Captura as odds de vitória (1x2) direto da tela de resumo do Flashscore """
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

def estruturar_e_enviar_bilhete(t1, t2, odd_c, odd_f, jogador_c, jogador_f):
    """ Monta o texto e os botões seguindo a API nativa do Telegram """
    texto_mensagem = (
        "✅ **BILHETE SUREBET** ⚽\n\n"
        "🎟️ **Aposta 1**\n"
        f"🔶 Classificação/Vitória: {t1}\n"
        f"🔶 Chutes no gol: {jogador_c}\n"
        f"🔶 Chutes no gol: {jogador_f}\n"
        "---\n"
        "🎟️ **Aposta 2**\n"
        f"🔶 Classificação/Vitória: {t2}\n"
        f"🔶 Chutes no gol: {jogador_c}\n"
        f"🔶 Chutes no gol: {jogador_f}\n"
        "---\n"
        "🌐 Betano\n"
        "📊 Estatísticas \n"
        "---\n"
        f"💡 *Odds Base Capturadas: {t1} ({odd_c:.2f}) | {t2} ({odd_f:.2f})*\n"
        "⚙️ *Ajuste os valores finais combinados abaixo para calcular as stakes:*"
    )
    
    # Criamos o markup usando o telebot e exportamos para JSON string (o requests exige string/json no reply_markup)
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("✏️ Odd Final Aposta 1", callback_data="def_odd1"),
        InlineKeyboardButton("✏️ Odd Final Aposta 2", callback_data="def_odd2"),
        InlineKeyboardButton("🧮 CALCULAR ENTRADAS", callback_data="calcular_stakes")
    )
    
    enviar_telegram_surebet_nativo(texto_mensagem, reply_markup_json=markup.to_json())

# --- LOOP DE VARREDURA ---
def executar_busca_surebet():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    
    print("🚀 Iniciando Varredura Avançada de Surebets (Módulo Isolado)...")
    
    for nome_comp, url in ligas.COMPETICOES.items():
        if nome_comp.strip() not in LIGAS_SUREBET_ELITE:
            continue
            
        print(f"\n🔥 [SUREBET ELITE] Verificando: {nome_comp}")
        driver.get(url)
        time.sleep(4)
        
        elementos_jogos = driver.find_elements(By.CSS_SELECTOR, ".event__match, [id^='g_1_']")
        ids_jogos = [el.get_attribute("id").split('_')[-1] for el in elementos_jogos if el.get_attribute("id")]
                
        for id_jogo in ids_jogos:
            try:
                url_jogo = f"https://www.flashscore.com.br/jogo/{id_jogo}/#/resumo-de-jogo"
                driver.get(url_jogo)
                time.sleep(3)
                
                t1 = driver.find_element(By.CSS_SELECTOR, ".duelParticipant__home").text.strip()
                t2 = driver.find_element(By.CSS_SELECTOR, ".duelParticipant__away").text.strip()
                
                # 1️⃣ FILTRO DE ODDS (>= 1.70)
                odd_casa, odd_fora = pegar_odds_vitoria_topo(driver)
                
                if not odd_casa or not odd_fora:
                    continue
                    
                if odd_casa < 1.70 or odd_fora < 1.70:
                    print(f"   ⏩ [FILTRO ODD] {t1} ({odd_casa:.2f}) x {t2} ({odd_fora:.2f}) - Descartado.")
                    continue
                    
                print(f"   🎯 [ODDS EM REGRA] {t1} x {t2} -> Puxando scouts de chutes...")
                
                # 2️⃣ RASPAGEM DE CHUTES (FASE 2)
                dados_jogo_fake = {"url_h2h_base": f"https://www.flashscore.com.br/jogo/{id_jogo}/#/h2h/overall"}
                acumulador_scouts = scouts_avancado.pegar_scouts_avancados(driver, dados_jogo_fake, t1, t2)
                
                melhor_jogador_casa = None
                melhor_jogador_fora = None
                
                for jogador, dados in acumulador_scouts.items():
                    if dados["c_jogos"] > 0:
                        media_chutes = dados["chutes"] / dados["c_jogos"]
                        
                        if dados["time"].upper() == t1.upper() and media_chutes >= 2.0 and not melhor_jogador_casa:
                            melhor_jogador_casa = f"{jogador} 1+"
                        if dados["time"].upper() == t2.upper() and media_chutes >= 2.0 and not melhor_jogador_fora:
                            melhor_jogador_fora = f"{jogador} 1+"
                
                # 3️⃣ ENVIO SE QUALIFICADO
                if melhor_jogador_casa and melhor_jogador_fora:
                    print(f"   ✅ [SUREBET GERADA] Enviando via requisição nativa...")
                    estruturar_e_enviar_bilhete(t1, t2, odd_casa, odd_fora, melhor_jogador_casa, melhor_jogador_fora)
                else:
                    print(f"   ⏩ [SEM SCOUTS] Média de chutes insuficiente para este confronto.")
                    
            except Exception as e_jogo:
                print(f"   ⚠️ Erro no processamento do ID {id_jogo}: {e_jogo}")
                continue
                
    driver.quit()

# --- HANDLER DOS BOTÕES INTERATIVOS (TELEBOT) ---
if bot:
    @bot.callback_query_handler(func=lambda call: True)
    def escutar_botoes_surebet(call):
        uid = call.from_user.id
        if uid not in usuario_odds_teste:
            usuario_odds_teste[uid] = {"odd1": 3.05, "odd2": 4.20}
            
        if call.data == "def_odd1":
            msg = bot.send_message(uid, "Digite a Odd Final Combinada da **Aposta 1** na Betano:")
            bot.register_next_step_handler(msg, salvar_odd1)
        elif call.data == "def_odd2":
            msg = bot.send_message(uid, "Digite a Odd Final Combinada da **Aposta 2** na Betano:")
            bot.register_next_step_handler(msg, salvar_odd2)
        elif call.data == "calcular_stakes":
            o1 = usuario_odds_teste[uid]["odd1"]
            o2 = usuario_odds_teste[uid]["odd2"]
            banca_total = 90.00
            
            margem = (1 / o1) + (1 / o2)
            stake1 = banca_total / (margem * o1)
            stake2 = banca_total / (margem * o2)
            
            retorno = stake1 * o1
            lucro = retorno - banca_total
            
            texto_resultado = (
                "📊 **DIVISÃO INTELIGENTE CALCULADA**\n\n"
                f"💰 Investimento Total Fixo: R$ {banca_total:.2f}\n"
                f"📈 Margem Calculada: {margem*100:.1f}%\n"
                "----------------------------\n"
                f"🔹 **Aposta 1 (Odd {o1:.2f}):** Investir **R$ {stake1:.2f}**\n"
                f"🔹 **Aposta 2 (Odd {o2:.2f}):** Investir **R$ {stake2:.2f}**\n"
                "----------------------------\n"
                f"🟢 **Lucro Líquido Garantido: +R$ {lucro:.2f}**"
            )
            bot.send_message(call.message.chat.id, texto_resultado, parse_mode="Markdown")

    def salvar_odd1(message):
        try:
            usuario_odds_teste[message.from_user.id]["odd1"] = float(message.text.replace(",", "."))
            bot.send_message(message.from_user.id, "✅ Odd 1 salva!")
        except:
            bot.send_message(message.from_user.id, "❌ Valor incorreto.")

    def salvar_odd2(message):
        try:
            usuario_odds_teste[message.from_user.id]["odd2"] = float(message.text.replace(",", "."))
            bot.send_message(message.from_user.id, "✅ Odd 2 salva!")
        except:
            bot.send_message(message.from_user.id, "❌ Valor incorreto.")

if __name__ == "__main__":
    executar_busca_surebet()
    if bot:
        print("🤖 Escutando botões via Telebot Polling...")
        bot.infinity_polling()
        
