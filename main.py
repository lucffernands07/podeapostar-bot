import asyncio
import json
from playwright.async_api import async_playwright

async def testar_analise_valencia():
    async with async_playwright() as p:
        # Launch do navegador (headless=False se quiser ver o robô trabalhando)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = await context.new_page()

        # IDs para o teste (Valencia: 2828 | Alavés: 2885)
        # Link de comparação conforme seu print
        url_sofa = "https://www.sofascore.com/pt/football/team/compare?ids=2828%2C2885"
        url_espn = "https://www.espn.com.br/futebol/time/resultados/_/id/2594" # ID ESPN Valencia

        relatorio_bruto = {
            "time": "Valencia",
            "origem_sofascore": {},
            "origem_espn": {"ultimos_5_jogos": []},
            "validacao_regras": {}
        }

        print("🔍 Coletando dados de Elite no SofaScore...")
        try:
            await page.goto(url_sofa, wait_until="networkidle", timeout=60000)
            
            # Mapeando os dados das suas imagens
            relatorio_bruto["origem_sofascore"] = {
                "chances_criadas_jogo": await page.locator('text="Grandes chances de gol por jogo" >> xpath=../..').get_by_role("cell").nth(0).inner_text(),
                "chutes_certos_jogo": await page.locator('text="Chutes certos por jogo" >> xpath=../..').get_by_role("cell").nth(0).inner_text(),
                "escanteios_media": await page.locator('text="Escanteios" >> xpath=../..').get_by_role("cell").nth(0).inner_text(),
                "jogos_sem_sofrer_gols": await page.locator('text="Jogos sem sofrer gols" >> xpath=../..').get_by_role("cell").nth(0).inner_text(),
                "gols_sofridos_total": await page.locator('text="Gols sofridos" >> xpath=../..').get_by_role("cell").nth(0).inner_text()
            }
        except Exception as e:
            relatorio_bruto["origem_sofascore"]["erro"] = str(e)

        print("📅 Coletando Forma Recente na ESPN (Regra 5/5)...")
        try:
            await page.goto(url_espn, wait_until="networkidle")
            rows = await page.query_selector_all(".Table__TR--sm")
            for row in rows[:5]:
                cols = await row.query_selector_all("td")
                if len(cols) >= 3:
                    txt = await cols[2].inner_text()
                    relatorio_bruto["origem_espn"]["ultimos_5_jogos"].append(txt)
        except Exception as e:
            relatorio_bruto["origem_espn"]["erro"] = str(e)

        # --- APLICAÇÃO DAS SUAS REGRAS PARA VALIDAÇÃO ---
        sofa = relatorio_bruto["origem_sofascore"]
        espn = relatorio_bruto["origem_espn"]["ultimos_5_jogos"]

        # Regra 1: Dupla Chance (Baseada em Clean Sheets e Derrotas 0/5)
        derrotas = sum(1 for jogo in espn if "D" in jogo)
        relatorio_bruto["validacao_regras"]["dupla_chance"] = {
            "aprovado": derrotas <= 1 and int(sofa.get("jogos_sem_sofrer_gols", 0)) >= 5,
            "motivo": f"Derrotas recentes: {derrotas} | Clean Sheets: {sofa.get('jogos_sem_sofrer_gols')}"
        }

        # Regra 2: Escanteios (Baseada em Chutes Certos e Escanteios Média)
        escanteios_num = float(sofa.get("escanteios_media", "0").replace(",", "."))
        relatorio_bruto["validacao_regras"]["escanteios"] = {
            "aprovado": escanteios_num >= 5.0,
            "valor_encontrado": escanteios_num
        }

        # Saída do JSON Bruto solicitado
        print("\n=== JSON BRUTO PARA VALIDAÇÃO ===")
        print(json.dumps(relatorio_bruto, indent=4, ensure_ascii=False))
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(testar_analise_valencia())
    
