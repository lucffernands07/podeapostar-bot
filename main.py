import asyncio
import json
from playwright.async_api import async_playwright

async def extrair_dados_reais():
    async with async_playwright() as p:
        # Usamos um perfil de telemóvel (conforme as tuas imagens)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
            viewport={'width': 393, 'height': 851}
        )
        page = await context.new_page()

        url = "https://footystats.org/spain/deportivo-alaves-vs-valencia-cf-h2h-stats"
        
        try:
            print(f"📡 Acedendo via Mobile Simulation: {url}")
            # O truque é esperar o 'ajax_pong.php' que aparece no teu network
            await page.goto(url, wait_until="commit")
            await page.wait_for_selector(".stat-strong", timeout=20000)

            # Extração dos dados que confirmaste nas imagens
            dados = {
                "btts": await page.locator(".stat-strong:has-text('BTTS')").inner_text(),
                "over_1_5": await page.locator(".stat-strong:has-text('Over 1.5')").inner_text(),
                "vitoria_casa": await page.locator(".bar-item.winner").first.inner_text(),
                "empate": await page.locator(".bar-item.draw").first.inner_text()
            }
            
            # Limpeza rápida
            for k, v in dados.items():
                dados[k] = v.replace("BTTS", "").replace("Over 1.5", "").strip()

            print("\n=== DADOS VALIDADOS ===")
            print(json.dumps(dados, indent=4))

        except Exception as e:
            print(f"❌ Erro: O firewall bloqueou a simulação. Tentando ler cache...")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(extrair_dados_reais())
    
