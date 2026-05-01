import os
import json
import time
import pytesseract
from PIL import Image

def extrair_texto(caminho_img):
    try:
        # Extração local usando Tesseract
        texto = pytesseract.image_to_string(Image.open(caminho_img), lang='por')
        return texto.upper()
    except Exception as e:
        print(f"❌ Erro no OCR Tesseract: {e}")
        return None

def identificar_dados(texto):
    # Deixamos a identificação básica por enquanto
    # Depois que você me mandar o log, vamos "amaciar" essas regras
    status = "RED" if "PERDIDA" in texto else "GREEN" if ("GANHOU" in texto or "PRÊMIO" in texto or "VENCIDA" in texto) else "OUTRO"
    
    porcentagem = ""
    for p in ["100%", "90%", "85%", "80%", "75%", "70%"]:
        if p in texto:
            porcentagem = p
            break
    
    mercado = "OUTROS"
    if "BINGO" in texto:
        mercado = "BINGO 1" if "1" in texto else "BINGO 5" if "5" in texto else "BINGO 7" if "7" in texto else "BINGO"
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
    log_path = "ocr_debug.log"  # Onde vamos ver o que o Tesseract leu
    pasta_prints = "prints/"
    
    if os.path.exists(db_path):
        with open(db_path, 'r', encoding='utf-8') as f:
            try: db = json.load(f)
            except: db = {"processados": [], "stats": {}}
    else:
        db = {"processados": [], "stats": {}}

    if "stats" not in db: db["stats"] = {}
    if "processados" not in db: db["processados"] = []

    if not os.path.exists(pasta_prints):
        print("Pasta prints/ não encontrada.")
        return

    arquivos = [f for f in os.listdir(pasta_prints) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    mudanca = False

    # Abrimos o arquivo de log para acrescentar os novos textos brutos
    with open(log_path, "a", encoding="utf-8") as log_file:
        for arquivo in arquivos:
            if arquivo not in db["processados"]:
                print(f"🚀 Analisando: {arquivo}")
                texto_bruto = extrair_texto(os.path.join(pasta_prints, arquivo))
                
                if texto_bruto:
                    # REGISTRO PARA DEBUG: Salva exatamente o que a IA leu
                    log_file.write(f"\n===== INÍCIO: {arquivo} =====\n")
                    log_file.write(texto_bruto)
                    log_file.write(f"\n===== FIM: {arquivo} =====\n")

                    nome_mercado, status = identificar_dados(texto_bruto)
                    
                    if status != "OUTRO":
                        if nome_mercado not in db["stats"]:
                            db["stats"][nome_mercado] = {"green": 0, "red": 0}
                        
                        chave = "green" if status == "GREEN" else "red"
                        db["stats"][nome_mercado][chave] += 1
                        db["processados"].append(arquivo)
                        mudanca = True
                        print(f"✅ {nome_mercado} -> {status}")
                    else:
                        # Se não identificou, ainda assim marcamos como processado para não 
                        # ficar gastando tempo no próximo run, ou removemos para tentar de novo
                        # Por enquanto, não adicionamos ao 'processados' para podermos re-testar
                        print(f"⚠️ Status não identificado em {arquivo}. Veja {log_path}")
                
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
        if "BINGO" in m: bingos_lista.append(item)
        else: ranking_lista.append(item)

    ranking_lista.sort(key=lambda x: x["perc"], reverse=True)

    print("\n📊 --- RANKING DE ASSERTIVIDADE ---")
    print(f"{'MERCADO':<25} | {'GREEN':<5} | {'RED':<5} | {'% ACERTO'}")
    print("-" * 60)
    for i in ranking_lista:
        print(f"{i['nome']:<25} | {i['g']:<5} | {i['r']:<5} | {i['perc']:.1f}%")
    
    print("\n🎯 --- BILHETES BINGO ---")
    for b in bingos_lista:
        print(f"{b['nome']}: {b['g']} ✅ | {b['r']} ❌")

if __name__ == "__main__":
    main()
        
