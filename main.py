import os
import requests
import random
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown", "disable_web_page_preview": "true"}
    try:
        requests.post(url, json=payload, timeout=15)
    except: pass

def obter_data_hoje_br():
    return (datetime.utcnow() - timedelta(hours=3)).strftime('%Y-%m-%d')

def definir_palpite_estrategico():
    opcoes = [
        ("⚽ +1.5 Gols na Partida", 1.48),
        ("⚽ +2.5 Gols na Partida", 1.95),
        ("🎯 Ambas Marcam - Sim", 1.85),
        ("🛡️ Empate Anula Fav.", 1.42),
        ("🔥 Casa ou Fora (12)", 1.35),
        ("⚽ +0.5 Gols (Base Segura)", 1.12)
    ]
    escolha = random.choice(opcoes)
    return escolha[0], escolha[1]

def tornar_mais_seguro(palpite_original):
    # Se for algo de risco, baixa para +1.5 que ainda mantém odd boa
    if "+2.5" in palpite_original or "Ambas Marcam" in palpite_original:
        return "⚽ +1.5 Gols na Partida", 1.48
    if "Empate Anula" in palpite_original:
        return "🔥 Casa ou Empate", 1.25
    return palpite_original, 1.15

def executar_robo():
    hoje_br = obter_data_hoje_br()
    print(f"[{datetime.now().strftime('%H:%M')}] Iniciando busca para {hoje_br}...")
    
    # Lista de ligas expandida para ter mais volume de jogos
    ligas = ["bra.1", "bra.2", "bra.copa_do_brasil", "eng.1", "esp.1", "ita.1", "ger.1", "uefa.champions", "conmebol.libertadores", "conmebol.sudamericana", "usa.1", "aut.1", "por.1", "ned.1"]
    
    jogos_hoje = []
    for liga_id in ligas:
        url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{liga_id}/scoreboard"
        try:
            res = requests.get(url, timeout=10)
            data = res.json()
            for evento in data.get('events', []):
                dt_br = datetime.fromisoformat(evento.get('date').replace('Z', '')) - timedelta(hours=3)
                if dt_br.strftime('%Y-%m-%d') == hoje_br:
                    jogos_hoje.append({
                        "liga": liga_id.upper(),
                        "jogo": evento.get('name').replace(' at ', ' x ').replace(' & ', ' x '),
                        "hora": dt_br.strftime("%H:%M"),
                        "link": evento.get('links')[0].get('href')
                    })
        except: continue

    if len(jogos_hoje) < 10:
        print(f"Poucos jogos hoje ({len(jogos_hoje)}).")
        return

    # Aumentado para 10.000 tentativas para garantir a Odd
    for tentativa in range(10000):
        selecao = random.sample(jogos_hoje, 10)
        
        # Gerar Bilhete 1
        b1_lista, odd_t1 = [], 1.0
        for j in selecao:
            p, o = definir_palpite_estrategico()
            odd_t1 *= o
            b1_lista.append({**j, "aposta": p, "odd": o})

        if 90 <= odd_t1 <= 110:
            # Tentar calibrar o Bilhete 2 com base no Bilhete 1
            b2_lista, odd_t2, limite_25 = [], 1.0, 1
            for j in b1_lista:
                if "+2.5" in j['aposta'] and limite_25 > 0:
                    nova_p, nova_o = j['aposta'], j['odd']
                    limite_25 -= 1
                else:
                    nova_p, nova_o = tornar_mais_seguro(j['aposta'])
                odd_t2 *= nova_o
                b2_lista.append({**j, "aposta": nova_p, "odd": nova_o})

            # Se o B2 atingir a meta, envia ambos e encerra
            if 80 <= odd_t2 <= 100:
                # MSG 1
                m1 = f"🚀 *BILHETE 1: ALAVANCAGEM (ODD {odd_t1:.2f})*\n_Hoje ({hoje_br}) | 100x_\n\n"
                for i, x in enumerate(b1_lista, 1):
                    m1 += f"{i}. 🏟️ *{x['jogo']}*\n🕒 {x['hora']} | 🎯 *{x['aposta']}*\n📊 [Stats]({x['link']})\n\n"
                enviar_telegram(m1)

                # MSG 2
                m2 = f"🛡️ *BILHETE 2: SEGURANÇA (ODD {odd_t2:.2f})*\n_Hoje ({hoje_br}) | 80-100x (Máx 1 jogo +2.5)_\n\n"
                for i, x in enumerate(b2_lista, 1):
                    m2 += f"{i}. 🏟️ *{x['jogo']}*\n🕒 {x['hora']} | 🎯 *{x['aposta']}*\n📊 [Stats]({x['link']})\n\n"
                m2 += "💸 [Bet365](https://www.bet365.com/) | [Betano](https://br.betano.com/)"
                enviar_telegram(m2)
                print(f"Sucesso na tentativa {tentativa}!")
                return

    print("Limite de tentativas atingido sem sucesso duplo.")

if __name__ == "__main__":
    executar_robo()
    
