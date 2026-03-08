import os
import asyncio
from playwright.async_api import async_playwright

async def run():
    # Chaves de ambiente
    api_key = os.getenv("ZENROWS_KEY")
    url_jogo = "https://footystats.org/brazil/se-palmeiras-vs-gremio-novorizontino-h2h-stats"
    
    # Endpoint corrigido para evitar erro de certificado (api.zenrows.com)
    ws_endpoint = f"wss://api.zenrows.com/v1/playwright?apikey={api_key}&js_render=true&wait_for=.stat-strong"

    async with async_playwright() as pw:
        print("🚀 Conectando ao navegador remoto da ZenRows...")
        try:
            # Conexão via CDP (Chrome DevTools Protocol)
            browser = await pw.chromium.connect_over_cdp(ws_endpoint)
            
            # Criamos o contexto ignorando erros de HTTPS/SSL
            context = await browser.new_context(ignore_https_errors=True)
            page = await context.new_page()

            print(f"📡 Acedendo a: {url_jogo}")
            await page.goto(url_jogo, wait_until="networkidle")
            
            # Espera até que as estatísticas (como o 80%) estejam visíveis na página
            print("⏳ Aguardando renderização das estatísticas...")
            await page.wait_for_selector(".stat-strong", timeout=30000)

            # Extração direta via JavaScript dentro do navegador
            dados = await page.evaluate('''() => {
                const resultados = {
                    "o15": "0%", "o25": "0%", "o35": "0%", 
                    "btts": "0%", "cs_pal": "0%", "cs_nov": "0%"
                };
                
                const itens = document.querySelectorAll('.grid-item');
                
                itens.forEach(item => {
                    const statStrong = item.querySelector('.stat-strong');
                    if (!statStrong) return;

                    // Captura apenas o texto do valor (ex: 80%)
                    const valor = statStrong.childNodes[0].textContent.trim();
                    const mercado = item.querySelector('span') ? item.querySelector('span').innerText : "";
                    const subTexto = item.querySelector('.stat-text') ? item.querySelector('.stat-text').innerText : "";

                    if (mercado.includes("Over 1.5")) resultados["o15"] = valor;
                    if (mercado.includes("Over 2.5")) resultados["o25"] = valor;
                    if (mercado.includes("Over 3.5")) resultados["o35"] = valor;
                    if (mercado.includes("BTTS")) resultados["btts"] = valor;
                    
                    if (mercado.includes("Clean Sheets")) {
                        if (subTexto.includes("Palmeiras")) resultados["cs_pal"] = valor;
                        if (subTexto.includes("Novorizontino")) resultados["cs_nov"] = valor;
                    }
                });
                return resultados;
            }''')

            # Exibição dos resultados no log do GitHub Actions
            print("\n📊 DADOS EXTRAÍDOS COM SUCESSO:")
            print(f"📍 Over 1.5: {dados['o15']}")
            print(f"📍 Over 2.5: {dados['o25']}")
            print(f"📍 Over 3.5: {dados['o35']}")
            print(f"📍 BTTS: {dados['btts']}")
            print(f"📍 Clean Sheets Palmeiras: {dados['cs_pal']}")
            print(f"📍 Clean Sheets Novorizontino: {dados['cs_nov']}")

            # Validação da regra de segurança (80%)
            o15_int = int(dados['o15'].replace('%', ''))
            if o15_int >= 80:
                print(f"\n✅ JOGO APROVADO: Segurança de {o15_int}% no Over 1.5.")
            else:
                print(f"\n⚠️ JOGO REPROVADO: Apenas {o15_int}% no Over 1.5.")

            await browser.close()
            print("\n🏁 Processo concluído.")

        except Exception as e:
            print(f"\n❌ ERRO DURANTE A EXECUÇÃO: {str(e)}")

if __name__ == "__main__":
    asyncio.run(run())
            
