import os
import json
import base64
import time
from openai import OpenAI

# Configuração OpenRouter
client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=os.getenv("OPENROUTER_API_KEY"),
)

def analisar_com_openrouter(caminho_img):
    with open(caminho_img, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    try:
        # Tenta o Gemma 4 31B que é multimodal e gratuito
        response = client.chat.completions.create(
            model="google/gemma-4-31b:free", 
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analise a imagem. Se for um bilhete de Telegram com 'BINGO', responda: {'tipo': 'SUGESTAO'}. Se for um print da Betano com 'GANHOU', responda: {'tipo': 'GREEN'}. Retorne apenas o JSON puro."},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }
                    ]
                }
            ]
        )
        
        res_text = response.choices[0].message.content
        print(f"DEBUG - Resposta do Modelo para {os.path.basename(caminho_img)}: {res_text}")
        
        # Limpa markdown caso o modelo coloque
        json_txt = res_text.replace("```json", "").replace("```", "").strip()
        return json.loads(json_txt)
    except Exception as e:
        print(f"❌ Erro ao processar {caminho_img}: {e}")
        return None

def main():
    # Caminho correto para o repositório no GitHub Actions
    db_path = "ranking_db.json"
    pasta_prints = "prints/"
    
    if os.path.exists(db_path):
        with open(db_path, 'r') as f:
            db = json.load(f)
    else:
        db = {"processados": [], "ranking": {}}

    arquivos = [f for f in os.listdir(pasta_prints) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    mudanca = False

    for arquivo in arquivos:
        if arquivo not in db["processados"]:
            print(f"🚀 Analisando ficheiro novo: {arquivo}")
            resultado = analisar_com_openrouter(os.path.join(pasta_prints, arquivo))
            
            if resultado:
                db["processados"].append(arquivo)
                tipo = resultado.get("tipo")
                
                if tipo == "GREEN":
                    # Adiciona 10 pontos ao ranking geral
                    db["ranking"]["Geral"] = db["ranking"].get("Geral", 0) + 10
                    print(f"✨ Green validado para {arquivo}!")
                
                mudanca = True
                time.sleep(2) # Evita rate limit

    if mudanca:
        with open(db_path, 'w') as f:
            json.dump(db, f, indent=4)
        print("✅ ranking_db.json atualizado com novos dados!")
    else:
        print("ℹ️ Nenhuma alteração relevante detetada nas imagens.")

if __name__ == "__main__":
    main()
  
