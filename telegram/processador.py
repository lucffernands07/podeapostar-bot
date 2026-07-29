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

    # 👈 CORRIGIDO: Agora reconhece "cb_ver_provaveis" vindo do Worker e menus.py
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

            # Extração numérica do tamanho do bingo
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
    """Lê o arquivo JSON de prováveis e retorna a string formatada filtrando vazios."""
    caminhos_tentar = ["telegram/provaveis.json", "provaveis.json"]
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
            
        lista_jogos = dados_provaveis.get("jogos", []) if isinstance(dados_provaveis, dict) else dados_provaveis
        
        jogos_validos = []
        for j in lista_jogos:
            jogadores = j.get("jogadores") or j.get("provaveis") or j.get("scouts") or []
            if jogadores and len(jogadores) > 0:
                jogos_validos.append(j)

        if not jogos_validos:
            return "⚠️ *Não há escalações prováveis disponíveis na base no momento.*"

        corpo_msg = "📋 *ESCALAÇÕES PROVÁVEIS CONFIRMADAS*\n\n"
        for item in jogos_validos:
            casa = item.get("time_casa", "Casa")
            fora = item.get("time_fora", "Fora")
            horario = item.get("horario", "")
            jogadores = item.get("jogadores") or item.get("provaveis") or item.get("scouts") or []
            
            header = f"🏟️ *{casa} x {fora}*"
            if horario:
                header = f"⏱️ {horario} | " + header
                
            corpo_msg += f"{header}\n```\n"
            for jog in jogadores:
                if isinstance(jog, dict):
                    nome = jog.get("nome", "Jogador")
                    med = jog.get("media") or jog.get("med")
                    txt_med = f" | Méd: {med}" if med else ""
                    corpo_msg += f"• {nome}{txt_med}\n"
                else:
                    corpo_msg += f"• {str(jog)}\n"
            corpo_msg += "
