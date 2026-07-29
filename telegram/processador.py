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
    Lê a string unificada e separa os filtros para montar o bilhete ou ações de prováveis.
    Garante que o callback do botão se sobreponha a qualquer padrão.
    """
    print("\n--- [LOG PASSO 1] DESCODIFICANDO COMANDO ---")
    print(f"📥 Recebido tipo_bruto: '{tipo_bruto}'")

    config = {"bingo": 3, "horario": "PROXIMOS", "aviso": "", "acao": "GERAR"}
    tipo_limpo = tipo_bruto.strip() if tipo_bruto else ""

    # 0. AÇÕES RELACIONADAS AOS PROVÁVEIS
    if "cb_atualizar" in tipo_limpo or "ATUALIZAR" in tipo_limpo:
        config["acao"] = "ATUALIZAR_PROVAVEIS"
        config["aviso"] = "🔄 *Solicitação de Atualização de Escalações Recebida!*"
        print("✅ Ação detectada: Rodar raspagem de prováveis")
        return config

    if "cb_ver_provaveis" in tipo_limpo or "cb_provaveis" in tipo_limpo or "VER_PROVAVEIS" in tipo_limpo:
        config["acao"] = "VER_PROVAVEIS"
        config["aviso"] = "📋 *Consulta de Prováveis Recebida!*"
        print("✅ Ação detectada: Ler e exibir prováveis cadastrados")
        return config

    # 1. PROCESSAMENTO DE CALLBACKS DIRETO DO TELEGRAM (BINGOS)
    if "cb_bingo_" in tipo_limpo:
        partes = tipo_limpo.split("_")
        for p in partes:
            if p.isdigit():
                config["bingo"] = int(p)
                break
        config["aviso"] = f"🎲 Escolheu: *Bingo {config['bingo']}*"
        print(f"✅ Configuração gerada por callback direto: {config}")
        return config

    # 2. PROCESSAMENTO PARA STRINGS COMPOSTAS (Webhook / Worker Cloudflare)
    if "BINGO:" in tipo_limpo:
        try:
            partes = tipo_limpo.split("|")
            print(f"⚙️ A processar comando composto. Partes detetadas: {partes}")
            
            valor_b = ""
            for parte in partes:
                if parte.startswith("BINGO:"):
                    valor_b = parte.split(":")[1].upper()
                elif parte.startswith("HORA:"):
                    config["horario"] = parte.split(":")[1]

            digitos = "".join([c for c in valor_b if c.isdigit()])
            if digitos:
                config["bingo"] = int(digitos)
            else:
                digitos_brutos = "".join([c for c in tipo_limpo if c.isdigit()])
                config["bingo"] = int(digitos_brutos) if digitos_brutos else 3

            txt_janela = f"{config['horario']}" if config['horario'] not in ["DIA", "PROXIMOS"] else "Próximos"

            config["aviso"] = f"🎲 Bingo: *{config['bingo']}*\n⏱️ Janela: *{txt_janela}*"
            print(f"✅ Configuração gerada do comando composto: {config}")
            return config
        except Exception as e:
            print(f"⚠️ Erro ao processar string composta ({e}), a usar fallbacks...")

    # 3. FALLBACK GERAL
    digitos_soltos = "".join([c for c in tipo_limpo if c.isdigit()])
    config["bingo"] = int(digitos_soltos) if digitos_soltos else 3
    
    config["aviso"] = f"🚀 A processar comando recebido: *Bingo {config['bingo']}*"
    print(f"✅ Configuração gerada por fallback geral: {config}")
    return config

def obter_mensagem_provaveis_formatada():
    """Lê o arquivo JSON de prováveis e retorna a string formatada em estilo monoespaçado (estilo bilhete)."""
    diretorio_script = os.path.dirname(os.path.abspath(__file__))
    diretorio_raiz = os.path.dirname(diretorio_script)

    caminhos_tentar = [
        os.path.join(diretorio_script, "escalacoes", "provaveis.json"),
        os.path.join(diretorio_raiz, "telegram", "escalacoes", "provaveis.json"),
        os.path.join(diretorio_script, "provaveis.json"),
        os.path.join(diretorio_raiz, "telegram", "provaveis.json"),
        "telegram/escalacoes/provaveis.json",
        "telegram/provaveis.json",
        "provaveis.json"
    ]
    
    caminho_provaveis = None
    for path in caminhos_tentar:
        if os.path.exists(path):
            caminho_provaveis = path
            break

    if not caminho_provaveis:
        return "⚠️ *Nenhum dado de prováveis encontrado localmente.*\nClique em *Atualizar* para realizar a raspagem."

    try:
        with open(caminho_provaveis, "r", encoding="utf-8") as f:
            dados_provaveis = json.load(f)
            
        if isinstance(dados_provaveis, dict):
            lista_jogos = dados_provaveis.get("jogos", list(dados_provaveis.values()))
        else:
            lista_jogos = dados_provaveis
        
        agora_br = datetime.utcnow() - timedelta(hours=3)
        data_hoje_br = agora_br.strftime("%Y-%m-%d")

        mapa_horarios = {}
        caminhos_jogos_hoje = [
            os.path.join(diretorio_script, f"jogos_{data_hoje_br}.json"),
            f"telegram/jogos_{data_hoje_br}.json"
        ]
        for c_hoje in caminhos_jogos_hoje:
            if os.path.exists(c_hoje):
                try:
                    with open(c_hoje, "r", encoding="utf-8") as f_jogos:
                        banco_jogos = json.load(f_jogos)
                        for item_j in banco_jogos:
                            c = str(item_j.get("time_casa", "")).strip().lower()
                            f = str(item_j.get("time_fora", "")).strip().lower()
                            h = item_j.get("horario")
                            if c and f and h:
                                mapa_horarios[f"{c}x{f}"] = h
                    break
                except Exception:
                    pass

        jogos_validos = []
        for j in lista_jogos:
            tem_jogadores = j.get("titulares_casa") or j.get("jogadores") or j.get("provaveis")
            if not tem_jogadores:
                continue

            casa_norm = str(j.get("time_casa", "")).strip().lower()
            fora_norm = str(j.get("time_fora", "")).strip().lower()
            chave_conf = f"{casa_norm}x{fora_norm}"

            horario_str = str(j.get("horario", "")).strip()
            
            if (not horario_str or horario_str == "None") and chave_conf in mapa_horarios:
                horario_str = str(mapa_horarios[chave_conf]).strip()
                j["horario"] = horario_str

            if not horario_str or ":" not in horario_str:
                continue

            data_ref_str = data_hoje_br
            atualizado_em = str(j.get("atualizado_em", ""))
            if atualizado_em and " " in atualizado_em:
                data_ref_str = atualizado_em.split(" ")[0]

            try:
                ano_j, mes_j, dia_j = map(int, data_ref_str.split("-"))
                h_partes = horario_str.split(":")
                hora_h, min_m = int(h_partes[0]), int(h_partes[1])

                hora_jogo = datetime(ano_j, mes_j, dia_j, hora_h, min_m, 0)
                if hora_h < 4 and agora_br.hour > 20:
                    hora_jogo += timedelta(days=1)

                if hora_jogo < agora_br:
                    continue

                j["datetime_real"] = hora_jogo
                jogos_validos.append(j)
            except Exception:
                continue

        if not jogos_validos:
            return "⚠️ *Não há escalações prováveis de jogos futuros disponíveis no momento.*"

        jogos_validos.sort(key=lambda x: x.get("datetime_real", agora_br))

        linhas = ["📋 *ESCALAÇÕES PROVÁVEIS CONFIRMADAS*\n"]
        
        for item in jogos_validos:
            casa = item.get("time_casa", "Casa")
            fora = item.get("time_fora", "Fora")
            horario = item.get("horario", "")
            
            linhas.append(f"⏱️ {horario} | 🏟️ *{casa} x {fora}*")
            
            # --- INCÍCIO DO BLOCO DE CÓDIGO (FONTE PEQUENA/MONOESPAÇADA) ---
            linhas.append("```")
            
            tit_casa = item.get("titulares_casa", [])
            tit_fora = item.get("titulares_fora", [])

            if tit_casa or tit_fora:
                if tit_casa:
                    linhas.append(f"🏠 {casa.upper()}:")
                    linhas.append(", ".join(tit_casa))
                if tit_casa and tit_fora:
                    linhas.append("") # Linha em branco separando os times
                if tit_fora:
                    linhas.append(f"🚀 {fora.upper()}:")
                    linhas.append(", ".join(tit_fora))
            else:
                jogadores = item.get("jogadores") or item.get("provaveis") or []
                linhas.append("\n".join([f"• {str(jog)}" for jog in jogadores]))
            
            linhas.append("```\n")

        corpo_msg = "\n".join(linhas)

        if len(corpo_msg) > 4000:
            corpo_msg = corpo_msg[:3900] + "\n```\n...(Lista resumida por limite)"

        return corpo_msg
    except Exception as e:
        return f"⚠️ Erro ao carregar escalações prováveis: {e}"
            
            
def executar():
    token = os.getenv('TELEGRAM_TOKEN') or os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID') or os.getenv('TELEGRAM_CHAT_ID')
    tipo_bruto = os.getenv('TIPO_BINGO', '') or os.getenv('TELEGRAM_TIPO', '')
    
    if token:
        token = token.strip()
    url_msg = f"https://api.telegram.org/bot{token}/sendMessage"
    
    config = processar_comando_direto(tipo_bruto)
    menu_botoes = menus.extrair_markup_filtros() if hasattr(menus, 'extrair_markup_filtros') else None

    # --- FLUXO 1: APENAS VER PROVÁVEIS ---
    if config.get("acao") == "VER_PROVAVEIS":
        texto_provaveis = obter_mensagem_provaveis_formatada()
        payload = {
            "chat_id": chat_id,
            "text": texto_provaveis,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        if menu_botoes: payload["reply_markup"] = menu_botoes
        requests.post(url_msg, json=payload)
        return

    # --- FLUXO 2: ATUALIZAR PROVÁVEIS ---
    if config.get("acao") == "ATUALIZAR_PROVAVEIS":
        print("\n--- [LOG EXTRA] EXECUTANDO RASPAGEM DE PROVÁVEIS ---")
        try:
            requests.post(url_msg, json={
                "chat_id": chat_id,
                "text": "🔄 *Atualizando Escalações Prováveis...*\n\n⚠️ Aguarde alguns minutos, foi iniciado o servidor para atualizar a base de dados.",
                "parse_mode": "Markdown"
            })
            
            import raspagem_provaveis
            if hasattr(raspagem_provaveis, 'executar_raspagem_escalacoes'):
                raspagem_provaveis.executar_raspagem_escalacoes()
            elif hasattr(raspagem_provaveis, 'executar'):
                raspagem_provaveis.executar()
            
            texto_provaveis = obter_mensagem_provaveis_formatada()
            
            payload = {
                "chat_id": chat_id,
                "text": f"✅ *Atualização Concluída!*\n\n{texto_provaveis}",
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }
            if menu_botoes: payload["reply_markup"] = menu_botoes
            requests.post(url_msg, json=payload)
            return
            
        except Exception as e:
            print(f"❌ Erro ao executar raspagem_provaveis: {e}")
            requests.post(url_msg, json={
                "chat_id": chat_id,
                "text": f"⚠️ *Falha ao atualizar escalações:* {e}",
                "parse_mode": "Markdown"
            })
            return

    # --- FLUXO 3: GERAR BILHETES ---
    qtd_alvo = config["bingo"]
    filtro_hora = config["horario"]

    print("\n--- [LOG PASSO 2] INICIANDO EXECUÇÃO ---")
    print(f"🎯 Quantidade alvo de confrontos a procurar: {qtd_alvo}")
    print(f"⏱️ Filtro de horário ativo: '{filtro_hora}'")

    msg_aguarde = f"{config['aviso']}\n\n⏳ *A procurar os melhores jogos na base de dados, aguarde um momento...*"
    try:
        requests.post(url_msg, json={
            "chat_id": chat_id,
            "text": msg_aguarde,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        })
    except Exception as e:
        print(f"⚠️ Erro ao enviar aviso de aguarde silencioso: {e}")

    agora_br = datetime.utcnow() - timedelta(hours=3)
    data_hoje = agora_br.strftime("%Y-%m-%d")
    
    diretorio_script = os.path.dirname(os.path.abspath(__file__))
    caminhos_banco = [
        os.path.join(diretorio_script, f"jogos_{data_hoje}.json"),
        f"telegram/jogos_{data_hoje}.json"
    ]
    
    caminho_json = None
    for c_banco in caminhos_banco:
        if os.path.exists(c_banco):
            caminho_json = c_banco
            break

    caminho_pendentes = os.path.join(os.path.dirname(diretorio_script), "ranking", "pendentes.json")

    if not caminho_json:
        print(f"❌ ERRO CRÍTICO: Ficheiro de jogos do dia não encontrado.")
        return

    with open(caminho_json, "r", encoding="utf-8") as f:
        jogos_banco = json.load(f)

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

    jogos_validos_horario = []
    for j in jogos_banco:
        try:
            h_partes = j['horario'].split(":")
            ano_j, mes_j, dia_j = map(int, data_hoje.split("-"))
            hora_jogo = datetime(ano_j, mes_j, dia_j, int(h_partes[0]), int(h_partes[1]), 0)
            
            if int(h_partes[0]) < 4 and agora_br.hour > 20:
                hora_jogo += timedelta(days=1)
            
            if hora_jogo < (agora_br - timedelta(minutes=15)):
                continue

            if filtro_hora not in ["DIA", "PROXIMOS"] and "H" in filtro_hora:
                try:
                    horas_limite = int(filtro_hora.replace("H", ""))
                    if hora_jogo > agora_br + timedelta(hours=horas_limite):
                        continue
                except: 
                    pass
                
            j["datetime_real"] = hora_jogo
            jogos_validos_horario.append(j)
        except Exception as e:
            if filtro_hora in ["DIA", "PROXIMOS"]: 
                jogos_validos_horario.append(j)

    jogos_validos_horario.sort(key=lambda x: x.get("datetime_real", agora_br))

    bilhetes_gerados = bingo357.montar_bilhetes_estrategicos(
        jogos_validos_horario, 
        qtd_alvo=qtd_alvo
    )
    
    texto_final = bingo357.formatar_para_telegram(bilhetes_gerados, dict_cache_links)

    if texto_final:
        try:
            payload = {
                "chat_id": chat_id, "text": texto_final, "parse_mode": "Markdown", "disable_web_page_preview": False
            }
            if menu_botoes: payload["reply_markup"] = menu_botoes
            requests.post(url_msg, json=payload)
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
                            
