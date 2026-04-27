def verificar_vitoria_casa(s):
    # --- REGRA EXCLUSIVA: DOMÍNIO EM CASA (H2H) ---
    # Verifica se há histórico suficiente (mínimo 5 jogos)
    if s["h2h_jogos"] >= 5:
        vitorias_h2h_casa = s["h2h_vitorias_t1"]
        total_jogos = s["h2h_jogos"]
        
        # MÍNIMO 4 VITÓRIAS EM 5 OU 6 JOGOS
        # Diferente da Dupla Chance, aqui NÃO somamos os empates. 
        # É vitória seca (ML).
        
        if vitorias_h2h_casa >= 4:
            if vitorias_h2h_casa >= 6: 
                pct = "100%"
            elif vitorias_h2h_casa == 5: 
                pct = "100%" if total_jogos == 5 else "85%"
            else: 
                # Caso de 4 vitórias em 5 ou 6 jogos
                pct = "80%" if total_jogos == 5 else "70%"
                
            return [f"Vitória Casa 🔥 ({pct})"]

    # Se não bater o critério de domínio de vitórias, não envia nada
    return []
