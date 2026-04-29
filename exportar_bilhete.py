import json
import os
from datetime import datetime

def salvar_bingos_do_dia(dicionario_bingos):
    """
    Recebe os bingos (ex: {'Bingo 3': [...], 'Bingo 5': [...]})
    e salva como apostas únicas para o ranking final.
    """
    if not dicionario_bingos:
        print("⚠️ Sem bingos para salvar.")
        return

    arquivo_json = 'bilhetes_salvos.json'
    data_hoje = datetime.now().strftime("%d/%m/%Y")
    
    # 1. Carregar histórico existente
    if os.path.exists(arquivo_json):
        with open(arquivo_json, 'r', encoding='utf-8') as f:
            try:
                historico = json.load(f)
            except:
                historico = []
    else:
        historico = []

    # 2. Fatiar bingos e remover duplicados para o ranking de mercados
    apostas_unicas = {}

    for nome_bingo, lista_jogos in dicionario_bingos.items():
        for jogo in lista_jogos:
            # Chave única: Data + Times + Mercado (para não repetir no ranking)
            chave = f"{data_hoje}_{jogo['time_casa']}_{jogo['mercado']}"
            
            if chave not in apostas_unicas:
                apostas_unicas[chave] = {
                    "data": data_hoje,
                    "time_casa": jogo['time_casa'],
                    "time_fora": jogo['time_fora'],
                    "mercado": jogo['mercado'],
                    "odd": jogo['odd'],
                    "bingos": [nome_bingo], # Lista de quais bingos ele participa
                    "status": "Pendente"
                }
            else:
                # Se o jogo já existe (veio de outro bingo), apenas adiciona o nome do novo bingo à lista
                if nome_bingo not in apostas_unicas[chave]["bingos"]:
                    apostas_unicas[chave]["bingos"].append(nome_bingo)

    # 3. Adicionar as novas apostas ao histórico (sem duplicar o dia inteiro)
    ids_existentes = [f"{a.get('data')}_{a.get('time_casa')}_{a.get('mercado')}" for a in historico]
    
    novos_registros = 0
    for chave, dados in apostas_unicas.items():
        if chave not in ids_existentes:
            historico.append(dados)
            novos_registros += 1

    # 4. Salvar arquivo
    with open(arquivo_json, 'w', encoding='utf-8') as f:
        json.dump(historico, f, indent=4, ensure_ascii=False)

    print(f"✅ Etapa 1 Concluída: {novos_registros} novas apostas únicas salvas para os rankings.")
    
