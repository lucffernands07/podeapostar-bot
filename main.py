import os
import requests
from bs4 import BeautifulSoup

def analisar_grid_neo():
    api_key = os.getenv("ZENROWS_KEY")
    url = "https://footystats.org/brazil/se-palmeiras-vs-gremio-novorizontino-h2h-stats"
    
    params = {
        'url': url,
        'apikey': api_key,
        'js_render': 'true',
        'premium_proxy': 'true',
        'wait': '5000' 
    }

    print("📡 Capturando dados do Grid H2H...")
    response = requests.get('https://api.zenrows.com/v1/', params=params)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Dicionário para guardar os resultados
        resultados = {
            "Over 1.5": "0%", "Over 2.5": "0%", "BTTS": "0%",
            "CS_Novorizontino": "0%", "CS_Palmeiras": "0%"
        }

        # Buscamos cada item do grid
        itens = soup.select(".grid-item")
        
        for item in itens:
            # Pega a porcentagem (ex: 80%)
            valor_el = item.select_one(".stat-strong")
            if not valor_el: continue
            
            # Limpa o valor para pegar só o que vem antes do <span>
            porcentagem = valor_el.get_text(strip=True).split('%')[0] + '%'
            
            # Pega o nome do mercado (ex: Over 1.5 ou Clean Sheets)
            mercado = item.select_one("span").get_text(strip=True)
            
            # Pega o texto de apoio (ex: 8/10 matches ou o nome do time)
            sub_texto = item.select_one(".stat-text").get_text(strip=True)

            # Mapeamento
            if "Over 1.5" in mercado: resultados["Over 1.5"] = porcentagem
            if "Over 2.5" in mercado: resultados["Over 2.5"] = porcentagem
            if "BTTS" in mercado:     resultados["BTTS"] = porcentagem
            
            # Lógica para Clean Sheets separada por time
            if "Clean Sheets" in mercado:
                if "Palmeiras" in sub_texto:
                    resultados["CS_Palmeiras"] = porcentagem
                elif "Novorizontino" in sub_texto:
                    resultados["CS_Novorizontino"] = porcentagem

        print("\n📊 DADOS EXTRAÍDOS COM SUCESSO:")
        for k, v in resultados.items():
            print(f"📍 {k}: {v}")

        # --- Validação da sua regra de 4/5 (80%) ---
        try:
            o15_int = int(resultados["Over 1.5"].replace('%', ''))
            if o15_int >= 80:
                print(f"\n✅ SEGURANÇA: Over 1.5 com {o15_int}% (Mínimo 4/5 atingido).")
            else:
                print(f"\n⚠️ AVISO: Over 1.5 abaixo de 80%.")
        except:
            print("\n❌ Erro ao validar regra.")

    else:
        print(f"❌ Erro na API: {response.status_code}")

if __name__ == "__main__":
    analisar_grid_neo()
                    
