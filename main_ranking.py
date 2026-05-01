import os
import json
import base64
import time
from openai import OpenAI

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=os.getenv("OPENROUTER_API_KEY"),
)

def extrair_texto(caminho_img):
    with open(caminho_img, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
    try:
        response = client.chat.completions.create(
            model="baidu/qianfan-ocr-fast:free", 
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": "Extract all text from this bet slip."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}
            ]
        )
        return response.choices[0].message.content.upper()
    except Exception as e:
        print(f"❌ Erro OCR: {e}")
        return None

def identificar_dados(texto):
    # Identifica Status
    status = "RED" if "PERDIDA" in texto else "GREEN" if ("GANHOU" in texto or "PRÊMIO" in texto or "VENCIDA" in texto) else "OUTRO"
    
    # Identifica Porcentagem (70, 80, 100)
    porcentagem = "70%" if "70%" in texto else "80%" if "80%" in texto else "100%" if "100%" in texto else ""
    
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
    elif "VASCO" in texto or "FLUMINENSE" in texto or "CASA" in texto: # Exemplo de detecção de vitória casa
        mercado = "VITÓRIA CASA"

    nome_final = f"{mercado} {porcentagem}".strip()
    return nome_final, status

def main():
    db_path = "ranking_db.json"
    pasta_prints = "prints/"
    
    if os.path.exists(db_path):
        with open(db_path, 'r', encoding='utf-8') as f:
            db = json.load(f)
    else:
        db = {"processados": [], "stats": {}}

    arquivos = [f for f in os.listdir(pasta_prints) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    for arquivo in arquivos:
        if arquivo not in db["processados"]:
            print(f"🚀 Analisando: {arquivo}")
            texto = extrair_texto(os.path.join(pasta_prints, arquivo))
            
            if texto:
                nome_mercado, status = identificar_dados(texto)
                
                if status != "OUTRO":
                    if nome_mercado not in db["stats"]:
                        db["stats"][nome_mercado] = {"green": 0, "red": 0}
                    
                    chave = "green" if status == "GREEN" else "red"
                    db["stats"][nome_mercado][chave] += 1
                    db["processados"].append(arquivo)
                    print(f"✅ {nome_mercado} -> {status}")
            
            time.sleep(15)

    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

    # --- GERAR RELATÓRIO ORDENADO ---
    ranking_lista = []
    bingos_lista = []

    for m, v in db["stats"].items():
        total = v["green"] + v["red"]
        perc = (v["green"] / total * 100) if total > 0 else 0
        item = {"nome": m, "g": v["green"], "r": v["red"], "perc": perc}
        
        if "BINGO" in m:
            bingos_lista.append(item)
        else:
            ranking_lista.append(item)

    # Ordena por porcentagem de acerto
    ranking_lista.sort(key=lambda x: x["perc"], reverse=True)

    print("\n📊 --- RANKING FINAL ---")
    print(f"{'MERCADO':<20} | {'GREEN':<5} | {'RED':<5} | {'% ACERTO'}")
    for i in ranking_lista:
        print(f"{i['nome']:<20} | {i['g']:<5} | {i['r']:<5} | {i['perc']:.1f}%")
    
    print("\n🎯 --- BINGOS ---")
    for b in bingos_lista:
        print(f"{b['nome']}: {b['g']} ✅ | {b['r']} ❌")

if __name__ == "__main__":
    main()
  
