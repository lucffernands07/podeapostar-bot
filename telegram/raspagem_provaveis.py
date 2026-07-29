# telegram/raspagem_provaveis.py

import os
import json
import re
from datetime import datetime, timedelta

DIRETORIO_ESCALACOES = "telegram/escalacoes"
CAMINHO_PROVAVEIS = os.path.join(DIRETORIO_ESCALACOES, "provaveis.json")

def garantir_diretorio():
    if not os.path.exists(DIRETORIO_ESCALACOES):
        os.makedirs(DIRETORIO_ESCALACOES)

def formatar_slug(texto):
    """Transforma 'Barracas Central' em 'barracas-central'"""
    texto_limpo = re.sub(r'[^\w\s-]', '', texto.lower())
    return re.sub(r'[-\s]+', '-', texto_limpo).strip('-')

def extrair_url_escalacao(jogo_json, cache_pendentes):
    """
    Converte o link do jogo/H2H na URL direta de escalações previstas do Flashscore
    """
    casa = jogo_json.get("time_casa", "").strip()
    fora = jogo_json.get("time_fora", "").strip()
    chave = f"{casa.lower()}x{fora.lower()}"
    
    # 1. Tenta pegar o link H2H do cache
    info_extra = cache_pendentes.get(chave, {})
    link_h2h = jogo_json.get("link_h2h") or info_extra.get("link_h2h")
    
    if link_h2h and "flashscore" in link_h2h:
        # Troca a aba do H2H para a aba de equipes/escalações
        base = link_h2h.split("/#/")[0].split("/resumo")[0].rstrip("/")
        return f"{base}/resumo/equipes/"
    
    return None

def executar_raspagem_escalacoes():
    garantir_diretorio()
    agora_br = datetime.now() - timedelta(hours=3)
    data_hoje = agora_br.strftime("%Y-%m-%d")
    
    caminho_jogos_diario = f"telegram/jogos_{data_hoje}.json"
    caminho_pendentes = "ranking/pendentes.json"

    if not os.path.exists(caminho_jogos_diario):
        print(f"⚠️ Ficheiro {caminho_jogos_diario} não encontrado.")
        return

    with open(caminho_jogos_diario, "r", encoding="utf-8") as f:
        jogos = json.load(f)

    cache_pendentes = {}
    if os.path.exists(caminho_pendentes):
        try:
            with open(caminho_pendentes, "r", encoding="utf-8") as f:
                dados_p = json.load(f)
                lista_p = dados_p.get("jogos", []) if isinstance(dados_p, dict) else dados_p
                for item in lista_p:
                    c = item.get("time_casa", "").lower().strip()
                    f_time = item.get("time_fora", "").lower().strip()
                    cache_pendentes[f"{c}x{f_time}"] = item
        except Exception as e:
            print(f"⚠️ Erro ao carregar pendentes: {e}")

    dados_provaveis = {}

    print("🔍 [ESCALAÇÕES] Montando URLs do Flashscore para partidas com 'Chutes no gol'...")
    
    for j in jogos:
        mercado = str(j.get("mercado", "")).lower()
        if "chute" in mercado:
            casa = j.get("time_casa")
            fora = j.get("time_fora")
            chave = f"{str(casa).strip().lower()}x{str(fora).strip().lower()}"
            
            if chave not in dados_provaveis:
                url_escalacao = extrair_url_escalacao(j, cache_pendentes)
                
                if url_escalacao:
                    print(f"⚽ URL Gerada ({casa} x {fora}):\n   🔗 {url_escalacao}")
                    
                    # Guardamos a URL gerada e a estrutura inicial para o scraper ler os titulares
                    dados_provaveis[chave] = {
                        "time_casa": casa,
                        "time_fora": fora,
                        "url_flashscore": url_escalacao,
                        "titulares_casa": [], # O Playwright/Selenium vai preencher aqui
                        "titulares_fora": [],
                        "atualizado_em": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }

    # Salva em telegram/escalacoes/provaveis.json
    with open(CAMINHO_PROVAVEIS, "w", encoding="utf-8") as f:
        json.dump(dados_provaveis, f, ensure_ascii=False, indent=4)
        
    print(f"\n✅ {len(dados_provaveis)} URLs de escalações salvas em {CAMINHO_PROVAVEIS}!")

if __name__ == "__main__":
    executar_raspagem_escalacoes()
