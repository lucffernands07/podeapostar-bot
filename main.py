import os
import requests
from bs4 import BeautifulSoup
import re

def limpar_porcentagem(texto):
    # Procura o padrão de número + % (ex: 80%)
    match = re.search(r'(\d+)%', texto)
    return match.group(0) if match else "0%"

def analisar_partida(api_key, url):
    params = {
        'url': url,
        'apikey': api_key,
        'js_render': 'true',
        'premium_proxy': 'true',
        'wait_for': '.stat-strong', 
        'wait': '3000'
    }

    try:
        print(f"📡 Capturando dados de: {url.split('/')[-1]}...")
        response = requests.get('https://api.zenrows.com/v1/', params=params)
        
        if response.status_code != 200:
            print(f"❌ Erro ZenRows: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        res = {
            "o15": "0%", "o25": "0%", "btts": "0%", 
            "cs_home": "0%", "cs_away": "0%"
        }

        # Localiza os itens do grid de estatísticas
        itens = soup.select(".grid-item")
        
        for index, item in enumerate(itens):
            # Pega o texto de toda a caixinha (ex: "80% Over 1.5")
            texto_total = item.get_text(separator=" ").upper()
            valor = limpar_porcentagem(texto_total)

            # Lógica Robusta: Tenta pelo nome ou pela posição no grid (Over 1.5 é sempre o 1º)
            if "OVER 1.5" in texto_total or index == 0:
                res["o15"] = valor
            elif "OVER 2.5" in texto_total:
                res["o25"] = valor
            elif "BTTS" in texto_total:
                res["btts"] = valor
            elif "CLEAN SHEETS" in texto_total:
                sub_texto = item.select_one(".stat-text").get_text().upper() if item.select_one(".stat-text") else ""
                # Identifica se a Clean Sheet é da Lazio (Home) ou Sassuolo (Away)
                if "LAZIO" in sub_texto or "LAZIO" in texto_total:
                    res["cs_home"] = valor
                else:
                    res["cs_away"] = valor
        
        return res

    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return None

if __name__ == "__main__":
    key = os.getenv("ZENROWS_KEY")
    url_hoje = "https://footystats.org/italy/ss-lazio-vs-us-sassuolo-calcio-h2h-stats"
    
    dados = analisar_partida(key, url_hoje)

    if dados:
        print("\n🚀 DADOS EXTRAÍDOS (LAZIO vs SASSUOLO):")
        print(f"📍 Over 1.5: {dados['o15']}")
        print(f"📍 Over 2.5: {dados['o25']}")
        print(f"📍 BTTS: {dados['btts']}")
        print(f"📍 Clean Sheets Lazio: {dados['cs_home']}")
        print(f"📍 Clean Sheets Sassuolo: {dados['cs_away']}")

        # Validação da regra de 80%
        try:
            val_o15 = int(dados['o15'].replace('%', ''))
            if val_o15 >= 80:
                print(f"\n✅ SEGURANÇA: Over 1.5 com {val_o15}% - APROVADO!")
            else:
                print(f"\n⚠️ ATENÇÃO: Over 1.5 com {val_o15}% - Abaixo da meta.")
        except:
            print("\n❌ Erro ao validar valores.")
    else:
        print("❌ Falha ao obter dados.")
        
