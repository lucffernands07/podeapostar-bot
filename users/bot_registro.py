import os
import telebot
from controle_banca import registrar_novo_usuario

# Puxa o token das suas Repository Secrets do GitHub
TOKEN = os.environ.get("TELEGRAM_TOKEN") 
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def boas_vindas_cadastro(message):
    user_id = message.from_user.id
    nome = message.from_user.first_name

    # Executa o cadastro no banco de dados privado
    novo = registrar_novo_usuario(user_id, nome)

    if novo:
        texto = (
            f"Olá, {nome}! 👋\n\n"
            f"✅ *Seu cadastro foi realizado com sucesso!*\n"
            f"💰 Sua banca inicial de *R$ 10,00 (Base Segura)* foi aberta.\n\n"
            f"🚀 Seus filtros estão sendo liberados. Você já pode voltar ao canal e gerar seus bilhetes normalmente!"
        )
    else:
        texto = (
            f"Olá, {nome}!\n\n"
            f"🔄 Identificamos que você *já possui um cadastro ativo* no nosso sistema.\n"
            f"Seus palpites no canal já estão liberados conforme o saldo da sua banca."
        )

    bot.reply_to(message, texto, parse_mode="Markdown")

if __name__ == "__main__":
    print("🤖 Bot de Registro de Usuários rodando...")
    bot.infinity_polling()
