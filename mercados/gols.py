def verificar_gols(s):
    # Calcula a média baseada nos 5 jogos que você definiu
    ch15 = calcular_chance(s["casa_15"], s["fora_15"])
    ch25 = calcular_chance(s["casa_25"], s["fora_25"])
    
    resultados = []

    # REMOVEMOS A TRAVA casa_ult_sofreu DAQUI
    # Agora o módulo confia na filtragem que a main.py já faz
    if ch15:
        resultados.append(f"+1.5 Gols ({ch15})")
            
    if ch25:
        resultados.append(f"+2.5 Gols ({ch25})")
            
    return resultados
    
