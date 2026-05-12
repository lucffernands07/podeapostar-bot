import re
import json
import os
import requests

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
    caminho = 'ranking/ranking_db.json'
    if os.path.exists(caminho):
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                return json.load(f).get("stats", {})
        except: return {}
    return {}

def montar_bilhetes_estrategicos(dados_entrada):
    bilhetes = []
    
    if isinstance(dados_entrada, dict) and 'jogos' in dados_entrada:
        lista_jogos = dados_entrada['jogos']
    else:
        lista_jogos = [j for j in dados_entrada if isinstance(j, dict) and 'mercado' in j]

    if not lista_jogos: return bilhetes

    # --- TRAVA DE SEGURANÇA: DUPLA CHANCE > VITÓRIA ---
    jogos_agrupados = {}
    for jogo in lista_jogos:
        chave = f"{jogo['time_casa']}x{jogo['time_fora']}".lower().strip()
        if chave not in jogos_agrupados: jogos_agrupados[chave] = []
        jogos_agrupados[chave].append(jogo)

    lista_filtrada = []
    for mercados in jogos_agrupados.values():
        tem_dupla = any(re.search(r'\b(1x|x2|2x)\b', m['mercado'].lower()) for m in mercados)
        if tem_dupla:
            for m in mercados:
                if "vitória" not in m['mercado'].lower() and "vitoria" not in m['mercado'].lower():
                    lista_filtrada.append(m)
        else:
            lista_filtrada.extend(mercados)
    
    lista_jogos = lista_filtrada

    # --- LÓGICA DE SELEÇÃO (BINGO 3, 5 e PRO) ---
    # Bingo 3
    if len(lista_jogos) >= 3:
        l3 = sorted(lista_jogos, key=lambda x: extrair_odd(x.get('odd', '1.0')), reverse=True)[:3]
        l3.sort(key=lambda x: x.get('horario', '00:00'))
        bilhetes.append({"id": "BINGO3", "nome": "🔥 BINGO 3: VALOR", "jogos": l3})

    # Bingo 5
    if len(lista_jogos) >= 5:
        b5 = sorted(lista_jogos, key=lambda x: extrair_odd(x.get('odd', '1.0')), reverse=True)[:3]
        sobra = [j for j in lista_jogos if j not in b5]
        b5.extend(sorted(sobra, key=lambda x: extrair_porcentagem(x.get('mercado', '')), reverse=True)[:2])
        b5.sort(key=lambda x: x.get('horario', '00:00'))
        bilhetes.append({"id": "BINGO5", "nome": "💰 BINGO 5: ESTRUTURADO", "jogos": b5[:5]})

    # Bingo Pro
    stats_db = carregar_ranking_db()
    def calc_premium(j):
        stat = stats_db.get(j.get('mercado', ""))
        if not stat: return (0.0, 0)
        total = stat.get("green", 0) + stat.get("red", 0)
        return (stat.get("green", 0) / total if total > 0 else 0.0, stat.get("green", 0))

    lista_pro = sorted([j for j in lista_jogos if calc_premium(j)[0] > 0], key=calc_premium, reverse=True)[:7]
    if lista_pro:
        lista_pro.sort(key=lambda x: x.get('horario', '00:00'))
        bilhetes.append({"id": "PREMIUM", "nome": "💎 BINGO PRO: ELITE", "jogos": lista_pro})

    return bilhetes

def enviar_bingo_telegram(chat_id, bilhetes, cache_dados):
    token = os.getenv('TELEGRAM_TOKEN')
    if not bilhetes: return

    for b in bilhetes:
        corpo = f"*{b['nome']}*\n\n"
        odd_total = 1.0
        
        # Agrupamento visual por jogo
        agrupados = {}
        for j in b['jogos']:
            chave = f"{j['horario']}_{j['time_casa']}_{j['time_fora']}"
            if chave not in agrupados:
                agrupados[chave] = {"h": j['horario'], "c": j['time_casa'], "f": j['time_fora'], "m": []}
            agrupados[chave]["m"].append(f"🔶 {j['mercado']} | Odd: {j['odd']}")
            odd_total *= extrair_odd(j['odd'])

        for j in agrupados.values():
            corpo += f"⏱️ {j['h']} | 🏟️ {j['c']} x {j['f']}\n" + "\n".join(j['m']) + "\n\n"
        
        corpo += f"📈 *Odd Total: {odd_total:.2f}*\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"

        payload = {
            "chat_id": chat_id,
            "text": corpo,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
            "reply_markup": {
                "keyboard": [
                    [{"text": "🔥 Bingo 3"}, {"text": "🔥 Bingo 5"}],
                    [{"text": "💎 Bingo Pro"}, {"text": "📊 Ranking"}]
                ],
                "resize_keyboard": True,
                "persistent": True
            }
        }
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json=payload)
                                  
