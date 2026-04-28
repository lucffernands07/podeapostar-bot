import sys
import os
import requests
import re
import urllib.parse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def buscar_link_via_jina(time_casa, time_fora):
    print(f"🚀 [ROBÔ] Buscando via Jina Reader (bypass): {time_casa} x {time_fora}")
    
    # Termo de busca
    termo = f"site:betano.bet.br/odds {time_casa} {time_fora}"
    
    # O Jina Reader transforma qualquer site em texto para IA. 
    # Vamos pedir para ele ler a busca do Google/DuckDuckGo por nós.
    url_busca = f"https://www.google.com/search?q={urllib.parse.quote(termo)}&hl=pt-BR"
    jina_url = f"https://r.jina.ai/{url_busca}"
    
    # O Jina não bloqueia o GitHub Actions!
    headers = {
        "X-Return-Format": "text"
    }

    try:
        response = requests.get(jina_url, headers=headers, timeout=30)
        conteudo = response.text

        # Log para a gente ver o que ele trouxe
        with open("log_html_google.txt", "w", encoding="utf-8") as f:
            f.write(conteudo)
        print("💾 Log do Jina salvo.")

        if response.status_code != 200:
            print(f"⚠️ Erro no Jina: {response.status_code}")
            return None

        # Agora a Regex fica muito mais fácil, pois o Jina limpa o HTML e deixa só texto
        # Procuramos links da Betano
        padrao = r'https://www\.betano\.bet\.br/odds/[a-zA-Z0-9\-/]+'
        links = re.findall(padrao, conteudo)

        if links:
            # Remove duplicados mantendo a ordem
            links = list(dict.fromkeys(links))
            for link in links:
                # Se o link tiver o nome do time ou a palavra 'odds', é o nosso alvo
                if time_casa.lower()[:4] in link.lower():
                    print(f"✅ Link Encontrado pelo Jina: {link}")
                    return link
            
            print(f"✅ Link aproximado: {links[0]}")
            return links[0]

        print("❌ Nenhum link da Betano encontrado no texto retornado.")

    except Exception as e:
        print(f"⚠️ Erro na execução: {e}")
    
    return None

if __name__ == "__main__":
    resultado = buscar_link_via_jina("Cruzeiro", "Boca Juniors")
    print("\n" + "="*50)
    print(f"RESULTADO FINAL: {resultado}")
    print("="*50)
    
