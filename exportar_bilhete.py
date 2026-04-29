import csv
import os
import re
from datetime import datetime

def salvar_lista_geral(lista_jogos):
    """
    Recebe a lista de jogos do dia e salva em um CSV para controle de Green/Red.
    """
    if not lista_jogos:
        print("⚠️ Sem dados para exportar.")
        return

    arquivo = 'historico_previsoes.csv'
    # Verifica se o arquivo já existe para não repetir o cabeçalho
    file_exists = os.path.isfile(arquivo)
    
    try:
        with open(arquivo, 'a', newline='', encoding='utf-8-sig') as f:
            campos = ['data', 'horario', 'liga', 'time_casa', 'time_fora', 'mercado', 'porcentagem', 'odd', 'resultado_real']
            writer = csv.DictWriter(f, fieldnames=campos, delimiter=';')
            
            if not file_exists:
                writer.writeheader()
            
            for j in lista_jogos:
                # Extrai apenas o número da porcentagem (ex: 85)
                pct_match = re.search(r'\((\d+)%\)', j['mercado'])
                porcentagem = pct_match.group(1) if pct_match else ""
                
                # Limpa o texto do mercado para a planilha (remove a parte da porcentagem)
                mercado_limpo = re.sub(r'\s*\(\d+%\)', '', j['mercado']).strip()

                writer.writerow({
                    'data': datetime.now().strftime("%d/%m/%Y"),
                    'horario': j['horario'],
                    'liga': j['liga'],
                    'time_casa': j['time_casa'],
                    'time_fora': j['time_fora'],
                    'mercado': mercado_limpo,
                    'porcentagem': porcentagem,
                    'odd': j['odd'],
                    'resultado_real': '' # Espaço para você preencher o Green/Red
                })
        print(f"✅ Dados exportados com sucesso para {arquivo}")
    except Exception as e:
        print(f"❌ Erro ao salvar CSV: {e}")
