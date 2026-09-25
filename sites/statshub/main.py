import os
import time
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Importa o módulo diretamente da mesma pasta
from sites.statshub.funcoes.raspagem_h2h import pegar_estatisticas_statshub

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
    
    # Define a linguagem do navegador explicitamente para Português (BR)
    options.add_argument("--lang=pt-BR")
    options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)

    # Emula fuso de Brasília (UTC-3)
    driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {
        "timezoneId": "America/Sao_Paulo"
    })

    return driver

def expandir_todas_as_ligas(driver):
    """
    Clica no botão 'Expandir Tudo' usando o XPath exato fornecido.
    """
    xpath_btn = '//*[@id="main-content-area"]/div[2]/main/div/div[1]/div[8]/div[1]/div[2]/button[3]/span'
    
    try:
        elemento_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, xpath_btn))
        )
        driver.execute_script("arguments[0].click();", elemento_btn)
        print("🔓 Botão 'Expandir Tudo' acionado com sucesso via XPath!")
        time.sleep(4)
        return True
    except Exception as e:
        print(f"⚠️ Erro ao clicar no botão 'Expandir Tudo' via XPath: {e}")
        try:
            js_fallback = """
                let spans = Array.from(document.querySelectorAll('span'));
                for (let s of spans) {
                    if (s.innerText && s.innerText.trim() === 'Expandir Tudo') {
                        let btn = s.closest('button') || s;
                        btn.click();
                        return true;
                    }
                }
                return false;
            """
            if driver.execute_script(js_fallback):
                print("🔓 Botão 'Expandir Tudo' acionado via Fallback JS!")
                time.sleep(4)
                return True
        except Exception as e_fb:
            print(f"⚠️ Fallback JS também falhou: {e_fb}")
            
    return False

def limpar_nome_time(nome_bruto):
    """
    Remove hashs aleatórios e limpa o nome do time.
    Exemplo: 'Malta Mufu7E' -> 'Malta', 'Germany Mug03R' -> 'Germany'
    """
    if not nome_bruto:
        return ""
    nome_limpo = re.sub(r'\s+[A-Za-z0-9]*\d+[A-Za-z0-9]*$', '', nome_bruto.strip())
    return nome_limpo.strip()

def obter_jogos_da_liga(driver, nome_liga):
    """
    Localiza a liga com base no link  do cabeçalho (/leagues/) 
    e extrai os jogos estritamente contidos em seu container.
    """
    js_script = """
        let nomeAlvo = arguments[0].toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g, "");
        
        // Busca especificamente todos os links de liga do StatsHub
        let linksLiga = Array.from(document.querySelectorAll("a[href*='/leagues/']"));
        
        for (let aLiga of linksLiga) {
            let textoLiga = (aLiga.innerText || "").toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g, "").trim();
            let hrefLiga = (aLiga.getAttribute("href") || "").toLowerCase();
            
            // Quebra o nome em palavras-chave para garantir o casamento exato
            let palavrasChave = nomeAlvo.split(" ").filter(p => p.length > 2);
            let bateuTexto = palavrasChave.every(p => textoLiga.includes(p));
            let bateuHref = palavrasChave.every(p => hrefLiga.includes(p));
            
            if (bateuTexto || bateuHref) {
                // Sobe no DOM até o container do card da liga (limita para não subir à página inteira)
                let containerLiga = aLiga;
                while (containerLiga && containerLiga.tagName !== 'BODY') {
                    let parent = containerLiga.parentElement;
                    if (!parent) break;
                    
                    // O container correto tem links de jogos e não engloba outros links de liga
                    let outrosLinksLiga = parent.querySelectorAll("a[href*='/leagues/']");
                    if (outrosLinksLiga.length > 1) {
                        // Se encontrou mais de um link de liga, o elemento atual já é o container isolado da liga!
                        break;
                    }
                    containerLiga = parent;
                }
                
                if (containerLiga) {
                    containerLiga.scrollIntoView({block: 'center'});
                    
                    let resultados = [];
                    let linksFixture = Array.from(containerLiga.querySelectorAll("a[href*='/fixture/']"));
                    
                    // Deduplicação imediata por URL no JS
                    let urlsVistas = new Set();
                    
                    linksFixture.forEach(a => {
                        let href = a.href;
                        if (!urlsVistas.has(href)) {
                            urlsVistas.add(href);
                            
                            // Pega o card/linha do jogo
                            let linhaJogo = a.closest("div") || a.parentElement;
                            if (linhaJogo && linhaJogo.parentElement && linhaJogo.innerText.length < 15) {
                                linhaJogo = linhaJogo.parentElement;
                            }
                            
                            let fullText = linhaJogo ? (linhaJogo.innerText || "") : "";
                            let lines = fullText.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
                            
                            resultados.push({
                                url: href,
                                texto_card: fullText,
                                linhas: lines
                            });
                        }
                    });
                    
                    return resultados;
                }
            }
        }
        return null;
    """
    return driver.execute_script(js_script, nome_liga)

