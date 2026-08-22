import time
import re
from selenium.webdriver.common.by import By

def extrair_numero(texto):
    """Extrai números decimais ou inteiros de uma string."""
    try:
        match = re.search(r'[\d\.]+', texto)
        if match:
            return float(match.group())
    except:
        pass
    return 0.0

def pegar_estatisticas_coletivas(driver, dados_jogo):
    """
    Acessa a aba de estatísticas no Superscore e extrai todas as médias 
    e dados coletivos necessários para os módulos de mercados atualizados.
    """
    stats_coletivas = {
        # Médias gerais usadas por Gols, Chutes, etc.
        "media_gols_mandante": 0.0,
        "media_gols_visitante": 0.0,
        "media_finalizacoes_mandante": 0.0,
        "media_finalizacoes_visitante": 0.0,
        "media_chutes_gol_mandante": 0.0,
        "media_chutes_gol_visitante": 0.0,
        "media_escanteios_mandante": 0.0,
        "media_escanteios_visitante": 0.0,
        "media_cartoes_amarelos_mandante": 0.0,
        "media_cartoes_amarelos_visitante": 0.0,

        # Listas detalhadas usadas por Escanteios e Cartões
        "cantos_mandante_h2h": [],
        "cantos_visitante_h2h": [],
        "cartoes_mandante_h2h": [],
        "cartoes_visitante_h2h": [],
        "dados_incompletos_cartoes": False
    }

    try:
        url_base = dados_jogo.get("url_h2h_base", "").split('?')[0].rstrip('/')
        if not url_base:
            url_h2h = dados_jogo.get("url_h2h", "")
            if "superscore.com/jogo/" in url_h2h:
                url_base = url_h2h.split("#")[0].rstrip('/')

        if not url_base:
            return stats_coletivas

        # ==========================================
        # RASPAR ABA DE ESTATÍSTICAS DO SUPERSCORE
        # ==========================================
        url_estats = f"{url_base}/estatisticas"
        driver.get(url_estats)
        time.sleep(1.5)
        
        print(f"      📊 [Superscore] Coletando estatísticas e médias para os mercados...")
        
        # 1. Captura de Médias Gerais baseadas nos nomes das estatísticas na página
        nomes_estatisticas = [
            ("Gols", "media_gols_mandante", "media_gols_visitante"),
            ("Finalizações Totais", "media_finalizacoes_mandante", "media_finalizacoes_visitante"),
            ("Chutes no gol", "media_chutes_gol_mandante", "media_chutes_gol_visitante"),
            ("Escanteios", "media_escanteios_mandante", "media_escanteios_visitante"),
            ("Cartões amarelos", "media_cartoes_amarelos_mandante", "media_cartoes_amarelos_visitante")
        ]

        for nome_pt, chave_mandante, chave_visitante in nomes_estatisticas:
            try:
                elemento_texto = driver.find_element(By.XPATH, f"//div[text()='{nome_pt}']")
                linha_pai = elemento_texto.find_element(By.XPATH, "./..") 
                textos = linha_pai.text.split('\n')
                
                if len(textos) >= 3:
                    stats_coletivas[chave_mandante] = extrair_numero(textos[0])
                    stats_coletivas[chave_visitante] = extrair_numero(textos[-1])
            except Exception:
                continue

        # 2. Captura de blocos detalhados para popular listas de Escanteios e Cartões
        linhas_estatisticas = driver.find_elements(By.CSS_SELECTOR, "div[class*='stat'], div[class*='row'], div[class*='category']")
        
        cantos_casa, cantos_fora = [], []
        cartoes_casa, cartoes_fora = [], []

        for linha in linhas_estatisticas:
            texto_linha = linha.text.lower()
            
            if "escanteios" in texto_linha or "cantos" in texto_linha:
                numeros = re.findall(r'\d+', texto_linha)
                if len(numeros) >= 2:
                    cantos_casa.append(float(numeros[0]))
                    cantos_fora.append(float(numeros[1]))
            
            elif "cartões" in texto_linha or "amarelos" in texto_linha:
                numeros = re.findall(r'\d+', texto_linha)
                if len(numeros) >= 2:
                    cartoes_casa.append(float(numeros[0]))
                    cartoes_fora.append(float(numeros[1]))

        if cantos_casa:
            stats_coletivas["cantos_mandante_h2h"] = cantos_casa
            stats_coletivas["cantos_visitante_h2h"] = cantos_fora
            
        if cartoes_casa:
            stats_coletivas["cartoes_mandante_h2h"] = cartoes_casa
            stats_coletivas["cartoes_visitante_h2h"] = cartoes_fora
        else:
            stats_coletivas["dados_incompletos_cartoes"] = True

    except Exception as e:
        print(f"      ⚠️ Erro ao raspar estatísticas coletivas no Superscore: {e}")
        stats_coletivas["dados_incompletos_cartoes"] = True

    return stats_coletivas
            
