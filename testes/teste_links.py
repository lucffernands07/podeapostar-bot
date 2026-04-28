import sys
import os
import requests
import re
import urllib.parse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def buscar_link_bing(time_casa, time_fora):
    print(f"🚀 [ROBÔ] Tentando via BING: {time_casa} x {time_fora}")
    
    # Termo de busca focado
    termo = f"betano odds {time_casa} {time_fora}"
    url_bing = f"https://www.bing.com/search?q={urllib.parse.quote(termo)}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9"
    }

    try:
        response = requests.get(url_bing, headers=headers, timeout=20)
        html = response.text

        # Log para conferência
        with open("log_html_google.txt", "w", encoding="utf-8") as f:
            f.write(html)

        if response.status_code != 200:
            print(f"⚠️ Bing retornou status: {response.status_code}")
            return None

        # No Bing, os links da Betano costumam vir limpos no href
        # Procuramos o padrão betano.bet.br/odds/ seguido de algo
        padrao = r'https://www\.betano\.bet\.br/odds/[a-zA-Z0-9\-/]+'
        links = re.findall(padrao, html)

        if links:
            # Remove duplicados
            links = list(dict.fromkeys(links))
            for link in links:
                # Se tiver o nome do time no link, é vitória
                if time_casa.lower()[:4] in link.lower() or time_fora.lower()[:4] in link.lower():
                    print(f"✅ Link Encontrado no Bing: {link}")
                    return link
            
            return links[0]

        print("❌ Bing também não mostrou links da Betano.")

    except Exception as e:
        print(f"⚠️ Erro: {e}")
    
    return None

if __name__ == "__main__":
    resultado = buscar_link_bing("Cruzeiro", "Boca Juniors")
    print("\n" + "="*50)
    print(f"RESULTADO: {resultado}")
    print("="*50)
    
