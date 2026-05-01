import os
import json
import time
import pytesseract
from PIL import Image

# Não precisamos mais do cliente OpenAI/OpenRouter para o OCR

def extrair_texto(caminho_img):
    try:
        # O Tesseract processa a imagem localmente
        # 'lang=por' ajuda a reconhecer caracteres como acentos e cedilha
        texto = pytesseract.image_to_string(Image.open(caminho_img), lang='por')
        return texto.upper()
    except Exception as e:
        print(f"❌ Erro no OCR Tesseract: {e}")
        return None

def identificar_dados(texto):
    # Identifica Status
    status = "RED" if "PERDIDA" in texto else "GREEN" if ("GANHOU" in texto or "PRÊMIO" in texto or "VENCIDA" in texto) else "OUTRO"
    
    # Identifica Porcentagem (70, 80, 100)
    porcentagem = ""
    # Busca a maior porcentagem presente no texto
    if "100%" in texto: porcentagem = "100%"
    elif "90%" in texto: porcentagem = "90%"
    elif "85%" in texto: porcentagem = "85%"
    elif "80%" in texto: porcentagem = "80%"
    elif "75%" in texto: porcentagem = "75%"
    elif "70%" in texto: porcentagem = "70%"
    
    # Identifica Mercado
    mercado = "OUTROS"
    if "BINGO" in texto:
        if "BINGO 1" in texto: mercado = "BINGO 1"
        elif "BINGO 5" in texto: mercado = "BINGO 5"
        elif "BINGO 7" in texto: mercado = "BINGO 7"
        else: mercado = "BINGO"
    elif "AMBAS MARCAM" in texto or "AMBAS EQUIPES" in texto: mercado = "AMBAS MARCAM"
    elif "MAIS DE 1.5" in texto or "+1.5" in texto: mercado = "GOLS +1.5"
    elif "MAIS DE 2.5" in texto or "+2.5" in texto: mercado = "GOLS +2.5"
    elif "1X" in texto: mercado = "1X"
    elif "2X" in texto: mercado = "2X"
    elif "CASA" in texto: mercado = "VITÓRIA CASA"

    nome_final = f"{mercado} {porcentagem}".strip()
    return nome_final, status

def main():
    db_path = "ranking_db.json"
    pasta_prints = "prints/"
    
    # Carregamento Seguro
    if os.path.exists(db_path):
        with open(db_path, 'r', encoding='utf-8') as f:
            try:
                db = json.load(f)
            except:
                db = {"processados": [], "stats": {}}
    else:
        db = {"processados": [], "stats": {}}

    if "stats" not in db: db["stats"] = {}
    if "processados" not in db: db["processados"] = []

    if not os.path.exists(pasta_prints):
        print("Pasta prints/ não encontrada.")
        return

    arquivos = [f for f in os.listdir(pasta_prints) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    mudanca = False

    for arquivo in arquivos:
        if arquivo not in db["processados"]:
            print(f"🚀 Analisando Localmente: {arquivo}")
            texto = extrair_texto(os.path.join(pasta_prints, arquivo))
            
            if texto:
                nome_mercado, status = identificar_dados(texto)
                
                if status != "OUTRO":
                    if nome_mercado not in db["stats"]:
                        db["stats"][nome_mercado] = {"green": 0, "red": 0}
                    
                    chave = "green" if status == "GREEN" else "red"
                    db["stats"][nome_mercado][chave] += 1
                    db["processados"].append(arquivo)
                    mudanca = True
                    print(f"✅ {nome_mercado} -> {status}")
                else:
                    print(f"⚠️ Status não identificado em {arquivo}")
            
            # Com Tesseract não precisamos de sleep longo, mas 1s evita sobrecarga
            time.sleep(0.5)

    if mudanca:
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=4, ensure_ascii=False)

    # --- RELATÓRIO ORDENADO ---
    ranking_lista = []
    bingos_lista = []

    for m, v in db.get("stats", {}).items():
        total = v["green"] + v["red"]
        perc = (v["green"] / total * 100) if total > 0 else 0
        item = {"nome": m, "g": v["green"], "r": v["red"], "perc": perc}
        
        if "BINGO" in m:
            bingos_lista.append(item)
        else:
            ranking_lista.append(item)

    # Ordena por % de acerto (do maior para o menor)
    ranking_lista.sort(key=lambda x: x["perc"], reverse=True)

    print("\n📊 --- RANKING DE ASSERTIVIDADE (LOCAL OCR) ---")
    print(f"{'MERCADO':<25} | {'GREEN':<5} | {'RED':<5} | {'% ACERTO'}")
    print("-" * 60)
    for i in ranking_lista:
        print(f"{i['nome']:<25} | {i['g']:<5} | {i['r']:<5} | {i['perc']:.1f}%")
    
    print("\n🎯 --- BILHETES BINGO ---")
    for b in bingos_lista:
        print(f"{b['nome']}: {b['g']} ✅ | {b['r']} ❌")

if __name__ == "__main__":
    main()
      
