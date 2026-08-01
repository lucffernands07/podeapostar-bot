# mercados/vitorias.py

def verificar_vitorias(stats):
    """
    Regras de Vitória Casa e Vitória Fora (Recorte Casa/Fora - Mínimo 4/5):
    
    - Vitória Casa: Mandante com >= 4 vitórias em 5 jogos em casa 
                    AND Visitante com <= 1 vitória em 5 jogos fora.
    - Vitória Fora: Visitante com >= 4 vitórias em 5 jogos fora 
                    AND Mandante com <= 1 vitória em 5 jogos em casa.
    """
    retorno = []
    
    # Vitórias filtradas do novo raspagem_h2h (Casa em Casa / Visitante Fora)
    vitorias_casa = stats.get("casa_vitorias_recente", 0)
    vitorias_fora = stats.get("fora_vitorias_recente", 0)
    
    # -----------------------------------------------------------------
    # 🏠 VITÓRIA CASA (Mandante forte em casa vs Visitante fraco fora)
    # -----------------------------------------------------------------
    if vitorias_casa >= 4 and vitorias_fora <= 1:
        pct = "100%" if (vitorias_casa == 5 and vitorias_fora == 0) else "85%"
        retorno.append(f"Vitória Casa ({pct})")
        
    # -----------------------------------------------------------------
    # ✈️ VITÓRIA FORA (Visitante forte fora vs Mandante fraco em casa)
    # -----------------------------------------------------------------
    if vitorias_fora >= 4 and vitorias_casa <= 1:
        pct = "100%" if (vitorias_fora == 5 and vitorias_casa == 0) else "85%"
        retorno.append(f"Vitória Fora ({pct})")
        
    return retorno
    
