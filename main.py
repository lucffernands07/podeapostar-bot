import os
import requests
from bs4 import BeautifulSoup

def testar_extracao():
    api_key = os.getenv("ZENROWS_KEY")
    # URL do jogo do Palmeiras que você pediu
    url = "https://footystats.org/brazil/se-palmeiras-vs-gremio-novorizontino-h2h-stats"
    
    params = {
        'url': url,
        'apikey': api_key,
        'js_render': 'true',
        'premium_proxy': 'true',
        'wait': '4000' # Tempo extra para garantir que todas as tabelas carreguem
    }

    print("📡 Iniciando teste de captura de dados...")
    response = requests.get('https://api.zenrows.com/v1/', params=params)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Teste Gols e BTTS
        print("\n--- [TESTE: MERCADOS DE GOLS] ---")
        stats = soup.select(".stat-strong")
        for s in stats:
            texto_pai = s.parent.get_text().upper()
            valor = s.get_text(strip=True)
            
            if "OVER 1.5" in texto_pai: print(f"📍 Over 1.5 detectado: {valor}")
            if "OVER 2.5" in texto_pai: print(f"📍 Over 2.5 detectado: {valor}")
            if "BTTS" in texto_pai:     print(f"📍 BTTS detectado: {valor}")

        # 2. Teste Clean Sheets (Tabela H2H)
        print("\n--- [TESTE: CLEAN SHEETS (FOLHA LIMPA)] ---")
        # Procuramos a linha que contém o texto "Clean Sheets"
        linhas = soup.find_all("tr")
        for linha in linhas:
            if "Clean Sheets" in linha.get_text():
                colunas = linha.find_all("td")
                if len(colunas) >= 3:
                    print(f"📍 CS Palmeiras (Casa): {colunas[0].get_text(strip=True)}")
                    print(f"📍 CS Novorizontino (Fora): {colunas[2].get_text(strip=True)}")
                    break
                    
        print("\n--- FIM DO TESTE ---")
    else:
        print(f"❌ Falha no teste. Status: {response.status_code}")
        if response.status_code == 401: print("Motivo: Chave API inválida.")
        if response.status_code == 403: print("Motivo: Bloqueio de Proxy.")

if __name__ == "__main__":
    testar_extracao()
                
