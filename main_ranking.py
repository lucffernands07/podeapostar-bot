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
    """Limpeza agressiva para garantir match entre plataformas"""
    match = re.search(r'([A-Z0-9À-Ú \(\)]+)\s*[X]\s*([A-Z0-9À-Ú \(\)]+)', texto)
    if match:
        t1, t2 = match.group(1).strip(), match.group(2).strip()
        # Remove termos comuns que variam entre as casas
        subs = [r'\(.*\)', r' FC', r' SFC', r' RIYADH', r' SAUDI', r'^[^A-Z0-9]+', r'[^A-Z0-9]+$']
        for s in subs:
            t1 = re.sub(s, '', t1).strip()
            t2 = re.sub(s, '', t2).strip()
        return f"{t1} X {t2}" if (len(t1) > 2 and len(t2) > 2) else None
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
                for k in db.keys():
                    if k in carregado:
                        if isinstance(db[k], dict): db[k].update(carregado[k])
                        else: db[k] = list(set(db[k] + carregado[k]))
        except: pass

    if not os.path.exists(pasta): return
    arquivos = [f for f in os.listdir(pasta) if f.lower().endswith(('.png', '.jpg', '.jpeg')) and "_CONCLUIDO" not in f]
    
    mudanca = False
    resultados_rodada = []
    mercados_contados = 0

    for arquivo in arquivos:
        texto = extrair_texto(os.path.join(pasta, arquivo))
        if not texto: continue
        blocos = texto.split('\n')

        for i, linha in enumerate(blocos):
            jogo = limpar_nome_jogo(linha)
            if not jogo: continue
            contexto = " ".join(blocos[max(0, i-1):i+5])
            
            # --- TELEGRAM ---
            perc = re.search(r"(\d{2,3}%)", contexto)
            if perc:
                mercado = ""
                if "1.5" in contexto: mercado = "GOLS +1.5"
                elif "2.5" in contexto: mercado = "GOLS +2.5"
                elif "AMBAS" in contexto: mercado = "AMBAS MARCAM"
                elif "1X" in contexto: mercado = "1X"
                elif "2X" in contexto or "X2" in contexto: mercado = "2X"
                
                if mercado:
                    # Chave composta para NÃO sobrescrever mercados no mesmo jogo
                    chave_m = f"{jogo} | {mercado}"
                    db["pendentes"][chave_m] = {"mercado": mercado, "perc": perc.group(1), "jogo": jogo}
                    mudanca = True

            # --- BETANO ---
            placar = re.findall(r'(\d+)\s*[-X ]\s*(\d+)', contexto)
            if placar:
                # Procura todos os pendentes desse jogo
                para_remover = []
                for chave_m, info in db["pendentes"].items():
                    if info["jogo"] in jogo or jogo in info["jogo"]:
                        res = conferir_resultado(info["mercado"], int(placar[0][0]), int(placar[0][1]))
                        if res in ["GREEN", "RED"]:
                            stat_key = f"{info['mercado']} {info['perc']}"
                            if stat_key not in db["stats"]: db["stats"][stat_key] = {"green": 0, "red": 0}
                            db["stats"][stat_key][res.lower()] += 1
                            resultados_rodada.append(res)
                            mercados_contados += 1
                            para_remover.append(chave_m)
                            mudanca = True
                for rm in para_remover: del db["pendentes"][rm]

        os.rename(os.path.join(pasta, arquivo), os.path.join(pasta, f"{arquivo.split('.')[0]}_CONCLUIDO.{arquivo.split('.')[1]}"))

    # --- BINGO ESCALA 3, 5, 7 ---
    if resultados_rodada:
        if mercados_contados <= 3: cat = 3
        elif mercados_contados <= 5: cat = 5
        else: cat = 7
        status = "red" if "RED" in resultados_rodada else "green"
        chave_b = f"BINGO {cat}"
        if chave_b not in db["stats"]: db["stats"][chave_b] = {"green": 0, "red": 0}
        db["stats"][chave_b][status] += 1

    if mudanca:
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=4, ensure_ascii=False)

    print("\n📊 --- RANKING GERAL ATUALIZADO ---")
    for m, v in sorted(db["stats"].items()):
        total = v['green'] + v['red']
        print(f"{m:<25} | G: {v['green']} | R: {v['red']} | {(v['green']/total*100):.1f}%")

if __name__ == "__main__":
    main()
    
