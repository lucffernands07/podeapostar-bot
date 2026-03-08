import asyncio
import json
from playwright.async_api import async_playwright

async def validar_adam_choi_direto():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 1200})
        page = await context.new_page()

        url_liga = "https://www.adamchoi.co.uk/leagues/spain-la-liga"
        
        relatorio = {"partida": "Valencia x Alavés", "dados": {}}

        try:
            print(f"🚀 Acessando: {url_liga}")
            # Esperamos o carregamento total da rede
            await page.goto(url_liga, wait_until="networkidle", timeout=60000)

            # 1. Esperar o Widget existir no HTML
            print("⏳ Aguardando componente de estatísticas...")
            await page.wait_for_selector("league-fixtures-widget", timeout=20000)

            # 2. Localizar os Dropdowns (Usando seletores mais simples)
            # Tentamos clicar no primeiro select que aparecer dentro do widget
            dropdowns = page.locator("league-fixtures-widget select")
            
            print("🚩 Configurando: Total Match Corners...")
            # O primeiro select costuma ser o StatType
            await dropdowns.nth(0).select_option(label="Total Match Corners")
            await page.wait_for_timeout(2000)

            print("🚩 Configurando: Over 8.5...")
            # O segundo select costuma ser o Market/Line
            await dropdowns.nth(1).select_option(label="8.5")
            await page.wait_for_timeout(3000)

            # 3. Extrair os dados da tabela que apareceu
            # Vamos buscar a linha que contém o nome do Valencia
            print("📊 Extraindo valores da tabela...")
            linha_valencia = page.locator("tr").filter(has_text="Valencia").first
            
            # Pegamos o texto das células de resultado (os círculos coloridos)
            resultados = await linha_valencia.locator(".fixture-result-cell").all_inner_texts()
            
            relatorio["dados"] = {
                "time": "Valencia",
                "ultimos_resultados": resultados[:5], # Pega os últimos 5
                "sucesso": f"{len([r for r in resultados[:5] if r != '-'])}/5"
            }

        except Exception as e:
            relatorio["erro"] = str(e)[:200]

        print("\n=== JSON BRUTO (ADAM CHOI DIRETO) ===")
        print(json.dumps(relatorio, indent=4, ensure_ascii=False))
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(validar_adam_choi_direto())
