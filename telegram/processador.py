import sys
import os
import json
import requests
from datetime import datetime, timedelta

# --- AJUSTE DE CAMINHO ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import bingo357 
from telegram import menus # <--- IMPORTANTE: Importar o seu arquivo de menus

def executar():
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    tipo_bruto = os.getenv('TIPO_BINGO', '')
    
    hoje_ref = datetime.now() - timedelta(hours=3)
    data_hoje = hoje_ref.strftime("%Y-%m-%d")
    caminho_json = f"telegram/jogos_{data_hoje}.json"

    if not os.path.exists(caminho_json):
        print(f"Erro: Arquivo {caminho_json} not found.")
        return

    with open(caminho_json, "r", encoding="utf-8") as f:
        jogos_banco = json.load(f)

    agora_br = hoje_ref.strftime("%H:%M") 
    jogos_filtrados = [j for j in jogos_banco if j['horario'] >= agora_br]

    if not jogos_filtrados:
        texto_erro = f"⚠️ Não há mais jogos disponíveis para gerar bilhetes agora ({agora_br})."
        menus.enviar_menu_bingo(chat_id, texto_erro)
        return

    bilhetes_gerados = bingo357.montar_bilhetes_estrategicos(jogos_filtrados)
    
    cache_dados = {f"{j['time_casa']}x{j['time_fora']}": {
        "link": j.get("link_betano"),
        "liga": j.get("liga"),
        "horario": j.get("horario"),
        "odd": j.get("odd")
    } for j in jogos_filtrados}
    
    # --- BUSCA DO BILHETE (CORRIGIDA) ---
    tipo_alvo = tipo_bruto.upper().replace("_", "").replace(" ", "")
    bilhete_solicitado = [] # <--- IMPORTANTE: Inicializar a lista aqui

    for b in bilhetes_gerados:
        nome_limpo = b['nome'].upper().replace("_", "").replace(" ", "").replace(":", "").replace("💎", "")
        id_limpo = b.get('id', '').upper()

        # Se o que foi clicado bater com o nome ou com o ID (PREMIUM, BINGO3, BINGO5)
        if tipo_alvo in nome_limpo or tipo_alvo == id_limpo or (tipo_alvo == "BINGOPRO" and id_limpo == "PREMIUM"):
            bilhete_solicitado.append(b)
            break

    # --- 6. ENVIO CORRIGIDO ---
    if bilhete_solicitado:
        texto_gerado = bingo357.formatar_para_telegram(bilhete_solicitado, cache_dados)
        
        if texto_gerado:
            titulo = f"✅ *{tipo_bruto.upper().replace('_', ' ')} ATUALIZADO*\n_(Baseado em jogos após às {agora_br})_\n\n"
            texto_final = titulo + texto_gerado
            menus.enviar_menu_bingo(chat_id, texto_final)
    else:
        texto_vazio = f"ℹ️ Não há jogos futuros suficientes para montar o *{tipo_bruto}* neste momento."
        menus.enviar_menu_bingo(chat_id, texto_vazio)

if __name__ == "__main__":
    executar()
    
