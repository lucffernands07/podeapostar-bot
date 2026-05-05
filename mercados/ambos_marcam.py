import re

def verificar_btts(s):
    """
    Regra Ambas Marcam:
    1. BTTS no último jogo individual da Casa.
    2. BTTS no último jogo individual de Fora.
    3. Pelo menos um BTTS nos últimos dois confrontos diretos (H2H).
    
    Porcentagem:
    - 100% se os dois últimos H2H foram BTTS.
    - 80% se apenas um dos dois últimos H2H foi BTTS.
    """
    try:
        def tem_btts(placar):
            if not placar: 
                return False
            # Extrai apenas os dígitos para garantir a comparação
            nums = re.findall(r'\d+', str(placar))
            return len(nums) >= 2 and int(nums[0]) > 0 and int(nums[1]) > 0

        # --- COLETA DOS PLACARES ENVIADOS PELO MAIN ---
        p_casa = s.get("t1_placar_1")       # Último individual Casa
        p_fora = s.get("t2_placar_1")       # Último individual Fora
        p_h2h1 = s.get("h2h_placar_1")      # H2H mais recente
        p_h2h2 = s.get("h2h_placar_2")      # H2H segundo mais recente

        # --- VALIDAÇÃO DOS 3 CRITÉRIOS OBRIGATÓRIOS ---
        
        # Passo 1 e 2: Últimos jogos individuais
        casa_passou = tem_btts(p_casa)
        fora_passou = tem_btts(p_fora)
        
        # Passo 3: Confronto Direto (pelo menos um nos últimos dois)
        h2h1_btts = tem_btts(p_h2h1)
        h2h2_btts = tem_btts(p_h2h2)
        h2h_passou = h2h1_btts or h2h2_btts

        # --- VEREDITO FINAL ---
        if casa_passou and fora_passou and h2h_passou:
            # Se ambos os confrontos diretos foram BTTS -> Força Máxima
            if h2h1_btts and h2h2_btts:
                return "100%"
            
            # Se apenas um foi BTTS -> Segurança
            return "80%"
            
        # Se falhar em qualquer um dos 3 passos, o mercado é descartado
        return None

    except Exception as e:
        # Em caso de erro na raspagem ou dados vazios, ignora o jogo por segurança
        print(f"Erro ao processar Ambas Marcam: {e}")
        return None
        
