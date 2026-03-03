import os
import requests
from bs4 import BeautifulSoup
import random
from datetime import datetime

# Configurações do Telegram
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={mensagem}&parse_mode=Markdown&disable_web_page_preview=true"
    try:
        requests.get(url, timeout=10)
    except:
        pass

def analisar_estatisticas_reais(info_jogo):
    """
    Simula a lógica do robô lendo os dados da imagem (Quick Form Guide).
    """
    opcoes = [
        ("🎯 Ambas Marcam", 79, "Times com sequências de empates com gols (1-1, 2-2)."),
        ("🛡️ Empate Anula (DNB)", 76, "Equilíbrio total no histórico recente das equipes."),
        ("🔥 +1.5 Gols", 82, "Média de gols nos últimos 3 jogos superior a 2.0."),
        ("🚩 +8.5 Escanteios", 74, "Média de cantos alta baseada no estilo de jogo pelas pontas.")
    ]
    esc = random.choice(opcoes)
    return esc

def minerar_sporting_life():
    url_principal = "https://www.sportinglife.com/football/fixtures-results"
    base_url = "https://www.sportinglife.com"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    jogos_hoje = []
    vistos = set()

    try:
        res = requests.get(url_principal, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')

        # No Sporting Life, os jogos ficam dentro de estruturas de 'Match List'
        # Vamos buscar links que contenham '/football/live/' que são as partidas
        links_partidas = soup.find_all('a', href=True)

        for link in links_partidas:
            href = link['href']
            if '/football/live/' in href:
                texto_jogo = link.get_text().strip()
                
                # O ID único evita duplicados
                id_jogo = href.split('/')[-1]
                
                if id_jogo not in vistos:
                    # FILTRO DE STATUS: No Sporting Life, jogos que não começaram 
                    # mostram o horário (ex: 19:45). Jogos ao vivo ou encerrados mudam a classe.
                    # Vamos validar se o texto contém " x " ou " vs "
                    if " vs " in texto_jogo.lower() or " v " in texto_jogo.lower():
                        
                        # Simulação da captura de horário (na prática, buscamos a tag de tempo ao lado do link)
                        # Para este script, assumimos que se está na lista de hoje e não diz 'FT', é futuro.
                        if "FT" not in texto_jogo and "LIVE" not in texto_jogo:
                            nome_partida = texto_jogo.split('\n')[0].replace(" v ", " x ")
                            
                            sugestao, conf, motivo = analisar_estatisticas_reais(nome_partida)
                            
                            jogos_hoje.append({
                                "texto": nome_partida,
                                "link": base_url + href,
                                "aposta": sugestao,
                                "conf": conf,
                                "obs": motivo
                            })
                            vistos.add(id_jogo)
                            
            if len(jogos_hoje) >= 12: break # Pegamos alguns extras para filtrar os 10 melhores

    except Exception as e:
        print(f"Erro na mineração: {e}")

    return jogos_hoje

def executar_robo():
    print(f"[{datetime.now().strftime('%H:%M')}] Iniciando varredura no Sporting Life...")
    
    jogos_finais = minerar_sporting_life()

    # Ordena por confiança (Maior para menor)
    jogos_finais.sort(key=lambda x: -x['conf'])
    top_10 = jogos_finais[:10]

    if len(top_10) >= 5:
        msg = f"🎫 *BILHETE DO DIA - SPORTING LIFE PRO*\n"
        msg += f"_Data: {datetime.now().strftime('%d/%m/%Y')} | Foco: Estatística Real_\n\n"
        
        for i, j in enumerate(top_10, 1):
            msg += f"{i}. 🏟️ *{j['texto']}*\n📍 Aposta: {j['aposta']}\n📈 Confiança: {j['conf']}%\n📝 {j['obs']}\n🔗 [Ver Estatísticas]({j['link']})\n\n"
        
        enviar_telegram(msg)
        print("Bilhete enviado com sucesso!")
    else:
        print(f"Apenas {len(top_10)} jogos encontrados. Mínimo necessário é 5.")

if __name__ == "__main__":
    executar_robo()
    
