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
    # Limpeza para facilitar a busca
    t = texto.upper()
    
    # 1. IDENTIFICAÇÃO DE STATUS (Ajustado para o seu Log)
    status = "OUTRO"
    
    # Se no texto aparecer o placar (RESULTADO) mas não tiver "GANHOU", 
    # e for um print de conferência, precisamos de uma lógica.
    # Por enquanto, vamos manter as palavras que o Tesseract costuma ler:
    if any(x in t for x in ["GANH", "VENC", "PREM", "PRÊM", "PAGO"]):
        status = "GREEN"
    elif any(x in t for x in ["PERD", "PERO", "REO", "ERDI"]):
        status = "RED"
    # DICA: Se for print da Betano e tiver "RESULTADO", mas não for Green, 
    # geralmente é porque o check de 'Ganhou' não foi lido.
    
    # 2. IDENTIFICAÇÃO DE PORCENTAGEM
    porcentagem = ""
    for p in ["100%", "85%", "80%", "75%", "70%"]:
        if p in t:
            porcentagem = p
            break

    # 3. IDENTIFICAÇÃO DE MERCADO (Baseado no seu Log)
    mercado = "OUTROS"
    
    # Prioridade para BINGOS
    if "BINGO 5" in t: mercado = "BINGO 5"
    elif "BINGO 3" in t: mercado = "BINGO 3"
    elif "BINGO 1" in t: mercado = "BINGO 1"
    elif "BINGO 7" in t: mercado = "BINGO 7"
    
    # Mercados Técnicos
    elif "AMBAS MARCAM" in t or "AMBAS EQUIPES" in t or "SIM 1." in t:
        mercado = "AMBAS MARCAM"
    elif "+1.5" in t or "MAIS DE 1.5" in t or "1.5 GOLS" in t:
        mercado = "GOLS +1.5"
    elif "+2.5" in t or "MAIS DE 2.5" in t or "2.5 GOLS" in t:
        mercado = "GOLS +2.5"
    elif "1X" in t or "CHANCE DUPLA 1X" in t:
        mercado = "1X"
    elif "2X" in t or "X2" in t or "CHANCE DUPLA X2" in t:
        mercado = "2X"
    elif "CASA" in t or "VENCEDOR 1" in t:
        mercado = "VITÓRIA CASA"

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
        
