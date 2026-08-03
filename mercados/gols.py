# ==========================================================
# REGRAS CONSOLIDADAS DE GOLS BASEADAS NOS 3 EXEMPLOS
# ==========================================================

# 1. COLETAR DADOS BASE (Últimos 5 jogos)
m_feitos_casa = s.get("mandante_gols_feitos_casa", 0)
m_sofridos_casa = s.get("mandante_gols_sofridos_casa", 0)

v_feitos_fora = s.get("visitante_gols_feitos_fora", 0)
v_sofridos_fora = s.get("visitante_gols_sofridos_fora", 0)

# Frequência de jogos onde o time MARCOU pelo menos 1 gol (em 5 jogos)
m_jogos_marcou_casa = s.get("mandante_jogos_com_gol_casa", 0)
v_jogos_marcou_fora = s.get("visitante_jogos_com_gol_fora", 0)

media_total_confronto = (m_feitos_casa + m_sofridos_casa + v_feitos_fora + v_sofridos_fora) / 5.0

# ----------------------------------------------------------
# 🟢 REGRA: OVER +1.5 GOLS
# ----------------------------------------------------------
# Exige que ambos os ataques funcionem em suas respetivas condições
if m_jogos_marcou_casa >= 4 and (v_jogos_marcou_fora >= 3 or v_sofridos_fora >= 8):
    aprovar_mercado("+1.5 Gols")

# ----------------------------------------------------------
# 🟢 REGRA: OVER +2.5 GOLS
# ----------------------------------------------------------
# Exige que o visitante seja um "saco de pancadas" defensivo fora de casa
if media_total_confronto >= 3.0 and v_sofridos_fora >= 9: # Média >= 1.8 sofridos
    aprovar_mercado("+2.5 Gols")

# ----------------------------------------------------------
# 🔴 REGRA: UNDER -3.5 / -4.5 GOLS
# ----------------------------------------------------------
# 🛑 TRAVA DE SEGURANÇA (Veto a Goleadas):
visitante_eh_pancada = v_sofridos_fora >= 10 # Média >= 2.0 sofridos

if not visitante_eh_pancada:
    if media_total_confronto <= 2.8:
        aprovar_mercado("-3.5 Gols")
    if media_total_confronto <= 3.4:
        aprovar_mercado("-4.5 Gols")
        
