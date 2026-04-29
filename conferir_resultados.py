import os
import json
import google.generativeai as genai
from PIL import Image

# Configuração da API (A chave que você salvou no GitHub)
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

def extrair_dados_do_print(caminho_imagem):
    """Usa o Gemini para ler o print e devolver um JSON estruturado"""
    img = Image.open(caminho_imagem)
    
    prompt = """
    Analise este print de apostas. Para cada jogo listado, extraia:
    1. O nome do time (ou um dos times da partida).
    2. O mercado apostado.
    3. O resultado: se houver um ícone de check/visto verde ou círculo verde, use 'GREEN'. 
       Se houver um X vermelho ou círculo vermelho, use 'RED'.
    
    Retorne APENAS um JSON puro no formato:
    [{"time": "Nome", "mercado": "Tipo", "status": "GREEN"}]
    """
    
    response = model.generate_content([prompt, img])
    # Limpa possíveis marcações de markdown do Gemini
    texto_limpo = response.text.replace('```json', '').replace('```', '').strip()
    return json.loads(texto_limpo)

def processar_conferencia():
    arquivo_json = 'bilhetes_salvos.json'
    pasta_prints = 'prints/'

    if not os.path.exists(arquivo_json) or not os.path.exists(pasta_prints):
        print("⚠️ Arquivos ou pasta 'prints/' não encontrados.")
        return

    with open(arquivo_json, 'r', encoding='utf-8') as f:
        historico = json.load(f)

    for arquivo in os.listdir(pasta_prints):
        if arquivo.lower().endswith(('.png', '.jpg', '.jpeg')):
            print(f"🧐 Lendo print: {arquivo}...")
            try:
                resultados_ia = extrair_dados_do_print(os.path.join(pasta_prints, arquivo))
                
                for res in resultados_ia:
                    # Tenta encontrar a aposta correspondente no seu JSON
                    for aposta in historico:
                        # Verificação flexível de nome e mercado
                        time_bate = res['time'].lower() in aposta['time_casa'].lower() or res['time'].lower() in aposta['time_fora'].lower()
                        # Simplificamos a comparação do mercado para evitar erros de acentuação/espaço
                        if time_bate and aposta['status'] == "Pendente":
                            aposta['status'] = res['status']
                            print(f"✅ Atualizado: {aposta['time_casa']} -> {res['status']}")
            except Exception as e:
                print(f"❌ Erro ao processar {arquivo}: {e}")

    # Salva o progresso
    with open(arquivo_json, 'w', encoding='utf-8') as f:
        json.dump(historico, f, indent=4, ensure_ascii=False)
    print("🏁 Conferência finalizada!")

if __name__ == "__main__":
    processar_conferencia()
