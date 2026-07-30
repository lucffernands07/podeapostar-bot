import re
import json
import os

# --- CAMINHO DE RESERVA ---
PATH_RANKING_DIARIO = 'ranking/ranking_diario.json'

def extrair_porcentagem(texto_mercado):
    try:
        if not texto_mercado:
            return 0
        match = re.search(r'\((\d+)%\)', str(texto_mercado))
        return int(match.group(1)) if match else 0
    except:
        return 0

def extrair_odd(odd_str):
    try:
        if not odd_str or odd_str == "N/A" or odd_str == "":
            return 1.30
        
        odd_str_s = str(odd_str).strip()
        
        if "análise" in odd_str_s.lower() or "analise" in odd_str_s.lower():
            return 1.30
            
        if any(term in odd_str_s.lower() for term in ["chutes", "falta", "cartã", "cartao", "cantos"]):
            return 1.30
            
        if isinstance(odd_str, (int, float)):
            return float(odd_str)
            
        return float(odd_str_s.replace(',', '.'))
    except:
        return 1.30

def prioridade_mercado(mercado_texto):
    m = str(mercado_texto).lower()
    
    if "gols" in m: return 1
    if "ambas" in m: return 2
    if "1x" in m: return 3
    if "vitória" in m or "vitoria" in m: return 4   
    if "2x" in m or "x2" in m: return 5
    if "chute" in m: return 6
    if "falta" in m: return 7
    if "cartão" in m or "cartao" in m: return 8
    if "escanteio" in m: return 9
    
    return 10

def carregar_ranking_pro():
    """Lê o ranking pré-montado pelo ranking.py (Fallback)"""
    if os.path.exists(PATH_RANKING_DIARIO):
        try:
            with open(PATH_RANKING_DIARIO, 'r', encoding='utf-8') as f:
                conteudo = json.load(f)
                if isinstance(conteudo, dict):
                    return conteudo.get("mercados", [])
                return conteudo 
        except: return []
    return []

def montar_bilhetes_estrategicos(dados_entrada, qtd_alvo=3, **kwargs):
    """
    Recebe os jogos já filtrados pela janela de tempo,
    agrupa por confronto e monta o bilhete único final.
    """
    bilhetes = []
    if not dados_entrada: return bilhetes

    # 1. Agrupa todos os mercados por confronto preservando a ordem do fluxo
    jogos_agrupados = {}
    ordem_chaves = []
    
    for jogo in dados_entrada:
        casa = str(jogo.get('time_casa', '')).strip()
        fora = str(jogo.get('time_fora', '')).strip()
        chave = f"{casa}x{fora}".lower()
        
        if chave not in jogos_agrupados:
            jogos_agrupados[chave] = []
            ordem_chaves.append(chave)
            
        # EVITA ADICIONAR O MESMO DICIONÁRIO DE JOGO/MERCADO SE FOR DUPLICADO NA ENTRADA
        if jogo not in jogos_agrupados[chave]:
            jogos_agrupados[chave].append(jogo)

    # 2. Seleciona os N confrontos alvos (ex: Bingo 3, Bingo 5, etc)
    chaves_selecionadas = ordem_chaves[:qtd_alvo]
    
    jogos_selecionados = []
    for chave in chaves_selecionadas:
        jogos_selecionados.extend(jogos_agrupados[chave])
    
    total_reais = len(chaves_selecionadas)
    nome_bilhete = f"✨ BINGO {total_reais} JOGOS"

    if jogos_selecionados:
        bilhetes.append({
            "id": "BINGO_CUSTOM", 
            "nome": nome_bilhete, 
            "jogos": jogos_selecionados
        })

    return bilhetes

