import os
import requests
from bs4 import BeautifulSoup
import re

def limpar_porcentagem(texto):
    # Procura qualquer número seguido de % no texto (ex: "80%Over 1.5" -> "80%")
    match = re.search(r'(\d+)%', texto)
    return match.group(0) if match else "0%"

def analisar_com_fallback():
    api_key = os.getenv("ZENROWS_KEY")
    url = "https://footystats.org/brazil/se-palmeiras-vs-gremio-novorizontino-h2h-stats"
    
    params = {
        'url': url,
        'apikey': api_key,
        'js_render': 'true',
        'premium_proxy': 'true',
        'wait': '5000' 
    }

    print("📡 Capturando dados (Método Robusto)...")
    response = requests.get('https://api.zenrows.com/v1/', params=params)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Dicionário de resultados
        resultados = {
            "Over 1.5": "0%", "Over 2.5": "0%", "BTTS": "0%",
            "CS_Novorizontino": "0%", "CS_Palmeiras": "0%"
        }

        # --- ESTRATÉGIA: Busca por GRID-ITEM (O HTML que você mandou) ---
        itens = soup.select(".grid-item")
        
        for item in itens:
            texto_todo = item.get_text(separator=" ").upper()
            valor_encontrado = limpar_porcentagem(texto_todo)

            # Mapeamento baseado no texto do seu HTML
            if "OVER 1.5" in texto_todo:
                resultados["Over 1.5"] = valor_encontrado
            elif "OVER 2.5" in texto_todo:
                resultados["Over 2.5"] = valor_encontrado
            elif "BTTS" in texto_todo:
                resultados["BTTS"] = valor_encontrado
            elif "CLEAN SHEETS" in texto_todo:
                # Diferencia pelo sub-texto (Novorizontino ou Palmeiras)
                if "PALMEIRAS" in texto_todo:
                    resultados["CS_Palmeiras"] = valor_encontrado
                elif "NOVORIZONTINO" in texto_todo:
                    resultados["CS_Novorizontino"] = valor_encontrado

        # --- EXIBIÇÃO ---
        print("\n📊 RESULTADOS FINAIS:")
        for k, v in resultados.items():
            print(f"📍 {k}: {v}")

        # Validação Regra 4/5 (80%)
        try:
            o15 = int(resultados["Over 1.5"].replace('%', ''))
            if o15 >= 80:
                print(f"\n✅ SUCESSO: Over 1.5 atingiu {o15}% (4/5).")
            else:
                print(f"\n⚠️ AVISO: Critério de 80% não atingido.")
        except:
            print("\n❌ Erro na conversão dos dados.")

    else:
        print(f"❌ Erro na conexão: {response.status_code}")

if __name__ == "__main__":
    analisar_com_fallback()
        print(f"\n⚠️ AVISO: Over 1.5 abaixo de 80%.")
        except:
            print("\n❌ Erro ao validar regra.")

    else:
        print(f"❌ Erro na API: {response.status_code}")

if __name__ == "__main__":
    analisar_grid_neo()
                    
