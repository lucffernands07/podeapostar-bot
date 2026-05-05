import re

def extrair_btts_de_placares(lista_placares):
    """
    Recebe uma lista de strings ['1:1', '2:0', ...] e retorna 
    quantas vezes deu Ambas Marcam (ambos > 0).
    """
    sucessos = 0
    for placar in lista_placares:
        nums = re.findall(r'\d+', placar)
        if len(nums) >= 2:
            if int(nums[0]) > 0 and int(nums[1]) > 0:
                sucessos += 1
    return sucessos

def verificar_regra_ambos_marcam(dados):
    """
    Aplica a tua regra:
    1. Mínimo 4 de 5 nos últimos jogos de cada equipa.
    2. Pelo menos 1 Ambas Marcam nos últimos 2 do CD.
    """
    try:
        # Calcula a taxa de sucesso baseada nos placares reais raspados
        sucessos_casa = extrair_btts_de_placares(dados['ultimos_5_casa'])
        sucessos_fora = extrair_btts_de_placares(dados['ultimos_5_fora'])
        
        # Passo 1: Regra 4 de 5
        cond_4_de_5 = sucessos_casa >= 4 and sucessos_fora >= 4
        
        # Passo 2: H2H (Últimos 2 confrontos)
        h2h_sucessos = extrair_btts_de_placares(dados['h2h_2_jogos'])
        cond_h2h = h2h_sucessos >= 1

        if cond_4_de_5 and cond_h2h:
            # Se for 5/5 em ambos, retorna 100%, senão 85% (conforme tua preferência)
            pct = "100%" if (sucessos_casa == 5 and sucessos_fora == 5) else "85%"
            return f"AMBAS MARCAM ({pct})"
        
        return None
    except Exception as e:
        return f"Erro na análise: {e}"

# --- SIMULAÇÃO DA RASPAGEM DO LINK ENVIADO ---
# Sporting Cristal x Palmeiras
dados_raspados = {
    "jogo": "Sporting Cristal vs Palmeiras",
    # Simulando os 5 últimos jogos reais (Placares)
    "ultimos_5_casa": ["2:1", "1:1", "3:2", "1:2", "2:2"], # 5 de 5 (BTTS)
    "ultimos_5_fora": ["1:2", "0:1", "1:1", "2:1", "1:1"], # 4 de 5 (BTTS)
    # 2 últimos Confrontos Diretos (CD)
    "h2h_2_jogos": ["1:1", "0:2"] # Teve 1 BTTS
}

print(f"🧪 Testando Regra no jogo: {dados_raspados['jogo']}")
print("-" * 40)

resultado = verificar_regra_ambos_marcam(dados_raspados)

if resultado:
    print(f"✅ JOGO APROVADO: {resultado}")
else:
    print("❌ JOGO REPROVADO: Não atingiu os critérios de 4/5 ou H2H.")

# Relatório para conferência
c = extrair_btts_de_placares(dados_raspados['ultimos_5_casa'])
f = extrair_btts_de_placares(dados_raspados['ultimos_5_fora'])
h = extrair_btts_de_placares(dados_raspados['h2h_2_jogos'])

print(f"\nEstatísticas calculadas:")
print(f" - Casa BTTS: {c}/5")
print(f" - Fora BTTS: {f}/5")
print(f" - H2H BTTS: {h}/2")
