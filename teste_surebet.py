import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import telebot

# --- SEUS IMPORTS EXISTENTES ---
import ligas  # Onde está o dicionário COMPETICOES e a lista LIGAS_SUREBET_ELITE
import scouts_avancado  # Seu arquivo da Fase 2 fornecido

# --- CONFIGURAÇÃO DO SEU BOT DE TESTES ---
API_TOKEN = "SEU_TOKEN_TELEGRAM_AQUI"
CHAT_ID = "SEU_CHAT_ID_AQUI"
bot = telebot.TeleBot(API_TOKEN)

# Dicionário temporário na memória para guardar as odds do cálculo das stakes
usuario_odds_teste = {}

# --- LISTA DE LIGAS ELITE SELECIONADAS (Caso queira manter no mesmo arquivo) ---
LIGAS_SUREBET_ELITE = [
    "Brasileirão Série A", "Copa do Brasil", "Libertadores", "Sul-Americana",
    "Argentina - Liga Profesional", "Mundo - Copa do Mundo", "Europa - Champions League",
    "Inglaterra - Premier League", "Espanha - LaLiga", "Alemanha - Bundesliga",
    "Italia - Serie A", "França - Ligue 1", "Europa - League", "Inglaterra - FA Cup",
    "Espanha - Copa del Rey", "Alemanha - DFB Pokal", "Arábia Saudita - King Cup",
    "EUA - MLS", "Argentina - Copa"
]

def pegar_odds_vitoria_topo(driver):
    """
    Função auxiliar interna: Captura as odds de vitória (1x2) direto 
    da tela de resumo principal do Flashscore antes de navegar.
    """
    try:
        wait = WebDriverWait(driver, 8)
        # Seletores clássicos das três odds principais (Casa, Empate, Fora) no topo
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

def enviar_telegram_surebet(t1, t2, odd_c, odd_f, jogador_c, jogador_f):
    """Monta a mensagem estruturada com os botões interativos para o cálculo."""
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
    
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("✏️ Odd Final Aposta 1", callback_data="def_odd1"),
        InlineKeyboardButton("✏️ Odd Final Aposta 2", callback_data="def_odd2"),
        InlineKeyboardButton("🧮 CALCULAR ENTRADAS", callback_data="calcular_stakes")
    )
    bot.send_message(CHAT_ID, texto_mensagem, parse_mode="Markdown", reply_markup=markup)

