import asyncio
from playwright.async_api import async_playwright

async def teste_visual_barcelona():
    async with async_playwright() as p:
        print("🚀 Abrindo navegador e acessando resultados do Barcelona...")
        
        # Lançando o navegador (headless=True para rodar no servidor)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # URL direta dos resultados do Barcelona na ESPN
        url = "https://www.espn.com.br/futebol/time/resultados/_/id/83/esp.barcelona"
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Espera a tabela de resultados carregar no HTML
            print("✅ Página carregada. Lendo a tabela de jogos...")
            
            # Captura as linhas de resultados (classe padrão da ESPN para tabelas)
            rows = await page.query_selector_all(".Table__TR--sm")
            
            gols_marcados = 0
            jogos_over25 = 0
            historico = []

            for row in rows[:5]:  # Analisa os últimos 5 jogos
                cols = await row.query_selector_all("td")
                
                if len(cols) >= 3:
                    data = await cols[0].inner_text()
                    oponente = await cols[1].inner_text()
                    resultado_txt = await cols[2].inner_text() # Ex: "V 4 - 0"
                    
                    # Extrai apenas números e o hífen (ex: 4-0)
                    placar = "".join([c for c in resultado_txt if c.isdigit() or c == "-"])
                    
                    if "-" in placar:
                        gols = placar.split("-")
                        gm = int(gols[0]) # Gols do Barça (ou do time da casa na lista)
                        gr = int(gols[1]) # Gols do Rival
                        total = gm + gr
                        
                        gols_marcados += gm
                        if total >= 3:
                            jogos_over25 += 1
                            
                        historico.append(f"📅 {data} | {oponente} | Placar: {placar} (Total: {total})")

            print("\n--- RESULTADOS ENCONTRADOS NO HTML ---")
            for h in historico:
                print(h)
            
            print("-" * 38)
            print(f"📊 ESTATÍSTICAS PARA O ROBÔ:")
            print(f"   - Total de Gols Marcados: {gols_marcados}")
            print(f"   - Frequência Over 2.5: {jogos_over25}/5")
            
            if gols_marcados >= 7 or jogos_over25 >= 4:
                print("\n🔥 CONCLUSÃO: ATROPELO DETECTADO (+2.5 Gols)")
            else:
                print("\n⚽ CONCLUSÃO: JOGO NORMAL (+1.5 Gols)")

        except Exception as e:
            print(f"❌ Erro na extração: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    # Rodar o loop assíncrono
    asyncio.run(teste_visual_barcelona())
                            
