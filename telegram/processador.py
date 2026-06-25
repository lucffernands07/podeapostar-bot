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
    config = {"bingo": 5, "horario": "DIA", "bilhete": "ACERTOS", "aviso": "", "modo_elite": False}
    tipo_limpo = tipo_bruto.strip() if tipo_bruto else ""

    if "cb_bingo_" in tipo_limpo:
        # Formato esperado: cb_bingo_3_ELITE ou cb_bingo_5
        partes = tipo_limpo.split("_")
        try:
            # O número está na posição 2 (cb=0, bingo=1, 3 ou 5=2)
            config["bingo"] = int(partes[2])
        except (IndexError, ValueError):
            config["bingo"] = 5
            
        if "ELITE" in tipo_limpo.upper():
            config["modo_elite"] = True
            config["aviso"] = f"🚀 Comando: *Bingo {config['bingo']} Elite*"
        else:
            config["modo_elite"] = False
            config["aviso"] = f"🚀 Comando: *Bingo {config['bingo']}*"

    elif "cb_hora_" in tipo_limpo:
        # Formato esperado: cb_hora_3H
        config["horario"] = tipo_limpo.split("_")[-1]
        config["aviso"] = f"⏱️ Janela: *{config['horario']}*"

    elif "cb_tipo_" in tipo_limpo:
        # Formato esperado: cb_tipo_ODDS
        config["bilhete"] = tipo_limpo.split("_")[-1]
        config["aviso"] = f"📊 Estratégia: *{config['bilhete']}*"
    
    else:
        # Fallback para comandos de texto simples
        if "3" in tipo_limpo: config["bingo"] = 3
        elif "5" in tipo_limpo: config["bingo"] = 5
        elif "7" in tipo_limpo: config["bingo"] = 7
        if "ELITE" in tipo_limpo.upper(): config["modo_elite"] = True
        if "ODDS" in tipo_limpo: config["bilhete"] = "ODDS"
        config["aviso"] = f"🚀 Comando: *Bingo {config['bingo']} {'Elite' if config['modo_elite'] else ''}*"

    return config


def executar():
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    tipo_bruto = os.getenv('TIPO_BINGO', '')
    
    config = processar_comando_direto(tipo_bruto)
    
    # --- BUSCA DE DADOS ---
    agora_br = datetime.now() - timedelta(hours=3)
    data_hoje = agora_br.strftime("%Y-%m-%d")
    caminho_json = f"telegram/jogos_{data_hoje}.json"
    
    if not os.path.exists(caminho_json):
        print(f"Erro: Arquivo {caminho_json} não encontrado.")
        return

    with open(caminho_json, "r", encoding="utf-8") as f:
        jogos_banco = json.load(f)

    # --- DEFINIÇÃO DOS LINKS (CORRIGINDO O NAMEERROR) ---
    dict_cache_links = {}
    for j in jogos_banco:
        casa = j.get("time_casa")
        fora = j.get("time_fora")
        link_b = j.get("link_betano")
        if casa and fora and link_b:
            chave = f"{str(casa).strip().lower()}x{str(fora).strip().lower()}"
            if chave not in dict_cache_links: dict_cache_links[chave] = {}
            dict_cache_links[chave]["link_betano"] = link_b

    # --- PROCESSAMENTO ---
    bilhetes_gerados = bingo357.montar_bilhetes_estrategicos(
        jogos_banco, 
        qtd_alvo=config["bingo"], 
        estrategia=config["bilhete"].upper(),
        modo_elite=config["modo_elite"]
    )
    
    # Agora dict_cache_links existe e é passado com o cabeçalho aviso_menu
    texto_final = bingo357.formatar_para_telegram(
        bilhetes_gerados, 
        dict_cache_links, 
        aviso_menu=config["aviso"]
    )
    
    menu_botoes = menus.extrair_markup_filtros() if hasattr(menus, 'extrair_markup_filtros') else None

    # Envio
    payload = {"chat_id": chat_id, "text": texto_final or "⚠️ Sem jogos para este filtro.", "parse_mode": "Markdown"}
    if menu_botoes: payload["reply_markup"] = menu_botoes
    requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json=payload)

if __name__ == "__main__":
    executar()
    
