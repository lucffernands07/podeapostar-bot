import sys
import os
import requests
import re

# Garante que o script consiga importar módulos da raiz do projeto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def buscar_link_google_regex(time_casa, time_fora):
    print(f"🚀 [REGEX MODE] Buscando link no HTML para: {time_casa} x {time_fora}")
    
    # Termo de busca simples
    termo = f"betano odds {time_casa} vs {time_fora}".replace(" ", "+")
    url = f"https://www.google.com/search?q={termo}&hl=pt-BR"
    
    # Header para o Google não bloquear de cara
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=20)
        
        if response.status_code == 200:
            html_bruto = response.text
            
            # Regex para pescar links da Betano dentro do HTML/Scripts
            # Procuramos o padrão de links de odds da Betano
            padrao = r'https://www\.betano\.bet\.br/odds/[a-zA-Z0-9\-/]+'
            links = re.findall(padrao, html_bruto)
            
            if links:
                # Remove duplicados
                links = list(dict.fromkeys(links))
                
                for link in links:
                    # Filtro: tem que ter o nome de um dos times ou a palavra 'jogos'
                    if time_casa.lower()[:4] in link.lower() or "jogos" in link.lower():
                        print(f"✅ Link encontrado: {link}")
                        return link
                
                # Se não achou com o nome, retorna o primeiro link da betano que veio
                return links[0]
            else:
                print("❌ Nenhum link da Betano encontrado no HTML.")
        else:
            print(f"⚠️ Erro no Google: Status {response.status_code}")

    except Exception as e:
        print(f"⚠️ Erro na execução: {e}")
    
    return None

if __name__ == "__main__":
    print("=== INICIANDO TESTE REGEX (Lógica Reddit) ===")
    
    # Times para o teste
    casa = "Cruzeiro"
    fora = "Boca Juniors"
    
    resultado = buscar_link_google_regex(casa, fora)
    
    print("\n" + "="*50)
    if resultado:
        print(f"SUCESSO: {resultado}")
    else:
        print("FALHA: O link não pôde ser extraído.")
    print("="*50)
