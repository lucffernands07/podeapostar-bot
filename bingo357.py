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
        # 🚀 NOVO: Se a odd for a string de análise dos jogadores, injeta 1.50 para o cálculo matemático de multiplicador e ordenação
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
    # 🚀 AJUSTADO: Cartões adicionado junto com as prioridades analíticas de jogadores
    if "chutes" in m or "faltas" in m or "média" in m or "cartões" in m or "cartao" in m: return 6
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

def montar_bilhetes_estrategicos(dados_entrada, qtd_alvo=5, estrategia="ACERTOS", modo_elite=False):
    """
    Ordena e monta UM ÚNICO bilhete respeitando a estratégia escolhida.
    
    🚀 MODO ELITE: Filtra e traz os 3 JOGOS com maior volume/densidade de mercados,
    retornando TODOS os mercados aprovados desses jogos (sem limite de linhas).
    """
    bilhetes = []
    lista_jogos = dados_entrada
    
    if not lista_jogos: return bilhetes

    # 1. Filtro de duplicidade (Dupla Chance vs Vitória)
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
            
    # 2. 📊 Aplicação das Estratégias de Ordenação Tradicional
    if estrategia == "ODDS":
        jogos_ordenados = sorted(lista_filtrada, key=lambda x: extrair_odd(x.get('odd', '1.0')), reverse=True)
    elif estrategia == "ACERTOS":
        def pegar_assertividade(x):
            mercado_txt = x.get('mercado', '')
            if "%" in mercado_txt:
                return extrair_porcentagem(mercado_txt)
            if "5/5j" in mercado_txt: return 100
            if "4/5j" in mercado_txt: return 80
            if "3/5j" in mercado_txt: return 60
            if "3/3j" in mercado_txt: return 100
            if "2/3j" in mercado_txt: return 66
            # 🚀 AJUSTADO: Dá peso máximo na ordenação por acertos para o mercado de cartões analíticos (3 de 3 jogos coletados)
            if "confronto cartões" in mercado_txt.lower(): return 100
            return 50
        jogos_ordenados = sorted(lista_filtrada, key=lambda x: pegar_assertividade(x), reverse=True)
    else: # EQUILIBRADO / AMBAS
        def calcular_peso_equilibrado(x):
            odd = extrair_odd(x.get('odd', '1.0'))
            mercado_txt = x.get('mercado', '')
            if "%" in mercado_txt:
                pct = extrair_porcentagem(mercado_txt) / 100.0
            else:
                # 🚀 AJUSTADO: Validação equilibrada considerando os cartões analíticos (3/3 jogos coletados) como 1.0 (100%)
                pct = 1.0 if ("3/3j" in mercado_txt or "5/5j" in mercado_txt or "confronto cartões" in mercado_txt.lower()) else 0.66
            return odd * pct
        jogos_ordenados = sorted(lista_filtrada, key=lambda x: calcular_peso_equilibrado(x), reverse=True)

    # 3. 🚀 CORTE POR JOGO (SE FOR ELITE) VS CORTE POR MERCADO (TRADICIONAL)
    if modo_elite:
        # Conta o volume total de mercados que CADA jogo possui na lista final filtrada
        contagem_confrontos = {}
        for m in jogos_ordenados:
            chave_jogo = f"{m['time_casa']}x{m['time_fora']}".lower().strip()
            contagem_confrontos[chave_jogo] = contagem_confrontos.get(chave_jogo, 0) + 1
        
        # Ordena as chaves dos confrontos estritamente pelo maior volume de mercados gerados
        jogos_mais_densos = sorted(
            contagem_confrontos.keys(),
            key=lambda k: contagem_confrontos[k],
            reverse=True
        )
        
        # Pega no máximo os 3 confrontos que mais possuem mercados ativos
        top_3_jogos = jogos_mais_densos[:3]
        
        # Captura TODOS os mercados de forma irrestrita pertencentes apenas a esses 3 confrontos tops
        jogos_selecionados = [
            m for m in jogos_ordenados 
            if f"{m['time_casa']}x{m['time_fora']}".lower().strip() in top_3_jogos
        ]
        
        qtd_confrontos_real = len(top_3_jogos)
        aviso_escassez = ""
        if qtd_confrontos_real < 3:
            aviso_escassez = f"\n⚠️ *Nota:* Foram solicitados 3 jogos elite, mas a janela só possuía {qtd_confrontos_real} disponíveis."
            
        nome_bilhete = f"✨ BINGO ELITE DE {qtd_confrontos_real} JOGOS ({estrategia})"
    else:
        # Lógica padrão antiga: Corta estritamente por limite de mercados fixos (linhas)
        jogos_selecionados = jogos_ordenados[:qtd_alvo]
        qtd_real = len(jogos_selecionados)
        aviso_escassez = ""
        if qtd_real < qtd_alvo:
            aviso_escassez = f"\n⚠️ *Nota:* Foram solicitados {qtd_alvo} mercados, mas a janela só possuía {qtd_real} disponíveis."
            
        traducao_modo = "MAIORES ODDS" if estrategia == "ODDS" else "MAIS ACERTOS" if estrategia == "ACERTOS" else "EQUILIBRADO"
        nome_bilhete = f"🔥 BINGO DE {qtd_real} MERCADOS ({traducao_modo})"

    # Ordena cronologicamente os jogos selecionados para exibição limpa no Telegram
    jogos_selecionados.sort(key=lambda x: x.get('horario', '00:00'))

    # 4. Retorna o Bilhete Único estruturado
    if jogos_selecionados:
        bilhetes.append({
            "id": "BINGO_CUSTOM", 
            "nome": nome_bilhete, 
            "jogos": jogos_selecionados,
            "aviso_escassez": aviso_escassez
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
            # 🚀 Normalização rigorosa em minúsculas para encontrar no cache
            chave_cache = f"{str(j.get('time_casa')).strip().lower()}x{str(j.get('time_fora')).strip().lower()}"
            info_extra = cache_dados.get(chave_cache, {})
            
            horario = j.get('horario') or info_extra.get('horario', '00:00')
            liga = j.get('liga') or info_extra.get('liga', 'Futebol')
            odd_valor = j.get('odd') or info_extra.get('odd', '1.0')
            
            # 🚀 Puxa o link do objeto do jogo ou do cache unificado
            link_final = j.get('link_betano') or info_extra.get('link_betano') or "https://www.betano.bet.br/"
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
            
            mercado_limpo = j.get('mercado', '')
            
            # 🚀 REGRA EXTRAÇÃO / ARREDONDAMENTO PARA CHUTES E FALTAS
            if "Faltas Sofridas:" in mercado_limpo or "Chutes no Alvo:" in mercado_limpo:
                match_med = re.search(r'Méd:\s*([\d.]+)', mercado_limpo)
                if match_med:
                    media_num = float(match_med.group(1))
                    valor_arredondado = int(media_num + 0.5)
                    if valor_arredondado < 1: valor_arredondado = 1
                    mercado_limpo = re.sub(r'\(.*?\)', f'({valor_arredondado}+)', mercado_limpo)
                
                texto_final_linha = f"🔶 {mercado_limpo}"
                
            # 🚀 NOVA REGRA: IDENTIFICA E PADRONIZA CARTÕES NO MESMO VISUAL (X+)
            elif "confronto cartões:" in mercado_limpo.lower() or "confronto cartões" in mercado_limpo.lower():
                # Busca qualquer número decimal logo após "Cartões:" ou "cartões"
                match_med = re.search(r'(?:cartões|Cartões):\s*([\d.]+)', mercado_limpo)
                if match_med:
                    media_num = float(match_med.group(1))
                    # Regra Luciano de arredondamento:
                    valor_arredondado = int(media_num + 0.5)
                    if valor_arredondado < 1: valor_arredondado = 1
                    
                    # Reconstrói a string limpando os emojis poluídos e deixando o padrão correto
                    mercado_limpo = f"Confronto Cartões ({valor_arredondado}+)"
                else:
                    # Fallback de segurança se falhar o Regex, limpa o texto bruto tirando os emojis
                    mercado_limpo = mercado_limpo.split("(")[0].strip()
                    
                texto_final_linha = f"🔶 {mercado_limpo}"
            else:
                texto_final_linha = f"🔶 {mercado_limpo} | Odd: {odd_valor}"

            agrupados[chave_jogo]["mercados"].append({
                "texto": texto_final_linha,
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
        
        if b.get("aviso_escassez"):
            corpo += b["aviso_escassez"]
            
        blocos.append(corpo)
    
    return "\n\n".join(blocos)

    
    return "\n\n".join(blocos)
