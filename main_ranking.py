import os
import json
import easyocr
import cv2

# Configuração de caminhos
PASTA_PRINTS = "prints/"
DB_PATH = "ranking_db.json"

def carregar_db():
    if os.path.exists(DB_PATH):
        with open(DB_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"processados": [], "ranking": {}}

def salvar_db(db):
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

def processar_imagem(caminho_img):
    reader = easyocr.Reader(['pt', 'en'])
    resultado = reader.readtext(caminho_img, detail=0)
    texto_completo = " ".join(resultado).upper()
    
    # Identificação por Palavras-Chave
    tipo = "DESCONHECIDO"
    dados = {}

    if "BINGO" in texto_completo or "ODD TOTAL" in texto_completo:
        tipo = "BILHETE_SUGESTAO"
        print(f"✅ Identificado: Sugestão do Bot em {caminho_img}")
        # Lógica para extrair times/odds se necessário
        
    elif "GANHOU" in texto_completo or "PRÊMIOS" in texto_completo or "APOSTA" in texto_completo:
        tipo = "APOSTA_REALIZADA"
        print(f"✅ Identificado: Print da Betano em {caminho_img}")
        # Exemplo de extração de valor (busca por R$)
        for t in resultado:
            if "R$" in t:
                dados['valor'] = t
    
    return tipo, dados

def main():
    db = carregar_db()
    arquivos = [f for f in os.listdir(PASTA_PRINTS) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    mudanca = False
    for arquivo in arquivos:
        if arquivo not in db["processados"]:
            caminho = os.path.join(PASTA_PRINTS, arquivo)
            tipo, dados = processar_imagem(caminho)
            
            if tipo != "DESCONHECIDO":
                db["processados"].append(arquivo)
                # Aqui você pode adicionar lógica para somar pontos no ranking
                # Exemplo: db["ranking"]["usuario_teste"] += 1
                mudanca = True
                print(f"--- Arquivo {arquivo} processado como {tipo} ---")

    if mudanca:
        salvar_db(db)

if __name__ == "__main__":
    main()
