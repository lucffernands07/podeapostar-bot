import sys
import os
import json
import requests
from datetime import datetime, timedelta

# --- AJUSTE DE CAMINHO ---
# Isso permite que o script encontre o bingo357.py na pasta raiz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import bingo357 

def executar():
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    # O tipo_bingo vem do payload do GitHub (ex: "bingo_3", "bingo_5")
    tipo_bruto = os.getenv('TIPO_BINGO', '')
    
    # Ajuste de data (Brasília)
    hoje_ref = datetime.now() - timedelta(hours=3)
    data_hoje = hoje_ref.strftime("%Y-%m-%d")
    caminho_json = f"telegram/jogos_{data_hoje}.json"

    # 1. Verificação do Banco de Dados
    if not os.path.exists(caminho_json):
        print(f"Erro: Arquivo {caminho_json} não encontrado.")
        return

    with open(caminho_json, "r", encoding="utf-8") as f:
        jogos_banco = json.load(f)

    # 2. FILTRO DE HORÁRIO: Só o que ainda não começou
    agora_br = hoje_ref.strftime("%H:%M") 
    jogos_filtrados = [j for j in jogos_banco if j['horario'] >= agora_br]

    if not jogos_filtrados:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={
            "chat_id": chat_id, 
            "text": f"⚠️ Não há mais jogos disponíveis para gerar bilhetes agora ({agora_br})."
        })
        return

    # 3. Gera os bilhetes usando a lógica do bingo357
    bilhetes_gerados = bingo357.montar_bilhetes_estrategicos(jogos_filtrados)
    
    # 4. CACHE DE DADOS: O segredo para o link Betano e Odds funcionarem
    cache_dados = {f"{j['time_casa']}x{j['time_fora']}": {
        "link": j.get("link_betano"),
        "liga": j.get("liga"),
        "horario": j.get("horario"),
        "odd": j.get("odd")
    } for j in jogos_filtrados}

    # 5. FILTRO INTELIGENTE DO BILHETE
    # Limpamos o texto (ex: "bingo_3" vira "BINGO3")
    tipo_alvo = tipo_bruto.upper().replace("_", "").replace(" ", "")
    
    bilhete_solicitado = []
    for b in bilhetes_gerados:
        # Limpamos o nome do bilhete (ex: "🔥 BINGO 3: VALOR" vira "BINGO3VALOR")
        nome_limpo = b['nome'].upper().replace("_", "").replace(" ", "").replace(":", "")
        # Também checamos o ID (ex: "BINGO3")
        id_limpo = b.get('id', '').upper()
        
        if tipo_alvo in nome_limpo or tipo_alvo == id_limpo:
            bilhete_solicitado.append(b)
            break

    # 6. ENVIO
    if bilhete_solicitado:
        texto_final = bingo357.formatar_para_telegram(bilhete_solicitado, cache_dados)
        
        if texto_final:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            requests.post(url, data={
                "chat_id": chat_id,
                "text": f"✅ *{tipo_bruto.upper().replace('_', ' ')} ATUALIZADO*\n_(Baseado em jogos após às {agora_br})_\n\n{texto_final}",
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            })
    else:
        # Se não achou, avisa o motivo (provavelmente falta de jogos para aquele tipo)
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={
            "chat_id": chat_id,
            "text": f"ℹ️ Não há jogos futuros suficientes para montar o *{tipo_bruto}* neste momento.",
            "parse_mode": "Markdown"
        })

if __name__ == "__main__":
    executar()
    
