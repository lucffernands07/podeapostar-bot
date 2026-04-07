import os
import requests

# --- CONFIGURAÇÕES ---
API_KEY = os.getenv('RAPID_API_KEY')
BASE_URL = "https://api.witchgoals.io/v1/analyze"

def analisar_jogo(home, away, liga, hora):
    headers = {"X-API-KEY": API_KEY, "Content-Type": "application/json"}
    payload = {"sport": "soccer", "home": home, "away": away}

    try:
        print(f"📡 Consultando: {home} x {away}...")
        res = requests.post(BASE_URL, json=payload, headers=headers, timeout=15)
        
        if res.status_code != 200:
            print(f"❌ Erro API ({res.status_code}) para {home}")
            return None
        
        data = res.json()
        prob = data.get('probability', 0)
        volatilidade = data.get('volatility', 'high')
        
        mercados = []

        # --- REGRA DE GOLS AJUSTADA PARA O ARSENAL/REAL ---
        # Se a probabilidade for > 70%, já entra como o seu critério de gols
        if prob >= 0.85:
            mercados.append("🔶 ⚽ +1.5 Gols (100%)")
            mercados.append("🔶 ⚽ +2.5 Gols (100%)")
        elif prob >= 0.70:
            mercados.append("🔶 ⚽ +1.5 Gols (85%)")
        
        # --- REGRA 1X / 2X ---
        # Se a volatilidade não for alta, aplicamos a proteção
        if volatilidade != 'high':
            if "home" in data.get('prediction', '').lower():
                mercados.append("🔶 🛡️ 1X (100%)")
            else:
                mercados.append("🔶 🛡️ 2X (100%)")

        if mercados:
            print(f"✅ Jogo Aprovado: {home} com {len(mercados)} mercados.")
            return {"time": f"{home} x {away}", "liga": liga, "hora": hora, "mercados": mercados[:3]}
            
    except Exception as e:
        print(f"⚠️ Erro no processamento: {e}")
        return None

def main():
    # FORÇANDO OS JOGOS DA CHAMPIONS
    jogos_foco = [
        {"home": "Sporting CP", "away": "Arsenal", "liga": "Champions League", "hora": "16:00"},
        {"home": "Real Madrid", "away": "Bayern Munich", "liga": "Champions League", "hora": "16:00"}
    ]
    
    bilhete_final = []
    for jogo in jogos_foco:
        res = analisar_jogo(jogo['home'], jogo['away'], jogo['liga'], jogo['hora'])
        if res:
            bilhete_final.append(res)

    # IMPRESSÃO DO BILHETE (FRONT-END SOLICITADO)
    if not bilhete_final:
        print("⚠️ Os jogos ainda não atingiram o peso mínimo na API.")
        return

    print("\n🎯 BILHETE DO DIA")
    print("💰🍀 BOA SORTE!!!\n")
    for i, item in enumerate(bilhete_final, 1):
        print(f"{i}. 🏟️ {item['time']}")
        print(f"🕒 {item['hora']} | {item['liga']}")
        for m in item['mercados']:
            print(m)
        print("")
    
    print("---")
    print("💸 Bet365 | Betano")

if __name__ == "__main__":
    main()
