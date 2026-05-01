import os
import time
import re
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Importações originais
from ligas import COMPETICOES
from mercados import gols, ambos_marcam, vitoria_casa
# Importação do Novo Módulo de Teste
import teste_chance_dupla 
import odds  
import bingo357  
import links

def enviar_telegram(mensagem, chat_id_destino):
    token = os.getenv('TELEGRAM_TOKEN')
    if not token or not chat_id_destino: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(url, data={"chat_id": chat_id_destino, "text": mensagem, "parse_mode": "Markdown", "disable_web_page_preview": True})
    except Exception as e: print(f"Erro Telegram: {e}")

# ... (Mantenha as funções configurar_driver e pegar_estatisticas_h2h do seu main.py original) ...

def main():
    # ... (Parte inicial da raspagem igual ao seu main.py) ...
    
    # Onde chamamos os filtros, usamos o novo:
    res_cd = teste_chance_dupla.verificar_chance_dupla(s) 
    
    # --- PROCESSAMENTO E ENVIO FINAL (RESTRITO AO SEU ID) ---
    if lista_para_filtros:
        lista_para_filtros.sort(key=lambda x: (x['horario'], x['liga']))
        
        # Montagem das mensagens
        itens_listao = [f"⏱️ {j['horario']} | {j['liga']}\n🏟️ {j['time_casa']} x {j['time_fora']}\n🔶 {j['mercado']} | Odd: {j['odd']}" for j in lista_para_filtros]
        texto_listao = "🧪 *[AMBIENTE DE TESTE]*\n🎫 *LISTÃO GERAL*\n\n" + "\n\n---\n\n".join(itens_listao)
        
        novos_bilhetes = bingo357.montar_bilhetes_estrategicos(lista_para_filtros)
        cache_links = {f"{j['time_casa']}x{j['time_fora']}": j.get("link_betano") for j in lista_para_filtros if j.get("link_betano")}
        texto_bingos = bingo357.formatar_para_telegram(novos_bilhetes, cache_links)

        # SEU ID PESSOAL (Configurado no GitHub Secrets)
        meu_chat_id = os.getenv('CHAT_ID') 

        if meu_chat_id:
            # Envia o listão apenas para você
            enviar_telegram(texto_listao, meu_chat_id)
            
            # Envia os bingos (gerados com a regra nova) apenas para você
            if texto_bingos:
                enviar_telegram("🧪 *[BINGOS - REGRA NOVA]*\n\n" + texto_bingos, meu_chat_id)
            
            print("✅ Relatórios de teste enviados para o Telegram pessoal.")
    else:
        print("⚠️ A nova regra de teste não encontrou jogos compatíveis hoje.")

if __name__ == "__main__":
    main()
