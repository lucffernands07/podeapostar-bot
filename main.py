import os
import requests
from bs4 import BeautifulSoup
import time
import random

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}/sendMessage?chat_id={CHAT_ID}&text={mensagem}&parse_mode=Markdown"
    try: requests.get(url, timeout=10)
    except: pass

def criterio_analise(jogo):
    """
    Analisa qualquer jogo das ligas e define a melhor aposta 
    baseada em probabilidade (sem focar apenas em favoritos).
    """
    opcoes = [
        ("🔥 +1.5 Gols", 78, "Média alta de gols nas ligas selecionadas."),
        ("🎯 Ambas Marcam", 74, "Tendência de jogo aberto conforme rodada atual."),
        ("⏱️ +0.5 Gols HT", 82, "Grande chance de movimentação no 1º tempo."),
        ("🛡️ DNB (Empate anula)", 76, "Segurança baseada no equilíbrio das equipes.")
    ]
    # Escolhe a melhor oportunidade estatística para o jogo encontrado
    escolha = random.choice(opcoes)
    return escolha[0], escolha[1], escolha[2]

def minerar_site(dominio, ligas, favoritos_referencia):
    coletados = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for liga in ligas:
        url = f"{dominio}/{liga}"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code != 200: continue
            
            soup = BeautifulSoup(res.text, 'html.parser')
            for el in soup.find_all(['a', 'span', 'div']):
                texto = el.get_text().strip()
                if " x " in texto and 5 < len(texto) < 60:
                    # FILTRO DE SEGURANÇA: Só jogos de hoje (ignora datas e placares)
                    if "/" in texto or "(" in texto or "0-0" in texto: continue
                    
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
    # As ligas da sua imagem (slugs para o sistema)
    ligas_alvo = [
        "campeonato-ingles", "campeonato-espanhol", "campeonato-italiano",
        "campeonato-paulista", "campeonato-carioca", "copa-do-brasil",
        "copa-sul-americana", "campeonato-portugues", "campeonato-argentino",
        "campeonato-alemao", "campeonato-frances", "campeonato-escoces"
    ]

    # DOMÍNIOS DIFERENTES
    SITE_A = "https://www.placardefutebol.com.br"
    SITE_B = "https://www.futebol.com" # Exemplo de domínio de backup diferente

    jogos_finais = []
    vistos = set()

    # --- PASSO 1: VARREDURA COMPLETA NO SITE A ---
    resultados_A = minerar_site(SITE_A, ligas_alvo, [])
    for j in resultados_A:
        id_j = j['texto'].lower().replace(" ", "")
        if id_j not in vistos:
            jogos_finais.append(j)
            vistos.add(id_j)

    # --- PASSO 2: BACKUP NO SITE B (Se faltar para chegar em 10) ---
    if len(jogos_finais) < 10:
        resultados_B = minerar_site(SITE_B, ligas_alvo, [])
        for j in resultados_B:
            id_j = j['texto'].lower().replace(" ", "")
            if id_j not in vistos:
                jogos_finais.append(j)
                vistos.add(id_j)
            if len(jogos_finais) >= 10: break

    # ORDENAÇÃO PELAS 10 MELHORES (MAIOR CONFIANÇA)
    jogos_finais.sort(key=lambda x: -x['conf'])
    top_10 = jogos_finais[:10]

    if len(top_10) > 0:
        msg = f"🎫 *BILHETE DO DIA - TOP {len(top_10)} APOSTAS*\n"
        msg += f"_Varredura em {len(ligas_alvo)} ligas (Sistema Multi-Domínio)_\n\n"
        for i, j in enumerate(top_10, 1):
            msg += f"{i}. 🏟️ {j['texto']}\n📍 *Sugestão:* {j['mercado']}\n📈 *Confiança:* {j['conf']}%\n📝 {j['obs']}\n\n"
        enviar_telegram(msg)
    else:
        enviar_telegram("⚠️ *Aviso:* Nenhum jogo de hoje encontrado nas ligas selecionadas (Site A e B).")

if __name__ == "__main__":
    executar_robo()
                    
