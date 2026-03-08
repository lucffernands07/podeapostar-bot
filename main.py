async def capturar_dados_dicasbet(page, time_nome, url):
    await page.goto(url, wait_until="domcontentloaded")
    
    # 1. Busca pelo nome do time
    await page.fill('input[placeholder*="Buscar por Time"]', time_nome)
    await page.keyboard.press("Enter")
    
    # 2. SELECIONAR "ÚLTIMOS 5 JOGOS" (Crucial conforme seu print)
    # O robô clica no dropdown e escolhe a opção de 5 jogos para ativar a porcentagem
    await page.select_option('select:near(:text("Selecionar Número de Jogos"))', label="Últimos 5 jogos")
    
    # 3. FILTRAR "JOGOS EM CASA" (Para o Valencia aparecer com 60%)
    await page.click('text="Jogos em Casa"')
    await page.wait_for_timeout(2000) 

    # 4. CAPTURA DO VALOR
    # Buscamos a linha do Valencia que agora exibe "3/5" e "60%"
    dados = await page.locator("tr:has-text('Valencia')").first.inner_text()
    return dados
    
