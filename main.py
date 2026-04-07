import os
import tls_client
import requests
from datetime import datetime

# Sessão com identidade de Navegador Mobile (mais difícil de bloquearem)
session = tls_client.Session(client_identifier="chrome_120")

def minerar_v2():
    hoje = datetime.now().strftime("%Y-%m-%d")
    
    # --- ESTRATÉGIA 1: API MÓVEL ---
    # O endpoint móvel costuma ter menos proteção que o desktop
    url_mobile = f"https://api.sofascore.com/api/v1/sport/soccer/events/day/{hoje}"
    
    headers = {
        "User-Agent": "SofaScore/6.1.1 (iPhone; iOS 17.4; Scale/3.00)", # Fingindo ser o APP do iPhone
        "Accept": "*/*",
        "Host": "api.sofascore.com"
    }

    print(f"📡 Tentando Rota Mobile ({hoje})...")
    
    try:
        res = session.get(url_mobile, headers=headers)
        
        # Se der 404 ou 403, tentamos a Rota de Widgets (Web)
        if res.status_code != 200:
            print(f"⚠️ Rota Mobile falhou ({res.status_code}). Tentando Rota Web...")
            url_web = f"https://www.sofascore.com/api/v1/sport/soccer/events/day/{hoje}"
            headers_web = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                "Referer": "https://www.sofascore.com/"
            }
            res = session.get(url_web, headers=headers_web)

        if res.status_code == 200:
            print("✅ Sucesso! Dados capturados.")
            return res.json()
        else:
            print(f"❌ Bloqueio total do IP do GitHub (Status {res.status_code}).")
            # Aqui você poderia disparar um alerta pro seu Telegram avisando que o IP caiu
            return None
            
    except Exception as e:
        print(f"⚠️ Erro: {e}")
        return None
