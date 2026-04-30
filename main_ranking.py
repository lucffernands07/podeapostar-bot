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

def analisar_com_gemma4(caminho_img):
    with open(caminho_img, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    # Tentaremos até 3 vezes a mesma imagem se der Rate Limit
    for tentativa in range(3):
        try:
            response = client.chat.completions.create(
                model="google/gemma-4-31b-it:free", 
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Analyze this betting slip. If it has 'GANHOU' return {'tipo': 'GREEN'}. If it has 'BINGO', return {'tipo': 'SUGESTAO'}. Return ONLY JSON."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }
                ],
                temperature=0
            )
            
            res_text = response.choices[0].message.content
            print(f"DEBUG Gemma 4: {res_text}")
            json_txt = res_text.replace("```json", "").replace("```", "").strip()
            return json.loads(json_txt)

        except Exception as e:
            if "429" in str(e):
                print(f"⚠️ Rate limit atingido na tentativa {tentativa + 1}. Aguardando 40s para tentar de novo...")
                time.sleep(40) # Espera maior para limpar o limite
            else:
                print(f"❌ Erro fatal no Gemma 4: {e}")
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
  
