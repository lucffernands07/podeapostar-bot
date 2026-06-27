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
            return 1.30
        # 🟢 CORRIGIDO: Adicionado "falta" para assumir odd padrão na multiplicação do Bingo
        if isinstance(odd_str, str) and ("Análise" in odd_str or "chutes" in odd_str.lower() or "falta" in odd_str.lower() or "cartã" in odd_str.lower() or "cartao" in odd_str.lower()):
            return 1.30
        if isinstance(odd_str, (int, float)):
            return float(odd_str)
        return float(odd_str.replace(',', '.'))
    except:
        return 1.30

def prioridade_mercado(mercado_texto):
    m = str(mercado_texto).lower()
    
    if "gols" in m: return 1
    if "1x" in m: return 2
    
    # 🟢 CORRIGIDO: Agrupando chutes e faltas na mesma faixa de prioridade de scout de jogador
    if "chute" in m: return 3 
    if "falta" in m: return 3.1
    
    if "cartão" in m or "cartao" in m: return 4
    if "vitória" in m or "vitoria" in m: return 5
    if "ambas" in m: return 6
    if "2x" in m or "x2" in m: return 7
    
    return 8

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
    bilhetes = []
    if not dados_entrada: return bilhetes

    # 1. Agrupa todos os mercados por confronto
    jogos_agrupados = {}
    for jogo in dados_entrada:
        chave = f"{jogo['time_casa']}x{jogo['time_fora']}".lower().strip()
        if chave not in jogos_agrupados: jogos_agrupados[chave] = []
        jogos_agrupados[chave].append(jogo)

    # 2. Ordena os confrontos pelo número de mercados (mais densos primeiro)
    lista_chaves = sorted(jogos_agrupados.keys(), key=lambda k: len(jogos_agrupados[k]), reverse=True)
    
    # 🟢 CORREÇÃO: Fatiamos a lista de chaves exatamente no tamanho do alvo (Ex: se pedir 5, pega 5)
    chaves_selecionadas = lista_chaves[:qtd_alvo]
    
    jogos_selecionados = []
    for chave in chaves_selecionadas:
        jogos_selecionados.extend(jogos_agrupados[chave])
    
    total_reais = len(chaves_selecionadas)
    nome_bilhete = f"✨ BINGO {total_reais} JOGOS - {estrategia.upper()}"

    if jogos_selecionados:
        bilhetes.append({"id": "BINGO_CUSTOM", "nome": nome_bilhete, "jogos": jogos_selecionados})

    return bilhetes

def formatar_para_telegram(bilhetes, cache_dados, aviso_menu=""):
    if not bilhetes: return ""
    
    titulo_principal = aviso_menu if aviso_menu else "🚀 *MENU DE BINGOS DISPONÍVEIS*"
    corpo_total = f"{titulo_principal}\n\n"
    
    for b in bilhetes:
        corpo = f"*{b.get('nome', 'BINGO')}*\n\n"
        odd_total = 1.0
        agrupados = {}
        
        for idx, j in enumerate(b.get('jogos', [])):
            t1 = str(j.get('time_casa', 'Desconhecido')).strip().lower()
            t2 = str(j.get('time_fora', 'Desconhecido')).strip().lower()
            chave_cache = f"{t1}x{t2}"
            info_extra = cache_dados.get(chave_cache, {})
            
            horario = j.get('horario') or info_extra.get('horario', '00:00')
            liga = j.get('liga') or info_extra.get('liga', 'Futebol')
            odd_valor = j.get('odd') or info_extra.get('odd', '1.50')
            
            chave_jogo = f"{horario}_{t1}_{t2}"
            if chave_jogo not in agrupados:
                agrupados[chave_jogo] = {
                    "horario": horario, "liga": liga,
                    "time_casa": j.get('time_casa'), "time_fora": j.get('time_fora'),
                    "mercados": [], 
                    "link": j.get('link_betano') or info_extra.get('link', "https://www.betano.bet.br/"),
                    "link_h2h": info_extra.get('link_h2h') 
                }
            
            mercado_limpo = j.get('mercado', '')
            
            if "falta" in mercado_limpo.lower():
                match_nome = re.search(r':\s*([^|\n]+)', mercado_limpo)
                match_med = re.search(r'Méd:\s*([\d.]+)', mercado_limpo)
                nome = match_nome.group(1).strip() if match_nome else "Jogador"
                
                # 🟢 AJUSTE DA SIGLA: Coloca a sigla (ex: ARG) entre parênteses (ARG)
                match_sigla = re.match(r'^([A-ZÀ-Ú]+)\s+(.+)$', nome)
                if match_sigla:
                    nome = f"({match_sigla.group(1)}) {match_sigla.group(2)}"
                    
                med = match_med.group(1) if match_med else "N/A"
                texto_final = f"🔶 Faltas sofridas: {nome} | Méd: {med}"
                
            elif "chute" in mercado_limpo.lower():
                match_nome = re.search(r':\s*([^|\n]+)', mercado_limpo)
                match_med = re.search(r'Méd:\s*([\d.]+)', mercado_limpo)
                nome = match_nome.group(1).strip() if match_nome else "Jogador"
                
                # 🟢 AJUSTE DA SIGLA: Coloca a sigla (ex: ARG) entre parênteses (ARG)
                match_sigla = re.match(r'^([A-ZÀ-Ú]+)\s+(.+)$', nome)
                if match_sigla:
                    nome = f"({match_sigla.group(1)}) {match_sigla.group(2)}"
                    
                med = match_med.group(1) if match_med else "N/A"
                texto_final = f"🔶 Chutes no gol: {nome} | Méd: {med}"
                
            elif "cartão" in mercado_limpo.lower() or "cartao" in mercado_limpo.lower():
                texto_final = f"🔶 {mercado_limpo.split('|')[0].strip()}"
            else:
                texto_final = f"🔶 {mercado_limpo.split('|')[0].strip()}"
            
            agrupados[chave_jogo]["mercados"].append({
                "texto": texto_final, 
                "prioridade": prioridade_mercado(j.get('mercado', ''))
            })
            odd_total *= extrair_odd(odd_valor)

        lista_blocos = []
        for chave in sorted(agrupados.keys()):
            d = agrupados[chave]
            d["mercados"].sort(key=lambda x: x['prioridade'])
            
            linhas = "```\n" + "\n".join([m['texto'] for m in d["mercados"]]) + "\n```"
            
            bloco = f"⏱️ {d['horario']} | {d['liga']}\n🏟️ {d['time_casa']} x {d['time_fora']}\n{linhas}\n🌐 [Abrir na Betano]({d['link']})"
            
            if d.get("link_h2h"): 
                bloco += f"\n📊 [Estatísticas]({d['link_h2h']})"
            lista_blocos.append(bloco)

        corpo_total += corpo + "\n\n".join(lista_blocos) + f"\n\n📈 *Odd Total: {odd_total:.2f}*\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
    
    return corpo_total
