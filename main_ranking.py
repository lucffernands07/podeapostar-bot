import os
import json
import re
import pytesseract
from PIL import Image

def extrair_texto(caminho_img):
    try:
        texto = pytesseract.image_to_string(Image.open(caminho_img), lang='por')
        return texto.upper()
    except Exception as e:
        print(f"❌ Erro OCR: {e}")
        return None

def limpar_nome_jogo(texto):
    """Extrai nomes de times para cruzamento (ex: CARACAS X RACING)"""
    match = re.search(r'([A-Z0-9 ]+)\s*[X]\s*([A-Z0-9 ]+)', texto)
    if match:
        return f"{match.group(1).strip()} X {match.group(2).strip()}"
    return None

def conferir_resultado(mercado, g_casa, g_fora):
    total = g_casa + g_fora
    if "1.5" in mercado: return "GREEN" if total >= 2 else "RED"
    if "2.5" in mercado: return "GREEN" if total >= 3 else "RED"
    if "AMBAS" in mercado: return "GREEN" if (g_casa > 0 and g_fora > 0) else "RED"
    if "1X" in mercado: return "GREEN" if g_casa >= g_fora else "RED"
    if "2X" in mercado: return "GREEN" if g_fora >= g_casa else "RED"
    if "CASA" in mercado: return "GREEN" if g_casa > g_fora else "RED"
    return "OUTRO"

def main():
    db_path = "ranking_db.json"
    pasta = "prints/"
    
    if os.path.exists(db_path):
        with open(db_path, 'r', encoding='utf-8') as f:
            db = json.load(f)
    else:
        db = {"stats": {}, "pendentes": {}} # pendentes guarda info do Telegram

    arquivos = [f for f in os.listdir(pasta) if f.lower().endswith(('.png', '.jpg', '.jpeg')) and "_CONCLUIDO" not in f]
    
    for arquivo in arquivos:
        caminho = os.path.join(pasta, arquivo)
        texto = extrair_texto(caminho)
        if not texto: continue

        # --- PASSO 1: IDENTIFICAR JOGOS NO TEXTO ---
        # Divide por blocos de linhas para não misturar times de jogos diferentes
        blocos = texto.split('\n\n')
        
        for bloco in blocos:
            jogo = limpar_nome_jogo(bloco)
            if not jogo: continue

            # Se for print do TELEGRAM (tem porcentagem)
            perc_match = re.search(r"(\d{2,3}%)", bloco)
            if perc_match:
                # Extrai o mercado
                mercado = ""
                if "1.5" in bloco: mercado = "GOLS +1.5"
                elif "2.5" in bloco: mercado = "GOLS +2.5"
                elif "AMBAS" in bloco: mercado = "AMBAS MARCAM"
                elif "1X" in bloco: mercado = "1X"
                elif "2X" in bloco: mercado = "2X"
                
                if mercado:
                    db["pendentes"][jogo] = {"mercado": mercado, "perc": perc_match.group(1)}
                    print(f"📝 Pendente: {jogo} ({mercado} {perc_match.group(1)})")

            # Se for print da BETANO (tem Resultado/Placar)
            placar = re.findall(r'(\d+)\s*[-X ]\s*(\d+)', bloco)
            if placar and jogo in db["pendentes"]:
                info = db["pendentes"][jogo]
                res = conferir_resultado(info["mercado"], int(placar[0][0]), int(placar[0][1]))
                
                if res in ["GREEN", "RED"]:
                    chave = f"{info['mercado']} {info['perc']}".strip()
                    if chave not in db["stats"]: db["stats"][chave] = {"green": 0, "red": 0}
                    db["stats"][chave][res.lower()] += 1
                    
                    del db["pendentes"][jogo] # Remove das pendências
                    print(f"✅ Resultado: {jogo} -> {res}")

        # Marcar imagem como concluída
        nome_novo = arquivo.rsplit('.', 1)[0] + "_CONCLUIDO." + arquivo.rsplit('.', 1)[1]
        os.rename(caminho, os.path.join(pasta, nome_novo))

    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

    # RESUMO PARA TESTE
    print("\n📊 --- RANKING ACUMULADO ---")
    for m, v in db["stats"].items():
        total = v['green'] + v['red']
        acc = (v['green']/total*100) if total > 0 else 0
        print(f"{m:<25} | {v['green']}G - {v['red']}R | {acc:.1f}%")

if __name__ == "__main__":
    main()
        
