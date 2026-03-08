import asyncio
import json
from playwright.async_api import async_playwright

async def testar_analise_valencia():
    async with async_playwright() as p:
        # Launch com argumentos para evitar detecção
        browser = await p.chromium.launch(headless=True)
        # Criando um contexto com dimensões de tela real e User-Agent comum
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        url_sofa = "https://www.sofascore.com/pt/football/team/compare?ids=2828%2C2885"
        url_espn = "https://www.espn.com.br/futebol/time/resultados/_/id/2594"

        relatorio_bruto = {
            "time": "Valencia",
            "origem_sofascore": {},
            "origem_espn": {"ultimos_5_jogos": []},
            "validacao_regras": {}
        }

        print("🔍 Coletando dados no SofaScore (Modo Rápido)...")
        try:
            # Mudamos para 'domcontentloaded' que é muito mais rápido
            await page.goto(url_sofa, wait_until="domcontentloaded", timeout=30000)
            # Esperamos um seletor específico da tabela de comparação aparecer
            await page.wait_for_selector('text="Grandes chances de gol por jogo"', timeout=15000)
            
            # Captura de texto usando locators mais precisos para tabelas
            chances = await page.locator('div:has-text("Grandes chances de gol por jogo") + div').first.inner_text()
            chutes = await page.locator('div:has-text("Chutes certos por jogo") + div').first.inner_text()
            escanteios = await page.locator('div:has-text("Escanteios") + div').first.inner_text()
            clean_sheets = await page.locator('div:has-text("Jogos sem sofrer gols") + div').first.inner_text()

            relatorio_bruto["origem_sofascore"] = {
                "chances_criadas_jogo": chances.strip(),
                "chutes_certos_jogo": chutes.strip(),
                "escanteios_media": escanteios.strip(),
                "jogos_sem_sofrer_gols": clean_sheets.strip()
            }
        except Exception as e:
            relatorio_bruto["origem_sofascore"]["erro"] = f"Erro SofaScore: {str(e)}"

        print("📅 Coletando Forma Recente na ESPN...")
        try:
            await page.goto(url_espn, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_selector(".Table__TR--sm", timeout=10000)
            
            rows = await page.query_selector_all(".Table__TR--sm")
            for row in rows[:5]:
                cols = await row.query_selector_all("td")
                if len(cols) >= 3:
                    res = await cols[2].inner_text()
                    relatorio_bruto["origem_espn"]["ultimos_5_jogos"].append(res)
        except Exception as e:
            relatorio_bruto["origem_espn"]["erro"] = f"Erro ESPN: {str(e)}"

        # --- PROCESSAMENTO LOGICO ---
        sofa = relatorio_bruto["origem_sofascore"]
        espn = relatorio_bruto["origem_espn"]["ultimos_5_jogos"]

        if "erro" not in sofa and espn:
            derrotas = sum(1 for j in espn if "D" in j)
            # Converte valores para float para validar regras
            esc_val = float(sofa["escanteios_media"].replace(",", "."))
            
            relatorio_bruto["validacao_regras"] = {
                "dupla_chance_aprovada": derrotas <= 1,
                "escanteios_aprovado": esc_val >= 4.5,
                "analise_final": "BILHETE POSSÍVEL" if derrotas == 0 else "REVISAR"
            }

        print("\n=== JSON BRUTO PARA VALIDAÇÃO ===")
        print(json.dumps(relatorio_bruto, indent=4, ensure_ascii=False))
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(testar_analise_valencia())
    
