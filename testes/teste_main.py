import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Importa a função de raspagem do StatsHub (seu caminho mantido)
from testes.teste_raspagem_h2h import pegar_estatisticas_statshub

def configurar_driver():
    options = Options()
    
    # Flags essenciais para rodar sem crash no Linux / GitHub Actions
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--remote-allow-origins=*")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--window-size=1920,1080")
    
    # User-Agent Linux
    options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)

    # Emula fuso de Brasília (UTC-3)
    driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {
        "timezoneId": "America/Sao_Paulo"
    })

    return driver

def main():
    driver = configurar_driver()
    url_home = "https://www.statshub.com/pt"
    nome_liga_alvo = "UEFA Nations League"
    
    inicio_tempo_total = time.time()
    
    try:
        driver.get(url_home)
        time.sleep(3)
        
        # Localiza o nome da liga de forma case-insensitive
        xpath_liga = f"//*[(self::a or self::div or self::span) and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{nome_liga_alvo.lower()}')]"
        elemento_liga = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath_liga))
        )
        
        # Encontra o container clicável da liga
        container_liga = elemento_liga.find_element(By.XPATH, "./ancestor::div[contains(@class, 'flex') or contains(@class, 'cursor-pointer')][1]")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", container_liga)
        time.sleep(0.5)
        
        # Tenta buscar os jogos no bloco pai da sanfona
        bloco_pai_liga = container_liga.find_element(By.XPATH, "./ancestor::div[contains(@class, 'border') or contains(@class, 'rounded') or contains(@class, 'space-y') or contains(@class, 'flex-col')][2]")
        elementos_jogos = bloco_pai_liga.find_elements(By.XPATH, ".//a[contains(@href, '/fixture/')]")
        
        # Se estiver fechada/sem jogos visíveis, clica para expandir
        if not elementos_jogos:
            driver.execute_script("arguments[0].click();", container_liga)
            time.sleep(2)
            elementos_jogos = bloco_pai_liga.find_elements(By.XPATH, ".//a[contains(@href, '/fixture/')]")

        # LOG 1: Nome da liga encontrada
        print(f"\n==================================================")
        print(f"🏆 LIGA ENCONTRADA E EXPANDIDA: {nome_liga_alvo}")
        print(f"==================================================")
            
        jogos_encontrados = []
        for el in elementos_jogos:
            url_fixture = el.get_attribute("href")
            
            if url_fixture and url_fixture not in [j["url"] for j in jogos_encontrados]:
                texto_card = el.text.strip()
                
                # Extrai apenas os nomes dos times ignorando botões ("Escalações") e arbitragem
                spans = el.find_elements(By.XPATH, ".//span[contains(@class, 'truncate') or contains(@class, 'font-normal')]")
                nomes_times = [s.text.strip() for s in spans if s.text.strip() and "Escalações" not in s.text]
                
                # Procura elemento de horário (formato HH:MM)
                horario_el = el.find_elements(By.XPATH, ".//*[contains(text(), ':')]")
                horario = horario_el[0].text.strip() if horario_el else "--:--"

                # -------------------------------------------------------------
                # VALIDAÇÕES DE ESTADO SEGUNDO A INTERFACE DO STATSHUB
                # -------------------------------------------------------------
                # Placa / Resultado identificado por travessão ou hífen
                tem_placar = any(str_placar in texto_card for str_placar in ["0—", "1—", "2—", "3—", "4—", "5—", "0-", "1-", "2-", "3-", "4-", "5-"])
                is_ao_vivo = "AO VIVO" in texto_card.upper()
                
                # REGRA 1: Descartar jogos já encerrados (que exibem horário + placar juntas)
                if tem_placar and not is_ao_vivo:
                    print(f"⏭️ Descartando jogo encerrado: {texto_card.replace(chr(10), ' ')}")
                    continue

                # REGRA 2: Trava de segurança para jogos passados da madrugada (00h-02h)
                if horario != "--:--" and not is_ao_vivo:
                    try:
                        hora_int = int(horario.split(":")[0])
                        if hora_int < 3 and tem_placar:
                            print(f"⏭️ Descartando partida encerrada da madrugada: {horario}")
                            continue
                    except ValueError:
                        pass

                # Formata a string do card conforme a situação
                if len(nomes_times) >= 2:
                    t1_card, t2_card = nomes_times[0], nomes_times[1]
                    status_str = "AO VIVO" if is_ao_vivo else horario
                    info_formatada = f"{t1_card} x {t2_card} ({status_str})"
                else:
                    info_formatada = texto_card.replace("\n", " ").strip()

                jogos_encontrados.append({
                    "url": url_fixture,
                    "info_card": info_formatada
                })
                
        # LOG 2: Todos os jogos de hoje encontrados na liga
        print(f"\n📋 JOGOS DE HOJE ENCONTRADOS ({len(jogos_encontrados)} partidas):")
        for idx, j in enumerate(jogos_encontrados, 1):
            print(f"   {idx}. {j['info_card']}")
        print(f"--------------------------------------------------\n")
        
        if not jogos_encontrados:
            print("⚠️ Nenhum jogo pendente foi encontrado para esta liga hoje.")
            return

        # Processa cada jogo encontrado
        for idx, jogo in enumerate(jogos_encontrados, 1):
            url_jogo = jogo["url"]
            inicio_jogo = time.time()
            
            # Extração dos nomes dos times via URL da fixture
            try:
                slug_fixture = url_jogo.split("/fixture/")[1].split("/")[0]
                partes_times = slug_fixture.split("-vs-")
                
                t1 = partes_times[0].replace("-", " ").title().strip()
                
                raw_t2 = partes_times[1]
                if "-mub" in raw_t2:
                    raw_t2 = raw_t2.split("-mub")[0]
                t2 = raw_t2.replace("-", " ").title().strip()
            except Exception:
                t1, t2 = "Mandante", "Visitante"
            
            print(f"--------------------------------------------------")
            print(f"🏟️ [{idx}/{len(jogos_encontrados)}] {t1} x {t2}")
            print(f"🔗 {url_jogo}")
            print(f"--------------------------------------------------")
            
            try:
                pegar_estatisticas_statshub(driver, url_jogo, t1, t2)
                
                tempo_jogo = round(time.time() - inicio_jogo, 2)
                print(f"⏱️ Tempo de raspagem deste jogo: {tempo_jogo}s\n")
                
            except Exception as e_jogo:
                print(f"❌ Erro ao raspar {t1} x {t2}: {e_jogo}\n")

        tempo_total = round(time.time() - inicio_tempo_total, 2)
        print("="*50)
        print(f"⏱️ RASPAGEM FINALIZADA: {len(jogos_encontrados)} jogos processados em {tempo_total}s")
        print("="*50 + "\n")

    except Exception as e:
        print(f"❌ Erro durante a raspagem da página inicial: {e}")
        
    finally:
        try:
            driver.quit()
            print("🔒 Driver do Selenium encerrado.")
        except Exception:
            pass

if __name__ == "__main__":
    main()