def formatar_para_telegram(bilhetes, cache_dados, aviso_menu=""):
    if not bilhetes: return ""
    
    titulo_principal = aviso_menu if aviso_menu else "🚀 *BILHETE GERADO COM SUCESSO*"
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
            
            horario = j.get('horario') or info_extra.get('horario') or "00:00"
            liga = j.get('liga') or info_extra.get('liga', 'Futebol')
            odd_valor = str(j.get('odd') or info_extra.get('odd', '1.30')).strip()
            
            link_h2h_resolvido = j.get('link_h2h') or info_extra.get('link_h2h')
            
            chave_jogo = f"{horario}_{t1}_{t2}"
            if chave_jogo not in agrupados:
                agrupados[chave_jogo] = {
                    "horario": horario, 
                    "liga": liga,
                    "time_casa": j.get('time_casa'), 
                    "time_fora": j.get('time_fora'),
                    "mercados": [], 
                    "link": j.get('link_betano') or info_extra.get('link_betano') or "https://www.betano.bet.br/",
                    "link_h2h": link_h2h_resolvido
                }
            
            mercado_limpo = j.get('mercado', '')
            
            sufixo_odd = ""
            if "Análise" in odd_valor or "analise" in odd_valor.lower():
                sufixo_odd = ""
            elif odd_valor:
                sufixo_odd = f" ODD {odd_valor}"
                
            # --- TRATAMENTO DE SCOUTS DE JOGADORES ---
            if "falta" in mercado_limpo.lower():
                match_nome = re.search(r'([A-Za-zÀ-ÿ\s.\-]+(?:\s+[A-Za-zÀ-ÿ]\.)?\s*\([A-Z]{3}\))', mercado_limpo)
                nome = match_nome.group(1).strip() if match_nome else "Jogador"
                
                match_med = re.search(r'(?:Méd:|média|Méd\.|med:)\s*([\d.]+)', mercado_limpo, re.IGNORECASE)
                med = match_med.group(1) if match_med else None
                
                if med:
                    texto_final = f"🔶 Faltas sofridas: {nome} | Méd: {float(med):.1f}{sufixo_odd}"
                else:
                    texto_final = f"🔶 Faltas sofridas: {nome}{sufixo_odd}"
                
            elif "chute" in mercado_limpo.lower():
                match_nome = re.search(r'([A-Za-zÀ-ÿ\s.\-]+(?:\s+[A-Za-zÀ-ÿ]\.)?\s*\([A-Z]{3}\))', mercado_limpo)
                nome = match_nome.group(1).strip() if match_nome else "Jogador"
                
                match_med = re.search(r'(?:Méd:|média|Méd\.|med:)\s*([\d.]+)', mercado_limpo, re.IGNORECASE)
                med = match_med.group(1) if match_med else None
                
                if med:
                    texto_final = f"🔶 Chutes no gol: {nome} | Méd: {float(med):.1f}{sufixo_odd}"
                else:
                    texto_final = f"🔶 Chutes no gol: {nome}{sufixo_odd}"
                
            elif "cartã" in mercado_limpo.lower() or "cartao" in mercado_limpo.lower():
                match_med_cartao = re.search(r'[\d.]+', mercado_limpo)
                num_media = match_med_cartao.group(0) if match_med_cartao else "0.0"
                texto_final = f"🔶 Média de cartões: {num_media}{sufixo_odd}"
                
            else:
                texto_final = f"🔶 {mercado_limpo.split('|')[0].strip()}{sufixo_odd}"
                
            # --- TRAVA DE SEGURANÇA: SÓ ADICIONA SE O TEXTO AINDA NÃO EXISTIR NO JOGO ---
            item_mercado = {
                "texto": texto_final, 
                "prioridade": prioridade_mercado(j.get('mercado', ''))
            }
            
            textos_existentes = [m["texto"] for m in agrupados[chave_jogo]["mercados"]]
            if texto_final not in textos_existentes:
                agrupados[chave_jogo]["mercados"].append(item_mercado)
                # Só acumula a ODD na total se o mercado não for repetido!
                odd_total *= extrair_odd(odd_valor)

        lista_blocos = []
        for chave in sorted(agrupados.keys()):
            d = agrupados[chave]
            d["mercados"].sort(key=lambda x: x.get('best_score', x['prioridade']))
            
            linhas = "\n".join([m['texto'] for m in d["mercados"]])
            
            bloco = f"⏱️ {d['horario']} | {d['liga']}\n🏟️ {d['time_casa']} x {d['time_fora']}\n{linhas}\n\n🌐 [Abrir na Betano]({d['link']})"
            
            if d.get("link_h2h"): 
                bloco += f"\n📊 [Estatísticas]({d['link_h2h']})"
            lista_blocos.append(bloco)

        corpo_total += corpo + "\n\n".join(lista_blocos) + f"\n\n📈 *Odd Total: {odd_total:.2f}*\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
    
    return corpo_total
                                 
