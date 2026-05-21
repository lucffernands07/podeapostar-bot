import os
import time
import re
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Importação dos seus módulos
from ligas import COMPETICOES
from mercados import gols, ambos_marcam, chance_dupla, vitoria_casa
import odds  
import bingo357  
import links
from telegram import menus


def enviar_telegram(mensagem, chat_id_destino):
    token = os.getenv('TELEGRAM_TOKEN')
    if not token or not chat_id_destino:
        return
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(url, data={
            "chat_id": chat_id_destino, 
            "text": mensagem, 
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        })
    except Exception as e:
        print(f"Erro Telegram: {e}")

def configurar_driver():
    options = Options()
    options.add_argument("--headless=new") # Versão mais rápida do headless
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu") # Desliga processamento gráfico
    options.add_argument("--blink-settings=imagesEnabled=false") # Não carrega imagens (ganha muita velocidade)
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    # Define um tempo máximo de espera para o site carregar
    driver.set_page_load_timeout(30) 
    driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "UTC"})
    return driver

def pegar_estatisticas_h2h(driver, url_jogo, t1, t2):
    # Navegação inicial - Abre a aba do jogo
    driver.execute_script(f"window.open('{url_jogo}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    
    stats = {
        "link_betano": None,
        "casa_15": 0, "casa_25": 0, "casa_45_under": 0, "casa_btts": 0, 
        "casa_vitorias_recente": 0, "ultimo_gols_casa": 0, "t1_resultado_1": "",
        "fora_15": 0, "fora_25": 0, "fora_45_under": 0, "fora_btts": 0, 
        "ultimo_gols_fora": 0, "t2_resultado_1": "",
        "h2h_jogos": 0, "h2h_vitorias_t1": 0, "h2h_vitorias_t2": 0, "h2h_empates": 0,
        "h2h_res_1": "", "h2h_res_2": "", 
        "t1_placar_1": None, "t2_placar_1": None,     # Captura para Ambas Marcam
        "h2h_placar_1": None, "h2h_placar_2": None,   # Captura para Ambas Marcam
        "pular_gols": False 
    }
    
    try:
        wait = WebDriverWait(driver, 15)
        # 1. Vai para a aba H2H onde estão os seus links
        h2h_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/h2h')]")))
        h2h_tab.click()
        time.sleep(2)
        
        driver.execute_script("window.scrollTo(0, 800);")
        time.sleep(1)
        
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        
        for idx, secao in enumerate(secoes[:3]): 
            if idx == 2: 
                try:
                    seletor_btn = "span[data-testid='wcl-scores-caption-05']"
                    botao_mais = secao.find_element(By.CSS_SELECTOR, seletor_btn)
                    driver.execute_script("arguments[0].click();", botao_mais)
                    WebDriverWait(secao, 6).until(lambda s: len(s.find_elements(By.CSS_SELECTOR, ".h2h__row")) >= 6)
                except: pass 

            limite = 6 if idx == 2 else 5
            linhas = secao.find_elements(By.CSS_SELECTOR, ".h2h__row")[:limite] 
            
            for i, linha in enumerate(linhas):
                try:
                    n_casa_h2h = linha.find_element(By.CSS_SELECTOR, ".h2h__homeParticipant").text
                    n_fora_h2h = linha.find_element(By.CSS_SELECTOR, ".h2h__awayParticipant").text
                    res_texto = linha.find_element(By.CSS_SELECTOR, ".h2h__result").text
                    
                    # --- NOVO: CAPTURA DE PLACARES PARA REGRA AMBAS MARCAM ---
                    if idx == 0 and i == 0: stats["t1_placar_1"] = res_texto
                    if idx == 1 and i == 0: stats["t2_placar_1"] = res_texto
                    if idx == 2:
                        if i == 0: stats["h2h_placar_1"] = res_texto
                        if i == 1: stats["h2h_placar_2"] = res_texto

                    numeros_placar = re.findall(r'\d+', res_texto)
                    if len(numeros_placar) < 2: continue
                    g1, g2 = int(numeros_placar[0]), int(numeros_placar[1])
                    total = g1 + g2

                    if idx < 2: 
                        prefixo = "casa" if idx == 0 else "fora"
                        t_ref = t1 if idx == 0 else t2
                        if i == 0: stats[f"ultimo_gols_{prefixo}"] = total
                        if total > 1.5: stats[f"{prefixo}_15"] += 1
                        if total > 2.5: stats[f"{prefixo}_25"] += 1
                        if total <= 4: stats[f"{prefixo}_45_under"] += 1 
                        if g1 > 0 and g2 > 0: stats[f"{prefixo}_btts"] += 1
                        
                        res_atual = "E"
                        if (t_ref.lower() in n_casa_h2h.lower() and g1 > g2) or \
                           (t_ref.lower() in n_fora_h2h.lower() and g2 > g1):
                            res_atual = "V"
                            stats[f"{prefixo}_vitorias_recente"] += 1
                        elif (t_ref.lower() in n_casa_h2h.lower() and g1 < g2) or \
                             (t_ref.lower() in n_fora_h2h.lower() and g2 < g1):
                            res_atual = "D"
                        
                        if i == 0: stats[f"t{idx+1}_resultado_1"] = res_atual
                 
                    elif idx == 2: 
                        # Se o mando de campo estiver invertido (Mandante de hoje jogando fora no H2H),
                        # nós ignoramos a linha para buscar o próximo jogo real em casa.
                        if t1.lower() in n_fora_h2h.lower():
                            continue 

                        stats["h2h_jogos"] += 1
                        res_h2h = "E"
                        if g1 > g2:
                            res_h2h = "V"
                            stats["h2h_vitorias_t1"] += 1
                        elif g1 < g2:
                            res_h2h = "D"
                            stats["h2h_vitorias_t2"] += 1
                        
                        # Salva o primeiro H2H válido com mando correto que encontrar
                        if stats["h2h_res_1"] == "":
                            stats["h2h_res_1"] = res_h2h
                        # Salva o segundo H2H válido com mando correto
                        elif stats["h2h_res_2"] == "":
                            stats["h2h_res_2"] = res_h2h
                            break # Já achou os dois com mando certo, pode parar a tabela!

                        if g1 == g2: stats["h2h_empates"] += 1

                except: continue

        # --- CAPTURA DO LINK BETANO ---
        print(f"      🔗 Capturando link Betano para {t1} x {t2}...")
        stats["link_betano"] = links.extrair_url_betano(driver)

    except Exception as e:
        print(f"      ⚠️ Erro H2H {t1}x{t2}: {e}")
        
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return stats

def main():
    driver = configurar_driver()
    hoje_ref = datetime.now()
    amanha_no_site = (hoje_ref + timedelta(days=1)).strftime("%d.%m.")
    lista_para_filtros = []     
    jogos_para_pendentes = [] # <--- NOVO: Lista para o ranking
    total_mercados = 0 

    try:
        # LOOP DE COMPETIÇÕES
        for nome_comp, url in COMPETICOES.items():
            if total_mercados >= 120: break 
            print(f"\n--- Analisando: {nome_comp} ---")
            driver.get(url)
            time.sleep(4)
            elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
            
            for el in elementos:
                try:
                    tempo_raw = el.find_element(By.CSS_SELECTOR, ".event__time").text.strip()
                    h_obj = datetime.strptime(tempo_raw.split()[-1], "%H:%M")
                    h_br = (h_obj - timedelta(hours=3)).strftime("%H:%M")
                    
                    aceitar = False
                    if amanha_no_site in tempo_raw:
                        if h_obj.hour <= 3: aceitar = True
                    elif "." not in tempo_raw:
                        if (h_obj - timedelta(hours=3)).hour >= 7: aceitar = True

                    if aceitar:
                        times = el.find_elements(By.CSS_SELECTOR, "span[class*='wcl-name']")
                        t1, t2 = times[0].text.strip(), times[1].text.strip()
                        id_jogo = el.get_attribute('id').split('_')[-1]
                        
                        url_h2h_final = f"https://www.flashscore.com.br/jogo/{id_jogo}/#/h2h/overall"
                        s = pegar_estatisticas_h2h(driver, url_h2h_final, t1, t2)
                        
                        mercados_para_processar = []

                        # 1. Gols
                        res_gols = gols.verificar_gols(s)
                        for rg in res_gols:
                            mercados_para_processar.append({"texto": rg['mercado'], "chave": rg['tipo']})

                        # 2. Ambas Marcam
                        res_btts = ambos_marcam.verificar_btts(s)
                        if res_btts:
                            mercados_para_processar.append({"texto": f"Ambas Marcam: Sim ({res_btts})", "chave": "BTTS"})

                        # -----------------------------------------------------------------
                        # 3. Chance Dupla (Injetando a Lógica de Porcentagem com Segurança)
                        # -----------------------------------------------------------------
                        # Verificamos a consistência de vitórias para estipular a % do painel
                        # Se vitórias recentes >= 4 -> 100%, senão segue a escada de segurança
                        if s.get("casa_vitorias_recente", 0) >= 4 or s.get("fora_vitorias_recente", 0) >= 4:
                            s["chance_dupla_pct"] = "100%"
                        elif s.get("casa_vitorias_recente", 0) == 3 or s.get("fora_vitorias_recente", 0) == 3:
                            s["chance_dupla_pct"] = "90%"
                        else:
                            s["chance_dupla_pct"] = "80%"

                        res_cd = chance_dupla.verificar_chance_dupla(s)
                        for rc in res_cd:
                            tipo_cd = "1X" if "1X" in rc else "X2"
                            mercados_para_processar.append({"texto": rc, "chave": tipo_cd})
                        # -----------------------------------------------------------------

                        # 4. Vitória Casa
                        res_vc = vitoria_casa.verificar_vitoria_casa(s)
                        for rv in res_vc:
                            mercados_para_processar.append({"texto": rv, "chave": "VITORIA_CASA"})

                        # --- VALIDAÇÃO DE ODDS E FILTRAGEM ---
                        if mercados_para_processar:
                            v_odds = odds.capturar_todas_as_odds(driver, id_jogo)
                            
                            for item in mercados_para_processar:
                                m_texto = item["texto"]
                                m_chave = item["chave"]
                                valor_odd_str = v_odds.get(m_chave, "N/A")

                                try:
                                    odd_float = float(valor_odd_str.replace(',', '.'))
                                    
                                    if "M45" in m_chave and odd_float >= 4.0:
                                        continue 

                                    if odd_float >= 1.30:
                                        # Salva para o Listão/Telegram
                                        lista_para_filtros.append({
                                            "horario": h_br, "time_casa": t1, "time_fora": t2,
                                            "mercado": m_texto, "odd": valor_odd_str, "liga": nome_comp,
                                            "link_betano": s.get("link_betano")
                                        })
                                        
                                        # NOVO: Salva para o Ranking com links                                    # NOVO: Salva para o Ranking com link direto e porcentagem
                                        jogos_para_pendentes.append({
                                            "time_casa": t1,
                                            "time_fora": t2,
                                            "mercado": m_texto,
                                            "mercado_ranking": m_texto.upper(),
                                            "link_h2h": f"https://www.flashscore.com.br/jogo/{id_jogo}/#/resumo-de-jogo"
                                        })
                                                
                                        total_mercados += 1
                                except: continue
                except: continue

        # --- PROCESSAMENTO E ENVIO FINAL ---
        if lista_para_filtros:
            lista_para_filtros.sort(key=lambda x: (x['horario'], x['liga']))
            
            meu_chat_id = os.getenv('CHAT_ID')
            if meu_chat_id:
                cabecalho = "🎫 *LISTA DE MERCADOS DO DIA*\n\n"
                corpo = ""
                for j in lista_para_filtros:
                    bloco = f"⏱️ {j['horario']} | {j['liga']}\n🏟️ {j['time_casa']} x {j['time_fora']}\n🔶 {j['mercado']} | Odd: {j['odd']}\n\n------------------------------------\n\n"
                    
                    if len(cabecalho + corpo + bloco) > 4000:
                        enviar_telegram(cabecalho + corpo, meu_chat_id)
                        cabecalho = "🎫 *LISTA (Continuação)*\n\n"
                        corpo = bloco
                    else:
                        corpo += bloco
                
                enviar_telegram(cabecalho + corpo, meu_chat_id)
                print("📨 Listão enviado.")

            # --- GERAÇÃO E FORMATAÇÃO DOS BINGOS ---
            novos_bilhetes = bingo357.montar_bilhetes_estrategicos(lista_para_filtros)
            # Criamos um cache completo com todos os dados que costumam sumir (Hora, Liga, Odd)
            cache_dados = {}
            for j in lista_para_filtros:
                chave = f"{j['time_casa']}x{j['time_fora']}"
                cache_dados[chave] = {
                    "link": j.get("link_betano"),
                    "liga": j.get("liga"),
                    "horario": j.get("horario"),
                    "odd": j.get("odd")
                }
            # Agora passamos o cache robusto para o formatador
            texto_bingos_final = bingo357.formatar_para_telegram(novos_bilhetes, cache_dados)

            canal_id = os.getenv('CHANNEL_ID')
            if texto_bingos_final and canal_id:
                msg_bingo_formatada = "💰 *SUGESTÕES DE INVESTIMENTO*\n\n" + texto_bingos_final
                # Agora enviando com o menu de botões para o Canal
                menus.enviar_menu_bingo(canal_id, msg_bingo_formatada)
                print("📢 Bingos enviados com botões para o Canal.")


            # --- SALVAMENTO WITH TRAVA DE SEGURANÇA INTELIGENTE ---
            import json
            os.makedirs("ranking", exist_ok=True)
            caminho_p = "ranking/pendentes.json"
            data_hoje = hoje_ref.strftime("%Y-%m-%d")
            
            pode_gravar = True # Por padrão, tentamos gravar

            if os.path.exists(caminho_p):
                try:
                    with open(caminho_p, 'r', encoding='utf-8') as f:
                        conteudo = f.read().strip()
                        if not conteudo: # Arquivo existe mas está vazio (erro de escrita anterior)
                            pode_gravar = True
                        else:
                            dados_existentes = json.loads(conteudo)
                            # Se já existe gravação de HOJE e tem JOGOS, aí sim bloqueamos
                            if dados_existentes.get("data_geracao") == data_hoje:
                                if len(dados_existentes.get("jogos", [])) > 0:
                                    pode_gravar = False
                except (json.JSONDecodeError, Exception) as e:
                    # Se o arquivo estiver corrompido, ignoramos o bloqueio e gravamos por cima
                    print(f"⚠️ Arquivo de ranking corrompido ou ilegível, resetando: {e}")
                    pode_gravar = True

            if pode_gravar and jogos_para_pendentes: # <--- Use a lista de pendentes aqui
                dados_final = {
                    "data_geracao": data_hoje,
                    "jogos": jogos_para_pendentes # <--- E aqui também
                }
                
                with open(caminho_p, "w", encoding="utf-8") as f:
                    json.dump(dados_final, f, indent=4, ensure_ascii=False)
                print(f"✅ Ranking: Primeira execução do dia salva ({len(jogos_para_pendentes)} jogos).")
            
            elif not pode_gravar:
                print(f"🚫 BLOQUEIO: O Ranking de hoje ({data_hoje}) já foi consolidado na 1ª execução.")
            else:
                print("ℹ️ Nenhuma gravação feita: A varredura atual não encontrou jogos válidos.")

            # --- SALVAMENTO PARA O BOT DO TELEGRAM (SOB DEMANDA) ---
            os.makedirs("telegram", exist_ok=True)
            caminho_banco = f"telegram/jogos_{data_hoje}.json"

            # Criamos uma estrutura limpa e otimizada para o Bot ler rápido
            dados_para_o_bot = []
            for j in lista_para_filtros:
                dados_para_o_bot.append({
                    "horario": j.get("horario"),
                    "liga": j.get("liga"),
                    "time_casa": j.get("time_casa"),
                    "time_fora": j.get("time_fora"),
                    "mercado": j.get("mercado"),
                    "odd": j.get("odd"),
                    "link_betano": j.get("link_betano") # <--- O SEGREDO DO BOTÃO ESTÁ AQUI
                })

            # Salvamos o arquivo que o GitHub Actions vai consultar ao clicar no botão
            with open(caminho_banco, "w", encoding="utf-8") as f:
                json.dump(dados_para_o_bot, f, indent=4, ensure_ascii=False)

            print(f"📂 Banco de dados do dia salvo para o Bot: {caminho_banco}")


            print("✅ Processamento concluído com sucesso.")

    except Exception as e:
        print(f"❌ Erro Crítico no Main: {e}")
    finally:
        driver.quit()

                                    
if __name__ == "__main__":
    main()
            
