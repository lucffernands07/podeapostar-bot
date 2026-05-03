import os
import sys
import time

# Ajuste para importar o odds.py que está na raiz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import configurar_driver
import odds

def testar_jogo_novorizontino():
    # ID real do jogo Novorizontino x Avaí
    id_jogo = "8pNsVvYg" 
    
    print("🚀 Iniciando Teste de Odds - Segunda Linha (Betano)")
    print(f"🏟️ Jogo: Novorizontino x Avaí | ID: {id_jogo}")
    print("-" * 50)
    
    driver = configurar_driver()
    
    try:
        # Chama a função que acabamos de consolidar
        start_time = time.time()
        resultados = odds.capturar_todas_as_odds(driver, id_jogo)
        end_time = time.time()
        
        print(f"\n📊 RESULTADOS CAPTURADOS (Tempo: {int(end_time - start_time)}s):")
        print("-" * 50)
        
        for mercado, valor in resultados.items():
            status = "✅ OK" if valor != "N/A" else "❌ FALHOU"
            print(f"{status} | {mercado.ljust(15)} : {valor}")
            
        print("-" * 50)
        
        # Validação extra para o seu main.py
        if resultados["GOLS_15"] != "N/A":
            print("💎 Sucesso: Mercado de Gols agora está legível!")
        else:
            print("⚠️ Alerta: Gols ainda retornaram N/A. Verifique se as odds abriram no site.")

    except Exception as e:
        print(f"❌ Erro Crítico no Teste: {e}")
    finally:
        driver.quit()
        print("\n🏁 Teste finalizado.")

if __name__ == "__main__":
    testar_jogo_novorizontino()
    
