import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def pegar_estatisticas_statshub(driver, url_jogo, t1, t2, nome_comp=""):
    """
    Raspa os últimos 5 jogos do mandante (casa) e visitante (fora) no StatsHub
    acessando a aba 'Team Stats' e lendo diretamente as tabelas de estatísticas.
    """
    stats = {
        "casa_05": 0, "casa_15": 0, "casa_25": 0, "casa_35_under": 0, "casa_45_under": 0, "casa_55_under": 0, "casa_btts": 0, 
        "fora_05": 0, "fora_15": 0, "fora_25": 0, "fora_35_under": 0, "fora_45_under": 0, "fora_55_under": 0, "fora_btts": 0, 
        
        "mandante_vitorias_casa": 0,
        "visitante_vitorias_fora": 0,
        "mandante_sem_derrota_casa": 0,
        "visitante_sem_derrota_fora": 0,
        "visitante_derrotas_fora": 0,
        "visitante_gols_sofridos_fora": 0.0,
        "mandante_gols_sofridos_casa": 0.0,
        "mandante_gols_feitos_casa": 0.0,
        "visitante_gols_feitos_fora": 0.0,
        "mandante_jogos_com_gol_casa": 0,
        "visitante_jogos_com_gol_fora": 0,

        "t1_placar_1": None, "t2_placar_1": None,     
        "t1_resultado_1": None, "t2_resultado_1": None,
        "pular_gols": False,
        "url_h2h_base": url_jogo,
        "historico_chutes": {}, 
        "historico_mandante_am": {}, "historico_mandante_vm": {},
        "historico_visitante_am": {}, "historico_visitante_vm": {}
    }

    try:
        driver.get(url_jogo)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(3)

        # 1. Garante a navegação até a aba 'Team Stats'
        try:
            aba_team_stats = WebDriverWait(driver, 8).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Team Stats')] | //div[contains(text(), 'Team Stats')]"))
            )
            driver.execute_script("arguments[0].click();", aba_team_stats)
            time.sleep(3)
        except Exception:
            pass

        # 2. Localiza as tabelas de jogos exibidas na aba Team Stats
        # O StatsHub organiza os jogos em linhas dentro de cada seção (Lanús e Estudiantes)
        linhas_elementos = driver.find_elements(By.XPATH, "//tr[td] | //div[contains(@class, 'v-row') and .//div[contains(@class, 'text-center')]]")

        jogos_casa = []
        jogos_fora = []

        for elem in linhas_elementos:
            texto = elem.text.strip()
            if not texto:
                continue

            # Procura placares no formato "0 3", "1 0", "1 1", etc.
            match_placar = re.search(r'(\d+)\s*[\-–:]?\s*(\d+)', texto)
            if match_placar:
                g1, g2 = int(match_placar.group(1)), int(match_placar.group(2))
                partes = [p.strip() for p in texto.split('\n') if p.strip()]

                # Filtragem para Mandante (Lanús em Casa)
                if len(jogos_casa) < 5:
                    if any("lanú" in p.lower() or "lanus" in p.lower() for p in partes[:3]):
                        jogos_casa.append((g1, g2))

                # Filtragem para Visitante (Estudiantes Fora)
                if len(jogos_fora) < 5:
                    if any("estud" in p.lower() for p in partes[2:]):
                        jogos_fora.append((g1, g2))

        # --- PROCESSAMENTO DOS JOGOS DO MANDANTE (LANÚS EM CASA) ---
        print(f"   🔍 [CASA] Encontrados {len(jogos_casa)} jogos do {t1} em casa.")
        for i, (g1, g2) in enumerate(jogos_casa):
            placar_str = f"{g1}-{g2}"
            total = g1 + g2

            if i == 0: stats["t1_placar_1"] = placar_str

            if total > 0.5: stats["casa_05"] += 1
            if total > 1.5: stats["casa_15"] += 1
            if total > 2.5: stats["casa_25"] += 1
            if total <= 3: stats["casa_35_under"] += 1
            if total <= 4: stats["casa_45_under"] += 1
            if total <= 5: stats["casa_55_under"] += 1
            if g1 > 0 and g2 > 0: stats["casa_btts"] += 1

            stats["mandante_gols_feitos_casa"] += float(g1)
            stats["mandante_gols_sofridos_casa"] += float(g2)
            if g1 > 0: stats["mandante_jogos_com_gol_casa"] += 1

            if g1 > g2:
                res = "V"
                stats["mandante_vitorias_casa"] += 1
                stats["mandante_sem_derrota_casa"] += 1
            elif g1 < g2:
                res = "D"
            else:
                res = "E"
                stats["mandante_sem_derrota_casa"] += 1

            if i == 0: stats["t1_resultado_1"] = res

        # --- PROCESSAMENTO DOS JOGOS DO VISITANTE (ESTUDIANTES FORA) ---
        print(f"   🔍 [FORA] Encontrados {len(jogos_fora)} jogos do {t2} fora.")
        for i, (g1, g2) in enumerate(jogos_fora):
            placar_str = f"{g1}-{g2}"
            total = g1 + g2

            if i == 0: stats["t2_placar_1"] = placar_str

            if total > 0.5: stats["fora_05"] += 1
            if total > 1.5: stats["fora_15"] += 1
            if total > 2.5: stats["fora_25"] += 1
            if total <= 3: stats["fora_35_under"] += 1
            if total <= 4: stats["fora_45_under"] += 1
            if total <= 5: stats["fora_55_under"] += 1
            if g1 > 0 and g2 > 0: stats["fora_btts"] += 1

            stats["visitante_gols_feitos_fora"] += float(g2)
            stats["visitante_gols_sofridos_fora"] += float(g1)
            if g2 > 0: stats["visitante_jogos_com_gol_fora"] += 1

            if g2 > g1:
                res = "V"
                stats["visitante_vitorias_fora"] += 1
                stats["visitante_sem_derrota_fora"] += 1
            elif g2 < g1:
                res = "D"
                stats["visitante_derrotas_fora"] += 1
            else:
                res = "E"
                stats["visitante_sem_derrota_fora"] += 1

            if i == 0: stats["t2_resultado_1"] = res

    except Exception as e_geral:
        print(f"      ⚠️ Erro geral ao raspar StatsHub: {e_geral}")

    return stats
