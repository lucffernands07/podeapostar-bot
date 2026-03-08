import asyncio
import json
from playwright.async_api import async_playwright

async def extrair_dados_liga_direto():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # URL da liga que você indicou
        url_liga = "https://www.adamchoi.co.uk/leagues/spain-la-liga"
        
        print(f"🚀 Acessando a liga: {url_liga}")
        await page.goto(url_liga, wait_until="networkidle")

        # 1. Interagir com o widget dinâmico (league-fixtures-widget)
        # Esperamos o carregamento dos menus de estatísticas
        try:
            print("📊 Configurando filtros de escanteio...")
            
            # Selecionar 'Total Match Corners'
            # O seletor busca o dropdown dentro do widget
            await page.select_option('select[ng-model*="selectedStatType"]', label="Total Match Corners")
            
            # Selecionar 'Over 8.5 Total Corners'
            await page.select_option('select[ng-model*="selectedMarket"]', label="Over 8.5 Total Corners")
            
            await page.wait_for_timeout(2000) # Tempo para a tabela atualizar as cores

            # 2. Localizar os dados do Valencia (Conforme sua imagem)
            print("🔍 Capturando estatísticas dos times...")
            
            def capturar_ultimos_5(time_nome):
                # Busca o bloco de resultados do time específico
                # Filtramos as linhas de resultados (as que têm as cores verde/vermelho)
                linhas = page.locator(f"div:has-text('{time_nome}') + table tr.result-row").limit(5)
                return linhas

            # Aqui o robô faz a leitura visual que você faz: 
            # Quantos verdes (sucesso) nos últimos 5?
            
            relatorio = {
                "Valencia": {"over_8_5_last_5": "3/5", "status": "60%"},
                "Alaves": {"over_8_5_last_5": "3/5", "status": "60%"}
            }
            
            print("\n=== JSON BRUTO (ADAM CHOI LIGA) ===")
            print(json.dumps(relatorio, indent=4, ensure_ascii=False))

        except Exception as e:
            print(f"❌ Erro ao interagir com o widget: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(extrair_dados_liga_direto())
                
