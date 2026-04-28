import sys
import os
import requests
import re
import urllib.parse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def buscar_e_logar_html(time_casa, time_fora):
    print(f"🚀 [ROBÔ] Iniciando busca e gerando log para: {time_casa} x {time_fora}")
    
    termo = f"site:betano.bet.br/odds {time_casa} {time_fora}".replace(" ", "+")
    url_google = f"https://www.google.com/search?q={termo}&hl=pt-BR"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    try:
        response = requests.get(url_google, headers=headers, timeout=20)
        html = response.text

        # --- GERAÇÃO DO LOG ---
        # Salva o HTML capturado para você analisar
        with open("log_html_google.txt", "w", encoding="utf-8") as f:
            f.write(f"STATUS CODE: {response.status_code}\n")
            f.write(f"URL BUSCADA: {url_google}\n")
            f.write("-" * 50 + "\n")
            f.write(html)
        print("💾 Log do HTML salvo em 'log_html_google.txt'")
        # ----------------------

        if response.status_code != 200:
            print(f"⚠️ Status inesperado: {response.status_code}")
            return None

        # Tentativa de captura 1: Redirecionamento
        padrao_redirecionamento = r'/url\?q=(https://www\.betano\.bet\.br/odds/[^&]+)'
        match = re.search(padrao_redirecionamento, html)
        
        if match:
            return urllib.parse.unquote(match.group(1))
        
        # Tentativa de captura 2: Link Direto
        padrao_direto = r'https://www\.betano\.bet\.br/odds/[a-zA-Z0-9\-/]+'
        match_direto = re.search(padrao_direto, html)
        
        if match_direto:
            return match_direto.group(0)

        print("❌ Nenhum link encontrado no HTML.")

    except Exception as e:
        print(f"⚠️ Erro: {e}")
    
    return None

if __name__ == "__main__":
    resultado = buscar_e_logar_html("Cruzeiro", "Boca Juniors")
    print(f"\nFinal: {resultado}")
    
