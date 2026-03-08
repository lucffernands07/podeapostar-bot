import asyncio
import json
from playwright.async_api import async_playwright

async def analisar_footystats():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = "https://footystats.org/spain/deportivo-alaves-vs-valencia-cf-h2h-stats"
        
        print(f"🚀 Acessando FootyStats: {url}")
        await page.goto(url, wait_until="domcontentloaded")

        analise = {
            "partida": "Valencia CF vs Deportivo Alavés",
            "mercados": {},
            "probabilidades": {}
        }

        try:
            # 1. Capturar BTTS e Over Gols (Pelas classes grid-item)
            # Buscamos todos os blocos de estatísticas fortes
            stats = page.locator(".stat-strong")
            count = await stats.count()
            
            for i in range(count):
                texto = await stats.nth(i).inner_text()
                # O texto vem como '67%BTTS' ou '76%Over 1.5'
                if "BTTS" in texto:
                    analise["mercados"]["BTTS"] = texto.replace("BTTS", "").strip()
                elif "Over 1.5" in texto:
                    analise["mercados"]["Over_1_5"] = texto.replace("Over 1.5", "").strip()
                elif "Over 2.5" in texto:
                    analise["mercados"]["Over_2_5"] = texto.replace("Over 2.5", "").strip()

            # 2. Capturar Probabilidades de Vitória (Comparison Bar)
            # O Valencia é o primeiro (winner) e o empate é o segundo (draw)
            win_valencia = await page.locator(".bar-item.winner").first.inner_text()
            draw_prob = await page.locator(".bar-item.draw").first.inner_text()
            
            analise["probabilidades"] = {
                "vitoria_valencia": win_valencia.strip(),
                "empate": draw_prob.strip(),
                "dupla_chance_valencia": f"{int(win_valencia.replace('%','')) + int(draw_prob.replace('%',''))}%"
            }

            # --- VALIDAÇÃO DAS SUAS REGRAS ---
            btts_val = int(analise["mercados"]["BTTS"].replace("%",""))
            
            analise["veredito"] = {
                "btts_aprovado": btts_val >= 60, # Sua regra de 4/5 (80%) ou ajuste para 60%
                "seguranca": "Valencia ou Empate" if int(analise["probabilidades"]["dupla_chance_valencia"].replace("%","")) >= 60 else "Risco"
            }

        except Exception as e:
            analise["erro"] = str(e)

        print("\n=== JSON VALIDADO (FOOTYSTATS) ===")
        print(json.dumps(analise, indent=4, ensure_ascii=False))
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(analis_footystats())
            
