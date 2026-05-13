import re
import json
import os

def extrair_porcentagem(texto_mercado):
    try:
        if not texto_mercado: return 0
        match = re.search(r'\((\d+)%\)', texto_mercado)
        return int(match.group(1)) if match else 0
    except: return 0

def extrair_odd(odd_str):
    try:
        if not odd_str or odd_str == "N/A": return 1.0
        if isinstance(odd_str, (int, float)): return float(odd_str)
        return float(odd_str.replace(',', '.'))
    except: return 1.0

def prioridade_mercado(mercado_texto):
    """ Prioridade visual: 1. Gols, 2. 1X, 3. Ambas, 4. Vitória, 5. 2X """
    m = str(mercado_texto).lower()
    if "gols" in m: return 1
    if "1x" in m: return 2
    if "ambas" in m: return 3
    if "vitória" in m or "vitoria" in m: return 4
    if "2x" in m or "x2" in m: return 5
    return 6

def carregar_ranking_db():
    """Lê o histórico de greens do arquivo json dentro da pasta ranking"""
    caminho = 'ranking/ranking_db.json'
    if os.path.exists(caminho):
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                stats = json.load(f).get("stats", {})
                # Padroniza todas as chaves do ranking para MAIÚSCULO
                return {str(k).upper(): v for k, v in stats.items()}
        except: return {}
    return {}

def montar_bilhetes_estrategicos(dados_entrada):
    bilhetes = []
    
    if isinstance(dados_entrada, dict) and 'jogos' in dados_entrada:
        lista_jogos = dados_entrada['jogos']
    else:
        lista_jogos = dados_entrada

    lista_jogos = [j for j in lista_jogos if isinstance(j, dict) and 'mercado' in j]

    if not lista_jogos: 
        return bilhetes

    # --- TRAVA: DUPLA CHANCE > VITÓRIA (MESMO JOGO) ---
    jogos_agrupados = {}
    for jogo in lista_jogos:
        chave = f"{jogo['time_casa']}x{jogo['time_fora']}".lower().strip()
        if chave not in jogos_agrupados:
            jogos_agrupados[chave] = []
        jogos_agrupados[chave].append(jogo)

    lista_filtrada = []
    for chave, mercados in jogos_agrupados.items():
        tem_dupla = any(re.search(r'\b(1x|x2|2x)\b', m['mercado'].lower()) for m in mercados)
        if tem_dupla:
            for m in mercados:
                mercado_nome = m['mercado'].lower()
                if "vitória" not in mercado_nome and "vitoria" not in mercado_nome:
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
        bingo5_selecao = []
        maiores_odds = sorted(lista_jogos, key=lambda x: extrair_odd(x.get('odd', '1.0')), reverse=True)[:3]
        bingo5_selecao.extend(maiores_odds)
        
        restantes = [j for j in lista_jogos if j not in bingo5_selecao]
        maiores_porcentagens = sorted(restantes, key=lambda x: extrair_porcentagem(x.get('mercado', '')), reverse=True)[:2]
        bingo5_selecao.extend(maiores_porcentagens)
        
        if len(bingo5_selecao) < 5:
            sobra = [j for j in lista_jogos if j not in bingo5_selecao]
            bingo5_selecao.extend(sobra[:(5 - len(bingo5_selecao))])
            
        bingo5_selecao.sort(key=lambda x: x.get('horario', '00:00'))
        bilhetes.append({"id": "BINGO5", "nome": "💰 BINGO 5: ESTRUTURADO", "jogos": bingo5_selecao[:5]})

    # --- BINGO PREMIUM (PRO): ELITE ---
    stats_db = carregar_ranking_db()

    def calcular_performance_premium(jogo):
        try:
            # 1. Padroniza o mercado do jogo para bater com o ranking
            # Isso faz "+1.5 Gols (85%)" virar "+1.5 GOLS (85%)"
            mercado_raw = str(jogo.get('mercado', "")).upper().strip()
            
            # 2. Busca direta
            stat = stats_db.get(mercado_raw)
            
            # 3. Busca secundária (caso tenha diamante 💎 ou espaços duplos no ranking)
            if not stat:
                mercado_limpo = mercado_raw.replace("💎", "").replace("  ", " ").strip()
                stat = stats_db.get(mercado_limpo)
            
            if not stat: return (0.0, 0, 1.0)
            
            greens = stat.get("green", 0)
            reds = stat.get("red", 0)
            total = greens + reds
            
            aproveitamento = (greens / total) if total > 0 else 0.0
            # Retorna (Assertividade, Greens, Odd) para o critério de desempate
            return (aproveitamento, greens, extrair_odd(jogo.get('odd', '1.0')))
        except:
            return (0.0, 0, 1.0)

    # Filtro: Entra na lista se tiver histórico de Green OU se a análise do dia for >= 80%
    lista_candidatos = [j for j in lista_jogos if calcular_performance_premium(j)[1] > 0 or extrair_porcentagem(j.get('mercado')) >= 80]
    
    # Ordena: 1º por Assertividade, 2º por volume de Greens
    lista_premium = sorted(lista_candidatos, key=calcular_performance_premium, reverse=True)[:7]
    
    if lista_premium:
        lista_premium.sort(key=lambda x: x.get('horario', '00:00'))
        nome_bilhete = "💎 BINGO PRO: ELITE"
        if len(lista_premium) < 7:
            nome_bilhete += "\n⚠️ _Encontrados somente esses jogos nesse intervalo_"

        bilhetes.append({"id": "PREMIUM", "nome": nome_bilhete, "jogos": lista_premium})

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

            chave_jogo = f"{horario}_{j.get('time_casa')}_{j.get('time_fora')}"
            
            if chave_jogo not in agrupados:
                agrupados[chave_jogo] = {
                    "horario": horario, "liga": liga,
                    "time_casa": j.get('time_casa', 'Casa'),
                    "time_fora": j.get('time_fora', 'Fora'),
                    "mercados": [], "link": link_final
                }
            
            agrupados[chave_jogo]["mercados"].append({
                "texto": f"🔶 {j.get('mercado')} | Odd: {odd_valor}",
                "prioridade": prioridade_mercado(j.get('mercado', ''))
            })
            odd_total *= extrair_odd(odd_valor)

        lista_blocos_jogos = []
        for chave in agrupados:
            dados = agrupados[chave]
            dados["mercados"].sort(key=lambda x: x['prioridade'])
            linhas_mercados = "\n".join([m['texto'] for m in dados["mercados"]])
            link_limpo = dados['link'].replace(" ", "%20").replace("(", "%28").replace(")", "%29").strip()
            
            bloco_jogo = (
                f"⏱️ {dados['horario']} | {dados['liga']}\n"
                f"🏟️ {dados['time_casa']} x {dados['time_fora']}\n"
                f"{linhas_mercados}\n"
                f"🌐 [Abrir na Betano]({link_limpo})"
            )
            lista_blocos_jogos.append(bloco_jogo)

        corpo += "\n\n".join(lista_blocos_jogos)
        corpo += f"\n\n📈 *Odd Total: {odd_total:.2f}*\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
        blocos.append(corpo)
    
    return "\n\n".join(blocos)
                              
