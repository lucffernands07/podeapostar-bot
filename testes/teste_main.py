import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from testes.teste_raspagem_h2h import pegar_estatisticas_statshub

def iniciar_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    # Para rodar sem abrir a janela do navegador, descomente a linha abaixo:
    # options.add_argument("--headless=new")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def main():
    print("🚀 Iniciando teste de raspagem StatsHub...")

    # Lista de jogos ordenada por horário
    lista_jogos = [
        {
            "t1": "Barracas Central",
            "t2": "Independiente Rivadavia",
            "horario": "18:00",
            "url": "https://www.statshub.com/fixture/barracas-central-vs-independiente-rivadavia-mubbv9/383374"
        },
        {
            "t1": "Lanús",
            "t2": "Estudiantes",
            "horario": "21:15",
            "url": "https://www.statshub.com/fixture/lanus-vs-estudiantes-de-la-plata-mubbyl/383366"
        }
    ]

    driver = iniciar_driver()
    tempo_inicio = time.time()

    try:
        for jogo in lista_jogos:
            pegar_estatisticas_statshub(
                driver=driver,
                url_jogo=jogo["url"],
                t1=jogo["t1"],
                t2=jogo["t2"],
                horario=jogo["horario"]
            )
    finally:
        driver.quit()
        tempo_total = round(time.time() - tempo_inicio, 2)
        print(f"⏱️ Raspagem de todos os jogos concluída em {tempo_total}s")
        print("🔒 Driver do Selenium encerrado.")

if __name__ == "__main__":
    main()
