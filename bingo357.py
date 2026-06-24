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
    bilhetes = []
    if not dados_entrada: return bilhetes

    # Agrupa por confronto primeiro
    jogos_agrupados = {}
    for jogo in dados_entrada:
        chave = f"{jogo['time_casa']}x{jogo['time_fora']}".lower().strip()
        if chave not in jogos_agrupados: jogos_agrupados[chave] = []
        jogos_agrupados[chave].append(jogo)

    # Ordena confrontos pela "densidade" se modo_elite, ou pela força da estratégia
    # Aqui estamos pegando as chaves (jogos) e ordenando-as
    lista_chaves = list(jogos_agrupados.keys())
    
    if modo_elite:
        # Ordena confrontos que possuem mais mercados (densos)
        lista_chaves.sort(key=lambda k: len(jogos_agrupados[k]), reverse=True)
    else:
        # Ordena de forma aleatória ou pelo primeiro mercado do jogo (padrão)
        pass 

    # Seleciona os confrontos até atingir a qtd_alvo
    jogos_selecionados = []
    for k in lista_chaves[:qtd_alvo]:
        jogos_selecionados.extend(jogos_agrupados[k])
    
    nome_bilhete = f"✨ BINGO {min(len(lista_chaves), qtd_alvo)} ({'DENSO' if modo_elite else 'PADRÃO'}) - {estrategia}"

    if jogos_selecionados:
        bilhetes.append({"id": "BINGO_CUSTOM", "nome": nome_bilhete, "jogos": jogos_selecionados})

    return bilhetes

def formatar_para_telegram(bilhetes, cache_dados, aviso_menu=""):
    if not bilhetes:
        return ""
    
    # Inicia com o aviso do menu
    corpo_total = f"{aviso_menu}\n\n"
    
    for b in bilhetes:
        corpo = f"*{b['nome']}*\n\n"
        odd_total = 1.0
        agrupados = {}
        
        # Agrupa os jogos do bilhete
        for j in b['jogos']:
            chave_cache = f"{str(j.get('time_casa')).strip().lower()}x{str(j.get('time_fora')).strip().lower()}"
            info_extra = cache_dados.get(chave_cache, {})
            horario = j.get('horario') or info_extra.get('horario', '00:00')
            liga = j.get('liga') or info_extra.get('liga', 'Futebol')
            odd_valor = j.get('odd') or info_extra.get('odd', '1.50')
            
            chave_jogo = f"{horario}_{j.get('time_casa')}_{j.get('time_fora')}"
            if chave_jogo not in agrupados:
                agrupados[chave_jogo] = {
                    "horario": horario, "liga": liga,
                    "time_casa": j.get('time_casa'), "time_fora": j.get('time_fora'),
                    "mercados": [], "link": j.get('link_betano') or info_extra.get('link_betano', "https://www.betano.bet.br/"),
                    "link_h2h": info_extra.get('link_h2h')
                }
            
            # Formatação de mercados (seu código existente)
            mercado_limpo = j.get('mercado', '')
            texto_final = f"🔶 {mercado_limpo} | Odd: {odd_valor}" # Simplificado para teste
            
            agrupados[chave_jogo]["mercados"].append({"texto": texto_final, "prioridade": prioridade_mercado(j.get('mercado', ''))})
            odd_total *= extrair_odd(odd_valor)

        # AQUI É A CORREÇÃO: Inicializamos a lista_blocos dentro do loop do bilhete
        lista_blocos = []
        for chave in sorted(agrupados.keys()):
            d = agrupados[chave]
            d["mercados"].sort(key=lambda x: x['prioridade'])
            linhas = "\n".join([m['texto'] for m in d["mercados"]])
            bloco = f"⏱️ {d['horario']} | {d['liga']}\n🏟️ {d['time_casa']} x {d['time_fora']}\n{linhas}\n🌐 [Abrir na Betano]({d['link']})"
            if d.get("link_h2h"): bloco += f"\n📊 [Estatísticas]({d['link_h2h']})"
            lista_blocos.append(bloco)

        # Monta o corpo do bilhete
        corpo_total += corpo + "\n\n".join(lista_blocos) + f"\n\n📈 *Odd Total: {odd_total:.2f}*\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
    
    return corpo_total
    
    return "\n\n".join(blocos)
            
