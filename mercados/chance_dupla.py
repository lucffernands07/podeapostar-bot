def verificar_chance_dupla(s):
    # --- REGRA EXCLUSIVA: CONFRONTO DIRETO (H2H) ---
    # Verifica se há histórico suficiente (mínimo 5 jogos)
    if s["h2h_jogos"] >= 5:
        sucesso_h2h_t1 = s["h2h_vitorias_t1"] + s["h2h_empates"]
        sucesso_h2h_t2 = s["h2h_vitorias_t2"] + s["h2h_empates"]
        
        # MÍNIMO 4 SUCESSOS (Vitória ou Empate)
        
        # Lógica para o Time da Casa (1X)
        if sucesso_h2h_t1 >= 4:
            # Porcentagem baseada em 5 ou 6 jogos
            if sucesso_h2h_t1 >= 6: pct = "100%"
            elif sucesso_h2h_t1 == 5: pct = "85%"
            else: pct = "70%" # Caso seja 4/5 ou 4/6
            return [f"1X 🔥 ({pct})"]
            
        # Lógica para o Time de Fora (2X)
        if sucesso_h2h_t2 >= 4:
            if sucesso_h2h_t2 >= 6: pct = "100%"
            elif sucesso_h2h_t2 == 5: pct = "85%"
            else: pct = "70%" # Caso seja 4/5 ou 4/6
            return [f"2X 🔥 ({pct})"]

    # Se não atingir o mínimo de 4/5 no H2H, não envia nada
    return []
    
