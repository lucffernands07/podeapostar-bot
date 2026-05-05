import re

def verificar_btts(s):
    try:
        def tem_btts(placar):
            if not placar: return False
            # Extrai apenas os números para evitar erro com espaços ou caracteres
            nums = re.findall(r'\d+', str(placar))
            return len(nums) >= 2 and int(nums[0]) > 0 and int(nums[1]) > 0

        # --- 1. COLETA DOS PLACARES REAIS ---
        p_casa = s.get("t1_placar_1")       # Último jogo individual da Casa
        p_fora = s.get("t2_placar_1")       # Último jogo individual de Fora
        p_h2h1 = s.get("h2h_placar_1")      # Confronto Direto mais recente
        p_h2h2 = s.get("h2h_placar_2")      # Segundo confronto direto mais recente

        # --- 2. VALIDAÇÃO DOS 3 CRITÉRIOS OBRIGATÓRIOS ---
        
        # Passo 1: Casa teve BTTS no último individual?
        cond_casa = tem_btts(p_casa)
        
        # Passo 2: Fora teve BTTS no último individual?
        cond_fora = tem_btts(p_fora)
        
        # Passo 3: Pelo menos um dos dois últimos H2H teve BTTS?
        # (Isso garante a entrada no bilhete)
        h2h1_btts = tem_btts(p_h2h1)
        h2h2_btts = tem_btts(p_h2h2)
        cond_h2h = h2h1_btts or h2h2_btts

        # --- 3. DEFINIÇÃO DA PERCENTAGEM E SAÍDA ---
        if cond_casa and cond_fora and cond_h2h:
            # Se passou nos 3 e AMBOS os H2H foram BTTS -> 100%
            if h2h1_btts and h2h2_btts:
                return "100%"
            
            # Se passou nos 3 mas apenas UM do H2H foi BTTS -> 80%
            return "80%"
            
        return None
    except:
        return None
        
