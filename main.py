import asyncio
import json
from playwright.async_api import async_playwright

async def validar_extrais_valencia():
    async with async_playwright() as p:
        # Launch com viewport para garantir que os botões apareçam
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 900})
        page = await context.new_page()

        urls = {
            "escanteios": "https://dicasbet.com.br/estatisticas-de-escanteios/",
            "resultados": "https://dicasbet.com.br/estatisticas-de-resultados/"
        }

        relatorio_bruto = {
            "partida": "Valencia x Alavés",
            "dicasbet_escanteios": {},
            "dicasbet_resultados": {}
        }

        for chave, url in urls.items():
            print(f"📡 Acessando {chave} no Dicasbet...")
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                
                # 1. Busca pelo nome (Valencia)
                search = page.locator('input[placeholder*="Buscar"]').first
                await search.fill("Valencia")
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(2000)

                # 2. SELECIONAR "ÚLTIMOS 5 JOGOS" (Filtro do seu print)
                # O site usa um <select> para definir a quantidade de jogos
                try:
                    await page.select_option('select.form-control', value="5")
                    await page.wait_for_timeout(1500)
                except:
                    pass # Caso o seletor tenha ID diferente, o robô tenta seguir

                # 3. FILTRAR "JOGOS EM CASA" (Para bater com os 60% do seu print)
                btn_casa = page.get_by_role("button", name="Jogos em Casa")
                if await btn_casa.count() > 0:
                    await btn_casa.click()
                else:
                    await page.click('text="Jogos em Casa"')
                
                await page.wait_for_timeout(2000)

                # 4. CAPTURAR LINHA DO VALENCIA
                # Pegamos a linha que contém o texto Valencia e extraímos as colunas
                linha = page.locator("tr:not([style*='display: none'])").filter(has_text="Valencia").first
                colunas = await linha.locator("td").all_inner_texts()
                
                # Mapeia os dados conforme a página (Frequência e Porcentagem)
                if len(colunas) >= 4:
                    relatorio_bruto[f"dicasbet_{chave}"] = {
                        "time": colunas[1].strip(),
                        "frequencia": colunas[2].strip(), # Ex: 3/5
                        "porcentagem": colunas[3].strip() # Ex: 60%
                    }
            except Exception as e:
                relatorio_bruto[f"dicasbet_{chave}"]["erro"] = str(e)

        # Saída do JSON Bruto
        print("\n=== JSON BRUTO DE VALIDAÇÃO (VALENCIA) ===")
        print(json.dumps(relatorio_bruto, indent=4, ensure_ascii=False))
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(validar_extrais_valencia())
    
