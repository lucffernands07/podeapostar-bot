import time
import re
import links 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def extrair_numero(texto):
    """Extrai números decimais ou inteiros de uma string."""
    try:
        match = re.search(r'[\d\.]+', texto)
        if match:
            return float(match.group())
    except:
        pass
    return 0.0

def pegar_estatisticas_h2h(driver, url_jogo_base, t1, t2, nome_comp=""):
    stats = {
        "link_betano": None,
        
        # Médias da aba de Estatísticas
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
        
        # Dados do H2H (Apenas 2025/2026, máx 5 jogos)
        "h2h_jogos_filtrados": [], 
        "h2h_vitorias_t1": 0,
        "h2h_vitorias_t2": 0,
        "h2h_empates": 0,
        
        "url_h2h_base": url_jogo_base,
    }

    try:
        url_base = url_jogo_base.split('?')[0].rstrip('/')
        
        # ==========================================
        # 1. CAPTURAR LINK BETANO
        # ==========================================
        try:
            driver.get(url_base)
            # Tratamento rápido do pop-up se aparecer na primeira abertura
            try:
                driver.execute_script("document.elementFromPoint(10, 10).click();")
            except:
                pass
                
            print(f"      🔗 Capturando link Betano para {t1} x {t2}...")
            url_capturada = links.extrair_url_betano(driver)
            if url_capturada:
                stats["link_betano"] = url_capturada
            else:
                t1_q, t2_q = t1.replace(" ", "%20"), t2.replace(" ", "%20")
                stats["link_betano"] = f"https://www.betano.bet.br/busca/?q={t1_q}%20x%20{t2_q}"
        except Exception as e_link:
            print(f"      ⚠️ Erro ao capturar link Betano: {e_link}")
            t1_q, t2_q = t1.replace(" ", "%20"), t2.replace(" ", "%20")
            stats["link_betano"] = f"https://www.betano.bet.br/busca/?q={t1_q}%20x%20{t2_q}"

        # ==========================================
        # 2. RASPAR ABA DE ESTATÍSTICAS (Média dos times)
        # ==========================================
        try:
            url_estats = f"{url_base}/estatisticas"
            driver.get(url_estats)
            time.sleep(1.5)
            
            print(f"      📊 Buscando médias de estatísticas...")
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
                        stats[chave_mandante] = extrair_numero(textos[0])
                        stats[chave_visitante] = extrair_numero(textos[-1])
                except Exception:
                    continue
        except Exception as e_est:
            print(f"      ⚠️ Erro ao raspar estatísticas: {e_est}")

        # ==========================================
        # 3. RASPAR ABA H2H (Filtro 2025/2026, máx 5)
        # ==========================================
        try:
            url_h2h = f"{url_base}/h2h"
            driver.get(url_h2h)
            time.sleep(1.5)
            
            print(f"      ⚔️ Analisando confrontos diretos (H2H 2025/2026)...")
            
            # Localiza os blocos de jogos na página de H2H do Superscore
            # (Ajustaremos o seletor exato após o primeiro teste de campo)
            jogos_h2h = driver.find_elements(By.CSS_SELECTOR, ".h2h__row, [class*='row'], div[class*='match']")
            
            contador_validos = 0
            vitorias_t1 = 0
            vitorias_t2 = 0
            empates = 0
            
            for jogo in jogos_h2h:
                if contador_validos >= 5:
                    break
                try:
                    texto_jogo = jogo.text
                    
                    # Verifica se o jogo é de 2025 ou 2026 pelo texto da data
                    if "25" in texto_jogo or "26" in texto_jogo:
                        # Extrai os placares e nomes para computar
                        nums = re.findall(r'\d+', texto_jogo)
                        if len(nums) >= 2:
                            # Lógica para registrar o confronto válido dos anos 2025/2026
                            contador_validos += 1
                            stats["h2h_jogos_filtrados"].append(texto_jogo)
                except:
                    continue
                    
            stats["h2h_vitorias_t1"] = vitorias_t1
            stats["h2h_vitorias_t2"] = vitorias_t2
            stats["h2h_empates"] = empates
            print(f"      ✅ H2H processado: {contador_validos} jogos encontrados de 2025/2026.")

        except Exception as e_h2h:
            print(f"      ⚠️ Erro ao raspar aba H2H: {e_h2h}")

    except Exception as e_geral:
        print(f"      ⚠️ Erro geral no Superscore: {e_geral}")

    return stats
