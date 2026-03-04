import os
import requests
import random
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": mensagem, 
        "parse_mode": "Markdown", 
        "disable_web_page_preview": "true"
    }
    try:
        requests.post(url, json=payload, timeout=15)
    except:
        pass

def obter_data_hoje_br():
    return (datetime.utcnow() - timedelta(hours=3)).strftime('%Y-%m-%d')

def definir_palpite_estrategico():
    # Mercado, Confiança, Odd Estimada
    opcoes = [
        ("⚽ +1.5 Gols na Partida", 82, 1.45),
        ("⚽ +2.5 Gols na Partida", 70, 1.90),
        ("🎯 Ambas Marcam - Sim", 75, 1.80),
        ("🛡️ Empate Anula Fav.", 85, 1.40),
        ("🔥 Casa ou Fora (12)", 78, 1.35),
        ("⚽ +0.5 Gols (Base Segura)", 94, 1.10)
    ]
    return random.choice(opcoes)

def tornar_mais_seguro(palpite_original):
    """
    Transforma palpites do B1 em opções mais seguras para o B2,
    mantendo odds competitivas para chegar no alvo de 80-100.
    """
    if "+2.5" in palpite_original or "Ambas Marcam" in palpite_original:
        return "⚽ +1.5 Gols na Partida", 1.45
    if "Empate Anula" in palpite_original:
        return "🔥 Casa ou Empate", 1.25
    return palpite_original, 1.15

def executar_robo():
    hoje_br = obter_data_hoje_br()
    print(f"[{datetime.now().strftime('%H:%M')}] Iniciando busca de jogos para {hoje_br}...")
    
    ligas = {
        "bra.1": "Série A Brasil", "bra.2": "Série B Brasil", "bra.copa_do_brasil": "Copa do Brasil",
        "bra.camp_paulista": "Paulistão", "bra.camp_carioca": "Cariocão",
        "conmebol.libertadores": "Libertadores", "conmebol.sudamericana": "Sul-Americana",
        "eng.1": "Premier League (Ing)", "esp.1": "LaLiga (Esp)", "esp.copa_del_rey": "Copa del Rey (Esp)",
        "ita.1": "Série A (Ita)", "ita.coppa_italia": "Coppa Italia (Ita)", "ger.1": "Bundesliga (Ale)",
        "por.1": "Liga Portugal (Por)", "uefa.champions": "Champions League",
        "ned.1": "Eredivisie (Hol)", "aut.1": "Bundesliga (Aut)", "bel.1": "Pro League (Bel)", "usa.1": "MLS (EUA)"
    }

    jogos_hoje = []
    for liga_id, liga_nome in ligas.items():
        url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{liga_id}/scoreboard"
        try:
            res = requests.get(url, timeout=15)
            data = res.json()
            for evento in data.get('events', []):
                dt_utc = datetime.fromisoformat(evento.get('date').replace('Z', ''))
                dt_br = dt_utc - timedelta(hours=3)
                if dt_br.strftime('%Y-%m-%d') == hoje_br:
                    jogos_hoje.append({
                        "liga": liga_nome,
                        "jogo": evento.get('name').replace(' at ', ' x ').replace(' & ', ' x '),
                        "hora": dt_br.strftime("%H:%M"),
                        "link": evento.get('links')[0].get('href')
                    })
        except: continue

    if len(jogos_hoje) < 10:
        print("Poucos jogos.")
        return

    # --- LOOP PRINCIPAL ---
    tentativas_globais = 0
    while tentativas_globais < 3000:
        selecao = random.sample(jogos_hoje, 10)
        
        # 1. Tentar gerar o Bilhete Alavancagem (90-110)
        b1_lista, odd_t1 = [], 1.0
        for j in selecao:
            p, c, o = definir_palpite_estrategico()
            odd_t1 *= o
            b1_lista.append({**j, "aposta": p, "odd": o})

        if 90 <= odd_t1 <= 110:
            # 2. Se o B1 deu certo, tentar calibrar o B2 (80-100) com os MESMOS jogos
            b2_lista, odd_t2, limite_25 = [], 1.0, 1
            
            for jogo_b1 in b1_lista:
                # Mantém apenas um +2.5 (o primeiro que encontrar)
                if "+2.5" in jogo_b1['aposta'] and limite_25 > 0:
                    nova_p, nova_o = jogo_b1['aposta'], jogo_b1['odd']
                    limite_25 -= 1
                else:
                    nova_p, nova_o = tornar_mais_seguro(jogo_b1['aposta'])
                
                odd_t2 *= nova_o
                b2_lista.append({**jogo_b1, "aposta": nova_p, "odd": nova_o})

            # Verifica se o bilhete de segurança ficou no intervalo 80-100
            if 80 <= odd_t2 <= 100:
                # ENVIAR BILHETE 1
                msg1 = f"🚀 *BILHETE 1: ALAVANCAGEM (ODD {odd_t1:.2f})*\n"
                msg1 += f"_Apenas jogos de HOJE ({hoje_br}) | Alvo: 100x_\n\n"
                for i, x in enumerate(b1_lista, 1):
                    msg1 += f"{i}. 🏟️ *{x['jogo']}*\n🕒 {x['hora']} | 🎯 *{x['aposta']}*\n📊 [Estatísticas]({x['link']})\n\n"
                enviar_telegram(msg1)

                # ENVIAR BILHETE 2
                msg2 = f"🛡️ *BILHETE 2: SEGURANÇA (ODD {odd_t2:.2f})*\n"
                msg2 += f"_Mesmos jogos | Máx 1 aposta +2.5 | Alvo: 80-100x_\n\n"
                for i, x in enumerate(b2_lista, 1):
                    msg2 += f"{i}. 🏟️ *{x['jogo']}*\n🕒 {x['hora']} | 🎯 *{x['aposta']}*\n📊 [Estatísticas]({x['link']})\n\n"
                
                msg2 += "---\n💸 *APOSTAR:* [Bet365](https://www.bet365.com/) | [Betano](https://br.betano.com/)"
                enviar_telegram(msg2)
                
                print(f"Sucesso! B1: {odd_t1:.2f} | B2: {odd_t2:.2f}")
                return
        
        tentativas_globais += 1

    print("Não foi possível calibrar os dois bilhetes.")

if __name__ == "__main__":
    executar_robo()
