import re

def verificar_btts_teste(s):
    try:
        def tem_btts(placar):
            nums = re.findall(r'\d+', placar)
            return len(nums) >= 2 and int(nums[0]) > 0 and int(nums[1]) > 0

        # --- COLETA DE DADOS ---
        p_casa = s.get("t1_placar_1", "0:0")
        p_fora = s.get("t2_placar_1", "0:0")
        p_h2h1 = s.get("h2h_placar_1", "0:0")
        p_h2h2 = s.get("h2h_placar_2", "0:0")

        # --- VALIDAÇÃO DOS PASSOS ---
        casa_passou = tem_btts(p_casa)
        fora_passou = tem_btts(p_fora)
        h2h_passou = tem_btts(p_h2h1) or tem_btts(p_h2h2)

        # --- IMPRESSÃO DOS RESULTADOS DETALHADOS ---
        print(f"   Casa: {p_casa} -> {'✅ passou' if casa_passou else '❌ falhou'}")
        print(f"   Fora: {p_fora} -> {'✅ passou' if fora_passou else '❌ falhou'}")
        print(f"   H2H:  {p_h2h1} e {p_h2h2} -> {'✅ passou' if h2h_passou else '❌ falhou'}")

        # --- GATILHO FINAL ---
        if casa_passou and fora_passou and h2h_passou:
            casa_freq = s.get("casa_btts", 0)
            fora_freq = s.get("fora_btts", 0)
            
            pct = "100%" if (casa_freq >= 4 and fora_freq >= 4) else "85%"
            return pct
            
        return None
    except Exception as e:
        return f"Erro: {e}"

# --- CENÁRIOS PARA VALIDAR ---
testes = [
    {
        "nome": "JOGO APROVADO (Tudo OK)",
        "dados": {
            "t1_placar_1": "3:1", "t2_placar_1": "1:1", 
            "h2h_placar_1": "0:0", "h2h_placar_2": "1:1",
            "casa_btts": 4, "fora_btts": 4
        }
    },
    {
        "nome": "JOGO REPROVADO (Falha no H2H)",
        "dados": {
            "t1_placar_1": "2:1", "t2_placar_1": "1:2", 
            "h2h_placar_1": "1:0", "h2h_placar_2": "2:0",
            "casa_btts": 5, "fora_btts": 5
        }
    }
]

print("🧪 TESTANDO LOGICA: ULTIMOS + H2H\n" + "="*40)
for t in testes:
    print(f"\n🔹 Cenário: {t['nome']}")
    res = verificar_btts_teste(t['dados'])
    status = f"⭐ RESULTADO FINAL: {res}" if res else "🚫 RESULTADO FINAL: Ignorado"
    print(status)
    
