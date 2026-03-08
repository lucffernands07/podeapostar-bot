import os
import requests
from bs4 import BeautifulSoup
import re

def limpar_porcentagem(texto):
    # Busca qualquer número seguido de % no texto (ex: "80%Over")
    match = re.search(r'(\d+)%', texto)
    return match.group(0) if match else "0%"

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
        resultados = {
            "Over 1.5": "0%", "Over 2.5": "0%", "BTTS": "0%",
            "CS_Novorizontino": "0%", "CS_Palmeiras": "0%"
        }

        itens = soup.select(".grid-item")
        for item in itens:
            # Pega todo o texto da caixinha (ex: "80% Over 1.5 8 / 10 matches")
            texto_todo = item.get_text(separator=" ").upper()
            valor = limpar_porcentagem(texto_todo)

            if "OVER 1.5" in texto_todo:
                resultados["Over 1.5"] = valor
            elif "OVER 2.5" in texto_todo:
                resultados["Over 2.5"] = valor
            elif "BTTS" in texto_todo:
                resultados["BTTS"] = valor
            elif "CLEAN SHEETS" in texto_todo:
                # Verifica qual time está no texto de apoio (stat-text)
                sub_texto = item.select_one(".stat-text").get_text().upper() if item.select_one(".stat-text") else ""
                if "PALMEIRAS" in sub_texto or "PALMEIRAS" in texto_todo:
                    resultados["CS_Palmeiras"] = valor
                elif "NOVORIZONTINO" in sub_texto or "NOVORIZONTINO" in texto_todo:
                    resultados["CS_Novorizontino"] = valor

        print("\n📊 DADOS EXTRAÍDOS COM SUCESSO:")
        for k, v in resultados.items():
            print(f"📍 {k}: {v}")

        # Validação da regra 4/5 (80%)
        try:
            o15_num = int(resultados["Over 1.5"].replace('%', ''))
            if o15_num >= 80:
                print(f"\n✅ SEGURANÇA: Over 1.5 aprovado ({o15_num}%).")
            else:
                print(f"\n⚠️ AVISO: Over 1.5 abaixo de 80%.")
        except:
            print("\n❌ Erro ao converter valores.")
    else:
        print(f"❌ Erro na API: {response.status_code}")

if __name__ == "__main__":
    analisar_grid_neo()
                       
