def verificar_btts(s):
    """
    Regra: Mínimo 4 de 5 sucessos para ambos os times.
    Ajuste: Removida a trava obrigatória de BTTS nos dois últimos jogos
    para aumentar o volume de entradas em ligas propensas a gols.
    """
    
    # 1. Pegamos a frequência de BTTS nos últimos 5 jogos
    casa_frequencia = s.get("casa_btts", 0)
    fora_frequencia = s.get("fora_btts", 0)

    # 2. Verifica a frequência mínima (4/5 para ambos)
    # Isso garante que os times são propensos a marcar e sofrer
    if casa_frequencia >= 4 and fora_frequencia >= 4:
        
        # 3. Retorna a porcentagem baseada na média (100% ou 85%)
        if casa_frequencia == 5 and fora_frequencia == 5:
            return "100%"
        else:
            return "85%"
            
    return None
    
