import os
import json
import time
import google.generativeai as genai

# --- CONFIGURAÇÃO ---
PASTA_PRINTS = "prints/"
DB_PATH = "ranking_db.json"
API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=API_KEY)

def carregar_db():
    if os.path.exists(DB_PATH):
        with open(DB_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"processados": [], "pontuacao": {}}

def salvar_db(db):
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

def analisar_com_gemini(caminho_img):
    """Envia a imagem para o Gemini classificar e extrair dados."""
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    try:
        # Upload do arquivo para a API
        img_upload = genai.upload_file(path=caminho_img)
        
        prompt = """
        Analise esta imagem de aposta:
        1. Se for um print do Telegram com 'BINGO' ou 'Sugestão', classifique como 'SUGESTAO'.
        2. Se for um print da Betano com selo 'GANHOU' ou 'PRÊMIOS', classifique como 'GREEN'.
        3. Extraia: Nome dos Times, Valor da Odd e Valor do Prêmio (se houver).
        Retorne APENAS um JSON puro no formato:
        {"tipo": "SUGESTAO" ou "GREEN", "times": "time1 x time2", "odd": 0.00, "premio": 0.00}
        """
        
        response = model.generate_content([prompt, img_upload])
        # Limpa a resposta para garantir que seja um JSON válido
        json_txt = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(json_txt)
    except Exception as e:
        print(f"❌ Erro ao analisar {caminho_img}: {e}")
        return None

def main():
    db = carregar_db()
    if not os.path.exists(PASTA_PRINTS):
        os.makedirs(PASTA_PRINTS)

    arquivos = [f for f in os.listdir(PASTA_PRINTS) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    mudanca = False

    for arquivo in arquivos:
        if arquivo not in db["processados"]:
            print(f"🔍 Analisando novo print: {arquivo}")
            caminho = os.path.join(PASTA_PRINTS, arquivo)
            
            resultado = analisar_com_gemini(caminho)
            
            if resultado:
                db["processados"].append(arquivo)
                
                # Lógica simples de Ranking: Ganhou na Betano = 10 pontos
                if resultado.get("tipo") == "GREEN":
                    # Aqui você pode separar por usuário se o nome do arquivo tiver o nome dele
                    usuario = "Geral" 
                    db["pontuacao"][usuario] = db["pontuacao"].get(usuario, 0) + 10
                
                print(f"✅ Processado: {resultado['tipo']} | {resultado['times']}")
                mudanca = True
                time.sleep(5) # Evita limite de taxa da API

    if mudanca:
        salvar_db(db)
        print("💾 Banco de dados de Ranking atualizado!")

if __name__ == "__main__":
    main()
        
