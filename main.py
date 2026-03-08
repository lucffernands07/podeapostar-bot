import asyncio
import json
from playwright.async_api import async_playwright

async def validar_valencia_iframe():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Importante: iFrames às vezes detectam headless. Usaremos um User-Agent real.
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        url_esc = "https://dicasbet.com.br/estatisticas-de-escanteios/"
        
        relatorio = {"time": "Valencia", "dados_iframe": {}}

        print("🌐 Acessando Dicasbet...")
        await page.goto(url_esc, wait_until="domcontentloaded", timeout=60000)

        # 1. LOCALIZAR O IFRAME (Conforme o HTML que você mandou)
        print("🔗 Entrando no iFrame do Adam Choi...")
        # Esperamos o iFrame carregar na página
        iframe_element = await page.wait_for_selector("#adam-choi-iframe")
        iframe = await iframe_element.content_frame()

        if iframe:
            try:
                # 2. SELECIONAR "8.5" (Dropdown de mercado)
                # Dentro do iFrame, os seletores costumam ser diferentes
                print("🚩 Selecionando mercado 8.5...")
                await iframe.select_option('select[ng-model="vm.selectedMarket"]', label="8.5")
                
                # 3. BUSCAR TIME (Campo de busca dentro do iFrame)
                print("🔍 Buscando Valencia...")
                search_input = iframe.locator('input[placeholder*="Search"], input[ng-model="searchString"]')
                await search_input.fill("Valencia")
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(3000)

                # 4. CAPTURAR OS DADOS (Linha da tabela)
                # O Adam Choi usa tabelas com classes específicas
                linha = iframe.locator("tr").filter(has_text="Valencia").first
                colunas = await linha.locator("td").all_inner_texts()

                if len(colunas) >= 3:
                    relatorio["dados_iframe"] = {
                        "time": colunas[0].strip(),
                        "frequencia": colunas[1].strip(), # Ex: 3/5
                        "porcentagem": colunas[2].strip()  # Ex: 60%
                    }
            except Exception as e:
                relatorio["dados_iframe"]["erro"] = f"Erro dentro do iFrame: {str(e)[:100]}"
        else:
            relatorio["dados_iframe"]["erro"] = "iFrame não encontrado ou inacessível."

        print("\n=== JSON BRUTO (VALENCIA VIA IFRAME) ===")
        print(json.dumps(relatorio, indent=4, ensure_ascii=False))
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(validar_valencia_iframe())
                                                                              
