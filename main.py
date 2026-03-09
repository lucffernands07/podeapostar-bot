import os
import requests
from bs4 import BeautifulSoup
import re

def extrair_valor(texto_completo, mercado):
    # Procura a porcentagem que aparece PERTO do nome do mercado
    # Ex: Procura "80%" que esteja vindo antes ou depois de "OVER 1.5"
    padrao = r'(\d+)%\s*' + re.escape(mercado)
    match = re.search(padrao, texto_completo, re.IGNORECASE)
    if not match:
        # Tenta o inverso: "OVER 1.5" seguido de "80%"
        padrao_inverso = re.escape(mercado) + r'.*?(\d+)%'
        match = re.search(padrao_inverso, texto_completo, re.IGNORECASE | re.DOTALL)
    
    return match.group(1) + "%" if match else "0%"

def analisar_partida(api_key, url):
    params = {
        'url': url,
        'apikey': api_key,
        'js_render': 'true',
        'premium_proxy': 'true',
        'wait_for': '.stat-strong',
        'wait': '4000'
    }

    try:
        print(f"📡 Varredura Total em: {url.split('/')[-1]}...")
        response = requests.get('https://api.zenrows.com/v1/', params=params)
        
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        # Pegamos todo o texto da página de uma vez, removendo espaços extras
        texto_pagina = soup.get_text(separator=" ", strip=True).upper()

        res = {
            "o15": extrair_valor(texto_pagina, "OVER 1.5"),
            "o25": extrair_valor(texto_pagina, "OVER 2.5"),
            "btts": extrair_valor(texto_pagina, "BTTS"),
            "cs_lazio": extrair_valor(texto_pagina, "CLEAN SHEETS LAZIO"),
            "cs_sassuolo": extrair_valor(texto_pagina, "CLEAN SHEETS SASSUOLO")
        }
        
        return res

    except Exception as e:
        print(f"❌ Erro: {e}")
        return None

if __name__ == "__main__":
    key = os.getenv("ZENROWS_KEY")
    url_hoje = "https://footystats.org/italy/ss-lazio-vs-us-sassuolo-calcio-h2h-stats"
    
    dados = analisar_partida(key, url_hoje)

    if dados:
        print("\n🚀 RELATÓRIO DE VARREDURA:")
        for k, v in dados.items():
            print(f"📍 {k.upper()}: {v}")

        # Validação de segurança
        o15_num = int(dados['o15'].replace('%', ''))
        if o15_num >= 80:
            print(f"\n✅ APROVADO: Over 1.5 está com {o15_num}%!")
        else:
            print(f"\n⚠️ AVISO: Over 1.5 ainda retornou {o15_num}%.")
    else:
        print("❌ Falha crítica na captura.")
        
