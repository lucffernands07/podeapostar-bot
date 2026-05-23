import sys
import os
import json
import requests
from datetime import datetime, timedelta

# --- AJUSTE DE CAMINHO ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import bingo357 
from telegram import menus # <--- IMPORTANTE: Importar o seu arquivo de menus

def decodificar_parametros(tipo_bruto):
    """
    Decodifica a string enviada pelo Bot de: 'BINGO:5|HORA:3H|TIPO:AMBAS'
    Para um dicionário limpo do Python. Se for o formato antigo, aplica o fallback estável.
    """
    # Valores padrão de segurança
    config = {"bingo": 5, "horario": "DIA", "bilhete": "ACERTOS"}
    
    if "|" in tipo_bruto:
        partes = tipo_bruto.split("|")
        for parte in partes:
            if ":" in parte:
                chave, valor = parte.split(":")
                chave = chave.strip().lower()
                valor = valor.strip().upper()
                if chave == "bingo": config["bingo"] = int(valor)
                if chave == "hora": config["horario"] = valor
                if chave == "tipo": config["bilhete"] = valor
    else:
        # Fallback inteligente para caso rode o formato antigo
        tipo_limpo = tipo_bruto.upper()
        if "3" in tipo_limpo: config["bingo"] = 3
        if "7" in tipo_limpo or "PRO" in tipo_limpo: config["bingo"] = 7
        if "ODDS" in tipo_limpo: config["bilhete"] = "ODDS"
        
    return config

