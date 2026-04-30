import os
import json
import google.generativeai as genai
from PIL import Image

# Configuração da API
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Ajuste: Adicionamos a configuração de geração para garantir o formato JSON
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    generation_config={"response_mime_type": "application/json"}
)

def extrair_dados_do_print(caminho_imagem):
    """Usa o Gemini para ler o print e separar mercados de gols"""
    img = Image.open(caminho_imagem)
    
    prompt = """
    Analise este print de apostas da Betano. Extraia cada aposta individualmente.
    
    REGRAS IMPORTANTES:
    1. Identifique o mercado EXATO: Se for 'Mais de 1.5', escreva '+1.5'. Se for 'Mais de 2.5', escreva '+2.5'.
    2. Identifique o time e o status (GREEN para ✅, RED para ❌).
    3. Retorne um JSON neste formato:
    [{"time": "Nome", "mercado": "+1.5", "status": "GREEN"}]
    """
    
    response = model.generate_content([prompt, img])
    # Com a configuração acima, o response.text já deve vir como JSON puro
    return json.loads(response.text)

def processar_conferencia():
    arquivo_json = 'bilhetes_salvos.json'
    pasta_prints = 'prints/'

    if not os.path.exists(arquivo_json):
        print(f"⚠️ Arquivo {arquivo_json} não encontrado.")
        return
    
    if not os.path.exists(pasta_prints):
        os.makedirs(pasta_prints)
        print(f"⚠️ Pasta {pasta_prints} criada. Suba os arquivos lá.")
        return

    with open(arquivo_json, 'r', encoding='utf-8') as f:
        historico = json.load(f)

    for arquivo in os.listdir(pasta_prints):
        if arquivo.lower().endswith(('.png', '.jpg', '.jpeg')):
            if arquivo.startswith('.'): continue # Ignora arquivos ocultos
            print(f"🧐 Lendo print: {arquivo}...")
            try:
                resultados_ia = extrair_dados_do_print(os.path.join(pasta_prints, arquivo))
                
                for res in resultados_ia:
                    for aposta in historico:
                        # Busca o time no JSON
                        nome_ia = res['time'].lower()
                        time_casa = aposta['time_casa'].lower()
                        time_fora = aposta['time_fora'].lower()
                        
                        time_bate = nome_ia in time_casa or nome_ia in time_fora
                        
                        if time_bate and aposta['status'] == "Pendente":
                            aposta['status'] = res['status']
                            print(f"✅ Atualizado: {aposta['time_casa']} -> {res['status']}")
            except Exception as e:
                print(f"❌ Erro ao processar {arquivo}: {e}")

    with open(arquivo_json, 'w', encoding='utf-8') as f:
        json.dump(historico, f, indent=4, ensure_ascii=False)
    print("🏁 Conferência finalizada!")

if __name__ == "__main__":
    processar_conferencia()
    
