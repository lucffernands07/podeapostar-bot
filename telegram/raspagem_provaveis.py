# telegram/raspagem_provaveis.py

import os
import json
import re
import time
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

DIRETORIO_ESCALACOES = "telegram/escalacoes"
CAMINHO_PROVAVEIS = os.path.join(DIRETORIO_ESCALACOES, "provaveis.json")

def garantir_diretorio():
    if not os.path.exists(DIRETORIO_ESCALACOES):
        os.makedirs(DIRETORIO_ESCALACOES)

def formatar_linha_jogadores(lista_jogadores, por_linha=4):
    """
    Formata uma lista de jogadores em blocos de até N por linha.
    Exemplo:
    jogador1, jogador2, jogador3, jogador4
    jogador5, jogador6...
    """
    if not lista_jogadores:
        return "Escalação provável não disponível"
    
    linhas = []
    for i in range(0, len(lista_jogadores), por_linha):
        grupo = lista_jogadores[i:i + por_linha]
        linhas.append(", ".join(grupo))
    return "\n".join(linhas)

def extrair_url_escalacao(jogo_json, cache_pendentes):
    casa = jogo_json.get("time_casa", "").strip()
    fora = jogo_json.get("time_fora", "").strip()
    chave = f"{casa.lower()}x{fora.lower()}"
    
    info_extra = cache_pendentes.get(chave, {})
    link_h2h = jogo_json.get("link_h2h") or info_extra.get("link_h2h")
    
    if link_h2h and "flashscore" in link_h2h:
        base = link_h2h.split("/#/")[0].split("/resumo")[0].rstrip("/")
        return f"{base}/resumo/equipes/"
    return None

def raspar_titulares_flashscore(page, url):
    """Acessa a URL do Flashscore e raspa a lista de titulares previstos."""
    titulares_casa = []
    titulares_fora = []
    
    try:
        page.goto(url, timeout=30000, wait_until="domcontentloaded")
        time.sleep(3) # Aguarda renderização dos componentes
        
        # Seletores de escalação provável do Flashscore
        # Procura os elementos dos times
        jogadores_elementos = page.query_selector_all(".lf__participantName, .lf__player")
        
        # Se encontrou lista de escalação
        if jogadores_elementos:
            nomes = [el.text_content().strip() for el el in jogadores_elementos if el.text_content().strip()]
            # O Flashscore renderiza 11 do Mandante seguidos de 11 do Visitante
            if len(nomes) >= 22:
                titulares_casa = nomes[:11]
                titulares_fora = nomes[11:22]
            elif len(nomes) > 0:
                metade = len(nomes) // 2
                titulares_casa = nomes[:metade]
                titulares_fora = nomes[metade:]
    except Exception as e:
        print(f"⚠️ Erro ao raspar URL {url}: {e}")
        
    return titulares_casa, titulares_fora

def executar_raspagem_escalacoes():
    garantir_diretorio()
    agora_br = datetime.now() - timedelta(hours=3)
    data_hoje = agora_br.strftime("%Y-%m-%d")
    
    caminho_jogos_diario = f"telegram/jogos_{data_hoje}.json"
    caminho_pendentes = "ranking/pendentes.json"

    if not os.path.exists(caminho_jogos_diario):
        print(f"⚠️ Arquivo {caminho_jogos_diario} não encontrado.")
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
            print(f"⚠️ Erro no pendentes: {e}")

    dados_provaveis = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("🔍 [ESCALAÇÕES] Verificando jogos com 'Chutes no gol'...")
        for j in jogos:
            mercado = str(j.get("mercado", "")).lower()
            if "chute" in mercado:
                casa = j.get("time_casa")
                fora = j.get("time_fora")
                chave = f"{str(casa).strip().lower()}x{str(fora).strip().lower()}"
                
                if chave not in dados_provaveis:
                    url_escalacao = extrair_url_escalacao(j, cache_pendentes)
                    
                    if url_escalacao:
                        print(f"⚽ Raspando escalação de: {casa} x {fora}")
                        t_casa, t_fora = raspar_titulares_flashscore(page, url_escalacao)
                        
                        # Formata o texto final pronto para exibição no Telegram
                        texto_formatado = (
                            f"**{casa}**:\n"
                            f"{formatar_linha_jogadores(t_casa)}\n\n"
                            f"**{fora}**:\n"
                            f"{formatar_linha_jogadores(t_fora)}"
                        )

                        dados_provaveis[chave] = {
                            "time_casa": casa,
                            "time_fora": fora,
                            "url_flashscore": url_escalacao,
                            "titulares_casa": t_casa,
                            "titulares_fora": t_fora,
                            "texto_telegram": texto_formatado,
                            "atualizado_em": datetime.now().strftime("%Y-%m-%d %H:%M")
                        }

        browser.close()

    # Salva no arquivo final
    with open(CAMINHO_PROVAVEIS, "w", encoding="utf-8") as f:
        json.dump(dados_provaveis, f, ensure_ascii=False, indent=4)
        
    print(f"\n✅ Concluído! {len(dados_provaveis)} escalações salvas em {CAMINHO_PROVAVEIS}")

if __name__ == "__main__":
    executar_raspagem_escalacoes()
                     
