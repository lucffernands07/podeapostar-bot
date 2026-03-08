from bs4 import BeautifulSoup

def analisar_html_neo(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Dicionário para os dados que você foca
    resultados = {
        "Over 1.5": "0%", "Over 2.5": "0%", 
        "BTTS": "0%", "CS_Palmeiras": "0%", "CS_Novorizontino": "0%"
    }

    # 1. Pegando Over 1.5, 2.5 e BTTS
    itens = soup.select(".grid-item")
    for item in itens:
        valor = item.select_one(".stat-strong").get_text(strip=True)
        label = item.select_one("span").get_text(strip=True)
        sub_text = item.select_one(".stat-text").get_text(strip=True)

        if "Over 1.5" in label: resultados["Over 1.5"] = valor
        if "Over 2.5" in label: resultados["Over 2.5"] = valor
        if "BTTS" in label:     resultados["BTTS"] = valor
        
        # 2. Pegando Clean Sheets (Diferenciando por Time)
        if "Clean Sheets" in label:
            if "Palmeiras" in sub_text:
                resultados["CS_Palmeiras"] = valor
            elif "Novorizontino" in sub_text:
                resultados["CS_Novorizontino"] = valor

    # --- TESTE DE OUTPUT ---
    print("🚀 DADOS DO H2H-NEO (PALMEIRAS vs NOVORIZONTINO):")
    for k, v in resultados.items():
        print(f"📍 {k}: {v}")

    # Validação da sua regra 4/5 (80%)
    o15 = int(resultados["Over 1.5"].replace('%', ''))
    if o15 >= 80:
        print("\n✅ SEGURANÇA: Over 1.5 aprovado para o bilhete!")
    else:
        print("\n⚠️ SEGURANÇA: Abaixo de 80%, atenção.")

# Testando com o HTML que você mandou
html_bruto = """... cole o seu HTML aqui ...""" 
analisar_html_neo(html_bruto)
