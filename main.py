import os
import requests
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def enviar_telegram(mensagem):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": mensagem, "parse_mode": "Markdown"})

def minerar_flashscore():
    # Usamos o subdomínio 'd' (de data) que é mais estável que os números (6, 7, 8)
    # E mudamos o final para 'f_1_0_3_pt-br_1' (o 3 é o código para buscar o feed completo de hoje)
    url = "https://d.flashscore.com.br/x/feed/f_1_0_3_pt-br_1"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "x-fsign": "SW9D1eZo",
        "Referer": "https://www.flashscore.com.br/",
        "X-Requested-With": "XMLHttpRequest"
    }

    print("📡 Minerando Feed Estável do Flashscore...")
    
    try:
        # Tentativa 1: Subdomínio 'd'
        res = requests.get(url, headers=headers, timeout=20)
        
        # Se o 'd' falhar (DNS), tentamos o próprio domínio principal como fallback
        if res.status_code != 200:
            print("⚠️ Subdomínio 'd' falhou, tentando rota alternativa...")
            url_alt = "https://www.flashscore.com.br/x/feed/f_1_0_3_pt-br_1"
            res = requests.get(url_alt, headers=headers, timeout=20)

        if res.status_code == 200:
            return res.text
        else:
            print(f"❌ Falha no Flashscore: Status {res.status_code}")
            return None
    except Exception as e:
        print(f"⚠️ Erro de DNS ou Conexão: {e}")
        # Se der erro de DNS de novo, tentamos a URL sem subdomínio
        try:
            url_final = "https://www.flashscore.com.br/x/feed/f_1_0_3_pt-br_1"
            res = requests.get(url_final, headers=headers, timeout=20)
            return res.text if res.status_code == 200 else None
        except:
            return None

def processar_texto_flashscore(texto):
    if not texto: return []
    
    jogos = []
    # O Flashscore separa os dados por '~' e os blocos por '¬'
    blocos = texto.split('¬')
    
    time_casa = ""
    time_fora = ""
    hora_jogo = ""
    
    for bloco in blocos:
        # AE = Nome do Time da Casa, AF = Nome do Time de Fora, AD = Hora
        if bloco.startswith("AE÷"): time_casa = bloco.replace("AE÷", "")
        if bloco.startswith("AF÷"): time_fora = bloco.replace("AF÷", "")
        if bloco.startswith("AD÷"): 
            ts = bloco.replace("AD÷", "")
            hora_jogo = datetime.fromtimestamp(int(ts)).strftime("%H:%M")
        
        # Quando chega no final do bloco do jogo (geralmente começa com Z~ ou algo assim)
        if time_casa and time_fora and hora_jogo:
            jogos.append({
                "home": time_casa,
                "away": time_fora,
                "hora": hora_jogo
            })
            # Limpa para o próximo jogo
            time_casa, time_fora, hora_jogo = "", "", ""
            
    return jogos

def main():
    conteudo = minerar_flashscore()
    jogos = processar_texto_flashscore(conteudo)
    
    if jogos:
        print(f"✅ Sucesso! {len(jogos)} jogos minerados do Flashscore.")
        times_foco = ["Sporting", "Arsenal", "Real Madrid", "Bayern", "Corinthians"]
        achados = []

        for j in jogos:
            if any(t.lower() in j['home'].lower() or t.lower() in j['away'].lower() for t in times_foco):
                achados.append(f"🏟️ *{j['home']} x {j['away']}*\n🕒 {j['hora']}")

        if achados:
            msg = "🎯 *BILHETE FLASH ENCONTRADO!*\n\n" + "\n\n".join(achados)
            enviar_telegram(msg)
            print("✅ Mensagem enviada ao Telegram!")
    else:
        print("❌ A mineração não trouxe dados válidos.")

if __name__ == "__main__":
    main()
