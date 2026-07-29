import os
import json
import re
import time
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

DIRETORIO_ESCALACOES = "telegram/escalacoes"
CAMINHO_PROVAVEIS = os.path.join(DIRETORIO_ESCALACOES, "provaveis.json")

# 🟢 LISTA BRANCA DE LIGAS ELITE
LIGAS_ELITE_JOGADORES = [
    "Brasileirão Série A", "Copa do Brasil", "Libertadores", "Sul-Americana",
    "Brasileirão Série B", "Argentina - Liga Profesional", "Mundo - Copa do Mundo",
    "Europa - Champions League", "Inglaterra - Premier League", "Espanha - LaLiga",
    "Alemanha - Bundesliga", "Italia - Serie A", "França - Ligue 1",
    "Europa - League", "Inglaterra - FA Cup", "Espanha - Copa del Rey",
    "Alemanha - DFB Pokal", "Portugal - Primeira Liga", "Países Baixos - Eredivisie",
    "Mundo - Amistoso Internacional"
]

def validar_liga_para_jogadores(nome_liga):
    """Verifica se a liga do confronto pertence à lista de ligas elite permitidas."""
    if not nome_liga:
        return False
        
    liga_limpa = nome_liga.strip().lower()
    
    for liga_permitida in LIGAS_ELITE_JOGADORES:
        if liga_permitida.lower() in liga_limpa or liga_limpa in liga_permitida.lower():
            return True
            
    return False

def garantir_diretorio():
    if not os.path.exists(DIRETORIO_ESCALACOES):
        os.makedirs(DIRETORIO_ESCALACOES)

def formatar_linha_jogadores(lista_jogadores, por_linha=4):
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
        return f"{base}/#/resumo-do-jogo/escalacoes/equipes"
    return None

def raspar_titulares_flashscore(page, url):
    """Acessa a URL do Flashscore e extrai a escalação dos titulares."""
    titulares_casa = []
    titulares_fora = []
    
    try:
        page.goto(url, timeout=40000, wait_until="networkidle")
        
        # Espera o contêiner de escalações carregar
        page.wait_for_selector(".lf__lineUp, .lf__side, .lineupTable", timeout=10000)
        time.sleep(2)

        # 🟢 ESTRATÉGIA 1: Pega pelos blocos de campo ou laterais de escalação (Casas vs Fora)
        lados = page.query_selector_all(".lf__side, .lineup")

        if len(lados) >= 2:
            # Pega apenas elementos de nomes no bloco da Casa
            els_casa = lados[0].query_selector_all(".lf__participantName, .lineup__player .lineup__cell--name")
            titulares_casa = [el.text_content().strip() for el in els_casa if el.text_content().strip()]

            # Pega apenas elementos de nomes no bloco de Fora
            els_fora = lados[1].query_selector_all(".lf__participantName, .lineup__player .lineup__cell--name")
            titulares_fora = [el.text_content().strip() for el in els_fora if el.text_content().strip()]

        # 🟢 ESTRATÉGIA 2 (FALLBACK): Seleção direta por links de jogadores caso os blocos não venham separados
        if not titulares_casa or not titulares_fora:
            jogadores_links = page.query_selector_all("a[href*='/jogador/'] .lf__participantName, .lf__participantName")
            todos_nomes = []
            
            for el in jogadores_links:
                nome = el.text_content().strip()
                if nome and nome not in todos_nomes:
                    todos_nomes.append(nome)

            if len(todos_nomes) >= 22:
                titulares_casa = todos_nomes[:11]
                titulares_fora = todos_nomes[11:22]

        # Limpeza rápida de duplicados mantendo a ordem
        titulares_casa = list(dict.fromkeys(titulares_casa))[:11]
        titulares_fora = list(dict.fromkeys(titulares_fora))[:11]

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
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print("🔍 [ESCALAÇÕES] Verificando jogos válidos (Mercado 'Chutes no gol' + Ligas Elite)...")
        
        for j in jogos:
            mercado = str(j.get("mercado", "")).lower()
            liga = j.get("liga") or j.get("campeonato", "")
            
            # 🟢 DUPLEX FILTRO: Apenas mercado de chute E liga autorizada
            if "chute" in mercado and validar_liga_para_jogadores(liga):
                casa = j.get("time_casa")
                fora = j.get("time_fora")
                chave = f"{str(casa).strip().lower()}x{str(fora).strip().lower()}"
                
                if chave not in dados_provaveis:
                    url_escalacao = extrair_url_escalacao(j, cache_pendentes)
                    
                    if url_escalacao:
                        print(f"\n⚽ Partida Permitida: {casa} x {fora} | Liga: {liga}")
                        print(f"🔗 URL: {url_escalacao}")
                        print("⏳ Acessando página e extraindo titulares...")
                        
                        t_casa, t_fora = raspar_titulares_flashscore(page, url_escalacao)
                        
                        texto_formatado = (
                            f"**{casa}**:\n"
                            f"{formatar_linha_jogadores(t_casa)}\n\n"
                            f"**{fora}**:\n"
                            f"{formatar_linha_jogadores(t_fora)}"
                        )

                        dados_provaveis[chave] = {
                            "time_casa": casa,
                            "time_fora": fora,
                            "liga": liga,
                            "url_flashscore": url_escalacao,
                            "titulares_casa": t_casa,
                            "titulares_fora": t_fora,
                            "texto_telegram": texto_formatado,
                            "atualizado_em": datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
            elif "chute" in mercado:
                print(f"⏭️ [IGNORADO] {j.get('time_casa')} x {j.get('time_fora')} (Liga '{liga}' fora da lista elite)")

        browser.close()

    with open(CAMINHO_PROVAVEIS, "w", encoding="utf-8") as f:
        json.dump(dados_provaveis, f, ensure_ascii=False, indent=4)
        
    print(f"\n💾 [SALVANDO] Gravando dados em {CAMINHO_PROVAVEIS}...")
    print(f"✅ Concluído! {len(dados_provaveis)} escalações salvas em {CAMINHO_PROVAVEIS}.")

if __name__ == "__main__":
    executar_raspagem_escalacoes()
                
