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
    # Valores padrão iniciais caso algo falhe
    config = {"bingo": 5, "horario": "DIA", "bilhete": "ACERTOS", "aviso": ""}
    
    tipo_limpo = tipo_bruto.strip() if tipo_bruto else ""

    # --- NOVO BLOCO: SEPARA OS 3 FILTROS COMBINADOS ---
    if "BINGO:" in tipo_limpo and "HORA:" in tipo_limpo:
        try:
            # Transforma a string em uma lista: ['BINGO:3', 'HORA:3H', 'TIPO:ACERTOS']
            partes = tipo_limpo.split("|")
            
            for parte in partes:
                if parte.startswith("BINGO:"):
                    config["bingo"] = int(parte.split(":")[1])
                elif parte.startswith("HORA:"):
                    config["horario"] = parte.split(":")[1]
                elif parte.startswith("TIPO:"):
                    config["bilhete"] = parte.split(":")[1]
            
            # Ajuste de nomes visuais para o aviso de carregamento no Telegram
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

    # --- COMPATIBILIDADE COM CLIQUES ANTIGOS OU DIRETOS ---
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
    
    # Processa o clique simplificado
    config = processar_comando_direto(tipo_bruto)
    qtd_alvo = config["bingo"]
    filtro_hora = config["horario"]
    estrategia = config["bilhete"]

    # 1. ENVIA O AVISO DE "AGUARDE" TOTALMENTE LIMPO (SEM BOTÕES)
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

    # 2. Inicia a busca cronológica inteligente no JSON de hoje (Corrigido fuso UTC)
    agora_br = datetime.now() - timedelta(hours=3)
    data_hoje = agora_br.strftime("%Y-%m-%d")
    caminho_json = f"telegram/jogos_{data_hoje}.json"
    caminho_ranking = "ranking/ranking_db.json"

    if not os.path.exists(caminho_json):
        print(f"Erro: Arquivo {caminho_json} não encontrado.")
        return

    with open(caminho_json, "r", encoding="utf-8") as f:
        jogos_banco = json.load(f)

    agora_texto = agora_br.strftime("%H:%M") 
    
    jogos_filtrados = []
    limite_tempo = None
    if filtro_hora == "3H": limite_tempo = agora_br + timedelta(hours=3)
    if filtro_hora == "5H": limite_tempo = agora_br + timedelta(hours=5)

    for j in jogos_banco:
        try:
            h_partes = j['horario'].split(":")
            # Monta o datetime do jogo usando a referência de Brasília
            hora_jogo = agora_br.replace(hour=int(h_partes[0]), minute=int(h_partes[1]), second=0, microsecond=0)
            
            # Ajuste de fuso da madrugada (ex: jogo à 00:55 roda depois das 23h)
            if int(h_partes[0]) < 4 and agora_br.hour > 20:
                hora_jogo += timedelta(days=1)
            
            # Remove jogos que já começaram há mais de 15 minutos (baseado em Brasília)
            if hora_jogo < agora_br - timedelta(minutes=15):
                continue
                
            # Filtra pela janela limite (3H ou 5H)
            if limite_tempo and hora_jogo > limite_tempo:
                continue
                
            j["datetime_real"] = hora_jogo
            jogos_filtrados.append(j)
        except:
            if filtro_hora == "DIA": jogos_filtrados.append(j)

    if not jogos_filtrados:
        texto_erro = f"⚠️ Não há jogos disponíveis para os filtros selecionados agora ({agora_texto})."
        menus.enviar_menu_bingo(chat_id, texto_erro)
        return

    # Carrega ranking para as estratégias de Acertos e Ambas
    ranking_db = {}
    if os.path.exists(caminho_ranking):
        try:
            with open(caminho_ranking, 'r', encoding='utf-8') as f:
                ranking_db = json.load(f)
        except: pass

    # Aplica os pesos matemáticos
    for j in jogos_filtrados:
        try: odd_val = float(j.get("odd", "1.0").replace(",", "."))
        except: odd_val = 1.0
            
        mercado_nome = j.get("mercado", "").upper().strip()
        assertividade = 0.50
        if ranking_db and "stats" in ranking_db:
            if mercado_nome in ranking_db["stats"]:
                dados_m = ranking_db["stats"][mercado_nome]
                tot = dados_m.get("green", 0) + dados_m.get("red", 0)
                if tot > 0: assertividade = dados_m["green"] / tot

        if estrategia == "ODDS":
            j["score_filtro"] = odd_val
        elif estrategia == "ACERTOS":
            j["score_filtro"] = assertividade
        elif estrategia == "AMBAS":
            j["score_filtro"] = (assertividade * 0.60) + (odd_val * 0.40)

    # Ordena pelo melhor score da estratégia escolhida
    jogos_filtrados.sort(key=lambda x: x.get("score_filtro", 0), reverse=True)

    if len(jogos_filtrados) < qtd_alvo:
        texto_insuficiente = f"ℹ️ O listão possui apenas {len(jogos_filtrados)} jogos futuros para os parâmetros atuais. Não há partidas suficientes para fechar um Bingo {qtd_alvo}."
        menus.enviar_menu_bingo(chat_id, texto_insuficiente)
        return

    # Separa a quantidade exata de jogos solicitada
    jogos_selecionados = jogos_filtrados[:qtd_alvo]
    if "datetime_real" in jogos_selecionados[0]:
        jogos_selecionados.sort(key=lambda x: x["datetime_real"])

    # Embala no dicionário lido pelo seu formatador bingo357
    bilhete_solicitado = [{
        "nome": f"🎯 BINGO {qtd_alvo} PERSONALIZADO",
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

    # Entrega o bilhete final formatado com o painel de botões acoplado
    if bilhete_solicitado:
        texto_gerado = bingo357.formatar_para_telegram(bilhete_solicitado, cache_dados)
        if texto_gerado:
            # --- CONVERSÃO PARA OS NOMES VISUAIS EXATOS DO MENUS.PY ---
            nome_hora_visual = "Do Dia" if filtro_hora == "DIA" else filtro_hora
            
            nome_modo_visual = "Mais acertos"
            if estrategia == "ODDS":
                nome_modo_visual = "Maiores Odds"
            elif estrategia == "AMBAS":
                nome_modo_visual = "Equilibrado"

            titulo = f"🎫 *SEU BILHETE FICOU PRONTO!*\n"
            titulo += f"⚙️ Filtros aplicados: *Bingo {qtd_alvo}* | *{nome_hora_visual}* | Modo *{nome_modo_visual}*\n"
            titulo += f"📊 Processado às {agora_texto}\n\n"
            menus.enviar_menu_bingo(chat_id, titulo + texto_gerado)

if __name__ == "__main__":
    executar()
        
