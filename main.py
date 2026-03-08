import asyncio
import json
from playwright.async_api import async_playwright

async def analisar_partida(page, url):
    try:
        # User-Agent de navegador real para evitar o bloqueio
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        })
        
        print(f"📡 Acessando: {url}")
        await page.goto(url, wait_until="load", timeout=60000)
        
        # Espera específica para garantir que o conteúdo carregou
        await page.wait_for_selector(".stat-strong", timeout=15000)

        dados_jogo = {"url": url}
        
        # 1. BTTS e Over Gols
        stats = page.locator(".stat-strong")
        for i in range(await stats.count()):
            texto = await stats.nth(i).inner_text()
            if "BTTS" in texto: dados_jogo["BTTS"] = texto.replace("BTTS", "").strip()
            if "Over 1.5" in texto: dados_jogo["Over_1.5"] = texto.replace("Over 1.5", "").strip()
            if "Over 2.5" in texto: dados_jogo["Over_2.5"] = texto.replace("Over 2.5", "").strip()

        # 2. Probabilidades (Usando seletores mais genéricos caso as classes mudem)
        # Se .bar-item.winner falhar, tentamos pegar pelo texto da porcentagem
        win_elements = page.locator(".bar-item")
        if await win_elements.count() >= 3:
            v_casa = await win_elements.nth(0).inner_text()
            v_empate = await win_elements.nth(1).inner_text()
            
            p_casa = int(v_casa.replace('%',''))
            p_empate = int(v_empate.replace('%',''))
            
            dados_jogo["probabilidades"] = {
                "vitoria_casa": v_casa,
                "empate": v_empate,
                "dupla_chance_casa": f"{p_casa + p_empate}%"
            }

        return dados_jogo
    except Exception as e:
        return {"url": url, "erro": "Bloqueio ou Timeout ao carregar elementos."}

async def executar():
    async with async_playwright() as p:
        # Launch com 'channel: chrome' ajuda a parecer menos um robô
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        
        links = ["https://footystats.org/spain/deportivo-alaves-vs-valencia-cf-h2h-stats"]
        resultados = []

        for l in links:
            res = await analisar_partida(page, l)
            resultados.append(res)

        print("\n=== JSON FINAL DE VALIDAÇÃO ===")
        print(json.dumps(resultados, indent=4, ensure_ascii=False))
        await browser.close()

if __name__ == "__main__":
    asyncio.run(executar())
    
