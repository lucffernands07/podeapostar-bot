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

def analisar_com_ai(caminho_img):
    """
    Função para analisar a imagem usando o modelo Qwen-2-VL (ótimo para OCR).
    Tenta até 3 vezes em caso de Rate Limit (Erro 429).
    """
    with open(caminho_img, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    for tentativa in range(3):
        try:
            # Modelo Qwen 2-VL 7B (Geralmente mais livre que Gemma/Llama)
            response = client.chat.completions.create(
                model="qwen/qwen-2-vl-7b-instruct:free", 
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text", 
                                "text": "Analyze this betting slip. If it says 'GANHOU' or 'PRÊMIO', return {'tipo': 'GREEN'}. If it is a Telegram screen with 'BINGO', return {'tipo': 'SUGESTAO'}. Return ONLY the JSON object."
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                            }
                        ]
                    }
                ],
                temperature=0
            )
            
            res_text = response.choices[0].message.content
            print(f"DEBUG AI ({os.path.basename(caminho_img)}): {res_text}")
            
            # Limpeza simples de Markdown
            json_txt = res_text.replace("```json", "").replace("```", "").strip()
            return json.loads(json_txt)

        except Exception as e:
            if "429" in str(e):
                print(f"⚠️ Servidor ocupado (Tentativa {tentativa + 1}/3). Aguardando 30s...")
                time.sleep(30)
            else:
                print(f"❌ Erro na análise: {e}")
                return None
    return None

def main():
    db_path = "ranking_db.json"
    pasta_prints = "prints/"
    
    # Carrega ou cria o banco de dados local
    if os.path.exists(db_path):
        with open(db_path, 'r', encoding='utf-8') as f:
            db = json.load(f)
    else:
        db = {"processados": [], "ranking": {}}

    if not os.path.exists(pasta_prints):
        print("Pasta de prints não encontrada.")
        return

    # Lista arquivos de imagem
    arquivos = [f for f in os.listdir(pasta_prints) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    mudanca = False

    for arquivo in arquivos:
        if arquivo not in db["processados"]:
            print(f"🚀 Analisando: {arquivo}")
            caminho_completo = os.path.join(pasta_prints, arquivo)
            
            # Chama a função de análise (agora com o nome genérico para evitar erros)
            resultado = analisar_com_ai(caminho_completo)
            
            if resultado:
                db["processados"].append(arquivo)
                tipo = resultado.get("tipo")
                
                if tipo == "GREEN":
                    # Adiciona 10 pontos ao ranking geral
                    db["ranking"]["Geral"] = db["ranking"].get("Geral", 0) + 10
                    print(f"✨ GREEN validado para {arquivo}!")
                elif tipo == "SUGESTAO":
                    print(f"📩 Sugestão/Bingo detectada em {arquivo}.")
                
                mudanca = True
            
            # Espera obrigatória entre imagens para não ser banido pelo Rate Limit
            print("⏳ Aguardando 20 segundos para a próxima imagem...")
            time.sleep(20)

    # Salva se houve alguma alteração
    if mudanca:
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=4, ensure_ascii=False)
        print("✅ ranking_db.json atualizado com sucesso!")
    else:
        print("ℹ️ Nenhuma imagem nova processada com sucesso.")

if __name__ == "__main__":
    main()
                  
