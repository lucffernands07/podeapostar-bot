import os
import json
import base64
import time
from openai import OpenAI

# Configuração seguindo o padrão da documentação do Gemma 4 no OpenRouter
client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=os.getenv("OPENROUTER_API_KEY"),
)

def analisar_com_qwen(caminho_img):
    with open(caminho_img, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    for tentativa in range(3):
        try:
            response = client.chat.completions.create(
                model="qwen/qwen-2-vl-7b-instruct:free", 
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Task: Check betting status. If 'GANHOU' or 'PRÊMIO' is found, return {'tipo': 'GREEN'}. If 'BINGO' is found on a Telegram screen, return {'tipo': 'SUGESTAO'}. Return ONLY the JSON object."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }
                ],
                temperature=0.1
            )
            
            res_text = response.choices[0].message.content
            print(f"DEBUG Qwen: {res_text}")
            
            # Limpeza do JSON
            json_txt = res_text.replace("```json", "").replace("```", "").strip()
            return json.loads(json_txt)

        except Exception as e:
            if "429" in str(e):
                print(f"⚠️ Qwen ocupado (Tentativa {tentativa+1}). Aguardando 30s...")
                time.sleep(30)
            else:
                print(f"❌ Erro no Qwen: {e}")
                return None
    return None


def main():
    db_path = "ranking_db.json"
    pasta_prints = "prints/"
    
    if os.path.exists(db_path):
        with open(db_path, 'r', encoding='utf-8') as f:
            db = json.load(f)
    else:
        db = {"processados": [], "ranking": {}}

    if not os.path.exists(pasta_prints):
        os.makedirs(pasta_prints)
        return

    arquivos = [f for f in os.listdir(pasta_prints) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    mudanca = False

    for arquivo in arquivos:
        if arquivo not in db["processados"]:
            print(f"🚀 Processando com Gemma 4 31B: {arquivo}")
            resultado = analisar_com_gemma4(os.path.join(pasta_prints, arquivo))
            
            if resultado:
                db["processados"].append(arquivo)
                if resultado.get("tipo") == "GREEN":
                    db["ranking"]["Geral"] = db["ranking"].get("Geral", 0) + 10
                    print(f"✨ GREEN Detectado!")
                mudanca = True
            
            # --- AJUSTE AQUI ---
            # Esperamos 20 segundos para não estourar o limite de requisições gratuitas
            print("⏳ Aguardando 20 segundos para respeitar o Rate Limit...")
            time.sleep(20) 

    if mudanca:
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=4, ensure_ascii=False)
        print("✅ ranking_db.json atualizado!")

if __name__ == "__main__":
    main()
  
