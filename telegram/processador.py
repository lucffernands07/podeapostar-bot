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
    Lê a string unificada e separa os filtros para montar o bilhete.
    Garante que o callback do botão se sobreponha a qualquer padrão.
    """
    print("\n--- [LOG PASSO 1] DESCODIFICANDO COMANDO ---")
    print(f"📥 Recebido tipo_bruto: '{tipo_bruto}'")

    # Inicializa com valores padrão (sem referências a elite)
    config = {"bingo": 3, "horario": "DIA", "bilhete": "ACERTOS", "aviso": ""}
    tipo_limpo = tipo_bruto.strip() if tipo_bruto else ""

    # 1. PROCESSAMENTO DE CALLBACKS DO TELEGRAM (Maior Prioridade)
    if "cb_bingo_" in tipo_limpo:
        partes = tipo_limpo.split("_")
        for p in partes:
            if p.isdigit():
                config["bingo"] = int(p)
                break
        config["aviso"] = f"🎲 Escolheu: *Bingo {config['bingo']}*"
        print(f"✅ Configuração gerada por callback direto: {config}")
        return config

    # 2. PROCESSAMENTO PARA STRINGS COMPOSTAS (Webhook / Automatizado)
    if "BINGO:" in tipo_limpo and "HORA:" in tipo_limpo:
        try:
            partes = tipo_limpo.split("|")
            print(f"⚙️ A processar comando composto. Partes detetadas: {partes}")
            
            valor_b = ""
            for parte in partes:
                if parte.startswith("BINGO:"):
                    valor_b = parte.split(":")[1].upper()
                elif parte.startswith("HORA:"):
                    config["horario"] = parte.split(":")[1]
                elif parte.startswith("TIPO:"):
                    config["bilhete"] = parte.split(":")[1]

            # Extração puramente numérica para o tamanho do bingo
            digitos = "".join([c for c in valor_b if c.isdigit()])
            if digitos:
                config["bingo"] = int(digitos)
            else:
                # Se não achar número nenhum, tenta buscar na string bruta inteira
                digitos_brutos = "".join([c for c in tipo_limpo if c.isdigit()])
                config["bingo"] = int(digitos_brutos) if digitos_brutos else 3

            txt_janela = f"{config['horario']}" if config['horario'] != "DIA" else "Do Dia"
            txt_modo = "Mais acertos"
            if config['bilhete'] == "ODDS": txt_modo = "Maiores Odds"
            elif config['bilhete'] == "AMBAS": txt_modo = "Equilibrado"

            config["aviso"] = (f"🎲 Bingo: *{config['bingo']}*\n⏱️ Janela: *{txt_janela}*\n📊 Modo: *{txt_modo}*")
            print(f"✅ Configuração gerada do comando composto: {config}")
            return config
        except Exception as e:
            print(f"⚠️ Erro ao processar string composta ({e}), a usar fallbacks...")

    # 3. FALLBACK GERAL
    digitos_soltos = "".join([c for c in tipo_limpo if c.isdigit()])
    if digitos_soltos:
        config["bingo"] = int(digitos_soltos)
    else:
        config["bingo"] = 3
        
    if "ODDS" in tipo_limpo: config["bilhete"] = "ODDS"
    
    config["aviso"] = f"🚀 A processar comando recebido: *{config['bingo']}*"
    print(f"✅ Configuração gerada por fallback geral: {config}")
    return config

def executar():
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    tipo_bruto = os.getenv('TIPO_BINGO', '')
    
    config = processar_comando_direto(tipo_bruto)
    qtd_alvo = config["bingo"]
    filtro_hora = config["horario"]
    estrategia = config["bilhete"].strip().upper()

    print("\n--- [LOG PASSO 2] INICIANDO EXECUÇÃO ---")
    print(f"🎯 Quantidade alvo de confrontos a procurar: {qtd_alvo}")
    print(f"⏱️ Filtro de horário ativo: '{filtro_hora}'")
    print(f"📊 Estratégia selecionada: '{estrategia}'")

    msg_aguarde = f"{config['aviso']}\n\n⏳ *A procurar os melhores jogos na base de dados, aguarde um momento...*"
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

    agora_br = datetime.now() - timedelta(hours=3)
    data_hoje = agora_br.strftime("%Y-%m-%d")
    caminho_json = f"telegram/jogos_{data_hoje}.json"
    caminho_pendentes = "ranking/pendentes.json"

    if not os.path.exists(caminho_json):
        print(f"❌ ERRO CRÍTICO: Ficheiro {caminho_json} não encontrado.")
        return

    with open(caminho_json, "r", encoding="utf-8") as f:
        jogos_banco = json.load(f)

    print(f"📂 Base de dados diária carregada com sucesso. Total de mercados no JSON: {len(jogos_banco)}")

    dict_cache_links = {}
    for j in jogos_banco:
        casa = j.get("time_casa")
        fora = j.get("time_fora")
        link_b = j.get("link_betano")
        if casa and fora and link_b:
            chave_confronto = f"{str(casa).strip().lower()}x{str(fora).strip().lower()}"
            if chave_confronto not in dict_cache_links:
                dict_cache_links[chave_confronto] = {}
            dict_cache_links[chave_confronto]["link_betano"] = link_b

    if os.path.exists(caminho_pendentes):
        try:
            with open(caminho_pendentes, "r", encoding="utf-8") as f:
                dados_pendentes = json.load(f)
                lista_jogos_p = dados_pendentes.get("jogos", []) if isinstance(dados_pendentes, dict) else dados_pendentes
                
                for item in lista_jogos_p:
                    casa = item.get("time_casa")
                    fora = item.get("time_fora")
                    link_h2h = item.get("link_h2h")
                    if casa and fora and link_h2h:
                        chave_confronto = f"{str(casa).strip().lower()}x{str(fora).strip().lower()}"
                        if chave_confronto not in dict_cache_links:
                            dict_cache_links[chave_confronto] = {}
                        dict_cache_links[chave_confronto]["link_h2h"] = link_h2h
        except Exception as e:
            print(f"⚠️ Erro ao processar links H2H do pendentes.json: {e}")

    print("\n--- [LOG PASSO 3] FILTRANDO JOGOS POR HORÁRIO ---")
    jogos_validos_horario = []
    
    for j in jogos_banco:
        try:
            h_partes = j['horario'].split(":")
            ano_j, mes_j, dia_j = map(int, data_hoje.split("-"))
            hora_jogo = datetime(ano_j, mes_j, dia_j, int(h_partes[0]), int(h_partes[1]), 0)
            
            if int(h_partes[0]) < 4 and agora_br.hour > 20:
                hora_jogo += timedelta(days=1)
            
            estado_filtro = "APROVADO"
            if filtro_hora != "DIA" and "H" in filtro_hora:
                try:
                    horas_limite = int(filtro_hora.replace("H", ""))
                    if hora_jogo > agora_br + timedelta(hours=horas_limite) or hora_jogo < agora_br - timedelta(minutes=15):
                        continue
                except: pass
            elif filtro_hora != "DIA" and hora_jogo < agora_br - timedelta(minutes=15):
                continue
                
            j["datetime_real"] = hora_jogo
            jogos_validos_horario.append(j)
        except Exception as e:
            if filtro_hora == "DIA": 
                jogos_validos_horario.append(j)

    jogos_validos_horario.sort(key=lambda x: x.get("datetime_real", agora_br))

    print("\n--- [LOG PASSO 4] ENVIANDO PARA BINGO357 ---")
    bilhetes_gerados = bingo357.montar_bilhetes_estrategicos(
        jogos_validos_horario, 
        qtd_alvo=qtd_alvo, 
        estrategia=estrategia
    )
    
    texto_final = bingo357.formatar_para_telegram(bilhetes_gerados, dict_cache_links)

    menu_botoes = menus.extrair_markup_filtros() if hasattr(menus, 'extrair_markup_filtros') else None

    if texto_final:
        try:
            payload = {
                "chat_id": chat_id, "text": texto_final, "parse_mode": "Markdown", "disable_web_page_preview": False
            }
            if menu_botoes: payload["reply_markup"] = menu_botoes
            requests.post(url_msg, json={**payload})
            print("🚀 [LOG PASSO 5] Mensagem enviada com sucesso ao Telegram!")
        except Exception as e: print(f"⚠️ Erro ao enviar Telegram: {e}")
    else:
        msg_erro = f"{config['aviso']}\n\n⚠️😢 Não foi encontrado nenhum bilhete com esse filtro."
        try:
            payload = {
                "chat_id": chat_id, "text": msg_erro, "parse_mode": "Markdown", "disable_web_page_preview": True
            }
            if menu_botoes: payload["reply_markup"] = menu_botoes
            requests.post(url_msg, json=payload)
            print("⚠️ [LOG PASSO 5] Mensagem de erro enviada.")
        except Exception as e: print(f"⚠️ Erro ao enviar erro Telegram: {e}")

if __name__ == "__main__":
    executar()
