import cloudscraper
import json
from bs4 import BeautifulSoup

def extrair_dados_footystats(url):
    # Cria um "raspador" que pula o desafio do Cloudflare
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False
        }
    )

    print(f"📡 Tentando acesso direto via CloudScraper: {url}")
    
    try:
        response = scraper.get(url, timeout=30)
        if response.status_code != 200:
            return {"erro": f"Status {response.status_code}. O site ainda está bloqueando o IP do servidor."}

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # O dicionário onde vamos guardar os dados "mastigados"
        dados = {
            "partida": "Valencia x Alavés",
            "mercados": {},
            "probabilidades": {}
        }

        # 1. Extrair BTTS e Overs (Baseado nas classes que você me deu)
        # No seu HTML: <div class="stat-strong">67%<span>BTTS</span></div>
        for item in soup.select(".grid-item"):
            strong = item.select_one(".stat-strong")
            if strong:
                texto = strong.get_text(strip=True)
                if "BTTS" in texto:
                    dados["mercados"]["BTTS"] = texto.replace("BTTS", "")
                elif "Over 1.5" in texto:
                    dados["mercados"]["Over_1.5"] = texto.replace("Over 1.5", "")
                elif "Over 2.5" in texto:
                    dados["mercados"]["Over_2.5"] = texto.replace("Over 2.5", "")

        # 2. Extrair Probabilidades (Barra de Comparação que você viu no Network)
        bar_items = soup.select(".bar-item")
        if len(bar_items) >= 2:
            v_casa = bar_items[0].get_text(strip=True).replace('%','')
            v_empate = bar_items[1].get_text(strip=True).replace('%','')
            
            dados["probabilidades"] = {
                "vitoria_casa": f"{v_casa}%",
                "empate": f"{v_draw}%",
                "dupla_chance_casa": f"{int(v_casa) + int(v_empate)}%"
            }

        return dados

    except Exception as e:
        return {"erro": f"Falha na requisição: {str(e)}"}

if __name__ == "__main__":
    url_jogo = "https://footystats.org/spain/deportivo-alaves-vs-valencia-cf-h2h-stats"
    resultado = extrair_dados_footystats(url_jogo)
    
    print("\n=== JSON EXTRAÍDO COM SUCESSO ===")
    print(json.dumps([resultado], indent=4, ensure_ascii=False))
