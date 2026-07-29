# telegram/raspagem_provaveis.py

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

def extrair_url_base(jogo_json, cache_pendentes):
    """Apenas recupera o link original cadastrado (link_h2h)."""
    casa = jogo_json.get("time_casa", "").strip()
    fora = jogo_json.get("time_fora", "").strip()
    chave = f"{casa.lower()}x{fora.lower()}"
    
    info_extra = cache_pendentes.get(chave, {})
    return jogo_json.get("link_h2h") or info_extra.get("link_h2h")

def raspar_titulares_flashscore(page, url_original):
    """Acessa a URL inicial, obtém o link redirecionado, formata para /resumo/equipes/ e raspa os titulares."""
    titulares_casa = []
    titulares_fora = []
    url_final = url_original
    
    try:
        # 1. Navega até o link original para que o Flashscore resolva os redirecionamentos
        page.goto(url_original, timeout=30000, wait_until="domcontentloaded")
        time.sleep(1.5)

        # 2. Captura a URL real carregada pelo navegador
        url_atual = page.url
        
        # 3. Trata a URL: deleta tudo a partir de '?' ou '#' e força /resumo/equipes/
        base_url = url_atual.split('?')[0].split('#')[0].rstrip('/')
        url_final = f"{base_url}/resumo/equipes/"
        
        print(f"🔗 URL Normalizada: {url_final}")

        # 4. Vai para a aba final de escalações
        if page.url != url_final:
            page.goto(url_final, timeout=30000, wait_until="domcontentloaded")
            time.sleep(2)

        # 5. Espera pelo container das escalações
        try:
            page.wait_for_selector(".lf__sidesBox, .lf_sidesBox", timeout=6000)
        except Exception:
            # Botão de backup caso caia numa página intermediária
            aba = page.query_selector("a[href*='equipes'], a[href*='escalacoes'], button:has-text('Escalações')")
            if aba:
                aba.click()
                time.sleep(2)

        # 6. Extração dos times no DOM
        lados = page.query_selector_all(".lf__sidesBox > .lf__side, .lf_sidesBox > .lf_side")

        if len(lados) >= 2:
            # Casa
            els_casa = lados[0].query_selector_all(".lf__participantNew, .lf_participantNew")
            for el in els_casa:
                nome = el.text_content().strip()
                nome_limpo = re.sub(r'^\d+\s*', '', nome)
                if nome_limpo and nome_limpo not in titulares_casa and len(titulares_casa) < 11:
                    titulares_casa.append(nome_limpo)

            # Fora
            els_fora = lados[1].query_selector_all(".lf__participantNew, .lf_participantNew")
            for el in els_fora:
                nome = el.text_content().strip()
                nome_limpo = re.sub(r'^\d+\s*', '', nome)
                if nome_limpo and nome_limpo not in titulares_fora and len(titulares_fora) < 11:
                    titulares_fora.append(nome_limpo)

    except Exception as e:
        print(f"⚠️ Aviso/Timeout ao raspar {url_original}: {e}")
        
    return titulares_casa, titulares_fora, url_final

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

    dados_provaveis = {}
    if os.path.exists(CAMINHO_PROVAVEIS):
        try:
            with open(CAMINHO_PROVAVEIS, "r", encoding="utf-8") as f:
                dados_provaveis = json.load(f)
        except Exception:
            dados_provaveis = {}

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

    jogos_processados_nesta_run = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print("🔍 [ESCALAÇÕES] Processando partidas...")
        
        for j in jogos:
            mercado = str(j.get("mercado", "")).lower()
            liga = j.get("liga") or j.get("campeonato", "")
            
            if "chute" in mercado and validar_liga_para_jogadores(liga):
                casa = j.get("time_casa")
                fora = j.get("time_fora")
                chave = f"{str(casa).strip().lower()}x{str(fora).strip().lower()}"
                
                # Deduplicação de loop na mesma execução
                if chave in jogos_processados_nesta_run:
                    continue
                
                jogo_existente = dados_provaveis.get(chave, {})
                t_casa_existente = jogo_existente.get("titulares_casa", [])
                t_fora_existente = jogo_existente.get("titulares_fora", [])

                if len(t_casa_existente) == 11 and len(t_fora_existente) == 11:
                    print(f"⏩ [PULADO] {casa} x {fora} já possui escalação completa.")
                    jogos_processados_nesta_run.add(chave)
                    continue

                url_original = extrair_url_base(j, cache_pendentes) or jogo_existente.get("url_flashscore")
                
                if url_original:
                    jogos_processados_nesta_run.add(chave)
                    
                    print(f"\n⚽ Buscando: {casa} x {fora} | Liga: {liga}")
                    print(f"🔗 URL Inicial: {url_original}")
                    
                    t_casa, t_fora, url_final = raspar_titulares_flashscore(page, url_original)
                    
                    if len(t_casa) > 0 or len(t_fora) > 0:
                        print(f"✅ Escalação capturada! Casa: {len(t_casa)} | Fora: {len(t_fora)}")
                    else:
                        print("⏳ Escalação ainda não liberada no Flashscore. Guardando dados do jogo...")

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
                        "url_flashscore": url_final,
                        "titulares_casa": t_casa,
                        "titulares_fora": t_fora,
                        "texto_telegram": texto_formatado,
                        "atualizado_em": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }

        browser.close()

    with open(CAMINHO_PROVAVEIS, "w", encoding="utf-8") as f:
        json.dump(dados_provaveis, f, ensure_ascii=False, indent=4)
        
    print(f"\n💾 [SALVANDO] Gravando dados em {CAMINHO_PROVAVEIS}...")
    print(f"✅ Concluído! {len(dados_provaveis)} partidas atualizadas no arquivo.")

if __name__ == "__main__":
    executar_raspagem_escalacoes()
