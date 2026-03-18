import telepot
from telepot.loop import MessageLoop
import time
import random
import os
from dotenv import load_dotenv
from openai import OpenAI

# =========================
# CONFIG
# =========================
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)
bot = telepot.Bot(BOT_TOKEN)

# =========================
# CONTROLE
# =========================
mensagens_gratis = {}
usuarios_premium = set()

LIMITE_GRATIS = 10

# =========================
# IA
# =========================
def gerar_resposta_ia(user_id, texto):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você é uma mulher sedutora, envolvente e misteriosa. "
                        "Você cria conexão emocional, curiosidade e provoca o usuário "
                        "sem entregar tudo de uma vez. Respostas naturais e curtas."
                    )
                },
                {"role": "user", "content": texto}
            ],
            max_tokens=200
        )
        return response.choices[0].message.content

    except Exception as e:
        print("Erro IA:", e)
        return "Hmm... algo deu errado aqui 😶 tenta de novo..."

# =========================
# HANDLER
# =========================
def handle(msg):
    try:
        chat_id = msg['chat']['id']
        user_id = msg['from']['id']
        texto = msg.get('text', '')

        count = mensagens_gratis.get(user_id, 0)

        # =========================
        # BLOQUEIO FREE (VENDA)
        # =========================
        if user_id not in usuarios_premium:
            if count >= LIMITE_GRATIS:
                bot.sendMessage(chat_id, """
😶 Eu queria continuar...

Mas aqui não dá mais...

Você me deixou curiosa demais...

👉 Desbloqueia meu lado secreto:
SEU_LINK_STRIPE
""")
                return

            mensagens_gratis[user_id] = count + 1

        # =========================
        # GATILHOS EMOCIONAIS
        # =========================
        if count == 7:
            bot.sendMessage(chat_id, "Você tá me deixando curiosa... 😳")

        if count == 9:
            bot.sendMessage(chat_id, "Se a gente tivesse em outro lugar... 😶")

        # =========================
        # RESPOSTA IA
        # =========================
        resposta = gerar_resposta_ia(user_id, texto)

        if random.random() < 0.4:
            resposta += "\n\n...não sei se deveria te contar isso 😶"

        bot.sendMessage(chat_id, resposta)

    except Exception as e:
        print("Erro no handle:", e)

# =========================
# START
# =========================
if __name__ == "__main__":
    print("🤖 Bot online...")

    MessageLoop(bot, handle).run_as_thread()

    while True:
        time.sleep(10)