def main():
    driver = configurar_driver()
    url_home = "https://www.statshub.com/pt"
    
    # Lista de ligas que deseja analisar
    ligas_alvo = [
        "UEFA Nations League",
        "Brasileirão Série B"
    ]
    
    inicio_tempo_total = time.time()
    total_jogos_processados = 0
    
    try:
        # 1. Carrega a página principal
        driver.get(url_home)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)
        
        # 2. Rola ligeiramente
        driver.execute_script("window.scrollTo(0, 300);")
        time.sleep(1)
        
        # 3. Clica em "Expandir Tudo"
        expandir_todas_as_ligas(driver)

        # 4. Rola a página para renderizar tudo
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)

        for nome_liga_alvo in ligas_alvo:
            print(f"\n==================================================")
            print(f"🔍 INICIANDO BUSCA DA LIGA: {nome_liga_alvo}")
            print(f"==================================================")
            
            try:
                # 5. Extrai apenas os jogos pertencentes a esta liga
                dados_jogos_raw = obter_jogos_da_liga(driver, nome_liga_alvo)
                
                if not dados_jogos_raw:
                    print(f"⚠️ Liga '{nome_liga_alvo}' não foi encontrada na página do dia.")
                    continue
                
                print(f"🏆 LIGA ENCONTRADA E EXPANDIDA: {nome_liga_alvo}")
                    
                jogos_encontrados = []
                for item in dados_jogos_raw:
                    url_fixture = item.get("url")
                    
                    if url_fixture and url_fixture not in [j["url"] for j in jogos_encontrados]:
                        texto_card = item.get("texto_card", "")
                        linhas = item.get("linhas", [])
                        
                        # Extrai o horário
                        match_horario = re.search(r'\b\d{1,2}:\d{2}\b', texto_card)
                        horario = match_horario.group(0) if match_horario else "--:--"

                        # Filtra nomes de times descartando números/arbitragem
                        nomes_times = []
                        for l in linhas:
                            if not re.search(r'\b\d{1,2}:\d{2}\b', l) and not re.search(r'\d+\.\d+', l) and len(l) > 2:
                                nomes_times.append(limpar_nome_time(l))

                        tem_placar = any(str_placar in texto_card for str_placar in ["0—", "1—", "2—", "3—", "4—", "5—", "0-", "1-", "2-", "3-", "4-", "5-"])
                        is_ao_vivo = "AO VIVO" in texto_card.upper()
                        
                        # Descartar jogos já encerrados
                        if tem_placar and not is_ao_vivo:
                            print(f"⏭️ Descartando jogo encerrado: {texto_card.replace(chr(10), ' ')}")
                            continue

                        if len(nomes_times) >= 2:
                            t1_card, t2_card = nomes_times[0], nomes_times[1]
                            status_str = "AO VIVO" if is_ao_vivo else horario
                            info_formatada = f"{t1_card} x {t2_card} ({status_str})"
                        else:
                            t1_card, t2_card = "Mandante", "Visitante"
                            info_formatada = texto_card.replace("\n", " ").strip()

                        jogos_encontrados.append({
                            "url": url_fixture,
                            "info_card": info_formatada,
                            "t1": t1_card,
                            "t2": t2_card,
                            "horario": horario
                        })
                        
                print(f"\n📋 JOGOS DE HOJE ENCONTRADOS EM '{nome_liga_alvo}' ({len(jogos_encontrados)} partidas):")
                for idx, j in enumerate(jogos_encontrados, 1):
                    print(f"   {idx}. {j['info_card']}")
                print(f"--------------------------------------------------\n")
                
                if not jogos_encontrados:
                    print(f"⚠️ Nenhum jogo pendente foi encontrado para a liga '{nome_liga_alvo}' hoje.\n")
                    continue

                # Processa cada jogo qualificado
                for idx, jogo in enumerate(jogos_encontrados, 1):
                    url_jogo = jogo["url"]
                    t1 = jogo["t1"]
                    t2 = jogo["t2"]
                    horario_jogo = jogo["horario"]
                    inicio_jogo = time.time()
                    
                    print(f"--------------------------------------------------")
                    print(f"🏟️ [{nome_liga_alvo}] Jogo [{idx}/{len(jogos_encontrados)}]: {t1} x {t2}")
                    print(f"🔗 {url_jogo}")
                    print(f"--------------------------------------------------")
                    
                    try:
                        pegar_estatisticas_statshub(driver, url_jogo, t1, t2, horario_jogo)
                        total_jogos_processados += 1
                        
                        tempo_jogo = round(time.time() - inicio_jogo, 2)
                        print(f"⏱️ Tempo de raspagem deste jogo: {tempo_jogo}s\n")
                        
                    except Exception as e_jogo:
                        print(f"❌ Erro ao raspar {t1} x {t2}: {e_jogo}\n")

            except Exception as e_liga:
                print(f"⚠️ Não foi possível processar a liga '{nome_liga_alvo}': {e_liga}\n")

        tempo_total = round(time.time() - inicio_tempo_total, 2)
        print("="*50)
        print(f"⏱️ RASPAGEM GERAL FINALIZADA: {total_jogos_processados} jogos processados no total em {tempo_total}s")
        print("="*50 + "\n")

    except Exception as e:
        print(f"❌ Erro durante a execução do script: {e}")
        
    finally:
        try:
            driver.quit()
            print("🔒 Driver do Selenium encerrado.")
        except Exception:
            pass

if __name__ == "__main__":
    main()
