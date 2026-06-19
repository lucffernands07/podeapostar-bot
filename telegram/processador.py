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
    Lê a string unificada do novo Worker ("BINGO:3|HORA:3H|TIPO:ACERTOS")
    e separa os 3 filtros reais para montar o bilhete exato.
    """
    config = {"bingo": 5, "horario": "DIA", "bilhete": "ACERTOS", "aviso": ""}
    tipo_limpo = tipo_bruto.strip() if tipo_bruto else ""

    if "BINGO:" in tipo_limpo and "HORA:" in tipo_limpo:
        try:
            partes = tipo_limpo.split("|")
            for parte in partes:
                if parte.startswith("BINGO:"):
                    config["bingo"] = int(parte.split(":")[1])
                elif parte.startswith("HORA:"):
                    config["horario"] = parte.split(":")[1]
                elif parte.startswith("TIPO:"):
                    config["bilhete"] = parte.split(":")[1]
            
            txt_janela = f"{config['horario']}" if config['horario'] != "DIA" else "Do Dia"
            txt_modo = "Mais acertos"
            if config['bilhete'] == "ODDS":
                txt_modo = "Maiores Odds"
            elif config['bilhete'] == "AMBAS":
                txt_modo = "Equilibrado"

            config["aviso"] = (
                f"🎲 Bingo: *{config['bingo']}*\n"
                f"⏱️ Janela: *{txt_janela}*\n"
                f"📊 Modo: *{txt_modo}*"
            )
            return config
        except Exception as e:
            print(f"⚠️ Erro ao processar string composta ({e}), usando fallbacks...")

    if "cb_bingo_" in tipo_limpo:
        config["bingo"] = int(tipo_limpo.split("_")[-1])
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
    else:
        if "3" in tipo_limpo: config["bingo"] = 3
        if "7" in tipo_limpo or "PRO" in tipo_limpo: config["bingo"] = 7
        if "ODDS" in tipo_limpo: config["bilhete"] = "ODDS"
        config["aviso"] = f"🚀 Processando comando recebido: *{tipo_limpo}*"

    return config


def executar():
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    tipo_bruto = os.getenv('TIPO_BINGO', '')
    
    config = processar_comando_direto(tipo_bruto)
    qtd_alvo = config["bingo"]
    filtro_hora = config["horario"]
    estrategia = config["bilhete"]

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
    bilhetes_gerados = bingo357.montar_bilhetes_estrategicos(jogos_validos_horario, qtd_alvo=qtd_alvo)
    
    # Repassa o cache contendo os dicionários de links limpos
    texto_final = bingo357.formatar_para_telegram(bilhetes_gerados, dict_cache_links)

    if texto_final:
        try:
            requests.post(url_msg, json={
                "chat_id": chat_id,
                "text": texto_final,
                "parse_mode": "Markdown",
                "disable_web_page_preview": False
            })
            print("🚀 Bilhetes do Bingo enviados com sucesso para o Telegram!")
        except Exception as e:
            print(f"⚠️ Erro ao enviar os bilhetes formatados para o Telegram: {e}")
    else:
        print("⚠️ Nenhum mercado passou nos critérios para gerar os bilhetes finais.")

if __name__ == "__main__":
    executar()
