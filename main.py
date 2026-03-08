import asyncio
import json
from playwright.async_api import async_playwright

async def validar_jogo_completo():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0...")
        page = await context.new_page()

        # URLs das fontes
        url_resultados = "https://dicasbet.com.br/estatisticas-de-resultados/"
        url_escanteios = "https://dicasbet.com.br/estatisticas-de-escanteios/"

        analise = {
            "partida": "Valencia vs Alavés",
            "estatisticas": {},
            "veredito": {}
        }

        try:
            # 1. Captura Probabilidade de Vitória
            await page.goto(url_resultados, wait_until="domcontentloaded")
            await page.select_option('select[name="liga"]', label="Espanha - La Liga") # Filtro por Liga
            await page.click('text="Jogando Hoje"') # Filtro por data
            await page.wait_for_timeout(2000)
            
            win_pct = await page.locator("tr:has-text('Valencia') .porcentagem").first.inner_text()
            analise["estatisticas"]["vitoria_casa"] = win_pct.strip()

            # 2. Captura Probabilidade de Escanteios
            await page.goto(url_escanteios, wait_until="domcontentloaded")
            await page.fill('input[placeholder="Buscar por Time"]', "Valencia")
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(2000)
            
            corn_pct = await page.locator(".porcentagem").first.inner_text()
            analise["estatisticas"]["escanteios_over"] = corn_pct.strip()

            # --- CRITÉRIOS DE VALIDAÇÃO ---
            v_win = int(win_pct.replace("%", ""))
            v_corn = int(corn_pct.replace("%", ""))

            analise["veredito"] = {
                "confianca_vitoria": "ALTA" if v_win >= 60 else "MEDIA",
                "mercado_sugerido": "Mais de 8.5 Escanteios" if v_corn >= 60 else "Analisar ao vivo",
                "bilhete_seguranca": "Valencia ou Empate (Dupla Chance)" if v_win >= 40 else "Risco"
            }

        except Exception as e:
            analise["erro"] = str(e)

        print(json.dumps(analise, indent=4, ensure_ascii=False))
        await browser.close()

if __name__ == "__main__":
    asyncio.run(validar_jogo_completo())
            