def executar():
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    tipo_bruto = os.getenv('TIPO_BINGO', '')
    
    # Decodifica os botões dinâmicos escolhidos pelo usuário
    escolhas = decodificar_parametros(tipo_bruto)
    qtd_alvo = escolhas["bingo"]
    filtro_hora = escolhas["horario"]
    estrategia = escolhas["bilhete"]

    # Mantendo seu ajuste original do fuso horário (-3h para bater com o site)
    hoje_ref = datetime.now() - timedelta(hours=3)
    data_hoje = hoje_ref.strftime("%Y-%m-%d")
    caminho_json = f"telegram/jogos_{data_hoje}.json"
    caminho_ranking = "ranking/ranking_db.json"

    if not os.path.exists(caminho_json):
        print(f"Erro: Arquivo {caminho_json} not found.")
        return

    with open(caminho_json, "r", encoding="utf-8") as f:
        jogos_banco = json.load(f)

    agora = datetime.now()
    agora_br = hoje_ref.strftime("%H:%M") 
    
    # --- PASSO 1: FILTRAGEM DE HORÁRIO DINÂMICA (CORRIGIDA) ---
    jogos_filtrados = []
    limite_tempo = None
    if filtro_hora == "3H": limite_tempo = agora + timedelta(hours=3)
    if filtro_hora == "5H": limite_tempo = agora + timedelta(hours=5)

    for j in jogos_banco:
        try:
            # Transforma a string "Horário" em um objeto datetime do dia atual
            h_partes = j['horario'].split(":")
            hora_jogo = agora.replace(hour=int(h_partes[0]), minute=int(h_partes[1]), second=0, microsecond=0)
            
            # Se o horário convertido for menor que 04:00 da manhã, 
            # pertence à madrugada seguinte (joga o dia para a frente na linha do tempo)
            if int(h_partes[0]) < 4:
                hora_jogo += timedelta(days=1)
            
            # Trava 1: O jogo já começou ou passou? (Margem de segurança de 15 minutos)
            if hora_jogo < agora - timedelta(minutes=15):
                continue
                
            # Trava 2: Se tiver filtro de 3h ou 5h, o jogo passa do limite da janela?
            if limite_tempo and hora_jogo > limite_tempo:
                continue
                
            # Guarda o objeto datetime real para usar na ordenação cronológica depois se necessário
            j["datetime_real"] = hora_jogo
            jogos_filtrados.append(j)
            
        except Exception as e:
            # Fallback de segurança caso falte algum dado no parse
            if filtro_hora == "DIA": 
                jogos_filtrados.append(j)

    if not jogos_filtrados:
        texto_erro = f"⚠️ Não há jogos disponíveis para os filtros selecionados agora ({agora_br})."
        menus.enviar_menu_bingo(chat_id, texto_erro)
        return

    # Carrega banco do ranking para validar assertividade
    ranking_db = {}
    if os.path.exists(caminho_ranking):
        try:
            with open(caminho_ranking, 'r', encoding='utf-8') as f:
                ranking_db = json.load(f)
        except: pass

    # --- PASSO 2: APLICAÇÃO DOS PESOS MATEMÁTICOS NAS ODDS/RANKING ---
    for j in jogos_filtrados:
        try:
            odd_val = float(j.get("odd", "1.0").replace(",", "."))
        except:
            odd_val = 1.0
            
        mercado_nome = j.get("mercado", "").upper().strip()
        
        assertividade = 0.50  # Neutro por padrão
        if ranking_db and "stats" in ranking_db:
            if mercado_nome in ranking_db["stats"]:
                dados_m = ranking_db["stats"][mercado_nome]
                tot = dados_m.get("green", 0) + dados_m.get("red", 0)
                if tot > 0: assertividade = dados_m["green"] / tot

        # Regras de Score baseadas nas escolhas do painel:
        if estrategia == "ODDS":
            j["score_filtro"] = odd_val
        elif estrategia == "ACERTOS":
            j["score_filtro"] = assertividade
        elif estrategia == "AMBAS":
            # Regra Híbrida: 60% peso do ranking de acertos + 40% peso do valor da Odd
            j["score_filtro"] = (assertividade * 0.60) + (odd_val * 0.40)

    # Ordena do melhor score (maior pontuação) para o pior
    jogos_filtrados.sort(key=lambda x: x.get("score_filtro", 0), reverse=True)

    if len(jogos_filtrados) < qtd_alvo:
        texto_insuficiente = f"ℹ️ O listão possui apenas {len(jogos_filtrados)} jogos futuros nesta janela ({filtro_hora}). Não há partidas suficientes para montar um Bingo {qtd_alvo}."
        menus.enviar_menu_bingo(chat_id, texto_insuficiente)
        return

    # --- PASSO 3: MONTAGEM DO BILHETE ESTRUTURADO NO PADRÃO DO BINGO357 ---
    # Pegamos os top N melhores jogos baseados na estratégia selecionada
    jogos_selecionados = jogos_filtrados[:qtd_alvo]

    # Reordena os jogos finais por horário cronológico real para o bilhete ficar bonito na tela
    if "datetime_real" in jogos_selecionados[0]:
        jogos_selecionados.sort(key=lambda x: x["datetime_real"])

    # Embala o dicionário exatamente no formato esperado pelo seu formatador bingo357
    bilhete_solicitado = [{
        "nome": f"🎯 BILHETE PERSONALIZADO: {estrategia}",
        "id": f"BINGO_{qtd_alvo}",
        "jogos": [{
            "time_casa": j["time_casa"],
            "time_fora": j["time_fora"],
            "mercado": j["mercado"]
        } for j in jogos_selecionados]
    }]

    cache_dados = {f"{j['time_casa']}x{j['time_fora']}": {
        "link": j.get("link_betano"),
        "liga": j.get("liga"),
        "horario": j.get("horario"),
        "odd": j.get("odd")
    } for j in jogos_selecionados}

    # --- PASSO 4: ENVIO FORMATADO PELO MOTOR DO BINGO357 ---
    if bilhete_solicitado:
        texto_gerado = bingo357.formatar_para_telegram(bilhete_solicitado, cache_dados)
        
        if texto_gerado:
            titulo = f"🎫 *BILHETE PERSONALIZADO GERADO*\n"
            titulo += f"🔥 Configuração: *Bingo {qtd_alvo}* | Modo: *{estrategia}*\n"
            titulo += f"⏱️ Janela de Horário: *{filtro_hora}* (Filtrado após às {agora_br})\n\n"
            
            texto_final = titulo + texto_gerado
            # Envia o bilhete e cola o painel interativo de volta embaixo
            menus.enviar_menu_bingo(chat_id, texto_final)
    else:
        texto_vazio = f"ℹ️ Erro inesperado ao processar a estratégia *{estrategia}*."
        menus.enviar_menu_bingo(chat_id, texto_vazio)

if __name__ == "__main__":
    executar()
        