# --- LOOP PRINCIPAL DO ROBO DE TESTE ---
def executar_busca_surebet():
    # Inicialização padrão do seu Chrome Driver
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Mantenha ativado no ambiente do GitHub Actions
    driver = webdriver.Chrome(options=options)
    
    print("🚀 Iniciando Varredura Avançada de Surebets...")
    
    for nome_comp, url in ligas.COMPETICOES.items():
        # Filtra apenas pelas copas e ligas fortes definidas
        if nome_comp.strip() not in LIGAS_SUREBET_ELITE:
            continue
            
        print(f"\n🔥 [SUREBET ELITE] Verificando: {nome_comp}")
        driver.get(url)
        time.sleep(4)
        
        # Coleta os elementos e extrai os IDs dos jogos na lista do dia
        elementos_jogos = driver.find_elements(By.CSS_SELECTOR, ".event__match, [id^='g_1_']")
        ids_jogos = []
        for el in elementos_jogos:
            id_attr = el.get_attribute("id")
            if id_attr:
                ids_jogos.append(id_attr.split('_')[-1])
                
        # Varre individualmente os jogos da competição de Elite
        for id_jogo in ids_jogos:
            try:
                url_jogo = f"https://www.flashscore.com.br/jogo/{id_jogo}/#/resumo-de-jogo"
                driver.get(url_jogo)
                time.sleep(3)
                
                # Nomes das equipes no topo do resumo
                t1 = driver.find_element(By.CSS_SELECTOR, ".duelParticipant__home").text.strip()
                t2 = driver.find_element(By.CSS_SELECTOR, ".duelParticipant__away").text.strip()
                
                # 1️⃣ VALIDAR SE AS ODDS DE VITÓRIA PASSAM NA REGRA (>= 1.70)
                odd_casa, odd_fora = pegar_odds_vitoria_topo(driver)
                
                if not odd_casa or not odd_fora:
                    print(f"   ⏩ [SEM ODDS] Não foi possível capturar odds de 1X2 para {t1} x {t2}.")
                    continue
                    
                if odd_casa < 1.70 or odd_fora < 1.70:
                    print(f"   ⏩ [FILTRO ODD] {t1} ({odd_casa:.2f}) x {t2} ({odd_fora:.2f}) - Fora do padrão equilibrado.")
                    continue
                    
                print(f"   🎯 [APROVADO POR ODD] {t1} ({odd_casa:.2f}) x {t2} ({odd_fora:.2f}) -> Investigando chutes...")
                
                # 2️⃣ SE PASSOU, EXECUTAMOS A RASPAGEM DE CHUTES (FASE 2)
                # Simulamos o dicionário básico 'dados_jogo' exigido pela sua função da Fase 2
                dados_jogo_fake = {"url_h2h_base": f"https://www.flashscore.com.br/jogo/{id_jogo}/#/h2h/overall"}
                
                # Chama a sua função real do arquivo scouts_avancado.py
                acumulador_scouts = scouts_avancado.pegar_scouts_avancados(driver, dados_jogo_fake, t1, t2)
                
                melhor_jogador_casa = None
                melhor_jogador_fora = None
                
                # Varre o retorno conforme a estrutura criada na sua Fase 2
                for jogador, dados in acumulador_scouts.items():
                    # Evita divisão por zero caso o jogador não tenha partidas salvas
                    if dados["c_jogos"] > 0:
                        media_chutes = dados["chutes"] / dados["c_jogos"]
                        
                        # Valida se o jogador pertence ao time da casa e possui média >= 2.0
                        if dados["time"].upper() == t1.upper() and media_chutes >= 2.0 and not melhor_jogador_casa:
                            melhor_jogador_casa = f"{jogador} 1+"
                        
                        # Valida se o jogador pertence ao time de fora e possui média >= 2.0
                        if dados["time"].upper() == t2.upper() and media_chutes >= 2.0 and not melhor_jogador_fora:
                            melhor_jogador_fora = f"{jogador} 1+"
                
                # 3️⃣ SE ENCONTRAR DOIS JOGADORES VALIDADOS, DISPARA O RETORNO
                if melhor_jogador_casa and melhor_jogador_fora:
                    print(f"   ✅ [SUREBET MATCH] Par de bilhetes gerados com sucesso para o Telegram!")
                    enviar_telegram_surebet(t1, t2, odd_casa, odd_fora, melhor_jogador_casa, melhor_jogador_fora)
                else:
                    print(f"   ⏩ [SEM SCOUTS MÍNIMOS] Sem jogadores com média de chutes >= 2.0 nas duas equipes.")
                    
            except Exception as e_jogo:
                print(f"   ⚠️ Erro ao processar o jogo {id_jogo}: {e_jogo}")
                continue
                
    driver.quit()

# --- LÓGICA DO MENU INTERATIVO DO TELEGRAM ---
@bot.callback_query_handler(func=lambda call: True)
def escutar_botoes_surebet(call):
    uid = call.from_user.id
    if uid not in usuario_odds_teste:
        usuario_odds_teste[uid] = {"odd1": 3.05, "odd2": 4.20} # Padrão do seu print caso não digite
        
    if call.data == "def_odd1":
        msg = bot.send_message(uid, "Digite a Odd Final Combinada da **Aposta 1** na Betano (Ex: 3.10):")
        bot.register_next_step_handler(msg, salvar_odd1)
    elif call.data == "def_odd2":
        msg = bot.send_message(uid, "Digite a Odd Final Combinada da **Aposta 2** na Betano (Ex: 4.05):")
        bot.register_next_step_handler(msg, salvar_odd2)
    elif call.data == "calcular_stakes":
        o1 = usuario_odds_teste[uid]["odd1"]
        o2 = usuario_odds_teste[uid]["odd2"]
        banca_total = 90.00
        
        # Matemática de Arbitragem Dinâmica
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
        bot.send_message(message.from_user.id, "✅ Odd 1 registrada!")
    except:
        bot.send_message(message.from_user.id, "❌ Valor incorreto.")

def salvar_odd2(message):
    try:
        usuario_odds_teste[message.from_user.id]["odd2"] = float(message.text.replace(",", "."))
        bot.send_message(message.from_user.id, "✅ Odd 2 registrada!")
    except:
        bot.send_message(message.from_user.id, "❌ Valor incorreto.")

if __name__ == "__main__":
    # Inicia a raspagem de teste
    executar_busca_surebet()
    # Mantém o bot do telegram ouvindo os botões de cálculo
    print("🤖 Bot ouvindo os botões do Telegram...")
    bot.infinity_polling()
