import os
import requests
from datetime import datetime

# --- CONFIGURAÇÕES DE SEGURANÇA --- #
# O token deve ser configurado como variável de ambiente (Environment Variable)
BSD_TOKEN = os.getenv('BSD_TOKEN')
BASE_URL = "https://sports.bzzoiro.com/api"

def buscar_jogos_hoje():
    """
    Busca os eventos do dia atual e imprime no log.
    Utiliza o endpoint /api/events/ com filtro de data.
    """
    if not BSD_TOKEN:
        print("❌ ERRO: Variável de ambiente 'BSD_TOKEN' não encontrada.")
        return

    # Define a data de hoje no formato YYYY-MM-DD
    hoje = datetime.now().strftime('%Y-%m-%d')
    
    # Parâmetros da API:
    # tz: Define o fuso horário para garantir que a data 'hoje' seja a do Brasil
    # date_from e date_to: Filtram exatamente para o dia de hoje
    params = {
        "date_from": hoje,
        "date_to": hoje,
        "tz": "America/Sao_Paulo"
    }
    
    headers = {
        "Authorization": f"Token {BSD_TOKEN}"
    }

    print(f"🚀 Iniciando busca de jogos para: {hoje}...")

    try:
        response = requests.get(f"{BASE_URL}/events/", headers=headers, params=params)
        
        if response.status_code == 200:
            dados = response.json()
            jogos = dados.get("results", [])
            
            if not jogos:
                print(f"📭 Nenhum jogo encontrado para a data {hoje}.")
                return

            print(f"✅ Sucesso! {len(jogos)} jogos encontrados.\n")
            print(f"{'HORÁRIO':<10} | {'COMPETIÇÃO':<20} | {'PARTIDA':<40}")
            print("-" * 75)

            for evento in jogos:
                # Formata a hora (A API retorna ISO 8601)
                data_iso = evento.get("event_date", "")
                hora = data_iso.split("T")[1][:5] if "T" in data_iso else "--:--"
                
                liga = evento.get("league", {}).get("name", "N/A")
                home = evento.get("home_team", "Time Casa")
                away = evento.get("away_team", "Time Fora")
                
                # Log no console
                print(f"{hora:<10} | {liga[:20]:<20} | {home} vs {away}")

        elif response.status_code == 401:
            print("❌ Erro 401: Token inválido ou não autorizado.")
        else:
            print(f"❌ Erro na API: Status {response.status_code}")
            print(f"Mensagem: {response.text}")

    except Exception as e:
        print(f"❌ Falha na requisição: {e}")

if __name__ == "__main__":
    buscar_jogos_hoje()
