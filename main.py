import os
import requests

# --- CONFIGURAÇÕES ---
RAPID_API_KEY = os.getenv('RAPID_API_KEY')
API_HOST = os.getenv('WITCH_API_HOST')

def testar_jogos_especificos():
    headers = {
        "x-rapidapi-key": RAPID_API_KEY,
        "x-rapidapi-host": API_HOST,
        "Content-Type": "application/json"
    }

    # Lista de confrontos para forçar o teste
    confrontos = [
        {"home": "Sporting CP", "away": "Arsenal"},
        {"home": "Real Madrid", "away": "Bayern Munich"}
    ]

    print("🧪 INICIANDO TESTE DE ELITE: WITCHGOALS V1.0\n")

    for jogo in confrontos:
        print(f"--------------------------------------------------")
        print(f"🏟️ ANALISANDO: {jogo['home']} x {jogo['away']}")
        
        payload = {"sport": "soccer", "home": jogo['home'], "away": jogo['away']}
        
        try:
            res = requests.post(f"https://{API_HOST}/v1/analyze", json=payload, headers=headers)
            if res.status_code != 200:
                print(f"❌ Erro na API (Status {res.status_code}): {res.text}")
                continue
            
            data = res.json()
            stats_h = data.get('home_stats', {})
            stats_a = data.get('away_stats', {})

            # Extração de Variáveis para Log
            gols_h = stats_h.get('goals_over_15', 0)
            gols_a = stats_a.get('goals_over_15', 0)
            derrotas_h = stats_h.get('losses', 0)
            derrotas_a = stats_a.get('losses', 0)
            ult_h = stats_h.get('last_result')
            ult_a = stats_a.get('last_result')

            print(f"📊 DADOS RECURSIVOS:")
            print(f"   -> {jogo['home']}: {gols_h}/5 Gols | {derrotas_h} Derrotas | Último: {ult_h}")
            print(f"   -> {jogo['away']}: {gols_a}/5 Gols | {derrotas_a} Derrotas | Último: {ult_a}")

            # --- VALIDAÇÃO DOS 4 MERCADOS ---
            print(f"\n✅ CHECKLIST DE MERCADOS:")
            
            # 1. Regra de Gols (5/5 + 5/5)
            if gols_h == 5 and gols_a == 5:
                print("   [OK] +1.5 e +2.5 Gols (100%) - Ambos 5/5")
            elif (gols_h >= 4 and gols_a >= 5) or (gols_h >= 5 and gols_a >= 4):
                print("   [OK] +1.5 Gols (85%) - Critério 5/4 atingido")
            else:
                print("   [--] Gols: Não atingiu critério 4/5 ou 5/5")

            # 2. Regra 1X
            if derrotas_h <= 1 and ult_h == 'W' and derrotas_a >= 2 and ult_a == 'L':
                print("   [OK] Mercado 1X: Aprovado (Mandante Sólido / Visitante Frágil)")
            else:
                print("   [--] Mercado 1X: Reprovado")

            # 3. Regra 2X
            if derrotas_a == 0 and derrotas_h >= 2 and ult_h == 'L':
                print("   [OK] Mercado 2X: Aprovado (Visitante Invictão)")
            else:
                print("   [--] Mercado 2X: Reprovado")

        except Exception as e:
            print(f"⚠️ Falha crítica no teste: {e}")

    print(f"--------------------------------------------------")
    print("\n🚀 Teste finalizado. Se os logs acima apareceram vazios, verifique os nomes dos times na API.")

if __name__ == "__main__":
    testar_jogos_especificos()
