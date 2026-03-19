import telepot
from telepot.loop import MessageLoop
import time
import random
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)
bot = telepot.Bot(BOT_TOKEN)

mensagens_gratis = {}
usuarios_premium = set()

LIMITE_GRATIS = 10

def gerar_resposta_ia(user_id, texto):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você é uma mulher sedutora, envolvente e misteriosa. "
                        "Crie conexão emocional, curiosidade e sempre termine com pergunta."
                    )
                },
                {"role": "user", "content": texto}
            ],
            max_tokens=200
        )
        return response.choices[0].message.content
    except:
        return "Hmm... algo deu errado 😶"

def handle(msg):
    try:
        chat_id = msg['chat']['id']
        user_id = msg['from']['id']
        texto = msg.get('text', '').lower()

        # VIP manual
        if texto == "vip123":
            usuarios_premium.add(user_id)
            bot.sendMessage(chat_id, "Agora sim... só pra você 😏")
            return

        count = mensagens_gratis.get(user_id, 0)

        if user_id not in usuarios_premium:
            if count >= LIMITE_GRATIS:
                bot.sendMessage(
                    chat_id,
                    "😶 Eu não queria parar agora...\n\n"
                    "Você mexeu comigo de um jeito diferente...\n\n"
                    "Mas aqui eu tenho que me segurar...\n\n"
                    "👉 Entra aqui: https://buy.stripe.com/5kQ00k5lwfrFe0530kgnK01"
                )
                return

            mensagens_gratis[user_id] = count + 1

        if count == 7:
            bot.sendMessage(chat_id, "Você tá me deixando curiosa... 😳")

        if count == 9:
            bot.sendMessage(chat_id, "Se a gente tivesse em outro lugar... 😶")

        time.sleep(random.randint(1, 2))

        resposta = gerar_resposta_ia(user_id, texto)

        if random.random() < 0.4:
            resposta += "\n\n...não sei se deveria te contar isso 😶"

        bot.sendMessage(chat_id, resposta)

    except Exception as e:
        print("Erro:", e)

print("🤖 Bot online...")
MessageLoop(bot, handle).run_as_thread()

while True:
    time.sleep(10)