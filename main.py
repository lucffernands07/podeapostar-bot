import requests
from datetime import datetime

# Configurações básicas de teste
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def teste_radar():
    hoje = datetime.now().strftime("%Y%m%d")
    # Ligas do seu print
    ligas = {
        "eng.1": "Premier League",
        "esp.1": "LALIGA",
        "ger.1": "Bundesliga",
        "ita.1": "Serie A",
        "fra.1": "Ligue 1",
        "por.1": "Português",
        "ned.1": "Holandês",
        "tur.1": "Turco",
        "bra.1": "Brasileirão", # Importante para quando começar a série A
        "bra.camp.gaucho": "Gauchão"
    }

    print(f"🔎 BUSCANDO JOGOS PARA A DATA: {hoje}")
    print("-" * 50)

    total_geral = 0

    for l_id, l_nome in ligas.items():
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{l_id}/scoreboard?dates={hoje}"
        try:
            res = requests.get(url, headers=HEADERS, timeout=10).json()
            eventos = res.get('events', [])
            
            print(f" League: {l_nome} ({l_id})")
            
            if not eventos:
                print("   ❌ Nenhum jogo encontrado nesta liga para hoje.")
            
            for ev in eventos:
                status = ev.get('status', {}).get('type', {}).get('state')
                nome_jogo = ev.get('name')
                hora = ev.get('date')[11:16]
                
                status_traduzido = "PRÉ-JOGO" if status == 'pre' else "EM ANDAMENTO/FINALIZADO"
                print(f"   🔹 [{hora}] {nome_jogo} | Status: {status_traduzido}")
                total_geral += 1
                
        except Exception as e:
            print(f"   ❌ Erro ao acessar {l_nome}: {e}")
        
        print("-" * 50)

    print(f"\n✅ TESTE CONCLUÍDO. Total de jogos mapeados: {total_geral}")

if __name__ == "__main__":
    teste_radar()
    
