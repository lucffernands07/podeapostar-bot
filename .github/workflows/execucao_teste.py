name: Execucao Teste Bot Apostas

on:
  push:
    paths:
      - 'testes/**'   # Dispara se você alterar qualquer arquivo na pasta testes
  workflow_dispatch:  # Permite rodar manualmente no botão do GitHub

jobs:
  run-test-bot:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - name: Checkout do repositorio
        uses: actions/checkout@v3

      - name: Configurar Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Instalar dependencias
        run: |
          pip install -r requirements.txt

      - name: 1. Executar bot de Teste (Regra Nova Dupla Chance)
        env:
          TELEGRAM_TOKEN: ${{ secrets.TELEGRAM_TOKEN }}
          CHAT_ID: ${{ secrets.CHAT_ID }}
          # Note que não passei o CHANNEL_ID aqui para garantir que o teste nunca poste no canal
        run: |
          # Adiciona a raiz do projeto ao PYTHONPATH para que o teste_main encontre os módulos originais
          export PYTHONPATH="${PYTHONPATH}:$(pwd)"
          python testes/teste_main.py
