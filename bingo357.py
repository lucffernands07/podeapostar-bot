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
    """
    Retorna a odd convertida para float.
    Para mercados estáticos/scouts (incluindo Finalizações Totais do Time),
    atribui a odd invisível padrão de 1.30 para não zerar nem cair em travas.
    """
    try:
        if not odd_str or odd_str == "N/A" or odd_str == "":
            return 1.30
        
        odd_str_s = str(odd_str).strip()
        
        if "análise" in odd_str_s.lower() or "analise" in odd_str_s.lower():
            return 1.30
            
        # 🟢 Garante odd invisível de 1.30 para Finalizações Totais do Time (e legados de scouts/cartões/cantos)
        if any(term in odd_str_s.lower() for term in ["chutes", "chute", "finaliza", "finalização", "finalizacao", "falta", "cartã", "cartao", "cantos", "escanteio"]):
            return 1.30
            
        if isinstance(odd_str, (int, float)):
            return float(odd_str)
            
        return float(odd_str_s.replace(',', '.'))
    except:
        return 1.30

def prioridade_mercado(mercado_texto):
    """
    Define a ordem em que os mercados aparecem no bloco de código do Telegram.
    """
    m = str(mercado_texto).lower()
    
    if "gols" in m: return 1
    if "ambas" in m: return 2
    if "1x" in m: return 3
    if "2x" in m or "x2" in m: return 4
    if "vitória" in m or "vitoria" in m: return 5   
    if "finalização" in m or "finalizacao" in m or "chute" in m: return 6  # 🎯 Finalizações do Time
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

def chave_ordenacao_horario(chave_jogo):
    horario = chave_jogo.split('_')[0]
    if horario == "00:00":
        return f"24:00_{chave_jogo}"
    return chave_jogo

def montar_bilhetes_estrategicos(dados_entrada, qtd_alvo=None, **kwargs):
    """
    Recebe os jogos já filtrados, agrupa por confronto.
    Se qtd_alvo for None, gera um bilhete com TODOS os jogos do dia.
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
        jogos_agrupados[chave].append(jogo)

    # 2. Se não foi definida uma quantidade, seleciona TODOS os jogos
    if qtd_alvo is None:
        qtd_alvo = len(ordem_chaves)

    chaves_selecionadas = ordem_chaves[:qtd_alvo]
    
    jogos_selecionados = []
    for chave in chaves_selecionadas:
        jogos_selecionados.extend(jogos_agrupados[chave])
    
    total_reais = len(chaves_selecionadas)
    nome_bilhete = f"✨ BILHETE COMPLETO DO DIA ({total_reais} JOGOS)" if total_reais > 5 else f"✨ BINGO {total_reais} JOGOS"

    if jogos_selecionados:
        bilhetes.append({
            "id": "BINGO_CUSTOM", 
            "nome": nome_bilhete, 
            "jogos": jogos_selecionados
        })

    return bilhetes


def formatar_para_telegram(bilhetes, cache_dados, aviso_menu=""):
    """
    Formata a mensagem interativa enviada para o Canal do Telegram.
    Divide as mensagens automaticamente em partes de ~3800 caracteres.
    Retorna uma LISTA de mensagens (strings).
    """
    if not bilhetes: return []
    
    mensagens_finais = []
    titulo_principal = aviso_menu if aviso_menu else "🚀 *BILHETE GERADO COM SUCESSO*"
    corpo_atual = f"{titulo_principal}\n\n"
    
    for b in bilhetes:
        corpo_atual += f"*{b.get('nome', 'BINGO')}*\n\n"
        odd_total = 1.0
        agrupados = {}
        
        for idx, j in enumerate(b.get('jogos', [])):
            t1 = str(j.get('time_casa', 'Desconhecido')).strip().lower()
            t2 = str(j.get('time_fora', 'Desconhecido')).strip().lower()
            chave_cache = f"{t1}x{t2}"
            info_extra = cache_dados.get(chave_cache, {})
            
            horario = j.get('horario') or info_extra.get('horario') or "00:00"
            liga = j.get('liga') or info_extra.get('liga', 'Futebol')
            
            mercado_raw = j.get('mercado', '')
            odd_valor = j.get('odd') or info_extra.get('odd', '1.30')
            
            # Mapeia a odd correta se presente no cache_dados
            if isinstance(info_extra, dict) and "odds_todas" in info_extra:
                odds_dic = info_extra["odds_todas"]
                m_lower = mercado_raw.lower()
                if "ambas marcam: não" in m_lower or "ambas marcam nao" in m_lower:
                    odd_valor = odds_dic.get("BTTS_NAO", odd_valor)
                elif "ambas marcam" in m_lower:
                    odd_valor = odds_dic.get("BTTS", odd_valor)
                elif "vitória fora" in m_lower or "vitoria fora" in m_lower:
                    odd_valor = odds_dic.get("VITORIA_FORA", odd_valor)
                elif "vitória casa" in m_lower or "vitoria casa" in m_lower:
                    odd_valor = odds_dic.get("VITORIA_CASA", odd_valor)
                elif "1x" in m_lower:
                    odd_valor = odds_dic.get("1X", odd_valor)
                elif "2x" in m_lower or "x2" in m_lower:
                    odd_valor = odds_dic.get("X2", odd_valor)
            
            odd_valor = str(odd_valor).strip()
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
            
            sufixo_odd = ""
            if "Análise" in odd_valor or "analise" in odd_valor.lower() or odd_valor == "N/A":
                sufixo_odd = ""
            elif odd_valor:
                sufixo_odd = f" ODD {odd_valor}"
                
            texto_final = f"🔶 {mercado_raw.split('|')[0].strip()}{sufixo_odd}"
                
            agrupados[chave_jogo]["mercados"].append({
                "texto": texto_final, 
                "prioridade": prioridade_mercado(mercado_raw)
            })
            
            odd_total *= extrair_odd(odd_valor)

        # 🟢 CONSTRUÇÃO DOS BLOCOS E CORTE INTELIGENTE
        for chave in sorted(agrupados.keys(), key=chave_ordenacao_horario):
            d = agrupados[chave]
            d["mercados"].sort(key=lambda x: x['prioridade'])
            
            linhas = "```\n" + "\n".join([m['texto'] for m in d["mercados"]]) + "\n```"
            bloco = f"⏱️ {d['horario']} | {d['liga']}\n🏟️ {d['time_casa']} x {d['time_fora']}\n{linhas}\n🌐 [Abrir na Betano]({d['link']})"
            
            if d.get("link_h2h"): 
                bloco += f"\n📊 [Estatísticas]({d['link_h2h']})"
                
            # Verifica se juntar este bloco ao texto atual ultrapassa o limite seguro do Telegram (~3800 chars)
            if len(corpo_atual) + len(bloco) > 3800:
                mensagens_finais.append(corpo_atual)    # Guarda a parte cheia
                corpo_atual = f"*(Continuação)*\n\n"    # Inicia uma nova parte
                
            corpo_atual += bloco + "\n\n"

        corpo_atual += f"📈 *Odd Total Estimada: {odd_total:.2f}*\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        
    if corpo_atual.strip():
        mensagens_finais.append(corpo_atual)
        
    return mensagens_finais
