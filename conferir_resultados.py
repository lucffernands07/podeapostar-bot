import os
import json
import google.generativeai as genai
from PIL import Image
import re

# 1. Configuração da API Gemini
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Configura o modelo para sempre responder em JSON puro
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    generation_config={"response_mime_type": "application/json"}
)

def limpar_nome(nome):
    """
    Remove parênteses, siglas de países, espaços extras e converte para minúsculo.
    Exemplo: 'Caracas (Ven)' vira 'caracas'
    """
    if not nome: return ""
    # Remove tudo que estiver dentro de parênteses
    nome = re.sub(r'\(.*?\)', '', nome)
    # Remove espaços extras e converte para minúsculo
    return nome.strip().lower()

def extrair_dados_do_print(caminho_imagem):
    """Usa a visão computacional do Gemini para ler o print da Betano"""
    try:
        img = Image.open(caminho_imagem)
        
        prompt = """
        Analise este print de apostas da Betano. Extraia cada aposta individualmente.
        REGRAS:
        1. Identifique o time e o status (GREEN para ✅/venceu, RED para ❌/perdeu).
        2. Retorne um JSON neste formato:
        [{"time": "Nome do Time", "status": "GREEN"}]
        """
        
        response = model.generate_content([prompt, img])
        return json.loads(response.text)
    except Exception as e:
        print(f"❌ Erro ao chamar IA para {caminho_imagem}: {e}")
        return []

def processar_conferencia():
    arquivo_json = 'bilhetes_salvos.json'
    pasta_prints = 'prints/'

    # Verificações de segurança
    if not os.path.exists(arquivo_json):
        print(f"⚠️ Erro: Arquivo {arquivo_json} não encontrado na raiz.")
        return
    
    if not os.path.exists(pasta_prints):
        os.makedirs(pasta_prints)
        print(f"⚠️ Pasta {pasta_prints} criada agora. Suba os prints nela.")
        return

    # Carrega o histórico de apostas
    with open(arquivo_json, 'r', encoding='utf-8') as f:
        historico = json.load(f)

    houve_alteracao = False

    # Percorre os arquivos na pasta de prints
    arquivos_na_pasta = [f for f in os.listdir(pasta_prints) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not arquivos_na_pasta:
        print("ℹ️ Nenhum print encontrado na pasta 'prints/'.")
        return

    for arquivo in arquivos_na_pasta:
        print(f"🧐 Analisando imagem: {arquivo}...")
        resultados_ia = extrair_dados_do_print(os.path.join(pasta_prints, arquivo))
        
        for res in resultados_ia:
            nome_ia = limpar_nome(res['time'])
            status_ia = res['status'].upper()
            
            for aposta in historico:
                # Limpa nomes do JSON para comparar
                casa = limpar_nome(aposta['time_casa'])
                fora = limpar_nome(aposta['time_fora'])
                
                # Se o nome lido pela IA estiver contido em um dos nomes do JSON (ou vice-versa)
                match_time = (nome_ia in casa or casa in nome_ia or nome_ia in fora or fora in nome_ia)
                
                if match_time and aposta['status'] == "Pendente":
                    aposta['status'] = status_ia
                    houve_alteracao = True
                    print(f"✅ MATCH! {aposta['time_casa']} vs {aposta['time_fora']} -> {status_ia}")

    # Salva o arquivo apenas se algo mudou
    if houve_alteracao:
        with open(arquivo_json, 'w', encoding='utf-8') as f:
            json.dump(historico, f, indent=4, ensure_ascii=False)
        print("💾 O arquivo bilhetes_salvos.json foi atualizado com os novos resultados!")
    else:
        print("ℹ️ A conferência rodou, mas nenhum jogo 'Pendente' foi encontrado nos prints.")

if __name__ == "__main__":
    processar_conferencia()
    
