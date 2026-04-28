import sys
import os
import requests
import re
import urllib.parse

# Garante que encontre os módulos da raiz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def buscar_e_limpar_link(time_casa, time_fora):
    print(f"🚀 [ROBÔ] Pesquisando no Google: {time_casa} x {time_fora}")
    
    # O "pulo do gato": site:betano.bet.br força o Google a trazer o link certo no topo
    termo = f"site:betano.bet.br/odds {time_casa} {time_fora}".replace(" ", "+")
    url_google = f"https://www.google.com/search?q={termo}&hl=pt-BR"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url_google, headers=headers, timeout=20)
        if response.status_code != 200:
            print(f"⚠️ Google bloqueou o acesso (Status {response.status_code})")
            return None

        html = response.text

        # REGEX PARA O LINK DO PRINT:
        # Ela procura por /url?q= seguido de um link da Betano até encontrar o próximo '&'
        padrao_redirecionamento = r'/url\?q=(https://www\.betano\.bet\.br/odds/[^&]+)'
        
        match = re.search(padrao_redirecionamento, html)
        
        if match:
            link_codificado = match.group(1)
            # A mágica da limpeza: transforma %2F em / e limpa o lixo
            link_limpo = urllib.parse.unquote(link_codificado)
            
            print(f"✅ Link capturado e limpo: {link_limpo}")
            return link_limpo
        
        # Caso o Google entregue o link direto (sem o /url?q=)
        padrao_direto = r'https://www\.betano\.bet\.br/odds/[a-zA-Z0-9\-/]+'
        match_direto = re.search(padrao_direto, html)
        
        if match_direto:
            print(f"✅ Link direto encontrado: {match_direto.group(0)}")
            return match_direto.group(0)

        print("❌ O robô não encontrou nenhum link da Betano nos resultados.")

    except Exception as e:
        print(f"⚠️ Erro no robô: {e}")
    
    return None

if __name__ == "__main__":
    print("=== INICIANDO BUSCA AUTOMATIZADA ===")
    
    # O robô recebe os times e faz todo o trabalho de garimpo
    jogo_teste = {"casa": "Cruzeiro", "fora": "Boca Juniors"}
    
    resultado = buscar_e_limpar_link(jogo_teste["casa"], jogo_teste["fora"])
    
    print("\n" + "="*50)
    print(f"RESULTADO PARA O MAIN.PY: {resultado}")
    print("="*50)
    
