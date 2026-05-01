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

def extrair_texto_da_imagem(caminho_img):
    with open(caminho_img, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    try:
        # ID CORRIGIDO: baidu/qianfan-ocr-fast:free
        response = client.chat.completions.create(
            model="baidu/qianfan-ocr-fast:free", 
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": "Extract all text from this image. Return only the text found."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
        )
        
        texto = response.choices[0].message.content
        return texto

    except Exception as e:
        print(f"❌ Erro no Baidu OCR: {e}")
        return None

def main():
    pasta_prints = "prints/"
    
    if not os.path.exists(pasta_prints):
        print("Pasta de prints não encontrada.")
        return

    arquivos = [f for f in os.listdir(pasta_prints) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    # Vamos testar apenas o primeiro para ver se o 404 sumiu
    if arquivos:
        arquivo = arquivos[0]
        print(f"🚀 Testando extração de: {arquivo}")
        
        resultado = extrair_texto_da_imagem(os.path.join(pasta_prints, arquivo))
        
        if resultado:
            print("\n✅ TEXTO EXTRAÍDO COM SUCESSO:")
            print("-" * 40)
            print(resultado)
            print("-" * 40)
        else:
            print("⚠️ Não foi possível extrair texto.")

if __name__ == "__main__":
    main()
  
