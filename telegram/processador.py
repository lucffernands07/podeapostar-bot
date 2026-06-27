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

    # Inicializa com valores padrão
    config = {"bingo": 3, "horario": "DIA", "bilhete": "ACERTOS", "aviso": "", "modo_elite": False}
    tipo_limpo = tipo_bruto.strip() if tipo_bruto else ""

    # 1. Processamento para strings compostas (Worker / Automatizado)
    if "BINGO:" in tipo_limpo and "HORA:" in tipo_limpo:
        try:
            partes = tipo_limpo.split("|")
            print(f"⚙️ A processar comando composto. Partes detetadas: {partes}")
            for parte in partes:
                if parte.startswith("BINGO:"):
                    valor_b = parte.split(":")[1]
                    
                    # Se for ELITE, tenta extrair o número ou assume 5 por padrão
                    if "ELITE" in valor_b.upper():
                        config["modo_elite"] = True
                        digitos = "".join([c for c in valor_b if c.isdigit()])
                        if digitos:
                            config["bingo"] = int(digitos)
                            print(f"👉 Bingo Elite com tamanho extraído: {config['bingo']}")
                        else:
                            config["bingo"] = 5  
                            print("🚨 [ALERTA DE ERRO] NÃO VEIO NÚMERO NO BINGO ELITE! Foi assumido o padrão de 5.")
                    else:
                        digitos = "".join([c for c in valor_b if c.isdigit()])
                        if digitos:
                            config["bingo"] = int(digitos)
                            print(f"👉 Bingo normal com tamanho extraído: {config['bingo']}")
                        else:
                            config["bingo"] = 3
                            print("🚨 [ALERTA DE ERRO] NÃO VEIO NÚMERO NO BINGO NORMAL! Foi assumido o padrão de 3.")
                        
                elif parte.startswith("HORA:"):
                    config["horario"] = parte.split(":")[1]
                elif parte.startswith("TIPO:"):
                    config["bilhete"] = parte.split(":")[1]
            
            txt_janela = f"{config['horario']}" if config['horario'] != "DIA" else "Do Dia"
            txt_modo = "Mais acertos"
            if config['bilhete'] == "ODDS": txt_modo = "Maiores Odds"
            elif config['bilhete'] == "AMBAS": txt_modo = "Equilibrado"

            txt_bingo = "✨ Elite" if config["modo_elite"] else config["bingo"]
            config["aviso"] = (f"🎲 Bingo: *{txt_bingo}*\n⏱️ Janela: *{txt_janela}*\n📊 Modo: *{txt_modo}*")
            print(f"✅ Configuração gerada do comando composto: {config}")
            return config
        except Exception as e:
            print(f"⚠️ Erro ao processar string composta ({e}), a usar fallbacks...")

    # 2. Processamento para Callbacks dos Botões do Telegram
    if "cb_bingo_" in tipo_limpo:
        partes = tipo_limpo.split("_")
        numero_detectado = False
        
        if "ELITE" in tipo_limpo.upper():
            config["modo_elite"] = True
            # Tenta varrer todas as partes do callback buscando o número do bingo (ex: "5")
            for p in partes:
                if p.isdigit():
                    config["bingo"] = int(p)
                    numero_detectado = True
            
            if not numero_detectado:
                config["bingo"] = 5 
                print(f"🚨 [ALERTA DE ERRO] NÃO VEIO NÚMERO NO CALLBACK ELITE! Recebido: '{tipo_limpo}'. Assumido: 5.")
            else:
                print(f"👉 Bingo Elite detetado com tamanho: {config['bingo']}")
                
            config["aviso"] = f"🎲 Escolheu: *Bingo {config['bingo']} (Denso/Elite)*"
        else:
            # Para callbacks normais (ex: "cb_bingo_5")
            for p in partes:
                if p.isdigit():
                    config["bingo"] = int(p)
                    numero_detectado = True
                    
            if not numero_detectado:
                config["bingo"] = 3
                print(f"🚨 [ALERTA DE ERRO] NÃO VEIO NÚMERO NO CALLBACK NORMAL! Recebido: '{tipo_limpo}'. Assumido: 3.")
            else:
                print(f"👉 Bingo normal detetado com tamanho: {config['bingo']}")
                
            config["aviso"] = f"🎲 Escolheu: *Bingo {config['bingo']}*"
        
        print(f"✅ Configuração gerada por callback de bingo: {config}")

    elif "cb_hora_" in tipo_limpo:
        config["horario"] = tipo_limpo.split("_")[-1]
        txt_h = config["horario"] if config["horario"] != "DIA" else "Do Dia"
        config["aviso"] = f"⏱️ Escolheu a janela: *{txt_h}*"
        print(f"✅ Configuração gerada por callback de hora: {config}")

    elif "cb_tipo_" in tipo_limpo:
        config["bilhete"] = tipo_limpo.split("_")[-1]
        txt_m = "Mais acertos"
        if config["bilhete"] == "ODDS": txt_m = "Maiores Odds"
        elif config["bilhete"] == "AMBAS": txt_m = "Equilibrado"
        config["aviso"] = f"📊 Escolheu a estratégia: *{txt_m}*"
        print(f"✅ Configuração gerada por callback de tipo: {config}")
    
    # 3. Fallback (Caso não seja callback nem comando conhecido)
    else:
        print("⚠️ Comando não reconhecido como callback padrão. A aplicar lógica de varredura...")
        numero_detectado = False
        
        if "3" in tipo_limpo: 
            config["bingo"] = 3
            numero_detectado = True
        elif "5" in tipo_limpo: 
            config["bingo"] = 5
            numero_detectado = True
        elif "7" in tipo_limpo or "PRO" in tipo_limpo: 
            config["bingo"] = 7
            numero_detectado = True
        elif "ELITE" in tipo_limpo.upper():
            config["bingo"] = 5
            config["modo_elite"] = True
            numero_detectado = True
            
        if not numero_detectado:
            print(f"🚨 [ALERTA DE ERRO] NÃO VEIO NÚMERO NO FALLBACK GERAL! Recebido: '{tipo_limpo}'. Assumido: 3.")
            
        if "ODDS" in tipo_limpo: config["bilhete"] = "ODDS"
        
        txt_bingo = "✨ Elite" if config["modo_elite"] else config["bingo"]
        config["aviso"] = f"🚀 A processar comando recebido: *{txt_bingo}*"
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

    # 🚀 MAPEAMENTO UNIFICADO DE LINKS
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

    # --- FILTRO DOS JOGOS POR HORÁRIO ---
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
                        estado_filtro = "REJEITADO (Fora da Janela de Horas)"
                        continue
                except: pass
            elif filtro_hora != "DIA" and hora_jogo < agora_br - timedelta(minutes=15):
                estado_filtro = "REJEITADO (Jogo já Iniciou / Passado)"
                continue
                
            j["datetime_real"] = hora_jogo
            jogos_validos_horario.append(j)
            print(f"➡️ Jogo: {j.get('time_casa')} x {j.get('time_fora')} [{j.get('horario')}] -> {estado_filtro}")
        except Exception as e:
            print(f"⚠️ Erro ao calcular horário para {j.get('time_casa')}x{j.get('time_fora')}: {e}")
            if filtro_hora == "DIA": 
                jogos_validos_horario.append(j)

    print(f"📊 Total de mercados sobreviventes aos filtros de horário: {len(jogos_validos_horario)}")

    confrontos_unicos = set(f"{j.get('time_casa')}x{j.get('time_fora')}".lower().strip() for j in jogos_validos_horario)
    print(f"🏟️ Total de confrontos únicos sobreviventes: {len(confrontos_unicos)} ({confrontos_unicos})")

    jogos_validos_horario.sort(key=lambda x: x.get("datetime_real", agora_br))

    # --- PROCESSAMENTO DOS BILHETES ---
    print("\n--- [LOG PASSO 4] ENVIANDO PARA BINGO357 ---")
    print(f"📤 Enviando {len(jogos_validos_horario)} mercados para montar_bilhetes_estrategicos (Qtd Alvo: {qtd_alvo})")
    
    bilhetes_gerados = bingo357.montar_bilhetes_estrategicos(
        jogos_validos_horario, 
        qtd_alvo=qtd_alvo, 
        estrategia=estrategia,
        modo_elite=config.get("modo_elite", False)
    )
    
    print(f"📥 Retorno do bingo357: {len(bilhetes_gerados)} bilhete(s) gerado(s).")
    if bilhetes_gerados:
        print(f"📋 Nome do bilhete final: '{bilhetes_gerados[0].get('nome')}'")
        print(f"🎮 Total de mercados incluídos no bilhete: {len(bilhetes_gerados[0].get('jogos', []))}")
        
    texto_final = bingo357.formatar_para_telegram(bilhetes_gerados, dict_cache_links)

    # --- ENVIO DOS RESULTADOS OU AVISO DE ERRO ---
    menu_botoes = menus.extrair_markup_filtros() if hasattr(menus, 'extrair_markup_filtros') else None

    if texto_final:
        try:
            payload = {
                "chat_id": chat_id,
                "text": texto_final,
                "parse_mode": "Markdown",
                "disable_web_page_preview": False
            }
            if menu_botoes:
                payload["reply_markup"] = menu_botoes

            requests.post(url_msg, json={**payload})
            print("🚀 [LOG PASSO 5] Mensagem enviada com sucesso ao Telegram!")
        except Exception as e:
            print(f"⚠️ Erro ao enviar os bilhetes formatados para o Telegram: {e}")
    else:
        msg_erro = f"{config['aviso']}\n\n⚠️😢 Não foi encontrado nenhum bilhete com esse filtro. Tente outra janela, bingo ou tente amanhã."
        try:
            payload = {
                "chat_id": chat_id,
                "text": msg_erro,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }
            if menu_botoes:
                payload["reply_markup"] = menu_botoes

            requests.post(url_msg, json=payload)
            print("⚠️ [LOG PASSO 5] Mensagem de 'não encontrado' enviada ao Telegram.")
        except Exception as e:
            print(f"⚠️ Erro ao enviar aviso de erro para o Telegram: {e}")

if __name__ == "__main__":
    executar()
