import os
import requests

# Ajuste os caminhos de acordo com as pastas do seu repositório
PASTA_TELEGRAM = "telegram"

def extrair_markup_filtros(escolhas=None):
    """
    Menu ajustado:
    - Bingo 3 e 5 com modo denso (Elite) por padrão.
    """
    return {
        "inline_keyboard": [
            # --- NOVO BOTÃO NO TOPO ---
            [
                {"text": "📊 RANKING DE MERCADOS ✅⛔", "callback_data": "cb_ver_ranking"}
            ],
            # --- SEÇÃO 1: BINGOS (Bingo 3 e 5 serão DENSOS) ---
            [{"text": "✅ Escolha um bingo:", "callback_data": "ignore"}],
            [
                {"text": "Bingo 3 (Denso)", "callback_data": "cb_bingo_3_ELITE"},
                {"text": "Bingo 5 (Denso)", "callback_data": "cb_bingo_5_ELITE"}
            ],
            # --- SEÇÃO 2: HORÁRIOS ---
            [{"text": "✅ Escolha uma janela:", "callback_data": "ignore"}],
            [
                {"text": "Janela 3H", "callback_data": "cb_hora_3H"},
                {"text": "Janela 5H", "callback_data": "cb_hora_5H"},
                {"text": "Do Dia", "callback_data": "cb_hora_DIA"}
            ],
            # --- SEÇÃO 3: ESTRATÉGIA ---
            [{"text": "✅ Escolha um modo:", "callback_data": "ignore"}],
            [
                {"text": "Maiores Odds", "callback_data": "cb_tipo_ODDS"},
                {"text": "Mais acertos", "callback_data": "cb_tipo_ACERTOS"},
                {"text": "Equilibrado", "callback_data": "cb_tipo_AMBAS"}
            ],
            # --- BOTÃO DE DISPARO DEFINITIVO ---
            [
                {"text": "🚀 GERAR BILHETE", "callback_data": "cb_acao_GERAR"}
            ]
        ]
    }

# ... (restante das funções enviar_menu_bingo e atualizar_menu_inline permanecem iguais)
