import os
import json
import re
import pytesseract
from PIL import Image
import requests

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

def enviar_telegram(mensagem, chat_id_destino):
    """Lógica de envio idêntica ao seu main.py"""
    token = os.getenv('TELEGRAM_TOKEN')
    if not token or not chat_id_destino:
        return
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(url, data={
            "chat_id": chat_id_destino, 
            "text": mensagem, 
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        })
    except Exception as e:
        print(f"❌ Erro Telegram: {e}")

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

    mudanca = False
    resultados_rodada = []
    mercados_contados = 0

    if os.path.exists(pasta):
        arquivos = [f for f in os.listdir(pasta) if f.lower().endswith(('.png', '.jpg', '.jpeg')) and "_CONCLUIDO" not in f]
        
        for arquivo in arquivos:
            caminho_img = os.path.join(pasta, arquivo)
            texto = extrair_texto(caminho_img)
            if not texto: continue
            blocos = texto.split('\n')

            for i, linha in enumerate(blocos):
                jogo = limpar_nome_jogo(linha)
                if not jogo: continue
                contexto = " ".join(blocos[max(0, i-1):i+5])
                
                perc = re.search(r"(\d{2,3}%)", contexto)
                if perc:
                    mercado = ""
                    if "1.5" in contexto: mercado = "GOLS +1.5"
                    elif "2.5" in contexto: mercado = "GOLS +2.5"
                    elif "AMBAS" in contexto: mercado = "AMBAS MARCAM"
                    elif "1X" in contexto: mercado = "1X"
                    elif "2X" in contexto or "X2" in contexto: mercado = "2X"
                    
                    if mercado:
                        chave_m = f"{jogo} | {mercado}"
                        db["pendentes"][chave_m] = {"mercado": mercado, "perc": perc.group(1), "jogo": jogo}
                        mudanca = True

                placar = re.findall(r'(\d+)\s*[-X ]\s*(\d+)', contexto)
                if placar:
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

            os.rename(caminho_img, os.path.join(pasta, f"{arquivo.split('.')[0]}_CONCLUIDO.{arquivo.split('.')[1]}"))

    if resultados_rodada:
        if mercados_contados <= 3: cat = 3
        elif mercados_contados <= 5: cat = 5
        else: cat = 7
        status = "red" if "RED" in resultados_rodada else "green"
        chave_b = f"BINGO {cat}"
        if chave_b not in db["stats"]: db["stats"][chave_b] = {"green": 0, "red": 0}
        db["stats"][chave_b][status] += 1
        mudanca = True

    if mudanca:
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=4, ensure_ascii=False)

    # --- MONTAGEM DO RANKING ORDENADO ---
    if db["stats"]:
        lista_mercados = []
        lista_bingos = []

        for nome, dados in db["stats"].items():
            total = dados['green'] + dados['red']
            taxa = (dados['green'] / total * 100) if total > 0 else 0
            
            item = {
                "nome": nome,
                "green": dados['green'],
                "red": dados['red'],
                "taxa": taxa,
                "emoji": "" if taxa >= 80 else "" if taxa >= 50 else ""
            }
            
            if "BINGO" in nome:
                lista_bingos.append(item)
            else:
                lista_mercados.append(item)

        # Ordenação: 1º Taxa de acerto (desc), 2º Quantidade de Greens (desc)
        lista_mercados.sort(key=lambda x: (x['taxa'], x['green']), reverse=True)
        lista_bingos.sort(key=lambda x: (x['taxa'], x['green']), reverse=True)

        resumo = "📊 *RANKING GERAL ATUALIZADO* 🏆\n\n"
        
        for i in lista_mercados:
            resumo += f"{i['emoji']} *{i['nome']}*\n✅ G: {i['green']} | ❌ R: {i['red']} | 📈 *{i['taxa']:.1f}%*\n\n"
        
        if lista_bingos:
            resumo += "--------------------------\n\n"
            for b in lista_bingos:
                resumo += f"{b['emoji']} *{b['nome']}*\n✅ G: {b['green']} | ❌ R: {b['red']} | 📈 *{b['taxa']:.1f}%*\n\n"

        print(resumo)
        meu_chat_id = os.getenv('CHAT_ID')
        enviar_telegram(resumo, meu_chat_id)

if __name__ == "__main__":
    main()
                
