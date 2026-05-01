import os
import json
import re
import pytesseract
from PIL import Image
import time

def extrair_texto(caminho_img):
    try:
        # 'lang=por' para garantir leitura de acentos e termos em português
        texto = pytesseract.image_to_string(Image.open(caminho_img), lang='por')
        return texto.upper()
    except Exception as e:
        print(f"❌ Erro OCR: {e}")
        return None

def limpar_nome_jogo(texto):
    """Extrai nomes de times ignorando números e símbolos no início"""
    # Procura o padrão Time A X Time B
    match = re.search(r'([A-ZÀ-Ú ]+)\s*[X]\s*([A-ZÀ-Ú ]+)', texto)
    if match:
        time1 = match.group(1).strip()
        time2 = match.group(2).strip()
        
        # Remove números soltos ou caracteres especiais que o OCR confunde no início
        time1 = re.sub(r'^[0-9€&%46 ]+', '', time1).strip()
        
        # Se após limpar, o nome ainda for muito curto (ex: só "X OLIMPIA"), 
        # o cruzamento pode falhar, mas já ajuda muito.
        return f"{time1} X {time2}"
    return None


def conferir_resultado(mercado, g_casa, g_fora):
    """Aplica a regra matemática baseada no mercado e placar"""
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
    log_path = "ocr_debug.log"
    pasta = "prints/"
    
    if not os.path.exists(pasta):
        print(f"Pasta {pasta} não encontrada.")
        return

    # --- CARREGAMENTO SEGURO DO BANCO DE DADOS ---
    if os.path.exists(db_path):
        with open(db_path, 'r', encoding='utf-8') as f:
            try: 
                db = json.load(f)
            except: 
                db = {}
    else:
        db = {}

    # Inicializa chaves caso não existam (Evita KeyError)
    if "stats" not in db: db["stats"] = {}
    if "pendentes" not in db: db["pendentes"] = {}
    if "processados" not in db: db["processados"] = []

    # Lista arquivos que não foram concluídos ainda
    arquivos = [f for f in os.listdir(pasta) if f.lower().endswith(('.png', '.jpg', '.jpeg')) and "_CONCLUIDO" not in f]
    
    mudanca = False

    with open(log_path, "a", encoding="utf-8") as log_file:
        for arquivo in arquivos:
            caminho_img = os.path.join(pasta, arquivo)
            print(f"🧐 Analisando: {arquivo}")
            texto = extrair_texto(caminho_img)
            
            if not texto: continue
            
            log_file.write(f"\n===== ARQUIVO: {arquivo} =====\n{texto}\n")

            # Divide o texto por quebras de linha duplas para tentar isolar blocos de jogos
            blocos = texto.split('\n\n')
            
            for bloco in blocos:
                jogo = limpar_nome_jogo(bloco)
                if not jogo: continue

                # --- LÓGICA TELEGRAM (Pega Mercado e Porcentagem) ---
                perc_match = re.search(r"(\d{2,3}%)", bloco)
                if perc_match:
                    mercado = ""
                    if "1.5" in bloco: mercado = "GOLS +1.5"
                    elif "2.5" in bloco: mercado = "GOLS +2.5"
                    elif "AMBAS" in bloco or "EQUIPES" in bloco: mercado = "AMBAS MARCAM"
                    elif "1X" in bloco: mercado = "1X"
                    elif "2X" in bloco or "X2" in bloco: mercado = "2X"
                    elif "CASA" in bloco: mercado = "VITÓRIA CASA"

                    if mercado:
                        db["pendentes"][jogo] = {"mercado": mercado, "perc": perc_match.group(1)}
                        print(f"   📝 Telegram: {jogo} -> {mercado} ({perc_match.group(1)}) registrado.")
                        mudanca = True

                # --- LÓGICA BETANO (Pega Resultado e Cruza) ---
                # Procura placares no formato 0-0, 1X1, 2-1
                placar = re.findall(r'(\d+)\s*[-X ]\s*(\d+)', bloco)
                if placar and jogo in db["pendentes"]:
                    info = db["pendentes"][jogo]
                    status = conferir_resultado(info["mercado"], int(placar[0][0]), int(placar[0][1]))
                    
                    if status in ["GREEN", "RED"]:
                        chave_rank = f"{info['mercado']} {info['perc']}".strip()
                        if chave_rank not in db["stats"]:
                            db["stats"][chave_rank] = {"green": 0, "red": 0}
                        
                        db["stats"][chave_rank][status.lower()] += 1
                        print(f"   ✅ Betano: {jogo} -> {status} (Cruzamento OK)")
                        
                        # Remove dos pendentes pois já foi processado
                        del db["pendentes"][jogo]
                        mudanca = True

            # --- FINALIZAÇÃO DO ARQUIVO ---
            nome_novo = arquivo.rsplit('.', 1)[0] + "_CONCLUIDO." + arquivo.rsplit('.', 1)[1]
            try:
                os.rename(caminho_img, os.path.join(pasta, nome_novo))
            except Exception as e:
                print(f"   ⚠️ Erro ao renomear {arquivo}: {e}")

            time.sleep(0.5) # Evita sobrecarga de I/O

    if mudanca:
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=4, ensure_ascii=False)
        print("\n✅ Banco de dados e imagens atualizados!")

    # --- RELATÓRIO DE TESTE NO TERMINAL ---
    if db["stats"]:
        print("\n📊 --- RANKING DE ASSERTIVIDADE ---")
        print(f"{'MERCADO':<25} | {'G':<4} | {'R':<4} | {'% ACERTO'}")
        print("-" * 55)
        for m, v in sorted(db["stats"].items()):
            total = v['green'] + v['red']
            acc = (v['green'] / total * 100) if total > 0 else 0
            print(f"{m:<25} | {v['green']:<4} | {v['red']:<4} | {acc:.1f}%")

if __name__ == "__main__":
    main()
                        
