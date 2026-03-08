import os
import requests
from bs4 import BeautifulSoup
import re

def analisar_separado():
    api_key = os.getenv("ZENROWS_KEY")
    url = "https://footystats.org/brazil/se-palmeiras-vs-gremio-novorizontino-h2h-stats"
    
    params = {
        'url': url,
        'apikey': api_key,
        'js_render': 'true',
        'premium_proxy': 'true',
        'wait': '5000' 
    }

    print("📡 Capturando com extração por tags separadas...")
    response = requests.get('https://api.zenrows.com/v1/', params=params)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        resultados = {"Over 1.5": "0%", "Over 2.5": "0%", "BTTS": "0%", "CS_Palmeiras": "0%", "CS_Novorizontino": "0%"}

        # Procuramos todas as divs que têm a classe 'stat-strong'
        stats = soup.select(".stat-strong")
        
        for s in stats:
            # 1. Pega apenas o primeiro pedaço de texto (o 80%)
            # O .contents[0] pega o que vem ANTES do <span>
            try:
                valor_bruto = s.contents[0].strip()
                if "%" not in valor_bruto:
                    continue
            except:
                continue

            # 2. Pega o nome do mercado dentro do span (Over 1.5, BTTS, etc)
            span = s.find("span")
            mercado = span.get_text(strip=True).upper() if span else ""
            
            # 3. Pega o texto de apoio que fica na mesma caixa (stat-text)
            caixa_pai = s.find_parent(class_="grid-item")
            sub_texto = caixa_pai.select_one(".stat-text").get_text().upper() if caixa_pai and caixa_pai.select_one(".stat-text") else ""

            # Mapeamento exato
            if "OVER 1.5" in mercado:
                resultados["Over 1.5"] = valor_bruto
            elif "OVER 2.5" in mercado:
                resultados["Over 2.5"] = valor_bruto
            elif "BTTS" in mercado:
                resultados["BTTS"] = valor_bruto
            elif "CLEAN SHEETS" in mercado:
                if "PALMEIRAS" in sub_texto:
                    resultados["CS_Palmeiras"] = valor_bruto
                elif "NOVORIZONTINO" in sub_texto:
                    resultados["CS_Novorizontino"] = valor_bruto

        print("\n📊 RESULTADOS (EXTRAÇÃO POR TAG):")
        for k, v in resultados.items():
            print(f"📍 {k}: {v}")

        # Validação 80%
        num_o15 = int(resultados["Over 1.5"].replace('%', ''))
        if num_o15 >= 80:
            print(f"\n✅ BINGO! Over 1.5 aprovado com {num_o15}%.")
        else:
            print("\n⚠️ AVISO: Ainda não chegamos nos 80% no Over 1.5.")

    else:
        print(f"❌ Erro na API: {response.status_code}")

if __name__ == "__main__":
    analisar_separado()
    
