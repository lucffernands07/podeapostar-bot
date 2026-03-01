import os
import requests
import pandas as pd

# Puxa os segredos do GitHub Settingsui
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
# Link da sua Google Sheet (Publicada como CSV)
SHEET_URL = os.getenv('GOOGLE_SHEET_URL')

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={mensagem}&parse_mode=Markdown"
    requests.get(url)

def analisar_jogos():
    try:
        # Lê a planilha diretamente da web
        df = pd.read_csv(SHEET_URL)
        
        # Exemplo de lógica para "1 a 3 Gols" e "HT"
        for index, row in df.iterrows():
            time_casa = row['Time_Casa']
            time_fora = row['Time_Fora']
            media_gols = row['Media_Gols']
            freq_ht = row['Frequencia_HT'] # % de jogos com gol no 1º tempo
            
            # --- SEU RACIOCÍNIO ESTRATÉGICO ---
            if 1.2 <= media_gols <= 3.2 and freq_ht >= 0.70:
                msg = (f"🎯 *PALPITE CONFIRMADO*\n"
                       f"⚽ {time_casa} x {time_fora}\n"
                       f"🔥 Mercado: 1-3 Gols & Over 0.5 HT\n"
                       f"📊 Confiança: Alta")
                enviar_telegram(msg)
                
    except Exception as e:
        print(f"Erro ao processar: {e}")

if __name__ == "__main__":
    analisar_jogos()
  
