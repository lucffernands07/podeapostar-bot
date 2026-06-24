import re
import json
import os

# --- NOVOS CAMINHOS PADRONIZADOS ---
PATH_RANKING_DIARIO = 'ranking/ranking_diario.json'

def extrair_porcentagem(texto_mercado):
    try:
        if not texto_mercado:
            return 0
        match = re.search(r'\((\d+)%\)', texto_mercado)
        return int(match.group(1)) if match else 0
    except:
        return 0

def extrair_odd(odd_str):
    try:
        if not odd_str or odd_str == "N/A" or odd_str == "":
            return 1.50
        if isinstance(odd_str, str) and ("Análise" in odd_str or "chutes" in odd_str.lower() or "cartã" in odd_str.lower() or "cartao" in odd_str.lower()):
            return 1.50
        if isinstance(odd_str, (int, float)):
            return float(odd_str)
        return float(odd_str.replace(',', '.'))
    except:
        return 1.50

def prioridade_mercado(mercado_texto):
    m = str(mercado_texto).lower()
    if "gols" in m: return 1
    if "1x" in m: return 2
    if "ambas" in m: return 3
    if "vitória" in m or "vitoria" in m: return 4
    if "2x" in m or "x2" in m: return 5
    if "chutes" in m or "média" in m or "cartões" in m or "cartao" in m: return 6
    return 7

def montar_bilhetes_estrategicos(dados_entrada, qtd_alvo=5, estrategia="ACERTOS", modo_elite=False):
    """
    Ordena e monta UM ÚNICO bilhete respeitando a estratégia e a quantidade pedida no menu.
    """
    bilhetes = []
    lista_jogos = dados_entrada

    if not lista_jogos:
        return bilhetes

    # 1. Filtro de duplicidade
    jogos_agrupados = {}
    for jogo in lista_jogos:
        chave = f"{jogo['time_casa']}x{jogo['time_fora']}".lower().strip()
        if chave not in jogos_agrupados:
            jogos_agrupados[chave] = []
        jogos_agrupados[chave].append(jogo)

    lista_filtrada = []
    for chave, mercados in jogos_agrupados.items():
        for m in mercados:
            if "falta" in m['mercado'].lower():
                continue
            if "chutes" in m['mercado'].lower() or "cartã" in m['mercado'].lower() or "cartao" in m['mercado'].lower():
                if not m.get('odd') or str(m['odd']) in ["N/A", "1.0"]:
                    m['odd'] = "1.50"
            lista_filtrada.append(m)

    # 2. 📊 Ordenação
    if estrategia == "ODDS":
        jogos_ordenados = sorted(lista_filtrada, key=lambda x: extrair_odd(x.get('odd', '1.50')), reverse=True)
    elif estrategia == "ACERTOS":
        def pegar_assertividade(x):
            mercado_txt = x.get('mercado', '')
            if "%" in mercado_txt:
                return extrair_porcentagem(mercado_txt)
            if "5/5j" in mercado_txt or "confronto cartões" in mercado_txt.lower() or "cartões totais" in mercado_txt.lower() or "chutes" in mercado_txt.lower():
                return 100
            return 50
        jogos_ordenados = sorted(lista_filtrada, key=lambda x: pegar_assertividade(x), reverse=True)
    else:
        def calcular_peso_equilibrado(x):
            odd = extrair_odd(x.get('odd', '1.50'))
            pct = extrair_porcentagem(x.get('mercado', '')) / 100.0 if "%" in x.get('mercado', '') else 0.7
            return odd * pct
        jogos_ordenados = sorted(lista_filtrada, key=lambda x: calcular_peso_equilibrado(x), reverse=True)

    # 3. 🚀 SELEÇÃO DINÂMICA (RESPEITA QTD_ALVO)
    if modo_elite:
        contagem_confrontos = {}
        for m in jogos_ordenados:
            chave_jogo = f"{m['time_casa']}x{m['time_fora']}".lower().strip()
            contagem_confrontos[chave_jogo] = contagem_confrontos.get(chave_jogo, 0) + 1

        jogos_ordenados.sort(key=lambda m: contagem_confrontos[f"{m['time_casa']}x{m['time_fora']}".lower().strip()], reverse=True)
        jogos_selecionados = jogos_ordenados[:qtd_alvo]
        nome_bilhete = f"✨ BINGO {len(jogos_selecionados)} (DENSO) - {estrategia}"
    else:
        jogos_selecionados = jogos_ordenados[:qtd_alvo]
        nome_bilhete = f"🔥 BINGO DE {len(jogos_selecionados)} JOGOS ({estrategia})"

    # Ordena cronologicamente
    jogos_selecionados.sort(key=lambda x: x.get('horario', '00:00'))

    if jogos_selecionados:
        bilhetes.append({
            "id": "BINGO_CUSTOM",
            "nome": nome_bilhete,
            "jogos": jogos_selecionados
        })

    return bilhetes

