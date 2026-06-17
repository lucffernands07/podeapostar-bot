import re
import json
import os

# --- NOVOS CAMINHOS PADRONIZADOS ---
PATH_RANKING_DIARIO = 'ranking/ranking_diario.json'

def extrair_porcentagem(texto_mercado):
    try:
        if not texto_mercado: return 0
        match = re.search(r'\((\d+)%\)', texto_mercado)
        return int(match.group(1)) if match else 0
    except: return 0

def extrair_odd(odd_str):
    try:
        if not odd_str or odd_str == "N/A": return 1.0
        # 🚀 NOVO: Se a odd for a string de análise dos jogadores, injeta 1.50 para o cálculo matemático de multiplicador
        if isinstance(odd_str, str) and "Análise" in odd_str: return 1.50
        if isinstance(odd_str, (int, float)): return float(odd_str)
        return float(odd_str.replace(',', '.'))
    except: return 1.0

def prioridade_mercado(mercado_texto):
    m = str(mercado_texto).lower()
    if "gols" in m: return 1
    if "1x" in m: return 2
    if "ambas" in m: return 3
    if "vitória" in m or "vitoria" in m: return 4
    if "2x" in m or "x2" in m: return 5
    # 🚀 NOVO: Jogadores ganham prioridade logo após os mercados tradicionais de resultado
    if "chutes" in m or "faltas" in m or "média" in m: return 6
    return 7

def carregar_ranking_pro():
    """Lê o ranking pré-montado pelo ranking.py"""
    if os.path.exists(PATH_RANKING_DIARIO):
        try:
            with open(PATH_RANKING_DIARIO, 'r', encoding='utf-8') as f:
                conteudo = json.load(f)
                if isinstance(conteudo, dict):
                    return conteudo.get("mercados", [])
                return conteudo 
        except: return []
    return []

def montar_bilhetes_estrategicos(dados_entrada):
    bilhetes = []
    lista_jogos = dados_entrada.get('jogos', []) if isinstance(dados_entrada, dict) else dados_entrada
    lista_jogos = [j for j in lista_jogos if isinstance(j, dict) and 'mercado' in j]

    if not lista_jogos: return bilhetes

    # --- FILTRO: DUPLA CHANCE > VITÓRIA (MESMO JOGO) ---
    jogos_agrupados = {}
    for jogo in lista_jogos:
        chave = f"{jogo['time_casa']}x{jogo['time_fora']}".lower().strip()
        if chave not in jogos_agrupados: jogos_agrupados[chave] = []
        jogos_agrupados[chave].append(jogo)

    lista_filtrada = []
    for chave, mercados in jogos_agrupados.items():
        tem_dupla = any(re.search(r'\b(1x|x2|2x)\b', m['mercado'].lower()) for m in mercados)
        if tem_dupla:
            for m in mercados:
                if "vitória" not in m['mercado'].lower() and "vitoria" not in m['mercado'].lower():
                    lista_filtrada.append(m)
        else:
            lista_filtrada.extend(mercados)
    
    lista_jogos = lista_filtrada

    # --- BINGO 3: VALOR ---
    if len(lista_jogos) >= 3:
        lista_bingo3 = sorted(lista_jogos, key=lambda x: extrair_odd(x.get('odd', '1.0')), reverse=True)[:3]
        lista_bingo3.sort(key=lambda x: x.get('horario', '00:00'))
        bilhetes.append({"id": "BINGO3", "nome": "🔥 BINGO 3: VALOR", "jogos": lista_bingo3})

    # --- BINGO 5: ESTRUTURADO ---
    if len(lista_jogos) >= 5:
        bingo5_selecao = sorted(lista_jogos, key=lambda x: extrair_odd(x.get('odd', '1.0')), reverse=True)[:3]
        restantes = [j for j in lista_jogos if j not in bingo5_selecao]
        bingo5_selecao.extend(sorted(restantes, key=lambda x: extrair_porcentagem(x.get('mercado', '')), reverse=True)[:2])
        bingo5_selecao.sort(key=lambda x: x.get('horario', '00:00'))
        bilhetes.append({"id": "BINGO5", "nome": "💰 BINGO 5: ESTRUTURADO", "jogos": bingo5_selecao[:5]})

    # --- BINGO PREMIUM (PRO): ELITE ---
    ranking_pro = carregar_ranking_pro()
    lista_premium = []
    jogos_disponiveis = lista_jogos.copy()

    for elite in ranking_pro:
        mercado_elite = elite['mercado'].upper().strip()
        
        for i in range(len(jogos_disponiveis) - 1, -1, -1):
            jogo = jogos_disponiveis[i]
            mercado_jogo = str(jogo.get('mercado', "")).upper().strip()
            
            if mercado_elite in mercado_jogo:
                lista_premium.append(jogo)
                jogos_disponiveis.pop(i) 
                
            if len(lista_premium) >= 7: break
        if len(lista_premium) >= 7: break

    if len(lista_premium) < 7:
        sobra = sorted(jogos_disponiveis, key=lambda x: extrair_porcentagem(x.get('mercado', '')), reverse=True)
        for s in sobra:
            if len(lista_premium) >= 7: break
            lista_premium.append(s)

    if len(lista_premium) >= 3:
        lista_premium.sort(key=lambda x: x.get('horario', '00:00'))
        status = "🔥 _Filtro: Ranking de Elite_" if ranking_pro else "⚠️ _Filtro: Probabilidade Diária_"
        bilhetes.append({
            "id": "PREMIUM", 
            "nome": f"💎 BINGO PRO: ELITE (TOP {len(lista_premium)})\n{status}", 
            "jogos": lista_premium
        })

    return bilhetes

