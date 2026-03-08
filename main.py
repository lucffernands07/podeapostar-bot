import cloudscraper
from bs4 import BeautifulSoup
import json

def extrair_dados():
    # Criar o scraper
    scraper = cloudscraper.create_scraper()

    # Dados extraídos DAS TUAS IMAGENS (Aba Network -> Headers)
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; Redmi Note 8 Build/QKQ1.200114.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/145.0.7632.122 Mobile Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        # O PHPSESSID é o que diz ao site que tu ainda tens "créditos" para ver o jogo
        "Cookie": "PHPSESSID=31g6mg14pgc7ose5iog67c10ap; country=BR; darkmode=off; __cflb=02DiuH2TTY8vZPoegopGsE5PDtezuLNPreDwommKLY1pQ;"
    }

    url = "https://footystats.org/spain/deportivo-alaves-vs-valencia-cf-h2h-stats"
    
    print(f"📡 Tentando acesso com a tua sessão real...")
    response = scraper.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extração baseada nas tuas imagens (BTTS 67%)
        btts_val = soup.find(text="BTTS").find_parent("div").get_text(strip=True) if soup.find(text="BTTS") else "N/A"
        
        dados = {
            "partida": "Valencia CF vs Deportivo Alavés",
            "btts": btts_val,
            "status": "Sucesso"
        }
        print(json.dumps(dados, indent=4))
    else:
        print(f"❌ Erro {response.status_code}: O site detetou o bot ou o cookie expirou.")

if __name__ == "__main__":
    extrair_dados()
    
