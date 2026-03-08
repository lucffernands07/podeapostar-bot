import asyncio
import json
from playwright.async_api import async_playwright

async def analisar_partida(page, url):
    """Extrai dados de qualquer link H2H do FootyStats"""
    try:
        # Aumentamos o timeout para garantir o carregamento em servidores mais lentos
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
        dados_jogo = {"url": url}
        
        # 1. Capturar Nome dos Times (do Título ou H1)
        dados_jogo["partida"] = await page.locator("h1").inner_text()

        # 2. Capturar BTTS e Over Gols (Pelas classes que você enviou)
        stats = page.locator(".stat-strong")
        count = await stats.count()
        for i in range(count):
            texto = await stats.nth(i).inner_text()
            if "BTTS" in texto:
                dados_jogo["BTTS"] = texto.replace("BTTS", "").strip()
            elif "Over 1.5" in texto:
                dados_jogo["Over_1_5"] = texto.replace("Over 1.5", "").strip()
            elif "Over 2.5" in texto:
                dados_jogo["Over_2_5"] = texto.replace("Over 2.5", "").strip()

        # 3. Capturar Probabilidades (Comparison Bar)
        # Primeiro item é a vitória do mandante, segundo é o empate
        win_a = await page.locator(".bar-item.winner").first.inner_text()
        draw = await page.locator(".bar-item.draw").first.inner_text()
        
        v_win = int(win_a.replace('%',''))
        v_draw = int(draw.replace('%',''))
        
        dados_jogo["probabilidades"] = {
            "vitoria_casa": f"{v_win}%",
            "empate": f"{v_draw}%",
            "dupla_chance_casa": f"{v_win + v_draw}%"
        }
        
        return dados_jogo
    except Exception as e:
        return {"url": url, "erro": str(e)}

async def executar_script():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # LISTA DE JOGOS: Basta adicionar os links do dia aqui
        links_do_dia = [
            "https://footystats.org/spain/deportivo-alaves-vs-valencia-cf-h2h-stats",
            # "adicione_outro_link_aqui"
        ]

        relatorio_final = []

        for link in links_do_dia:
            print(f"🧐 Analisando partida: {link}")
            resultado = await analisar_partida(page, link)
            relatorio_final.append(resultado)

        print("\n=== JSON FINAL DE VALIDAÇÃO ===")
        print(json.dumps(relatorio_final, indent=4, ensure_ascii=False))
        
        await browser.close()

if __name__ == "__main__":
    # Corrigido: Agora o nome da função bate com o definido acima
    asyncio.run(executar_script())