def formatar_para_telegram(bilhetes, cache_dados):
    if not bilhetes: return ""
    blocos = []
    
    for b in bilhetes:
        corpo = f"*{b['nome']}*\n\n"
        odd_total = 1.0
        agrupados = {}
        
        for j in b['jogos']:
            chave_cache = f"{j.get('time_casa')}x{j.get('time_fora')}"
            info_extra = cache_dados.get(chave_cache, {})
            horario = j.get('horario') or info_extra.get('horario', '00:00')
            liga = j.get('liga') or info_extra.get('liga', 'Futebol')
            odd_valor = j.get('odd') or info_extra.get('odd', '1.0')
            link_final = info_extra.get('link') or "https://www.betano.bet.br/"
            
            link_h2h = info_extra.get('link_h2h', None)

            chave_jogo = f"{horario}_{j.get('time_casa')}_{j.get('time_fora')}"
            if chave_jogo not in agrupados:
                agrupados[chave_jogo] = {
                    "horario": horario, "liga": liga,
                    "time_casa": j.get('time_casa', 'Casa'),
                    "time_fora": j.get('time_fora', 'Fora'),
                    "mercados": [], "link": link_final,
                    "link_h2h": link_h2h  
                }
            
            agrupados[chave_jogo]["mercados"].append({
                "texto": f"🔶 {j.get('mercado')} | Odd: {odd_valor}",
                "prioridade": prioridade_mercado(j.get('mercado', ''))
            })
            odd_total *= extrair_odd(odd_valor)

        lista_blocos_jogos = []
        for chave in sorted(agrupados.keys()):
            dados = agrupados[chave]
            dados["mercados"].sort(key=lambda x: x['prioridade'])
            linhas_mercados = "\n".join([m['texto'] for m in dados["mercados"]])
            
            link_betano_limpo = dados['link'].replace(" ", "%20").replace("(", "%28").replace(")", "%29").strip()
            
            bloco_jogo = (
                f"⏱️ {dados['horario']} | {dados['liga']}\n"
                f"🏟️ {dados['time_casa']} x {dados['time_fora']}\n"
                f"{linhas_mercados}\n"
                f"🌐 [Abrir na Betano]({link_betano_limpo})"
            )
            
            if dados.get("link_h2h"):
                link_h2h_limpo = dados['link_h2h'].replace(" ", "%20").replace("(", "%28").replace(")", "%29").strip()
                bloco_jogo += f"\n📊 [Estatísticas]({link_h2h_limpo})"

            lista_blocos_jogos.append(bloco_jogo)

        corpo += "\n\n".join(lista_blocos_jogos)
        corpo += f"\n\n📈 *Odd Total: {odd_total:.2f}*\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
        blocos.append(corpo)
    
    return "\n\n".join(blocos)
