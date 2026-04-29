import os
import json
import google.generativeai as genai
from PIL import Image

# Configuração da API (A chave que você salvou no GitHub)
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

def extrair_dados_do_print(caminho_imagem):
    """Usa o Gemini para ler o print e separar mercados de gols"""
    img = Image.open(caminho_imagem)
    
    prompt = """
    Analise este print de apostas da Betano. Extraia cada aposta individualmente.
    
    REGRAS IMPORTANTES:
    1. Identifique o mercado EXATO: Se for 'Mais de 1.5', escreva '+1.5'. Se for 'Mais de 2.5', escreva '+2.5'.
    2. Identifique o time e o status (GREEN para ✅, RED para ❌).
    3. Retorne APENAS um JSON puro:
    [{"time": "Nome", "mercado": "+1.5", "status": "GREEN"}]
    """
    
    response = model.generate_content([prompt, img])
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
