# telegram/raspagem_provaveis.py

import os
import json
import re
import time
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

DIRETORIO_ESCALACOES = "telegram/escalacoes"
CAMINHO_PROVAVEIS = os.path.join(DIRETORIO_ESCALACOES, "provaveis.json")

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
    if not nome_liga:
        return False
    liga_limpa = nome_liga.strip().lower()
    for liga_permitida in LIGAS_ELITE_JOGADORES:
        if liga_permitida.lower() in liga_limpa or liga_limpa in liga_permitida.lower():
            return True
    return False

def garantir_diretorio():
    if not os.path.exists(DIRETORIO_ESCALACOES):
        os.makedirs(DIRETORIO_ESCALACOES, exist_ok=True)

def formatar_linha_jogadores(lista_jogadores, por_linha=4):
    if not lista_jogadores:
        return "Escalação provável não disponível"
    linhas = []
    for i in range(0, len(lista_jogadores), por_linha):
        grupo = lista_jogadores[i:i + por_linha]
        linhas.append(", ".join(grupo))
    return "\n".join(linhas)

def extrair_url_base(jogo_json, cache_pendentes):
    casa = jogo_json.get("time_casa", "").strip()
    fora = jogo_json.get("time_fora", "").strip()
    chave = f"{casa.lower()}x{fora.lower()}"
    info_extra = cache_pendentes.get(chave, {})
    return jogo_json.get("link_h2h") or info_extra.get("link_h2h")

def raspar_titulares_flashscore(page, url_original):
    titulares_casa = []
    titulares_fora = []
    url_final = url_original

    try:
        page.goto(url_original, timeout=45000, wait_until="domcontentloaded")
        time.sleep(2)

        # 1. Normaliza a URL para a aba de formações/equipes
        url_atual = page.url
        base_url = url_atual.split('?')[0].split('#')[0].rstrip('/')
        
        if not base_url.endswith("/resumo/equipes"):
            url_final = f"{base_url}/resumo/equipes/"
        else:
            url_final = f"{base_url}/"
        
        if page.url != url_final:
            page.goto(url_final, timeout=30000, wait_until="domcontentloaded")
            time.sleep(2)

        # 2. Força o Scroll até o final da página para renderizar as tabelas inferiores (TITULARES e RESERVAS)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)

        # 3. Busca a seção específica de "TITULARES" na página
        # O Flashscore agrupa por blocos (substituídos, titulares, reservas)
        secoes = page.query_selector_all(".lf__sides, .lf__sidesBox")

        for secao in secoes:
            # Verifica se esta seção pertence ao bloco de TITULARES
            header_parent = secao.evaluate_handle("el => el.closest('.lf__section, .section') || el.parentElement")
            texto_cabecalho = header_parent.as_element().text_content().upper() if header_parent.as_element() else ""

            # Se for a seção de substitutos ou reservas, ignora
            if "RESERVAS" in texto_cabecalho or "SUBSTITUÍDOS" in texto_cabecalho:
                continue

            lados = secao.query_selector_all(".lf__side")
            if len(lados) >= 2:
                def extrair_nomes(lado_element):
                    nomes = []
                    elementos = lado_element.query_selector_all(".lf__participantNew, .lf__participant")
                    for el in elementos:
                        texto = el.text_content().strip()
                        if not texto:
                            continue
                        
                        linhas = [l.strip() for l in texto.split('\n') if l.strip()]
                        for linha in linhas:
                            nome_limpo = re.sub(r'^\d+\s*', '', linha)
                            nome_limpo = re.sub(r'\s*\d+(\.\d+)?$', '', nome_limpo).strip()
                            
                            # Remove tags de goleiro (G) se houver e limpa
                            nome_limpo = re.sub(r'\s*\(G\)', '', nome_limpo, flags=re.IGNORECASE).strip()
                            
                            if nome_limpo and not nome_limpo.replace('.', '').isdigit() and len(nome_limpo) > 2:
                                if nome_limpo not in nomes and len(nomes) < 11:
                                    nomes.append(nome_limpo)
                    return nomes

                tc = extrair_nomes(lados[0])
                tf = extrair_nomes(lados[1])

                # Se achou uma lista com volume real de titulares, assume o resultado
                if len(tc) >= 7 or len(tf) >= 7:
                    titulares_casa = tc
                    titulares_fora = tf
                    break

    except Exception as e:
        print(f"⚠️ Erro ao raspar {url_original}: {e}")
        
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
            print(f"⚠️ Erro ao ler pendentes: {e}")

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
                
                if chave in jogos_processados_nesta_run:
                    continue
                
                jogo_existente = dados_provaveis.get(chave, {})
                t_casa_existente = jogo_existente.get("titulares_casa", [])
                t_fora_existente = jogo_existente.get("titulares_fora", [])

                # Pula se já capturou os 11 de cada lado
                if len(t_casa_existente) == 11 and len(t_fora_existente) == 11:
                    print(f"⏩ [PULADO] {casa} x {fora} já possui escalação completa (11x11).")
                    jogos_processados_nesta_run.add(chave)
                    continue

                url_original = extrair_url_base(j, cache_pendentes) or jogo_existente.get("url_flashscore")
                
                if url_original:
                    jogos_processados_nesta_run.add(chave)
                    
                    print(f"\n⚽ Buscando: {casa} x {fora} | Liga: {liga}")
                    print(f"🔗 URL Inicial: {url_original}")
                    
                    t_casa, t_fora, url_final = raspar_titulares_flashscore(page, url_original)
                    
                    # PROTEÇÃO: Se a busca atual falhou/veio vazia mas tínhamos algo antigo, preserva
                    if len(t_casa) == 0 and len(t_casa_existente) > 0:
                        t_casa = t_casa_existente
                    if len(t_fora) == 0 and len(t_fora_existente) > 0:
                        t_fora = t_fora_existente

                    if len(t_casa) > 0 or len(t_fora) > 0:
                        print(f"✅ Escalação capturada! Casa: {len(t_casa)} | Fora: {len(t_fora)}")
                    else:
                        print("⏳ Escalação ainda não disponível no Flashscore.")

                    texto_formatado = (
                        f"**{casa}**:\n"
                        f"{formatar_linha_jogadores(t_casa)}\n\n"
                        f"**{fora}**:\n"
                        f"{formatar_linha_jogadores(t_fora)}"
                    )

                    # Atualiza o dicionário de saída
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

    # Garantia de salvamento
    garantir_diretorio()
    with open(CAMINHO_PROVAVEIS, "w", encoding="utf-8") as f:
        json.dump(dados_provaveis, f, ensure_ascii=False, indent=4)
        
    print(f"\n💾 [SALVANDO] Gravando dados em {CAMINHO_PROVAVEIS}...")
    print(f"✅ Concluído! {len(dados_provaveis)} partidas registradas no JSON.")

if __name__ == "__main__":
    executar_raspagem_escalacoes()
