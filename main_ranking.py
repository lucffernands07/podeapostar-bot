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
    match = re.search(r'([A-Z0-9À-Ú \(\)]+)\s*[X]\s*([A-Z0-9À-Ú \(\)]+)', texto)
    if match:
        t1 = re.sub(r'^[^A-ZÀ-Ú0-9]+', '', match.group(1)).strip()
        t2 = re.sub(r'[^A-ZÀ-Ú0-9]+$', '', match.group(2)).strip()
        t1 = re.sub(r'\s*\(.*\)', '', t1).strip()
        t2 = re.sub(r'\s*\(.*\)', '', t2).strip()
        return f"{t1} X {t2}"
    return None

def conferir_resultado(mercado, g_casa, g_fora):
    total = g_casa + g_fora
    if "1.5" in mercado: return "GREEN" if total >= 2 else "RED"
    if "2.5" in mercado: return "GREEN" if total >= 3 else "RED"
    if "AMBAS" in mercado: return "GREEN" if (g_casa > 0 and g_fora > 0) else "RED"
    if "1X" in mercado: return "GREEN" if g_casa >= g_fora else "RED"
    if "2X" in mercado or "X2" in mercado: return "GREEN" if g_fora >= g_casa else "RED"
    return "OUTRO"

def main():
    db_path = "ranking_db.json"
    pasta = "prints/"
    
    db = {"stats": {}, "pendentes": {}, "processados": []}
    if os.path.exists(db_path):
        try:
            with open(db_path, 'r', encoding='utf-8') as f:
                carregado = json.load(f)
                for k in ["stats", "pendentes", "processados"]:
                    if k in carregado:
                        if isinstance(db[k], dict): db[k].update(carregado[k])
                        else: db[k] = list(set(db[k] + carregado[k]))
        except: pass

    if not os.path.exists(pasta): return

    arquivos = [f for f in os.listdir(pasta) if f.lower().endswith(('.png', '.jpg', '.jpeg')) and "_CONCLUIDO" not in f]
    
    mercados_na_rodada = set() # Usamos um SET para contar mercados ÚNICOS
    resultados_na_rodada = []
    mudanca = False

    for arquivo in arquivos:
        caminho = os.path.join(pasta, arquivo)
        texto = extrair_texto(caminho)
        if not texto: continue

        blocos = texto.split('\n')
        for i, linha in enumerate(blocos):
            jogo = limpar_nome_jogo(linha)
            if not jogo: continue

            contexto = " ".join(blocos[max(0, i-1):i+5])

            # TELEGRAM (Captura mercado e %)
            perc_match = re.search(r"(\d{2,3}%)", contexto)
            if perc_match:
                mercado = ""
                if "1.5" in contexto: mercado = "GOLS +1.5"
                elif "1X" in contexto: mercado = "1X"
                elif "2X" in contexto or "X2" in contexto: mercado = "2X"
                elif "AMBAS" in contexto: mercado = "AMBAS MARCAM"
                
                if mercado:
                    db["pendentes"][jogo] = {"mercado": mercado, "perc": perc_match.group(1)}
                    mudanca = True

            # BETANO (Confere resultado)
            placar = re.findall(r'(\d+)\s*[-X ]\s*(\d+)', contexto)
            if placar and jogo in db["pendentes"]:
                info = db["pendentes"][jogo]
                res = conferir_resultado(info["mercado"], int(placar[0][0]), int(placar[0][1]))
                
                if res in ["GREEN", "RED"]:
                    chave = f"{info['mercado']} {info['perc']}"
                    if chave not in db["stats"]: db["stats"][chave] = {"green": 0, "red": 0}
                    db["stats"][chave][res.lower()] += 1
                    
                    # Rastreia mercados e resultados para o Bingo
                    mercados_na_rodada.add(info["mercado"]) 
                    resultados_na_rodada.append(res)
                    
                    del db["pendentes"][jogo]
                    mudanca = True

        os.rename(caminho, os.path.join(pasta, arquivo.split('.')[0] + "_CONCLUIDO." + arquivo.split('.')[1]))

    # --- LÓGICA DE BINGO POR MERCADO ---
    if resultados_na_rodada:
        num_mercados = len(mercados_na_rodada)
        if num_mercados >= 1: # Registra o bingo com base na variedade de mercados
            status_bingo = "red" if "RED" in resultados_na_rodada else "green"
            chave_bingo = f"BINGO {num_mercados}"
            
            if chave_bingo not in db["stats"]: db["stats"][chave_bingo] = {"green": 0, "red": 0}
            db["stats"][chave_bingo][status_bingo] += 1
            print(f"🎰 {chave_bingo} ({num_mercados} mercados) finalizado como {status_bingo.upper()}")

    if mudanca:
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=4, ensure_ascii=False)

    print("\n📊 --- RANKING GERAL ACUMULADO ---")
    for m, v in sorted(db["stats"].items()):
        total = v['green'] + v['red']
        if total > 0:
            print(f"{m:<25} | G: {v['green']} | R: {v['red']} | {(v['green']/total*100):.1f}%")

if __name__ == "__main__":
    main()
                
