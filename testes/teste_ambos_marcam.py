import re

def verificar_btts_regra_final(s):
    try:
        def tem_btts(placar):
            if not placar: return False
            nums = re.findall(r'\d+', str(placar))
            return len(nums) >= 2 and int(nums[0]) > 0 and int(nums[1]) > 0

        # --- COLETA DOS DADOS ---
        p_casa = s.get("t1_placar_1")       # Último individual Casa
        p_fora = s.get("t2_placar_1")       # Último individual Fora
        p_h2h1 = s.get("h2h_placar_1")      # H2H mais recente
        p_h2h2 = s.get("h2h_placar_2")      # H2H segundo mais recente

        # --- VALIDAÇÃO DOS 3 PASSOS OBRIGATÓRIOS ---
        casa_passou = tem_btts(p_casa)
        fora_passou = tem_btts(p_fora)
        
        h2h1_btts = tem_btts(p_h2h1)
        h2h2_btts = tem_btts(p_h2h2)
        h2h_passou = h2h1_btts or h2h2_btts

        # --- LOG DETALHADO (CONFORME VOCÊ PEDIU) ---
        print(f"   Casa (Último): {p_casa} -> {'✅ passou' if casa_passou else '❌ falhou'}")
        print(f"   Fora (Último): {p_fora} -> {'✅ passou' if fora_passou else '❌ falhou'}")
        print(f"   H2H (Últimos 2): {p_h2h1} e {p_h2h2} -> {'✅ passou' if h2h_passou else '❌ falhou'}")

        # --- GATILHO FINAL E PORCENTAGEM ---
        if casa_passou and fora_passou and h2h_passou:
            # Se os dois H2H foram BTTS -> 100%
            if h2h1_btts and h2h2_btts:
                return "100%"
            # Se apenas um do H2H foi BTTS -> 80%
            return "80%"
            
        return None
    except Exception as e:
        return f"Erro: {e}"

# --- CENÁRIO REAL: SPORTING CRISTAL vs PALMEIRAS ---
dados_palmeiras = {
    "t1_placar_1": "2:2",   # Sporting Cristal vs Cusco
    "t2_placar_1": "1:1",   # Palmeiras vs Santos
    "h2h_placar_1": "2:1",  # Palmeiras 2x1 Cristal (BTTS)
    "h2h_placar_2": "6:0"   # Palmeiras 6x0 Cristal (Não BTTS)
}

# --- OUTROS CENÁRIOS PARA VALIDAÇÃO ---
testes = [
    {
        "nome": "PALMEIRAS vs SPORTING CRISTAL (Dados do seu Print)",
        "dados": dados_palmeiras
    },
    {
        "nome": "EXEMPLO 100% (BTTS em tudo)",
        "dados": {
            "t1_placar_1": "3:1", "t2_placar_1": "1:2", 
            "h2h_placar_1": "1:1", "h2h_placar_2": "2:2"
        }
    },
    {
        "nome": "EXEMPLO REPROVADO (Sem BTTS no H2H)",
        "dados": {
            "t1_placar_1": "1:1", "t2_placar_1": "1:1", 
            "h2h_placar_1": "1:0", "h2h_placar_2": "2:0"
        }
    }
]

print("🧪 TESTANDO REGRA: ULTIMO INDIVIDUAL + 2 H2H\n" + "="*50)
for t in testes:
    print(f"\n🔹 Analisando: {t['nome']}")
    res = verificar_btts_regra_final(t['dados'])
    status = f"⭐ RESULTADO FINAL: {res}" if res else "🚫 RESULTADO FINAL: Ignorado (Não cumpre os 3 critérios)"
    print(status)
    print("-" * 50)
    
