import sys
import os
import tls_client

# Garante que encontre os módulos da raiz se necessário
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def buscar_link_betano_tls(time_casa, time_fora):
    print(f"🚀 [TLS-CLIENT MODE] Buscando link para: {time_casa} x {time_fora}")

    # Criando a sessão que simula o navegador Chrome (Lógica SofaScore)
    # Isso evita o bloqueio de "impressão digital" (JA3) do Cloudflare
    session = tls_client.Session(
        client_identifier="chrome_120",
        random_tls_extension_order=True
    )

    # API interna de busca da Betano - muito mais rápida que o Google
    search_url = "https://www.betano.bet.br/api/search/"
    params = {
        "q": f"{time_casa} {time_fora}",
        "limit": "5",
        "languageId": "pt"
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.betano.bet.br/",
        "X-Requested-With": "XMLHttpRequest"
    }

    try:
        response = session.get(search_url, params=params, headers=headers)
        
        if response.status_code == 200:
            dados = response.json()
            # Navega no JSON da Betano para achar o evento
            resultados = dados.get('data', {}).get('results', [])
            
            for item in resultados:
                # Verificamos se o resultado é um evento de jogo
                if item.get('type') == 'EVENT':
                    url_path = item.get('url')
                    if url_path:
                        link_final = f"https://www.betano.bet.br{url_path}"
                        print(f"✅ Link encontrado: {link_final}")
                        return link_final
            
            print("❌ Jogo não encontrado na API da Betano.")
        else:
            print(f"⚠️ Bloqueio detectado! Status: {response.status_code}")
            print(f"Resposta curta: {response.text[:100]}")

    except Exception as e:
        print(f"⚠️ Erro no TLS-Client: {e}")
    
    return None

if __name__ == "__main__":
    print("=== TESTE COM TLS-CLIENT (Lógica SofaScore) ===")
    # Teste com os times desejados
    casa = "Cruzeiro"
    fora = "Boca Juniors"
    
    resultado = buscar_link_betano_tls(casa, fora)
    
    print("\n" + "="*50)
    print(f"RESULTADO FINAL: {resultado if resultado else 'FALHA NO TLS'}")
    print("="*50)
    
