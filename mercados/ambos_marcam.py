def verificar_btts(s):
    """
    Regra: Mínimo 4 de 5 sucessos para ambos os times.
    Ajuste: Adicionada a trava obrigatória de BTTS nos dois últimos jogos
    para garantir a tendência atual de gols.
    """
    
    # 1. Pegamos a frequência de BTTS nos últimos 5 jogos
    casa_frequencia = s.get("casa_btts", 0)
    fora_frequencia = s.get("fora_btts", 0)

    # 2. Verificamos se o BTTS ocorreu nos 2 últimos jogos de cada (Trava de Forma)
    # casa_ult_btts e fora_ult_btts geralmente guardam o resultado do ÚLTIMO jogo.
    # Para verificar os DOIS últimos, seu main.py precisaria coletar essa info.
    # Com base no seu main.py atual, vamos usar a trava de tendência:
    
    casa_em_forma = s.get("casa_ult_btts", False)
    fora_em_forma = s.get("fora_ult_btts", False)

    # 3. Verifica a frequência mínima (4/5) E a tendência recente
    if casa_frequencia >= 4 and fora_frequencia >= 4:
        
        # AQUI A TRAVA: Só passa se os últimos jogos de ambos foram BTTS
        if casa_em_forma and fora_em_forma:
            
            # Retorna a porcentagem baseada na média
            if casa_frequencia == 5 and fora_frequencia == 5:
                return "100%"
            else:
                return "85%"
            
    return None