def formatar_para_telegram(bilhetes, cache_dados):
    if not bilhetes:
        return ""
    blocos = []

    for b in bilhetes:
        corpo = f"*{b['nome']}*\n\n"
        odd_total = 1.0
        agrupados = {}

        for j in b['jogos']:
            chave_cache = f"{str(j.get('time_casa')).strip().lower()}x{str(j.get('time_fora')).strip().lower()}"
            info_extra = cache_dados.get(chave_cache, {})
            horario = j.get('horario') or info_extra.get('horario', '00:00')
            liga = j.get('liga') or info_extra.get('liga', 'Futebol')
            odd_valor = j.get('odd') or info_extra.get('odd', '1.50')

            chave_jogo = f"{horario}_{j.get('time_casa')}_{j.get('time_fora')}"
            if chave_jogo not in agrupados:
                agrupados[chave_jogo] = {
                    "horario": horario,
                    "liga": liga,
                    "time_casa": j.get('time_casa'),
                    "time_fora": j.get('time_fora'),
                    "mercados": [],
                    "link": j.get('link_betano') or info_extra.get('link_betano', "https://www.betano.bet.br/"),
                    "link_h2h": info_extra.get('link_h2h')
                }

            mercado_limpo = j.get('mercado', '')
            if "Chutes no Alvo:" in mercado_limpo:
                match_med = re.search(r'Méd:\s*([\d.]+)', mercado_limpo)
                if match_med:
                    valor = int(float(match_med.group(1)) + 0.5)
                    mercado_limpo = re.sub(r'\(.*?\)', f'({max(1, valor)}+)', mercado_limpo)
                texto_final = f"🔶 {mercado_limpo}"
            elif "cartões" in mercado_limpo.lower() or "cartao" in mercado_limpo.lower():
                if "totais:" in mercado_limpo.lower():
                    texto_final = f"🔶 {mercado_limpo}"
                else:
                    match_med = re.search(r'(\d+[\.,]\d+)', mercado_limpo)
                    media = float(match_med.group(1).replace(',', '.')) if match_med else 1.0
                    if media >= 4.0:
                        texto = "Cartões Totais: +4.5"
                    elif media >= 3.0:
                        texto = "Cartões Totais: +2.5"
                    elif media >= 2.0:
                        texto = "Cartões Totais: +1.5"
                    else:
                        texto = "Cartões Totais: -3.5"
                    texto_final = f"🔶 {texto}"
            else:
                texto_final = f"🔶 {mercado_limpo} | Odd: {odd_valor}"

            agrupados[chave_jogo]["mercados"].append({"texto": texto_final, "prioridade": prioridade_mercado(j.get('mercado', ''))})
            odd_total *= extrair_odd(odd_valor)

        lista_blocos = []
        for chave in sorted(agrupados.keys()):
            d = agrupados[chave]
            d["mercados"].sort(key=lambda x: x['prioridade'])
            linhas = "\n".join([m['texto'] for m in d["mercados"]])
            bloco = f"⏱️ {d['horario']} | {d['liga']}\n🏟️ {d['time_casa']} x {d['time_fora']}\n{linhas}\n🌐 [Abrir na Betano]({d['link']})"
            if d.get("link_h2h"):
                bloco += f"\n📊 [Estatísticas]({d['link_h2h']})"
            lista_blocos.append(bloco)

        corpo += "\n\n".join(lista_blocos)
        corpo += f"\n\n📈 *Odd Total: {odd_total:.2f}*\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
        blocos.append(corpo)

    return "\n\n".join(blocos)
            
