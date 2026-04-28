import sys
import os
import requests
import re
import json

# Garante que encontre os módulos da raiz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def buscar_link_google_script(time_casa, time_fora):
    print(f"🚀 [REGEX MODE] Analisando scripts do Google para: {time_casa} x {time_fora}")
    
    termo = f"betano odds {time_casa} vs {time_fora}".replace(" ", "+")
    url = f"https://www.google.com/search?q={termo}&hl=pt-BR"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        # 1. Pegamos o HTML bruto
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"⚠️ Erro ao acessar Google: {response.status_code}")
            return None

        html_content = response.text
        
        # 2. Procuramos por URLs da Betano dentro de blocos de script ou do próprio HTML
        # Essa regex busca links da Betano que tenham a palavra 'odds'
        padrao_link = r'https://www\.betano\.bet\.br/odds/[a-zA-Z0-9\-/]+'
        links_encontrados = re.findall(padrao_link, html_content)
        
        # 3. Limpeza e Validação
        if links_encontrados:
            # Remove duplicados mantendo a ordem
            links_unicos = list(dict.fromkeys(links_encontrados))
            
            for link in links_unicos:
                # Prioriza links que contenham o nome do time (ou parte dele)
                if time_casa.lower()[:4] in link.lower() or "jogos" in link.lower():
                    print(f"✅ Link extraído via Regex: {link}")
                    return link
            
            # Se não achou um específico, retorna o primeiro da Betano que apareceu
            print(f"⚠️ Link aproximado encontrado: {links_unicos[0]}")
            return links_unicos[0]
        else:
            print("❌ Nenhum link da Betano encontrado no script da página.")
            
    except Exception as e:
        print(f"⚠️ Erro na extração: {e}")
    
    return None

if __name__ == "__main__":
    print("=== TESTE EXTRAÇÃO POR SCRIPT (Lógica Reddit) ===")
    res = buscar_link_google_script("Cruzeiro", "Boca Juniors")
    
    print("\n" + "="*50)
    print(f"RESULTADO: {res if res else 'NÃO ENCONTRADO'}")
    print("="*50)
    
