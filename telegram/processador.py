import sys
import os
import json
import requests
from datetime import datetime, timedelta

# --- AJUSTE DE CAMINHO ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import bingo357 
from telegram import menus

def processar_comando_direto(tipo_bruto):
    """
    Lê a string unificada e separa os filtros para montar o bilhete.
    Ajustada para garantir que o número do bingo vindo do callback seja respeitado.
    """
    # Inicializa com padrão 5 para evitar forçar 3
    config = {"bingo": 5, "horario": "DIA", "bilhete": "ACERTOS", "aviso": "", "modo_elite": False}
    tipo_limpo = tipo_bruto.strip() if tipo_bruto else ""

    # 1. Processamento para strings compostas (Worker)
    if "BINGO:" in tipo_limpo and "HORA:" in tipo_limpo:
        try:
            partes = tipo_limpo.split("|")
            for parte in partes:
                if parte.startswith("BINGO:"):
                    valor_b = parte.split(":")[1]
                    if valor_b.upper() == "ELITE":
                        config["bingo"] = 3
                        config["modo_elite"] = True
                    else:
                        config["bingo"] = int(valor_b)
                elif parte.startswith("HORA:"):
                    config["horario"] = parte.split(":")[1]
                elif parte.startswith("TIPO:"):
                    config["bilhete"] = parte.split(":")[1]
            
            txt_janela = f"{config['horario']}" if config['horario'] != "DIA" else "Do Dia"
            txt_modo = "Mais acertos"
            if config['bilhete'] == "ODDS": txt_modo = "Maiores Odds"
            elif config['bilhete'] == "AMBAS": txt_modo = "Equilibrado"

            txt_bingo = "✨ Elite" if config["modo_elite"] else config["bingo"]
            config["aviso"] = (f"🎲 Bingo: *{txt_bingo}*\n⏱️ Janela: *{txt_janela}*\n📊 Modo: *{txt_modo}*")
            return config
        except Exception as e:
            print(f"⚠️ Erro ao processar string composta ({e}), usando fallbacks...")

    # 2. Processamento para Callbacks dos Botões
    if "cb_bingo_" in tipo_limpo:
        partes = tipo_limpo.split("_")
        # Extrai o número do bingo da posição 2 (ex: cb_bingo_5_ELITE -> partes[2] é 5)
        # Usamos try/except para garantir que, se não houver número, ele mantenha o padrão
        try:
            config["bingo"] = int(partes[2])
        except (IndexError, ValueError):
            config["bingo"] = 5
            
        if "ELITE" in tipo_limpo.upper():
            config["modo_elite"] = True
            config["aviso"] = f"🎲 Você escolheu: *Bingo {config['bingo']} (Denso/Elite)*"
        else:
            config["aviso"] = f"🎲 Você escolheu: *Bingo {config['bingo']}*"

    elif "cb_hora_" in tipo_limpo:
        config["horario"] = tipo_limpo.split("_")[-1]
        txt_h = config["horario"] if config["horario"] != "DIA" else "Do Dia"
        config["aviso"] = f"⏱️ Você escolheu a janela: *{txt_h}*"

    elif "cb_tipo_" in tipo_limpo:
        config["bilhete"] = tipo_limpo.split("_")[-1]
        txt_m = "Mais acertos"
        if config["bilhete"] == "ODDS": txt_m = "Maiores Odds"
        elif config["bilhete"] == "AMBAS": txt_m = "Equilibrado"
        config["aviso"] = f"📊 Você escolheu a estratégia: *{txt_m}*"
    
    # 3. Fallback para comandos não formatados
    else:
        if "3" in tipo_limpo: config["bingo"] = 3
        elif "5" in tipo_limpo: config["bingo"] = 5
        elif "7" in tipo_limpo or "PRO" in tipo_limpo: config["bingo"] = 7
        elif "ELITE" in tipo_limpo.upper():
            config["bingo"] = 3
            config["modo_elite"] = True
            
        if "ODDS" in tipo_limpo: config["bilhete"] = "ODDS"
        
        txt_bingo = "✨ Elite" if config["modo_elite"] else config["bingo"]
        config["aviso"] = f"🚀 Processando comando recebido: *{txt_bingo}*"

    return config

