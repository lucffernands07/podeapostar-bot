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
    """
    Tenta extrair todo o texto visível na imagem usando o Baidu OCR.
    """
    with open(caminho_img, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    for tentativa in range(3):
        try:
            response = client.chat.completions.create(
                model="baidu/qianfan-ocr-fast", 
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text", 
                                "text": "Extract all text from this image accurately. Return only the transcript."
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                            }
                        ]
                    }
                ]
            )
            
            texto_extraido = response.choices[0].message.content
            return texto_extraido

        except Exception as e:
            if "429" in str(e):
                print(f"⚠️ Aguardando 40s (Rate Limit)... {tentativa+1}/3")
                time.sleep(40)
            else:
                print(f"❌ Erro: {e}")
                return None
    return None

def main():
    pasta_prints = "prints/"
    
    if not os.path.exists(pasta_prints):
        print("Pasta não encontrada.")
        return

    # Pega apenas uma imagem para teste inicial
    arquivos = [f for f in os.listdir(pasta_prints) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not arquivos:
        print("Nenhuma imagem na pasta.")
        return

    for arquivo in arquivos[:3]:  # Vamos testar com as 3 primeiras
        print(f"\n🔍 Lendo: {arquivo}")
        caminho = os.path.join(pasta_prints, arquivo)
        
        texto = extrair_texto_da_imagem(caminho)
        
        if texto:
            print(f"📝 TEXTO ENCONTRADO EM {arquivo}:")
            print("-" * 30)
            print(texto)
            print("-" * 30)
        else:
            print(f"🚫 Falha ao extrair texto de {arquivo}")
            
        time.sleep(10) # Pausa entre testes

if __name__ == "__main__":
    main()
