import os
import requests
from bs4 import BeautifulSoup
import re

def limpar_porcentagem(texto):
    # Procura o padrão de número + % (ex: 80%)
    match = re.search(r'(\d+)%', texto)
    return match.group(0) if match else "0%"

def analisar_partida(api_key, url):
    # Parâmetros para forçar a ZenRows a esperar o carregamento do JavaScript
    params = {
        'url': url,
        'apikey': api_key,
        'js_render': 'true',
        'premium_proxy': 'true',
        'wait_for': '.stat-strong', # Aguarda as porcentagens aparecerem
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
        
        for item in itens:
            texto_total = item.get_text(separator=" ").upper()
            valor = limpar_porcentagem(texto_total)

            if "OVER 1.5" in texto_total:
                res["o15"] = valor
            elif "OVER 2.5" in texto_total:
                res["o25"] = valor
            elif "BTTS" in texto_total:
                res["btts"] = valor
            elif "CLEAN SHEETS" in texto_total:
                # Lógica para identificar qual time é o dono da Clean Sheet
                # stat-text geralmente contém o nome do time abaixo da %
                sub_texto = item.select_one(".stat-text").get_text().upper() if item.select_one(".stat-text") else ""
                
                if "LAZIO" in sub_texto or "LAZIO" in texto_total:
                    res["cs_home"] = valor
                elif "SASSUOLO" in sub_texto or "SASSUOLO" in texto_total:
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

        # Validação da sua regra de 80% (4/5)
        try:
            val_o15 = int(dados['o15'].replace('%', ''))
            if val_o15 >= 80:
                print(f"\n✅ SEGURANÇA: Over 1.5 com {val_o15}% - APROVADO!")
            else:
                print(f"\n⚠️ ATENÇÃO: Over 1.5 com {val_o15}% - Abaixo da meta.")
        except:
            print("\n❌ Erro ao validar valores numéricos.")
    else:
        print("❌ Não foi possível obter os dados do jogo.")
        
