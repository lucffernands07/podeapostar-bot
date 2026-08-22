import time
import re
import links 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def formatar_rota_h2h(url_base):
    """
    Limpa qualquer parâmetro de busca e garante a URL raiz do H2H (/h2h).
    """
    path = url_base.split('?')[0].split('#')[0].rstrip('/')

    for sufixo in ['/overall', '/casa', '/fora', '/estatisticas']:
        if path.endswith(sufixo):
            path = path[:-len(sufixo)]

    if not path.endswith('/h2h'):
        path = f"{path}/h2h"

    return f"{path}/"

def obter_url_real_h2h(driver, url_jogo_input):
    """
    Resolve IDs ou garante a URL base limpa do Superscore para a aba H2H.
    """
    if '/futebol/' in url_jogo_input:
        return url_jogo_input.split('?')[0].replace('/estatisticas', '').replace('/h2h', '')

    return url_jogo_input.split('?')[0]

def pegar_estatisticas_h2h(driver, url_jogo_base, t1, t2, nome_comp=""):
    stats = {
        "link_betano": None,
        
        # Dados exclusivos do Confronto Direto (H2H) - Anos 2025/2026 (Máx 5 jogos)
        "h2h_jogos_total": 0,
        "h2h_vitorias_t1": 0,
        "h2h_vitorias_t2": 0,
        "h2h_empates": 0,
        "h2h_jogos_filtrados": [],
        
        # Último confronto direto registrado (se houver em 2025/2026)
        "h2h_ultimo_placar": None,
        "h2h_ultimo_vencedor": None,
        
        "url_h2h_base": url_jogo_base,
    }

    try:
        url_base = obter_url_real_h2h(driver, url_jogo_base)

        # ==========================================
        # 1. CAPTURAR LINK BETANO
        # ==========================================
        try:
            driver.get(url_base)
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
        # 2. RASPAR CONFRONTO DIRETO (H2H) - FILTRO 2025/2026 (MÁX 5)
        # ==========================================
        try:
            url_h2h = formatar_rota_h2h(url_base)
            driver.get(url_h2h)
            time.sleep(1.5)
            
            print(f"      ⚔️ Analisando aba H2H (Confrontos Diretos 2025/2026) para {t1} x {t2}...")
            
            # Localiza as linhas/blocos de confrontos diretos no Superscore
            linhas_h2h = driver.find_elements(By.CSS_SELECTOR, ".h2h__row, [class*='row'], div[class*='match']")
            
            jogos_validos = []
            vitorias_mandante = 0
            vitorias_visitante = 0
            total_empates = 0
            
            for linha in linhas_h2h:
                if len(jogos_validos) >= 5:
                    break
                try:
                    texto_linha = linha.text
                    
                    # Filtro estrito para considerar apenas os anos de 2025 ou 2026 presentes na data do jogo
                    if "25" in texto_linha or "26" in texto_linha:
                        # Extrai os placares da linha do confronto
                        nums = re.findall(r'\d+', texto_linha)
                        if len(nums) >= 2:
                            # Identifica os gols do time da casa (t1) e visitante (t2) no histórico
                            # Geralmente o placar aparece estruturado com os dois números principais da partida
                            gols_t1, gols_t2 = int(nums[0]), int(nums[1])
                            placar_str = f"{gols_t1}-{gols_t2}"
                            
                            jogos_validos.append({
                                "placar": placar_str,
                                "texto": texto_linha
                            })
                            
                            # Computa estatísticas do H2H filtrado
                            if gols_t1 > gols_t2:
                                vitorias_mandante += 1
                            elif gols_t2 > gols_t1:
                                vitorias_visitante += 1
                            else:
                                total_empates += 1
                except Exception:
                    continue

            stats["h2h_jogos_total"] = len(jogos_validos)
            stats["h2h_vitorias_t1"] = vitorias_mandante
            stats["h2h_vitorias_t2"] = vitorias_visitante
            stats["h2h_empates"] = total_empates
            stats["h2h_jogos_filtrados"] = jogos_validos
            
            if jogos_validos:
                stats["h2h_ultimo_placar"] = jogos_validos[0]["placar"]
                
            print(f"      ✅ H2H Filtrado com sucesso: {len(jogos_validos)} jogos válidos (2025/2026).")

        except Exception as e_h2h:
            print(f"      ⚠️ Erro ao raspar aba H2H: {e_h2h}")

    except Exception as e_geral:
        print(f"      ⚠️ Erro geral ao processar H2H: {e_geral}")

    return stats
