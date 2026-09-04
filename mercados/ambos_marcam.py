"""
REGRAS DE MERCADO - AMBAS MARCAM (VERSÃO AJUSTADA)
- BTTS SIM: Soma de gols do mandante em casa >= 8 E soma de gols do visitante fora >= 8 E visitante fora ganhou (vitória) por >= 3 gols? (Aguarde, vamos detalhar abaixo)
- BTTS NÃO: Caso contrário.
"""

def verificar_btts(s, outros_mercados_aprovados=None, mercados_gols_aprovados=None, odds_jogo=None):
    mercados_aprovados = []
    try:
        if not isinstance(s, dict):
            return mercados_aprovados

        # Lê os placares do último jogo (mandante em casa e visitante fora)[span_0](start_span)[span_0](end_span)
        placar_mandante_casa = s.get("t1_placar_1", "")  # Ex: "2-1[span_1](start_span)"[span_1](end_span)
        placar_visitante_fora = s.get("t2_placar_1", "") # Ex: "0-3[span_2](start_span)"[span_2](end_span)

        gols_mandante_feito, gols_mandante_sofrido = 0, 0
        gols_visitante_sofrido, gols_visitante_feito = 0, 0

        # Quebra o placar do mandante em casa (Gols feitos - Gols sofridos)
        if placar_mandante_casa and "-" in placar_mandante_casa:
            partes = placar_mandante_casa.split("-")
            gols_mandante_feito = int(partes[0].strip())
            gols_mandante_sofrido = int(partes[1].strip())

        # Quebra o placar do visitante fora (Gols sofridos - Gols feitos)[span_3](start_span)[span_3](end_span)
        if placar_visitante_fora and "-" in placar_visitante_fora:
            partes = placar_visitante_fora.split("-")
            gols_visitante_sofrido = int(partes[0].strip()) #[span_4](start_span)[span_4](end_span)
            gols_visitante_feito = int(partes[1].strip())   #[span_5](start_span)[span_5](end_span)

        # Soma total de gols do mandante em casa (feitos + sofridos no último jogo)
        soma_gols_mandante_casa = gols_mandante_feito + gols_mandante_sofrido
        
        # Soma total de gols do visitante fora (feitos + sofridos no último jogo)
        soma_gols_visitante_fora = gols_visitante_feito + gols_visitante_sofrido

        # Condição de vitória do visitante fora (gols feitos > gols sofridos) por diferença de 3 ou mais? 
        # (Ou se refere a gols feitos do visitante fora >= 3? Ajustei para os gols feitos do visitante fora >= 3 baseado na sua frase)
        visitante_condicao_vitoria = (gols_visitante_feito >= 3 and gols_visitante_feito > gols_visitante_sofrido)

        # 🟢 REGRA BTTS SIM:
        # Soma mandante casa >= 8 E Soma visitante fora >= 8 E Visitante fora cumpriu a condição de vitória
        if soma_gols_mandante_casa >= 8 and soma_gols_visitante_fora >= 8 and visitante_condicao_vitoria:
            mercados_aprovados.append({"mercado": "Ambas Marcam: Sim", "tipo": "BTTS_SIM"})
        else:
            # 🔴 SE NÃO, RETORNA BTTS NÃO
            mercados_aprovados.append({"mercado": "Ambas Marcam: Não", "tipo": "BTTS_NAO"})

        return mercados_aprovados

    except Exception as e:
        print(f"      ⚠️ Erro ao processar regra Ambas Marcam: {e}")
        return mercados_aprovados
        
