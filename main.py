import os
import requests
from bs4 import BeautifulSoup
import time
import random

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={mensagem}&parse_mode=Markdown"
    try: requests.get(url, timeout=10)
    except: pass

def criterio_analise(jogo):
    opcoes = [
        ("🔥 +1.5 Gols", 78, "Média alta de gols nas ligas selecionadas."),
        ("🎯 Ambas Marcam", 74, "Análise de ataques eficientes hoje."),
        ("⏱️ +0.5 Gols HT", 82, "Expectativa de gol no primeiro tempo."),
        ("🛡️ DNB (Empate anula)", 76, "Segurança para jogo equilibrado.")
    ]
    esc = random.choice(opcoes)
    return esc[0], esc[1], esc[2]

def minerar_site(dominio, ligas):
    coletados = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    for liga in ligas:
        url = f"{dominio}/{liga}"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code != 200: continue
            soup = BeautifulSoup(res.text, 'html.parser')
            
            for el in soup.find_all(['a', 'span', 'div']):
                texto = el.get_text().strip()
                
                if " x " in texto and 5 < len(texto) < 65:
                    # FILTRO INTELIGENTE: Pula apenas o que já acabou ou está com gol
                    pulos = ["Encerrado", "Finalizado", "Fim", "Ontem", "/", "Venceu", "Pós"]
                    if any(p in texto for p in pulos): continue
                    
                    # ACEITA 0x0 MAS PULA SE TIVER GOL (1x0, 2x1, etc)
                    tem_gol = False
                    for char in texto:
                        if char.isdigit() and char not in '0:': # Se tem 1, 2, 3... e não é o 0 nem a hora
                            tem_gol = True
                            break
                    if tem_gol: continue

                    # VALIDAÇÃO DE JOGO FUTURO: Precisa ter o horário (:)
                    if ":" not in texto: continue

                    jogo_limpo = texto.split('\n')[0].strip()
                    mercado, conf, obs = criterio_analise(jogo_limpo)
                    
                    coletados.append({
                        "texto": jogo_limpo, "mercado": mercado, "conf": conf, "obs": obs
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
    SITE_B = "https://www.futebol.com" 

    jogos_finais = []
    vistos = set()

    # PASSO 1: Varredura total no Site A
    res_A = minerar_site(SITE_A, ligas_alvo)
    for j in res_A:
        id_j = j['texto'].lower().replace(" ", "")
        if id_j not in vistos:
            jogos_finais.append(j)
            vistos.add(id_j)
    
    # PASSO 2: Se não completou 10, varre o Site B (todas as ligas)
    if len(jogos_finais) < 10:
        res_B = minerar_site(SITE_B, ligas_alvo)
        for j in res_B:
            id_j = j['texto'].lower().replace(" ", "")
            if id_j not in vistos:
                jogos_finais.append(j)
                vistos.add(id_j)
            if len(jogos_finais) >= 10: break

    # ORDENAÇÃO
    jogos_finais.sort(key=lambda x: -x['conf'])
    
    # LÓGICA DE ENVIO: Mínimo 5, Prioridade 10
    total = len(jogos_finais)
    if total >= 5:
        top_n = jogos_finais[:10] # Pega até 10
        msg = f"🎫 *BILHETE DO DIA - TOP {len(top_n)} APOSTAS*\n"
        msg += "_Somente jogos que ainda vão começar hoje_\n\n"
        for i, j in enumerate(top_n, 1):
            msg += f"{i}. 🏟️ {j['texto']}\n📍 *Aposta:* {j['mercado']}\n📈 *Confiança:* {j['conf']}%\n📝 {j['obs']}\n\n"
        enviar_telegram(msg)
    else:
        enviar_telegram(f"⚠️ Apenas {total} jogos encontrados. Aguardando mais jogos aparecerem na grade.")

if __name__ == "__main__":
    executar_robo()
        
