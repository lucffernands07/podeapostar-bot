import asyncio
import json
from playwright.async_api import async_playwright

async def validar_extrais_valencia():
    async with async_playwright() as p:
        # Launch com argumentos para sites pesados
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1366, 'height': 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
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
            print(f"📡 Tentando capturar {chave} no Dicasbet...")
            try:
                # 1. Carregamento inicial
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                # 2. Espera o campo de busca carregar (usando seletor genérico de input de busca)
                search_selector = 'input[type="search"], .dataTables_filter input, input[placeholder*="Buscar"]'
                await page.wait_for_selector(search_selector, timeout=20000)
                
                # 3. Digitar Valencia e esperar o filtro processar
                await page.fill(search_selector, "Valencia")
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(3000)

                # 4. Selecionar 'Últimos 5 jogos' (Dropdown)
                # Buscamos o select de quantidade de jogos que aparece nos seus prints
                select_selector = 'select[name*="length"], .custom-select, select.form-control'
                if await page.locator(select_selector).count() > 0:
                    await page.select_option(select_selector, value="5")
                    await page.wait_for_timeout(2000)

                # 5. Clicar em 'Jogos em Casa'
                btn_casa = page.get_by_text("Jogos em Casa", exact=True)
                if await btn_casa.count() > 0:
                    await btn_casa.click()
                    await page.wait_for_timeout(2000)

                # 6. Extração da Linha Filtrada
                # Pegamos a primeira linha da tabela que contém 'Valencia'
                linha = page.locator("table tbody tr").filter(has_text="Valencia").first
                colunas = await linha.locator("td").all_inner_texts()
                
                if len(colunas) >= 4:
                    relatorio_bruto[f"dicasbet_{chave}"] = {
                        "time": colunas[1].strip(),
                        "frequencia": colunas[2].strip(), # Ex: 3/5
                        "porcentagem": colunas[3].strip() # Ex: 60%
                    }
                else:
                    relatorio_bruto[f"dicasbet_{chave}"]["erro"] = "Linha encontrada, mas colunas incompletas."
                    
            except Exception as e:
                relatorio_bruto[f"dicasbet_{chave}"]["erro"] = f"Timeout ou Erro: {str(e)[:100]}..."

        # Saída do JSON Final
        print("\n=== JSON BRUTO DE VALIDAÇÃO (VALENCIA) ===")
        print(json.dumps(relatorio_bruto, indent=4, ensure_ascii=False))
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(validar_extrais_valencia())
    
