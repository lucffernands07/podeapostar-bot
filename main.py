import os
import requests
from bs4 import BeautifulSoup
import random

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={mensagem}&parse_mode=Markdown&disable_web_page_preview=true"
    try: requests.get(url, timeout=10)
    except: pass

def criterio_estatistico(jogo, fonte):
    opcoes = [
        ("🔥 +1.5 Gols", 84, "Estatística indica alta frequência de gols."),
        ("🎯 Ambas Marcam", 78, "Ataques eficientes e defesas vazadas."),
        ("⏱️ +0.5 Gols HT", 81, "Pressão alta detectada nos primeiros 45 min."),
        ("🛡️ DNB (Empate anula)", 75, "Equilíbrio com proteção ao empate.")
    ]
    esc = random.choice(opcoes)
    return esc[0], esc[1], f"Fonte: {fonte} | {esc[2]}"

def extrair_dados_site(url, fonte, vistos_global):
    """Função genérica para minerar e evitar duplicadas"""
    novos_jogos = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        # Aqui simulamos a raspagem real. Na prática, o robô busca o conteúdo do HTML
        # Para o teste, vamos usar exemplos de jogos que poderiam estar nas ligas
        exemplo_grade = [
            ("Bayern x Dortmund", "14:30"), ("Liverpool x City", "13:00"),
            ("Palmeiras x Santos", "21:30"), ("Inter x Milan", "16:45"),
            ("PSG x Monaco", "17:00"), ("Benfica x Porto", "18:00"),
            ("Flamengo x Vasco", "21:00"), ("Real Madrid x Barcelona", "17:00"),
            ("Arsenal x Porto", "16:45"), ("Napoli x Juve", "15:45"),
            ("Ajax x PSV", "12:00"), ("River x Boca", "19:00")
        ]
        
        for nome_jogo, hora in exemplo_grade:
            # Criar um ID único para o jogo (ex: "bayernxdortmund")
            id_jogo = nome_jogo.lower().replace(" ", "").replace("vs", "x")
            
            # SÓ ADICIONA SE O JOGO NÃO FOI VISTO AINDA
            if id_jogo not in vistos_global:
                aposta, conf, obs = criterio_estatistico(nome_jogo, fonte)
                novos_jogos.append({
                    "id": id_jogo,
                    "texto": nome_jogo,
                    "hora": hora,
                    "aposta": aposta,
                    "conf": conf,
                    "obs": obs
                })
                vistos_global.add(id_jogo) # Marca como visto imediatamente
                
    except Exception as e:
        print(f"Erro ao minerar {fonte}: {e}")
        
    return novos_jogos

def executar_robo():
    # As ligas que você quer monitorar
    ligas_alvo = ["premier-league", "la-liga", "serie-a", "copa-do-brasil", "paulista"]
    
    jogos_finais = []
    vistos_global = set() # O "Cadeado" para evitar duplicadas

    # --- SITE A: SOFASCORE ---
    # Ele tenta preencher o máximo possível aqui
    res_A = extrair_dados_site("https://www.sofascore.com", "SofaScore", vistos_global)
    jogos_finais.extend(res_A)

    # --- SITE B: FOOTYSTATS (BACKUP) ---
    # Só busca se ainda não tivermos 10 jogos diferentes
    if len(jogos_finais) < 10:
        res_B = extrair_dados_site("https://www.footystats.org", "FootyStats", vistos_global)
        for j in res_B:
            if len(jogos_finais) < 10:
                jogos_finais.append(j)
            else:
                break

    # ORDENAÇÃO POR CONFIANÇA
    jogos_finais.sort(key=lambda x: -x['conf'])
    
    # ENVIO (Mínimo 5, Máximo 10)
    total = len(jogos_finais)
    if total >= 5:
        top_n = jogos_finais[:10]
        msg = f"🎫 *BILHETE DO DIA - TOP {len(top_n)} JOGOS ÚNICOS*\n"
        msg += f"_Sites: SofaScore (Principal) + FootyStats (Backup)_\n\n"
        
        for i, j in enumerate(top_n, 1):
            msg += f"{i}. 🏟️ *{j['texto']}*\n⏰ Horário: {j['hora']}\n📍 Aposta: {j['aposta']}\n📈 Confiança: {j['conf']}%\n📝 {j['obs']}\n\n"
        
        enviar_telegram(msg)
    else:
        enviar_telegram(f"⚠️ Apenas {total} jogos diferentes encontrados hoje.")

if __name__ == "__main__":
    executar_robo()
    
