import re
from playwright.sync_api import sync_playwright

def tem_btts(placar):
    """Verifica se ambas as equipes marcaram no placar (ex: '2-1', '1-1')"""
    if not placar:
        return False
    nums = re.findall(r'\d+', str(placar))
    return len(nums) >= 2 and int(nums[0]) > 0 and int(nums[1]) > 0

def avaliar_ambos_marcam(jogos_casa_em_casa, jogos_fora_fora):
    """
    Aplica a regra:
    - Mínimo 4/5 para ambos os lados -> Ambas Marcam: Sim
    - Máximo 3/5 para ambos os lados -> Ambas Marcam: Não
    """
    if len(jogos_casa_em_casa) < 5 or len(jogos_fora_fora) < 5:
        return None, f"Dados insuficientes (Casa: {len(jogos_casa_em_casa)}, Fora: {len(jogos_fora_fora)})"

    btts_casa = sum(1 for p in jogos_casa_em_casa[:5] if tem_btts(p))
    btts_fora = sum(1 for p in jogos_fora_fora[:5] if tem_btts(p))

    # Mínimo 4/5 para os dois lados -> SIM
    if btts_casa >= 4 and btts_fora >= 4:
        porcentagem = "100%" if (btts_casa == 5 and btts_fora == 5) else "80%"
        return f"Ambas Marcam: Sim ({porcentagem})", f"Casa: {btts_casa}/5 BTTS | Fora: {btts_fora}/5 BTTS"

    # Máximo 3/5 para os dois lados -> NÃO
    if btts_casa <= 3 and btts_fora <= 3:
        porcentagem = "100%" if (btts_casa <= 1 and btts_fora <= 1) else "80%"
        return f"Ambas Marcam: Não ({porcentagem})", f"Casa: {btts_casa}/5 BTTS | Fora: {btts_fora}/5 BTTS"

    return None, f"Fora dos padrões (Casa: {btts_casa}/5 BTTS, Fora: {btts_fora}/5 BTTS)"

def raspar_e_analisar(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print(f"🌐 Acessando: {url}")
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
        # Fecha banner de privacidade/cookies se houver
        try:
            page.click("#onetrust-accept-btn-handler", timeout=3000)
        except:
            pass

        # ----------------------------------------------------
        # 1. RASPAGEM: MANDANTE JOGANDO EM CASA
        # ----------------------------------------------------
        print("\n⏳ Clicando no botão CASA do Mandante...")
        page.locator("button:has-text('CASA')").first.click()
        page.wait_for_timeout(1500)
        
        primeira_tabela = page.locator(".h2h__section").first
        elementos_resultados = primeira_tabela.locator(".h2h__result").all()
        
        # Extrai e formata o placar garantindo o hífen entre os gols (ex: '2-0')
        placares_casa = [
            "-".join(re.findall(r'\d+', el.inner_text())) 
            for el in elementos_resultados[:5]
        ]
        print(f"📌 Últimos 5 jogos do Casa (em casa): {placares_casa}")

        # ----------------------------------------------------
        # 2. RASPAGEM: VISITANTE JOGANDO FORA
        # ----------------------------------------------------
        print("\n⏳ Clicando no botão FORA do Visitante...")
        page.locator("button:has-text('FORA')").first.click()
        page.wait_for_timeout(1500)
        
        primeira_tabela_fora = page.locator(".h2h__section").first
        elementos_resultados_fora = primeira_tabela_fora.locator(".h2h__result").all()
        
        # Extrai e formata o placar garantindo o hífen entre os gols (ex: '1-2')
        placares_fora = [
            "-".join(re.findall(r'\d+', el.inner_text())) 
            for el in elementos_resultados_fora[:5]
        ]
        print(f"📌 Últimos 5 jogos do Fora (fora): {placares_fora}")

        browser.close()

        # ----------------------------------------------------
        # 3. VALIDAÇÃO DAS REGRAS
        # ----------------------------------------------------
        print("\n" + "="*50)
        resultado, detalhe = avaliar_ambos_marcam(placares_casa, placares_fora)
        
        if resultado:
            print(f"⭐ MERCADO GERADO: {resultado}")
        else:
            print(f"🚫 DESQUALIFICADO / IGNORADO")
        print(f"📊 Detalhes: {detalhe}")
        print("="*50)

url_teste = "https://www.flashscore.com.br/jogo/futebol/kolos-kovalivka-OfzUZGy6/zorya-j9Wy32w4/h2h/total/?mid=MoWTl8SF"
raspar_e_analisar(url_teste)
        
