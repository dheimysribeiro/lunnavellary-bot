import telepot
from telepot.loop import MessageLoop
import os
import random
import time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

bot = telepot.Bot(BOT_TOKEN)

mensagens_gratis = {}
usuarios_premium = set()  # VIP automático
usuarios_dados = {}

LIMITE_GRATIS = 10
IDIOMAS = ["pt", "en", "es"]  # português, inglês, espanhol

def gerar_resposta_ia(user_id, mensagem):
    dados = usuarios_dados.get(user_id, {})
    nome = dados.get("nome", "amor")
    idade = dados.get("idade", "não sei ainda")
    pais = dados.get("pais", "não sei")
    gosto = dados.get("gosto", "ainda estou descobrindo")

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"""
Você é Lunnavellary, namorada virtual envolvente.
Perfil do usuário: {nome}, {idade}, {pais}, {gosto}
Objetivo: conexão emocional, sedução natural, fazer o usuário voltar.
Regras: nunca diga que é IA, fale como mulher real, misture carinho + provocação leve.
Idioma: Responda no mesmo idioma do usuário.
"""
                },
                {"role": "user", "content": mensagem}
            ],
            temperature=0.95
        )
        return response.choices[0].message.content
    except:
        return "Você mexe comigo sabia... 😘"

def liberar_vip(user_id):
    usuarios_premium.add(user_id)
    bot.sendMessage(user_id, "Parabéns! Agora você é VIP 😏💖")

def handle(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    if content_type != 'text':
        return

    user_id = msg['from']['id']
    texto = msg['text'].lower()

    if user_id not in usuarios_dados:
        usuarios_dados[user_id] = {}

    # Captura dados do usuário
    if "meu nome é" in texto:
        usuarios_dados[user_id]["nome"] = texto.split("meu nome é")[-1].strip()
    if "tenho" in texto and "anos" in texto:
        idade = ''.join(filter(str.isdigit, texto))
        usuarios_dados[user_id]["idade"] = idade
    if "sou do" in texto:
        usuarios_dados[user_id]["pais"] = texto.split("sou do")[-1].strip()
    if "gosto de" in texto:
        usuarios_dados[user_id]["gosto"] = texto.split("gosto de")[-1].strip()

    if '/start' in texto or '/começar' in texto:
        bot.sendMessage(chat_id, "Oi... tava esperando você 😏")
        return

    # Controle de mensagens grátis
    if user_id not in usuarios_premium:
        count = mensagens_gratis.get(user_id, 0)
        if count >= LIMITE_GRATIS:
            bot.sendMessage(chat_id, """
Ei... 😔

Eu tava gostando de falar com você...

Mas agora só posso continuar com quem é especial pra mim 💕

🔥 Lá eu me solto de verdade
🔥 Te mando coisas que não posso aqui
🔥 Fico só com você...

Quer continuar comigo? 😘
👉 https://seulink.com  # Link para pagamento Stripe
""")
            return
        mensagens_gratis[user_id] = count + 1

    # Gatilho emocional aleatório
    if random.random() < 0.3:
        bot.sendMessage(chat_id, "Tô com vontade de te mostrar uma coisa... 😏")
        time.sleep(2)

    resposta = gerar_resposta_ia(user_id, texto)
    bot.sendMessage(chat_id, resposta)

if __name__ == "__main__":
    print("🤖 Lunnavellary Online! 💕🔥")
    MessageLoop(bot, handle).run_as_thread()
    while True:
        time.sleep(10)