import json
import os
import requests
from datetime import datetime
import bingo357 

def executar():
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    tipo_bingo = os.getenv('TIPO_BINGO')
    
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    caminho_json = f"telegram/jogos_{data_hoje}.json"

    if not os.path.exists(caminho_json):
        # Se não achar o arquivo do dia, tenta listar o que tem na pasta para debug
        arquivos = os.listdir("telegram") if os.path.exists("telegram") else "Pasta inexistente"
        print(f"Erro: Arquivo {caminho_json} não encontrado. Conteúdo da pasta: {arquivos}")
        return

    with open(caminho_json, "r", encoding="utf-8") as f:
        jogos_banco = json.load(f)

    # FILTRO DE HORÁRIO (Só o que ainda não começou)
    # Ajuste: Se o seu horário no JSON é string "15:30", comparamos com string
    agora_br = (datetime.now() - timedelta(hours=3)).strftime("%H:%M") 
    jogos_filtrados = [j for j in jogos_banco if j['horario'] >= agora_br]

    if not jogos_filtrados:
        # Avisa no Telegram que os jogos já acabaram
        return

    # Gera os bilhetes usando a lógica do bingo357
    bilhetes = bingo357.montar_bilhetes_estrategicos(jogos_filtrados)
    
    # IMPORTANTE: Criamos o cache para o formatador usar o LINK_BETANO que o Main salvou
    cache_dados = {f"{j['time_casa']}x{j['time_fora']}": {
        "link": j.get("link_betano"),
        "liga": j.get("liga"),
        "horario": j.get("horario"),
        "odd": j.get("odd")
    } for j in jogos_filtrados}

    texto_final = bingo357.formatar_para_telegram(bilhetes, cache_dados)
    
    # Envia a mensagem (Filtre aqui para mandar apenas o 'tipo_bingo' se desejar)
    if texto_final:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={
            "chat_id": chat_id,
            "text": f"✅ *{tipo_bingo} ATUALIZADO*\n\n{texto_final}",
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        })

if __name__ == "__main__":
    from datetime import timedelta # Necessário para o ajuste de hora se o server for UTC
    executar()
    
