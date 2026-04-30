import os
import json
import base64
from openai import OpenAI

# Configuração OpenRouter
client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=os.getenv("OPENROUTER_API_KEY"), # Crie essa KEY no site do OpenRouter
)

def analisar_com_openrouter(caminho_img):
    # Converte imagem para base64
    with open(caminho_img, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    try:
        response = client.chat.completions.create(
            # Aqui você escolhe um dos modelos free da sua lista
            model="google/gemma-4-31b:free", 
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analise a imagem e retorne apenas JSON: {'tipo': 'SUGESTAO' ou 'GREEN', 'times': 'time A x time B', 'odd': 0.00}. Se tiver 'BINGO' é SUGESTAO, se tiver 'GANHOU' é GREEN."},
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
        
        res_text = response.choices[0].message.content
        # Limpa o markdown se o modelo enviar
        json_txt = res_text.replace("```json", "").replace("```", "").strip()
        return json.loads(json_txt)
    except Exception as e:
        print(f"❌ Erro no OpenRouter: {e}")
        return None
        
