import os
import json
import time
from google import genai
from google.genai import types

# --- CONFIGURAÇÃO ---
PASTA_PRINTS = "prints/"
DB_PATH = "ranking_db.json"
API_KEY = os.getenv("GEMINI_API_KEY")

# Nova forma de configurar o cliente
client = genai.Client(api_key=API_KEY)

def carregar_db():
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"processados": [], "pontuacao": {}}
    return {"processados": [], "pontuacao": {}}

def salvar_db(db):
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

def analisar_com_gemini(caminho_img):
    try:
        # Carregando a imagem
        with open(caminho_img, "rb") as f:
            image_bytes = f.read()
        
        prompt = """
        Você é um auditor de apostas esportivas. Analise a imagem:
        1. Se for um print do Telegram com cabeçalho 'BINGO' ou 'Sugestão', tipo = 'SUGESTAO'.
        2. Se for um print da Betano com selo verde 'GANHOU' ou 'PRÊMIOS', tipo = 'GREEN'.
        Extraia os times envolvidos e o valor da Odd final.
        Retorne APENAS um JSON puro (sem markdown):
        {"tipo": "SUGESTAO" ou "GREEN", "times": "Time A x Time B", "odd": 0.00}
        """
        
        # Chamada usando a nova SDK
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[prompt, types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")]
        )
        
        json_txt = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(json_txt)
    except Exception as e:
        print(f"⚠️ Erro no Gemini para {caminho_img}: {e}")
        return None

def main():
    db = carregar_db()
    if not os.path.exists(PASTA_PRINTS):
        os.makedirs(PASTA_PRINTS)
        return

    arquivos = [f for f in os.listdir(PASTA_PRINTS) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    mudanca = False

    for arquivo in arquivos:
        if arquivo not in db["processados"]:
            print(f"🚀 Analisando: {arquivo}")
            caminho = os.path.join(PASTA_PRINTS, arquivo)
            
            resultado = analisar_com_gemini(caminho)
            
            if resultado:
                db["processados"].append(arquivo)
                if resultado.get("tipo") == "GREEN":
                    usuario = "Geral"
                    db["pontuacao"][usuario] = db["pontuacao"].get(usuario, 0) + 10
                    print(f"✨ GREEN Detectado! +10 pontos.")
                
                mudanca = True
                time.sleep(3) # Respeita o limite da API

    if mudanca:
        salvar_db(db)
        print("✅ Ranking atualizado!")

if __name__ == "__main__":
    main()
    
