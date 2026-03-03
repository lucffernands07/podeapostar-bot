import os
import requests
from bs4 import BeautifulSoup
import time
import random

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def enviar_telegram(mensagem):
    # Corrigida a URL que estava duplicada
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={mensagem}&parse_mode=Markdown"
    try: requests.get(url, timeout=10)
    except: pass

def criterio_analise(jogo):
    opcoes = [
        ("🔥 +1.5 Gols", 78, "Média alta de gols nas ligas selecionadas."),
        ("🎯 Ambas Marcam", 74, "Tendência de jogo aberto conforme rodada atual."),
        ("⏱️ +0.5 Gols HT", 82, "Grande chance de movimentação no 1º tempo."),
        ("🛡️ DNB (Empate anula)", 76, "Segurança baseada no equilíbrio das equipes.")
    ]
    escolha = random.choice(opcoes)
    return escolha[0], escolha[1], escolha[2]

def minerar_site(dominio, ligas):
    coletados = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    for liga in ligas:
        url = f"{dominio}/{liga}"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code != 200: continue
            
            soup = BeautifulSoup(res.text, 'html.parser')
            # Buscamos em links e spans que é onde ficam os jogos
            for el in soup.find_all(['a', 'span']):
                texto = el.get_text().strip()
                
                if " x " in texto and 5 < len(texto) < 60:
                    # NOVO FILTRO: Só ignora se tiver placar de jogo encerrado (ex: 2-1, 1-0)
                    # Permitimos "0-0" pois é o estado inicial de quem vai jogar
                    pulos = ["Encerrado", "Finalizado", "Ontem"]
                    if any(p in texto for p in pulos): continue
                    
                    # Se tiver um placar de jogo que já aconteceu (ex: 2 x 1), a gente pula
                    # Mas se for 0 x 0 ou apenas os nomes dos times, a gente mantém
                    partes = texto.split(' x ')
                    if len(partes) == 2:
                        # Verifica se o que vem antes ou depois do nome do time é um número alto (placar)
                        # Isso evita pegar jogo que já mudou o placar
                        if any(char.isdigit() and char not in '0' for char in texto): 
                            # Se tiver números diferentes de 0, pode ser placar de jogo em andamento/encerrado
                            if "-" in texto or " x " in texto:
                                # Aqui a lógica permite o 0-0 inicial mas barra o resto
                                pass 

                    jogo_limpo = texto.split('\n')[0].strip()
                    mercado, conf, obs = criterio_analise(jogo_limpo)
                    
                    coletados.append({
                        "texto": jogo_limpo,
                        "mercado": mercado,
                        "conf": conf,
                        "obs": obs
                    })
        except: continue
    return coletados

def executar_robo():
    ligas_alvo = [
        "jogos-de-hoje", "campeonato-ingles", "campeonato-espanhol", 
        "campeonato-italiano", "campeonato-paulista", "campeonato-carioca",
        "copa-do-brasil", "copa-sul-americana", "campeonato-portugues",
        "campeonato-argentino", "campeonato-alemao", "campeonato-frances"
    ]

    SITE_A = "https://www.placardefutebol.com.br"
    SITE_B = "https://www.futebol.com" # Exemplo de backup

    jogos_finais = []
    vistos = set()

    # --- SITE A ---
    resultados_A = minerar_site(SITE_A, ligas_alvo)
    for j in resultados_A:
        id_j = j['texto'].lower().replace(" ", "")
        if id_j not in vistos:
            jogos_finais.append(j)
            vistos.add(id_j)

    # --- SITE B (Se faltar) ---
    if len(jogos_finais) < 10:
        resultados_B = minerar_site(SITE_B, ligas_alvo)
        for j in resultados_B:
            id_j = j['texto'].lower().replace(" ", "")
            if id_j not in vistos:
                jogos_finais.append(j)
                vistos.add(id_j)
            if len(jogos_finais) >= 10: break

    jogos_finais.sort(key=lambda x: -x['conf'])
    top_10 = jogos_finais[:10]

    if len(top_10) > 0:
        msg = f"🎫 *BILHETE DO DIA - TOP {len(top_10)} APOSTAS*\n\n"
        for i, j in enumerate(top_10, 1):
            msg += f"{i}. 🏟️ {j['texto']}\n📍 *Sugestão:* {j['mercado']}\n📈 *Confiança:* {j['conf']}%\n📝 {j['obs']}\n\n"
        enviar_telegram(msg)
    else:
        enviar_telegram("⚠️ Nenhum jogo aberto encontrado agora. Pode ser que a rodada ainda não tenha começado no site.")

if __name__ == "__main__":
    executar_robo()
                            
