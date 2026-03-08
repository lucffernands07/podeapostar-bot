import os
import asyncio
from playwright.async_api import async_playwright

async def run():
    # Sua chave da API
    api_key = os.getenv("ZENROWS_KEY")
    url_jogo = "https://footystats.org/brazil/se-palmeiras-vs-gremio-novorizontino-h2h-stats"
    
    # URL de conexão do ZenRows (Modo Browser Renting)
    ws_endpoint = f"wss://proxy.zenrows.com/playwright?apikey={api_key}&js_render=true&wait_for=.stat-strong"

    async with async_playwright() as pw:
        print("🚀 Iniciando Playwright via ZenRows (Aguardando renderização)...")
        browser = await pw.chromium.connect_over_cdp(ws_endpoint)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(url_jogo, wait_until="networkidle")
        
        # Espera o widget do 80% carregar de verdade
        await page.wait_for_selector(".stat-strong")

        # Agora pegamos os dados direto da tela
        dados = await page.evaluate('''() => {
            const resultados = {};
            const itens = document.querySelectorAll('.grid-item');
            
            itens.forEach(item => {
                const valor = item.querySelector('.stat-strong').innerText;
                const mercado = item.querySelector('span').innerText;
                const sub = item.querySelector('.stat-text') ? item.querySelector('.stat-text').innerText : "";
                
                if (mercado.includes("Over 1.5")) resultados["o15"] = valor;
                if (mercado.includes("BTTS")) resultados["btts"] = valor;
                if (mercado.includes("Clean Sheets")) {
                    if (sub.includes("Palmeiras")) resultados["cs_pal"] = valor;
                    if (sub.includes("Novorizontino")) resultados["cs_nov"] = valor;
                }
            });
            return resultados;
        }''')

        print("\n📊 DADOS CAPTURADOS PELO PLAYWRIGHT:")
        print(f"📍 Over 1.5: {dados.get('o15')}")
        print(f"📍 BTTS: {dados.get('btts')}")
        print(f"📍 CS Palmeiras: {dados.get('cs_pal')}")
        print(f"📍 CS Novorizontino: {dados.get('cs_nov')}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
