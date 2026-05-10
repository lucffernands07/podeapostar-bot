import json
import os
import requests
from datetime import datetime
import bingo357  # Importa seu módulo de lógica

def filtrar_jogos_futuros(lista_jogos):
    """Remove jogos que já começaram baseando-se no horário atual"""
    agora = datetime.now().strftime("%H:%M")
    # Filtra apenas jogos cujo horário é maior que o horário de agora
    return [j for j in lista_jogos if j['horario'] > agora]

def executar():
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    tipo_bingo = os.getenv('TIPO_BINGO') # Ex: "BINGO 3", "PREMIUM"
    
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    caminho_json = f"telegram/jogos_{data_hoje}.json"

    # 1. Carrega o Banco de Dados do dia
    if not os.path.exists(caminho_json):
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                      data={"chat_id": chat_id, "text": "❌ Erro: O banco de dados de hoje ainda não foi criado."})
        return

    with open(caminho_json, "r", encoding="utf-8") as f:
        todos_os_jogos = json.load(f)

    # 2. FILTRO DE HORÁRIO: Só o que ainda vai acontecer
    jogos_disponiveis = filtrar_jogos_futuros(todos_os_jogos)

    if not jogos_disponiveis:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                      data={"chat_id": chat_id, "text": "⚠️ Não há mais jogos disponíveis para hoje que ainda não começaram."})
        return

    # 3. RE-GERAÇÃO DO BINGO ESPECÍFICO
    # O bingo357 vai olhar os jogos que restaram e montar o bilhete
    bilhetes_atualizados = bingo357.montar_bilhetes_estrategicos(jogos_disponiveis)
    
    # 4. BUSCA O CACHE DE LINKS/DADOS PARA O BOTÃO
    # Usamos a mesma lógica de cache que você já tem no main
    cache_dados = {f"{j['time_casa']}x{j['time_fora']}": {
        "link": j.get("link_betano"),
        "liga": j.get("liga"),
        "horario": j.get("horario"),
        "odd": j.get("odd")
    } for j in jogos_disponiveis}

    # 5. FORMATAÇÃO FINAL
    texto_final = bingo357.formatar_para_telegram(bilhetes_atualizados, cache_dados)
    
    # Filtra o texto para enviar apenas o Bingo que o usuário pediu
    # (Ou envia tudo se preferir)
    if texto_final:
        mensagem = f"✅ *{tipo_bingo} ATUALIZADO*\n(Jogos que ainda não começaram)\n\n" + texto_final
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                      data={"chat_id": chat_id, "text": mensagem, "parse_mode": "Markdown"})

if __name__ == "__main__":
    executar()
    
