import sys
import os
import json
import requests
from datetime import datetime, timedelta

# --- AJUSTE DE CAMINHO ---
# Isso permite que o script encontre o bingo357.py na pasta de cima
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import bingo357 

def executar():
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    tipo_bingo = os.getenv('TIPO_BINGO') # Ex: "BINGO 3"
    
    # Ajuste de data (Brasília)
    hoje_ref = datetime.now() - timedelta(hours=3)
    data_hoje = hoje_ref.strftime("%Y-%m-%d")
    caminho_json = f"telegram/jogos_{data_hoje}.json"

    # Verificação do Banco de Dados
    if not os.path.exists(caminho_json):
        arquivos = os.listdir("telegram") if os.path.exists("telegram") else "Pasta vazia"
        print(f"Erro: Arquivo {caminho_json} não encontrado. Arquivos na pasta: {arquivos}")
        return

    with open(caminho_json, "r", encoding="utf-8") as f:
        jogos_banco = json.load(f)

    # FILTRO DE HORÁRIO: Só o que ainda não começou
    agora_br = hoje_ref.strftime("%H:%M") 
    jogos_filtrados = [j for j in jogos_banco if j['horario'] >= agora_br]

    if not jogos_filtrados:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={
            "chat_id": chat_id, 
            "text": f"⚠️ Não há mais jogos disponíveis para o {tipo_bingo} agora ({agora_br})."
        })
        return

    # Gera os bilhetes usando a sua lógica
    bilhetes = bingo357.montar_bilhetes_estrategicos(jogos_filtrados)
    
    # CACHE DE DADOS: O segredo para o link Betano e Odds funcionarem
    cache_dados = {f"{j['time_casa']}x{j['time_fora']}": {
        "link": j.get("link_betano"),
        "liga": j.get("liga"),
        "horario": j.get("horario"),
        "odd": j.get("odd")
    } for j in jogos_filtrados}

    # FORMATAÇÃO
    # Filtramos os bilhetes para gerar texto apenas do que foi pedido no botão
    bilhete_solicitado = [b for b in bilhetes if b['nome'] == tipo_bingo]
    
    if bilhete_solicitado:
        texto_final = bingo357.formatar_para_telegram(bilhete_solicitado, cache_dados)
        
        if texto_final:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            requests.post(url, data={
                "chat_id": chat_id,
                "text": f"✅ *{tipo_bingo} ATUALIZADO*\n_(Horário base: {agora_br})_\n\n{texto_final}",
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            })
    else:
        print(f"O filtro não encontrou jogos suficientes para montar o {tipo_bingo} agora.")

if __name__ == "__main__":
    executar()
    
