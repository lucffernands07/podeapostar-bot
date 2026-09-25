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
    Localiza o container exclusivo da liga e extrai as informações de todos os links de jogos
    diretamente no JavaScript para evitar StaleElementReferenceException do Selenium.
    """
    js_script = """
        let nomeAlvo = arguments[0].toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g, "");
        let elementos = Array.from(document.querySelectorAll('div, span, p, h1, h2, h3, a'));
        
        for (let el of elementos) {
            if (el.children.length === 0 && el.innerText) {
                let textoNorm = el.innerText.toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g, "");
                
                if (textoNorm === nomeAlvo || textoNorm.includes(nomeAlvo)) {
                    // Sobe no DOM procurando o container individual da liga
                    let container = el.closest("div.border, div.rounded-lg, div.shadow-sm");
                    
                    if (!container) {
                        container = el.parentElement;
                        for (let i = 0; i < 3; i++) {
                            if (container && container.parentElement && container.parentElement.tagName !== 'BODY') {
                                if (container.querySelectorAll("a[href*='/fixture/']").length > 0) {
                                    break;
                                }
                                container = container.parentElement;
                            }
                        }
                    }
                    
                    if (container) {
                        container.scrollIntoView({block: 'center'});
                        
                        // Expande se estiver recolhido
                        let links = container.querySelectorAll("a[href*='/fixture/']");
                        if (links.length === 0) {
                            el.click();
                            // Aguarda um instante para renderização
                            let start = Date.now();
                            while (Date.now() - start < 500) {}
                            links = container.querySelectorAll("a[href*='/fixture/']");
                        }
                        
                        // Extrai os dados dos links diretamente em JS
                        let resultados = [];
                        links.forEach(a => {
                            let href = a.href;
                            let fullText = a.innerText || "";
                            
                            // Extrai textos dos spans internos
                            let spans = Array.from(a.querySelectorAll("span"))
                                            .map(s => s.innerText.trim())
                                            .filter(t => t.length > 0 && !t.includes("Escalações"));
                            
                            resultados.push({
                                url: href,
                                texto_card: fullText,
                                spans: spans
                            });
                        });
                        
                        return resultados;
                    }
                }
            }
        }
        return null;
    """
    return driver.execute_script(js_script, nome_liga)

def main():
    driver = configurar_driver()
    url_home = "https://www.statshub.com/pt"
    
    # 📌 Defina aqui a lista de ligas que deseja varrer
    ligas_alvo = [
        "UEFA Nations League",
        "Brasileirão Série B"
    ]
    
    inicio_tempo_total = time.time()
    total_jogos_processados = 0
    
    try:
        for nome_liga_alvo in ligas_alvo:
            print(f"\n==================================================")
            print(f"🔍 INICIANDO BUSCA DA LIGA: {nome_liga_alvo}")
            print(f"==================================================")
            
            try:
                # 1. Garante que abre a home limpa
                driver.get(url_home)
                WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                time.sleep(3)
                
                # 2. Rola a página suavemente para carregar todas as ligas do dia
                driver.execute_script("window.scrollTo(0, 1000);")
                time.sleep(1)
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)
                
                # 3. Busca e extrai os jogos diretamente no JS para evitar stale element
                dados_jogos_raw = obter_jogos_da_liga(driver, nome_liga_alvo)
                
                if dados_jogos_raw is None:
                    print(f"⚠️ Liga '{nome_liga_alvo}' não foi encontrada ou não possui jogos listados para hoje.")
                    continue
                
                print(f"🏆 LIGA ENCONTRADA E EXPANDIDA: {nome_liga_alvo}")
                    
                jogos_encontrados = []
                for item in dados_jogos_raw:
                    url_fixture = item.get("url")
                    
                    if url_fixture and url_fixture not in [j["url"] for j in jogos_encontrados]:
                        texto_card = item.get("texto_card", "")
                        spans = item.get("spans", [])
                        
                        # Limpa os nomes obtidos dos spans
                        nomes_times = [limpar_nome_time(n) for n in spans if n]
                        
                        # Tenta extrair o horário do texto completo
                        match_horario = re.search(r'\b\d{1,2}:\d{2}\b', texto_card)
                        horario = match_horario.group(0) if match_horario else "--:--"

                        # Validações de placar / status
                        tem_placar = any(str_placar in texto_card for str_placar in ["0—", "1—", "2—", "3—", "4—", "5—", "0-", "1-", "2-", "3-", "4-", "5-"])
                        is_ao_vivo = "AO VIVO" in texto_card.upper()
                        
                        # REGRA 1: Descartar jogos já encerrados
                        if tem_placar and not is_ao_vivo:
                            print(f"⏭️ Descartando jogo encerrado: {texto_card.replace(chr(10), ' ')}")
                            continue

                        # REGRA 2: Trava de segurança para jogos passados da madrugada
                        if horario != "--:--" and not is_ao_vivo:
                            try:
                                hora_int = int(horario.split(":")[0])
                                if hora_int < 3 and tem_placar:
                                    print(f"⏭️ Descartando partida encerrada da madrugada: {horario}")
                                    continue
                            except ValueError:
                                pass

                        # Captura e formata os nomes limpos em português
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

                # Processa cada jogo encontrado da liga atual
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
    
