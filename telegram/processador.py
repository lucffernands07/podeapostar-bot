
import os
import json
import requests
import sys

# Importamos as funções de lógica que estão na raiz do projeto
sys.path.append(os.getcwd())
from bingo357 import montar_bilhetes_estrategicos, formatar_para_telegram

def processar_solicitacao_bingo():
    # 1. Recupera as variáveis enviadas pelo GitHub Actions / Worker
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    tipo_solicitado = os.getenv('TIPO_BINGO') # ex: bingo_3, bingo_premium
    
    # 2. Carrega os jogos que o bot minerou hoje (estão na pasta ranking)
    caminho_jogos = 'ranking/pendentes.json'
    
    if not os.path.exists(caminho_jogos):
        print("Arquivo pendentes.json não encontrado!")
        return

    with open(caminho_jogos, 'r', encoding='utf-8') as f:
        lista_jogos = json.load(f)

    # 3. Monta todos os bilhetes possíveis usando a lógica do bingo357
    # Passamos um dicionário vazio para cache_links se não tivermos os links agora
    todos_bilhetes = montar_bilhetes_estrategicos(lista_jogos)
    
    # 4. Filtra apenas o bilhete que o usuário clicou
    # Mapeamento de IDs (ajuste conforme o ID que está no seu bingo357.py)
    mapeamento = {
        "bingo_3": "BINGO3",
        "bingo_5": "BINGO5",
        "bingo_7": "BINGO7",
        "bingo_premium": "PREMIUM" # Mude para "bingo_premium" se você já alterou no bingo357
    }
    
    id_alvo = mapeamento.get(tipo_solicitado)
    bilhete_filtrado = [b for b in todos_bilhetes if b['id'] == id_alvo]

    if not bilhete_filtrado:
        mensagem = f"⚠️ Não encontrei jogos suficientes para gerar o {tipo_solicitado} agora."
    else:
        # 5. Formata para o padrão do Telegram
        # Como o pendentes.json já tem os links, passamos um dicionário vazio para o cache
        mensagem = formatar_para_telegram(bilhete_filtrado, {})

    # 6. Envia para o Telegram
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": mensagem,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    
    requests.post(url, json=payload)
    print(f"Bingo {tipo_solicitado} enviado com sucesso!")

if __name__ == "__main__":
    processar_solicitacao_bingo()
