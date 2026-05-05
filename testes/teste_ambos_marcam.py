import re

def verificar_btts_teste(s):
    try:
        def tem_btts(placar):
            nums = re.findall(r'\d+', placar)
            return len(nums) >= 2 and int(nums[0]) > 0 and int(nums[1]) > 0

        # --- CONDIÇÃO OBRIGATÓRIA (OS 3 PASSOS) ---
        
        # 1. BTTS no último jogo individual da Casa
        casa_ultimo_btts = tem_btts(s.get("t1_placar_1", "0:0"))
        
        # 2. BTTS no último jogo individual de Fora
        fora_ultimo_btts = tem_btts(s.get("t2_placar_1", "0:0"))
        
        # 3. Pelo menos um BTTS nos últimos 2 do Confronto Direto (CD)
        h2h_btts = tem_btts(s.get("h2h_placar_1", "0:0")) or tem_btts(s.get("h2h_placar_2", "0:0"))

        # GATILHO DE ENTRADA: Precisa dos 3
        if casa_ultimo_btts and fora_ultimo_btts and h2h_btts:
            
            # --- FILTRO DE PORCENTAGEM (SUA REGRA DE SUCESSO 4/5) ---
            # Se além de bater o último, eles têm frequência alta nos últimos 5
            casa_freq = s.get("casa_btts", 0)
            fora_freq = s.get("fora_btts", 0)
            
            if casa_freq >= 4 and fora_freq >= 4:
                return "100%"
            return "85%"
            
        return None # Se falhar em qualquer um dos 3 passos, ignora o jogo
    except:
        return None

# --- CENÁRIOS PARA VALIDAR ---
testes = [
    {
        "nome": "✅ APROVADO (Bateu os 3 passos + Frequência alta)",
        "dados": {
            "t1_placar_1": "2:1", "t2_placar_1": "1:1", # Últimos jogos
            "h2h_placar_1": "0:0", "h2h_placar_2": "2:2", # H2H
            "casa_btts": 4, "fora_btts": 4 # Frequência
        }
    },
    {
        "nome": "❌ REPROVADO (Casa não teve BTTS no último)",
        "dados": {
            "t1_placar_1": "2:0", "t2_placar_1": "1:1", 
            "h2h_placar_1": "1:1", "h2h_placar_2": "1:1",
            "casa_btts": 5, "fora_btts": 5
        }
    },
    {
        "nome": "❌ REPROVADO (H2H sem BTTS recente)",
        "dados": {
            "t1_placar_1": "1:1", "t2_placar_1": "1:1", 
            "h2h_placar_1": "1:0", "h2h_placar_2": "2:0",
            "casa_btts": 5, "fora_btts": 5
        }
    }
]

print("🧪 TESTANDO LOGICA: ULTIMOS + H2H\n" + "="*40)
for t in testes:
    res = verificar_btts_teste(t['dados'])
    print(f"{t['nome']} -> Resultado: {res}")
    
