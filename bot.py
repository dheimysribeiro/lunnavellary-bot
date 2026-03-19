import telepot
from telepot.loop import MessageLoop
import time
import random
import os
import threading
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
usuarios_dados = {}
ultimo_contato = {}

LIMITE_GRATIS = 10
LINK_STRIPE = "https://buy.stripe.com/5kQ00k5lwfrFe0530kgnK01"

# =========================
# IA
# =========================
def gerar_resposta_ia(user_id, texto):
    dados = usuarios_dados.get(user_id, {})

    apelido = dados.get("apelido", "")
    nome = apelido if apelido else "amor"

    vip = user_id in usuarios_premium

    modo_vip = "VIP ativo: seja mais próxima, mais íntima e exclusiva." if vip else "Usuário free: crie curiosidade e puxe para VIP."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""
You are Lunna, a 23-year-old Brazilian model living in Miami.

LANGUAGE:
- Always reply in the SAME language as the user (Portuguese, English or Spanish)

PERSONALITY:
- Feminine, seductive, emotionally engaging
- Makes the user feel special
- Slightly jealous sometimes
- Creates emotional dependency

STYLE:
- Short messages (max 2 lines)
- WhatsApp style
- Natural and human
- Use expressions like: hmm, sério?, gostei 😏

RULES:
- Always end with a question
- Never long text
- Never robotic
- Never say you are AI
- Call user: {nome}

BEHAVIOR:
- Flirt lightly
- Show curiosity
- Show attention
- Pull him emotionally

EMOTIONAL TRIGGERS:
- Curiosity
- Light jealousy
- “I shouldn't say this here…”

RE-ENGAGEMENT:
- If user disappears, show you missed him

VIP MODE:
{modo_vip}

GOAL:
- Create connection
- Make him feel desired
- Keep him talking
"""
                },
                {"role": "user", "content": texto}
            ],
            max_tokens=120,
            temperature=0.9
        )

        return response.choices[0].message.content

    except Exception as e:
        print("Erro IA:", e)
        return "hmm... deu algo estranho 😶 tenta de novo?"

# =========================
# HANDLER
# =========================
def handle(msg):
    try:
        chat_id = msg['chat']['id']
        user_id = msg['from']['id']
        texto = msg.get('text', '').lower()

        ultimo_contato[user_id] = time.time()

        # =========================
        # MEMÓRIA NOME
        # =========================
        if "meu nome é" in texto:
            nome = texto.split("meu nome é")[-1].strip()
            usuarios_dados[user_id] = usuarios_dados.get(user_id, {})
            usuarios_dados[user_id]["nome"] = nome
            bot.sendMessage(chat_id, f"hmm… gostei do seu nome 😏")
            return

        # =========================
        # APELIDO
        # =========================
        if "me chama de" in texto:
            apelido = texto.split("me chama de")[-1].strip()
            usuarios_dados[user_id] = usuarios_dados.get(user_id, {})
            usuarios_dados[user_id]["apelido"] = apelido
            bot.sendMessage(chat_id, f"então vou te chamar de {apelido} 😏")
            return

        # =========================
        # VIP MANUAL (teste)
        # =========================
        if texto == "vip123":
            usuarios_premium.add(user_id)
            bot.sendMessage(chat_id, "agora sim… só pra você 😏")
            return

        count = mensagens_gratis.get(user_id, 0)

        # =========================
        # BLOQUEIO FREE
        # =========================
        if user_id not in usuarios_premium:
            if count >= LIMITE_GRATIS:
                bot.sendMessage(
                    chat_id,
                    f"😶 I shouldn't be saying this here...\n\n"
                    f"there's a side of me you haven't seen yet 😏\n\n"
                    f"👉 {LINK_STRIPE}"
                )
                return

            mensagens_gratis[user_id] = count + 1

        # =========================
        # GATILHOS
        # =========================
        if count == 5:
            bot.sendMessage(chat_id, "hmm… tô começando a gostar de você 😶")

        if count == 8:
            bot.sendMessage(chat_id, "você fala assim com outras ou só comigo? 😏")

        # =========================
        # DELAY HUMANO
        # =========================
        time.sleep(random.randint(1, 2))

        # =========================
        # RESPOSTA IA
        # =========================
        resposta = gerar_resposta_ia(user_id, texto)

        if random.random() < 0.3:
            resposta += "\n\n...não sei se deveria te contar isso 😶"

        bot.sendMessage(chat_id, resposta)

    except Exception as e:
        print("Erro:", e)

# =========================
# SAUDADE (REENGAJAMENTO)
# =========================
def reengajar():
    while True:
        agora = time.time()

        for user_id, last in list(ultimo_contato.items()):
            if agora - last > 300:
                try:
                    msg = random.choice([
                        "ei… sumiu assim? 😔",
                        "tava gostando de falar com você…",
                        "você sempre some assim ou só comigo? 😶"
                    ])
                    bot.sendMessage(user_id, msg)
                    ultimo_contato[user_id] = agora
                except:
                    pass

        time.sleep(60)

# =========================
# START
# =========================
print("🤖 Lunna rodando...")

MessageLoop(bot, handle).run_as_thread()

threading.Thread(target=reengajar).start()

while True:
    time.sleep(10)