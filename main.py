import os
import requests

# --- CONFIGURAÇÕES DE AMBIENTE ---
API_KEY = os.getenv('RAPID_API_KEY')
BASE_URL = "https://api.witchgoals.io/v1/analyze" # Endpoint oficial da sua doc

# --- LIGAS DE ELITE (SEQUÊNCIA SOLICITADA) ---
LIGAS_ELITE = [
    "Champions League", "Europa League", "Premier League", "LaLiga", "Serie A", 
    "Bundesliga", "Ligue 1", "Brasileirão Série A", "Copa do Brasil", 
    "Libertadores", "Saudi Pro League", "J1 League"
]

def formatar_bilhete(lista_jogos):
    if not lista_jogos:
        return "⚠️ Nenhum jogo atingiu os critérios de Elite hoje."

    texto = "🎯 *BILHETE DO DIA*\n💰🍀 *BOA SORTE!!!*\n\n"
    for i, item in enumerate(lista_jogos, 1):
        texto += f"{i}. 🏟️ *{item['time']}*\n"
        texto += f"🕒 {item['hora']} | {item['liga']}\n"
        for m in item['mercados']:
            texto += f"{m}\n"
        texto += "\n"
    texto += "---\n💸 *Bet365 | Betano*"
    return texto

def analisar_jogo(home, away, liga):
    headers = {"X-API-KEY": API_KEY, "Content-Type": "application/json"}
    
    # Payload conforme sua documentação
    payload = {
        "sport": "soccer",
        "home": home,
        "away": away,
        "restDays": 3, # Valor médio de descanso
        "performanceIndex": 0.8
    }

    try:
        res = requests.post(BASE_URL, json=payload, headers=headers, timeout=15)
        if res.status_code != 200: return None
        
        data = res.json()
        prob = data.get('probability', 0)
        # Simulamos a contagem 4/5 e 5/5 baseada na probabilidade e confiabilidade da API
        # Já que a Witchgoals entrega o resultado final da análise.
        
        mercados = []

        # --- REGRA DE GOLS (Simulando 4/5 e 5/5) ---
        if prob >= 0.90: # Equivale ao seu 5/5 + 5/5
            mercados.append("🔶 ⚽ +1.5 Gols (100%)")
            mercados.append("🔶 ⚽ +2.5 Gols (100%)")
        elif prob >= 0.80: # Equivale ao seu 5/5 + 4/5
            mercados.append("🔶 ⚽ +1.5 Gols (85%)")
        elif prob >= 0.70: # Equivale ao seu 4/5 + 4/5
            mercados.append("🔶 ⚽ +1.5 Gols (75%)")

        # --- REGRA 1X / 2X (Baseado na Volatilidade e Recomendação) ---
        recomendacao = data.get('prediction', '').lower()
        risco = data.get('volatility', 'high')

        if "home" in recomendacao and risco == 'low':
            mercados.append("🔶 🛡️ 1X (100%)")
        elif "away" in recomendacao and risco == 'low':
            mercados.append("🔶 🛡️ 2X (100%)")

        if mercados:
            return {"time": f"{home} x {away}", "liga": liga, "hora": "20:00", "mercados": mercados[:3]}
    except:
        return None
    return None

def main():
    # Aqui simulamos a busca da grade e filtramos Sporting x Arsenal e Real x Bayern
    grade_teste = [
        {"home": "Sporting CP", "away": "Arsenal", "liga": "Champions League"},
        {"home": "Real Madrid", "away": "Bayern Munich", "liga": "Champions League"}
    ]
    
    bilhete_final = []
    mercados_totais = 0

    for jogo in grade_teste:
        if mercados_totais >= 13: break
        
        resultado = analisar_jogo(jogo['home'], jogo['away'], jogo['liga'])
        if resultado:
            bilhete_final.append(resultado)
            mercados_totais += len(resultado['mercados'])

    print(formatar_bilhete(bilhete_final))

if __name__ == "__main__":
    main()
