4import sys
import os
import requests
import re
import urllib.parse

# Garante que encontre os módulos da raiz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def buscar_link_duckduckgo(time_casa, time_fora):
    print(f"🚀 [ROBÔ] Buscando via DuckDuckGo: {time_casa} x {time_fora}")
    
    # Termo focado na Betano
    termo = f"site:betano.bet.br/odds {time_casa} {time_fora}"
    
    # URL da versão HTML (sem JavaScript)
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(termo)}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=20)
        html = response.text

        # Salva o log para a gente conferir no GitHub Actions
        with open("log_html_google.txt", "w", encoding="utf-8") as f:
            f.write(html)
        print("💾 Log salvo (mesmo nome para aproveitar o .yml)")

        if response.status_code != 200:
            print(f"⚠️ Erro no DuckDuckGo: {response.status_code}")
            return None

        # O DuckDuckGo entrega o link dentro de um redirecionamento interno: /l/?kh=-1&uddg=URL_AQUI
        # Vamos pegar tudo que está depois de 'uddg='
        padrao_uddg = r'uddg=([^&"\']+)'
        matches = re.findall(padrao_uddg, html)

        if matches:
            for link_encodado in matches:
                link_limpo = urllib.parse.unquote(link_encodado)
                
                # Valida se é um link de odds da Betano e se tem relação com os times
                if "betano.bet.br/odds/" in link_limpo:
                    # Verifica se o nome do time (ou parte dele) está no link
                    if time_casa.lower()[:4] in link_limpo.lower() or "jogos" in link_limpo.lower():
                        print(f"✅ Link Extraído: {link_limpo}")
                        return link_limpo
            
            # Se não passou no filtro rigoroso, retorna o primeiro link da betano que achar
            for link_encodado in matches:
                link_limpo = urllib.parse.unquote(link_encodado)
                if "betano.bet.br/odds/" in link_limpo:
                    return link_limpo

        print("❌ Nenhum link da Betano encontrado nos resultados do DuckDuckGo.")

    except Exception as e:
        print(f"⚠️ Erro na execução: {e}")
    
    return None

if __name__ == "__main__":
    # Teste com o jogo que você mandou no print
    resultado = buscar_link_duckduckgo("Cruzeiro", "Boca Juniors")
    
    print("\n" + "="*50)
    print(f"RESULTADO PARA O BOT: {resultado}")
    print("="*50)
    