def executar():
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    tipo_bruto = os.getenv('TIPO_BINGO', '')
    
    config = processar_comando_direto(tipo_bruto)
    qtd_alvo = config["bingo"]
    filtro_hora = config["horario"]
    estrategia = config["bilhete"].strip().upper() # Força ficar em maiúsculo (ODDS, ACERTOS, AMBAS)

    msg_aguarde = f"{config['aviso']}\n\n⏳ *Buscando os melhores jogos no banco de dados, aguarde um instante...*"
    url_msg = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(url_msg, json={
            "chat_id": chat_id,
            "text": msg_aguarde,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        })
    except Exception as e:
        print(f"⚠️ Erro ao enviar aviso de aguarde silencioso: {e}")

    agora_br = datetime.now() - timedelta(hours=3)
    data_hoje = agora_br.strftime("%Y-%m-%d")
    caminho_json = f"telegram/jogos_{data_hoje}.json"
    caminho_pendentes = "ranking/pendentes.json"

    if not os.path.exists(caminho_json):
        print(f"Erro: Arquivo {caminho_json} not encontrado.")
        return

    with open(caminho_json, "r", encoding="utf-8") as f:
        jogos_banco = json.load(f)

    # 🚀 MAPEAMENTO UNIFICADO DE LINKS (Betano + H2H)
    dict_cache_links = {}

    # Passo A: Pega os links da Betano salvos no banco de dados do dia
    for j in jogos_banco:
        casa = j.get("time_casa")
        fora = j.get("time_fora")
        link_b = j.get("link_betano")
        if casa and fora and link_b:
            chave_confronto = f"{str(casa).strip().lower()}x{str(fora).strip().lower()}"
            if chave_confronto not in dict_cache_links:
                dict_cache_links[chave_confronto] = {}
            dict_cache_links[chave_confronto]["link_betano"] = link_b

    # Passo B: Cruza e adiciona os links H2H do pendentes.json se existirem
    if os.path.exists(caminho_pendentes):
        try:
            with open(caminho_pendentes, "r", encoding="utf-8") as f:
                dados_pendentes = json.load(f)
                lista_jogos_p = dados_pendentes.get("jogos", []) if isinstance(dados_pendentes, dict) else dados_pendentes
                
                for item in lista_jogos_p:
                    casa = item.get("time_casa")
                    fora = item.get("time_fora")
                    link_h2h = item.get("link_h2h")
                    if casa and fora and link_h2h:
                        chave_confronto = f"{str(casa).strip().lower()}x{str(fora).strip().lower()}"
                        if chave_confronto not in dict_cache_links:
                            dict_cache_links[chave_confronto] = {}
                        dict_cache_links[chave_confronto]["link_h2h"] = link_h2h
        except Exception as e:
            print(f"⚠️ Erro ao processar links H2H do pendentes.json: {e}")

    jogos_validos_horario = []
    for j in jogos_banco:
        try:
            h_partes = j['horario'].split(":")
            hora_jogo = agora_br.replace(hour=int(h_partes[0]), minute=int(h_partes[1]), second=0, microsecond=0)
            
            if int(h_partes[0]) < 4 and agora_br.hour > 20:
                hora_jogo += timedelta(days=1)
            
            if filtro_hora != "DIA" and "H" in filtro_hora:
                try:
                    horas_limite = int(filtro_hora.replace("H", ""))
                    if hora_jogo > agora_br + timedelta(hours=horas_limite) or hora_jogo < agora_br - timedelta(minutes=15):
                        continue
                except: pass
            elif hora_jogo < agora_br - timedelta(minutes=15):
                continue
                
            j["datetime_real"] = hora_jogo
            jogos_validos_horario.append(j)
        except:
            if filtro_hora == "DIA": 
                jogos_validos_horario.append(j)

    jogos_validos_horario.sort(key=lambda x: x.get("datetime_real", agora_br))

    # --- PROCESSAMENTO DOS BILHETES ---
    # 🚀 Injetado o parâmetro modo_elite que informa se deve priorizar jogos com alta densidade de mercados
    bilhetes_gerados = bingo357.montar_bilhetes_estrategicos(
        jogos_validos_horario, 
        qtd_alvo=qtd_alvo, 
        estrategia=estrategia,
        modo_elite=config.get("modo_elite", False)
    )
    
    # Repassa o cache contendo os dicionários de links limpos
    texto_final = bingo357.formatar_para_telegram(bilhetes_gerados, dict_cache_links)

    # --- ENVIO DOS RESULTADOS OU AVISO DE ERRO ---
    menu_botoes = menus.extrair_markup_filtros() if hasattr(menus, 'extrair_markup_filtros') else None

    if texto_final:
        try:
            payload = {
                "chat_id": chat_id,
                "text": texto_final,
                "parse_mode": "Markdown",
                "disable_web_page_preview": False
            }
            if menu_botoes:
                payload["reply_markup"] = menu_botoes

            requests.post(url_msg, json={**payload})
            print("🚀 Bilhetes do Bingo enviados com sucesso com o Menu anexado!")
        except Exception as e:
            print(f"⚠️ Erro ao enviar os bilhetes formatados para o Telegram: {e}")
    else:
        # Aviso personalizado quando não encontra jogos no listão
        msg_erro = f"{config['aviso']}\n\n⚠️😢 Não foi encontrado bilhete com esse filtro. Tente outra janela, bingo ou tente amanhã."
        try:
            payload = {
                "chat_id": chat_id,
                "text": msg_erro,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }
            if menu_botoes:
                payload["reply_markup"] = menu_botoes

            requests.post(url_msg, json=payload)
            print("⚠️ Aviso de 'Não foi encontrado bilhete' enviado com o Menu anexado!")
        except Exception as e:
            print(f"⚠️ Erro ao enviar aviso de erro para o Telegram: {e}")

if __name__ == "__main__":
    executar()
            
