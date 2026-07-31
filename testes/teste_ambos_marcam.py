import re

def tem_btts(placar):
    """Verifica se ambas as equipes marcaram no placar fornecido (ex: '2:1', '1-1')"""
    if not placar:
        return False
    nums = re.findall(r'\d+', str(placar))
    return len(nums) >= 2 and int(nums[0]) > 0 and int(nums[1]) > 0

def avaliar_ambos_marcam(jogos_casa_em_casa, jogos_fora_fora):
    """
    Avalia a sequência dos últimos 5 jogos:
    - Min 4/5 para ambos os lados -> "Ambas Marcam: Sim" (80% ou 100%)
    - Max 3/5 para ambos os lados -> "Ambas Marcam: Não"
    """
    if len(jogos_casa_em_casa) < 5 or len(jogos_fora_fora) < 5:
        return None, "Dados insuficientes (menos de 5 jogos em algum dos lados)"

    # Conta quantas partidas deram BTTS Sim nos últimos 5 jogos
    btts_casa = sum(1 for p in jogos_casa_em_casa[:5] if tem_btts(p))
    btts_fora = sum(1 for p in jogos_fora_fora[:5] if tem_btts(p))

    # --- REGRA: AMBAS MARCAM SIM ---
    # Requer pelo menos 4/5 em ambos os times
    if btts_casa >= 4 and btts_fora >= 4:
        porcentagem = "100%" if (btts_casa == 5 and btts_fora == 5) else "80%"
        return f"Ambas Marcam: Sim ({porcentagem})", f"Casa: {btts_casa}/5 BTTS | Fora: {btts_fora}/5 BTTS"

    # --- REGRA: AMBAS MARCAM NÃO ---
    # Requer no máximo 3/5 em ambos os times (baixa ocorrência de BTTS nos dois lados)
    if btts_casa <= 3 and btts_fora <= 3:
        porcentagem = "100%" if (btts_casa <= 1 and btts_fora <= 1) else "80%"
        return f"Ambas Marcam: Não ({porcentagem})", f"Casa: {btts_casa}/5 BTTS | Fora: {btts_fora}/5 BTTS"

    return None, f"Fora dos padrões (Casa: {btts_casa}/5 BTTS, Fora: {btts_fora}/5 BTTS)"


# --- CENÁRIOS DE TESTE ---
testes = [
    {
        "nome": "Cenário Ambas Marcam SIM (80%)",
        "casa_em_casa": ["2:1", "1:1", "3:1", "0:1", "2:2"], # 4/5 BTTS
        "fora_fora":     ["1:2", "2:2", "1:1", "3:1", "0:2"]  # 4/5 BTTS
    },
    {
        "nome": "Cenário Ambas Marcam NÃO (Poucos gols de ambos os lados)",
        "casa_em_casa": ["2:0", "1:0", "0:0", "1:1", "3:0"], # 1/5 BTTS
        "fora_fora":     ["0:1", "2:0", "1:1", "0:0", "1:0"]  # 1/5 BTTS
    },
    {
        "nome": "Cenário Inconclusivo (Casa muito alto e Fora mediano)",
        "casa_em_casa": ["2:1", "1:1", "3:1", "2:2", "2:1"], # 5/5 BTTS
        "fora_fora":     ["0:0", "1:0", "2:1", "0:1", "1:0"]  # 1/5 BTTS
    }
]

print("🧪 TESTANDO NOVA REGRA AMBAS MARCAM (CASA/FORA)\n" + "="*55)
for t in testes:
    print(f"\n🔹 {t['nome']}")
    resultado, detalhe = avaliar_ambos_marcam(t["casa_em_casa"], t["fora_fora"])
    if resultado:
        print(f"⭐ MERCADO GERADO: {resultado}")
    else:
        print(f"🚫 DESLOGADO/IGNORADO")
    print(f"📊 Detalhes: {detalhe}")
    print("-" * 55)
    
