import asyncio
import json
from playwright.async_api import async_playwright

async def validar_valencia_iframe():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 1000},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        url_esc = "https://dicasbet.com.br/estatisticas-de-escanteios/"
        relatorio = {"time": "Valencia", "dados_iframe": {}}

        print("🌐 Acessando Dicasbet...")
        await page.goto(url_esc, wait_until="domcontentloaded", timeout=60000)

        print("🔗 Localizando iFrame...")
        # Espera o iFrame estar presente na página
        try:
            iframe_handle = await page.wait_for_selector("#adam-choi-iframe", timeout=30000)
            iframe = await iframe_handle.content_frame()
            
            if not iframe:
                raise Exception("Não foi possível acessar o conteúdo do iFrame.")

            # 1. ESPERAR O WIDGET CARREGAR DENTRO DO IFRAME
            print("⏳ Aguardando widget carregar...")
            await iframe.wait_for_selector('select', timeout=20000)

            # 2. SELECIONAR "8.5" (Usando seletor de texto se o ng-model falhar)
            print("🚩 Selecionando mercado 8.5...")
            # Tentamos selecionar pelo rótulo visível
            await iframe.select_option('select', label="8.5")
            await page.wait_for_timeout(2000)

            # 3. FILTRAR JOGOS EM CASA (Botão do seu print)
            print("🏠 Filtrando Jogos em Casa...")
            btn_casa = iframe.get_by_role("button", name="Em casa")
            if await btn_casa.count() > 0:
                await btn_casa.click()
            else:
                await iframe.click('text="Em casa"')
            await page.wait_for_timeout(2000)

            # 4. BUSCAR VALENCIA
            print("🔍 Filtrando por 'Valencia'...")
            # O campo de busca costuma ser um input simples no topo da tabela
            search_input = iframe.locator('input[type="text"]').first
            await search_input.fill("Valencia")
            await page.wait_for_timeout(2000)

            # 5. CAPTURAR DADOS DA LINHA
            print("📊 Extraindo valores...")
            # Buscamos a linha que contém o Valencia
            linha = iframe.locator("tr:has-text('Valencia')").first
            # Pegamos todas as células daquela linha
            colunas = await linha.locator("td").all_inner_texts()

            if len(colunas) >= 3:
                relatorio["dados_iframe"] = {
                    "time": colunas[0].strip(),
                    "frequencia": colunas[1].strip(), # Ex: 3/5
                    "porcentagem": colunas[2].strip()  # Ex: 60%
                }
            else:
                relatorio["dados_iframe"]["erro"] = f"Dados incompletos. Colunas: {len(colunas)}"

        except Exception as e:
            relatorio["dados_iframe"]["erro"] = f"Erro no processo: {str(e)[:150]}"

        print("\n=== JSON BRUTO (VALENCIA VIA IFRAME) ===")
        print(json.dumps(relatorio, indent=4, ensure_ascii=False))
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(validar_valencia_iframe())
            
