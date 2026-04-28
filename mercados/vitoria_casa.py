def verificar_vitoria_casa(s):
    # --- REGRA EXCLUSIVA: DOMÍNIO EM CASA (H2H) ---
    total_jogos = s.get("h2h_jogos", 0)
    
    # Verifica se há histórico suficiente (mínimo 5 jogos)
    if total_jogos >= 5:
        vitorias_h2h_casa = s.get("h2h_vitorias_t1", 0)
        
        # MÍNIMO 4 VITÓRIAS EM 5 OU 6 JOGOS
        if vitorias_h2h_casa >= 4:
            # Cálculo de porcentagem dinâmica baseada no que foi raspado
            calculo_pct = (vitorias_h2h_casa / total_jogos) * 100
            
            if calculo_pct >= 95: pct = "100%"
            elif calculo_pct >= 80: pct = "80%"
            else: pct = f"{int(calculo_pct)}%"
                
            return [f"Vitória Casa 💎 ({pct})"]

    return []
    
