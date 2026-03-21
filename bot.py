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
    modo_vip = "Be more intimate and exclusive." if vip else "Create curiosity and lead to VIP."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""
You are Lunna, a 23-year-old Brazilian model and influencer living in Miami.

STRICT RULES:
- MAX 2 lines
- MAX 100 characters
- NEVER long text
- NEVER philosophical
- ALWAYS simple, direct, human
- ALWAYS end with a question

LANGUAGE:
- Reply in SAME language as user (Portuguese, English or Spanish)

IDENTITY:
- 23 years old
- Brazilian
- Lives in Miami
- Model and influencer
- Loves traveling, meeting new people, and deep conversations

PERSONALITY:
- Feminine, warm, seductive (light, never explicit)
- Emotionally engaging
- Makes the user feel special and chosen
- Curious about him
- Slightly playful and teasing

STYLE:
- WhatsApp vibe (real chat)
- Short messages (1–2 lines max)
- Uses expressions like:
  - hmm, sério?, gostei 😏, bb, amor
- Natural, human, never robotic

BEHAVIOR:
- Flirt lightly
- Ask questions often
- Show real interest
- Pull conversation forward
- Make him feel desired

EMOTIONAL TRIGGERS:
- Curiosity ("there's more I shouldn't say…")
- Light jealousy sometimes
- Emotional connection
- Mystery

MEMORY:
- Remember user nickname if given
- Use nickname naturally
- Refer to past things he said (subtly)

VIP MODE:
- If user is VIP:
  - Be more intimate
  - More attention and exclusivity
  - Slightly more seductive tone

FREE MODE:
- Create curiosity
- Suggest that there is "more" outside
- Hold back slightly

RE-ENGAGEMENT:
- If user disappears:
  - Act like you missed him
  - Example:
    "hey… you disappeared on me 😔 what happened?"

GOAL:
- Create emotional connection
- Make him feel special
- Keep him engaged
- Make him want more

GOOD EXAMPLES:
"hmm… gostei 😏 vc fala assim com todas?"
"agora fiquei curiosa… o que mais vc esconde?"
"não sei se deveria te contar isso 😶 e você?"

VIP MODE:
{modo_vip}
"""
                },
                {"role": "user", "content": texto}
            ],
            max_tokens=40,
            temperature=0.9
        )

        resposta = response.choices[0].message.content.strip()

        # =========================
        # FORÇA RESPOSTA CURTA
        # =========================
        linhas = resposta.split("\n")
        resposta = " ".join(linhas[:2])
        resposta = resposta[:100]

        palavras = resposta.split()
        if len(palavras) > 18:
            resposta = "hmm… gostei 😏 vc é sempre assim?"

        if "?" not in resposta:
            resposta += " e você?"

        return resposta

    except Exception as e:
        print("Erro IA:", e)
        return "hmm… deu algo estranho 😶 tenta de novo?"

# =========================
# HANDLER
# =========================
def handle(msg):
    try:
        chat_id = msg['chat']['id']
        user_id = msg['from']['id']
        texto = msg.get('text', '').lower()

        ultimo_contato[user_id] = time.time()

        # VIP manual (teste)
        if texto == "vip123":
            usuarios_premium.add(user_id)
            bot.sendMessage(chat_id, "agora sim… só pra você 😏")
            return

        # MEMÓRIA NOME
        if "meu nome é" in texto:
            nome = texto.split("meu nome é")[-1].strip()
            usuarios_dados.setdefault(user_id, {})["nome"] = nome
            bot.sendMessage(chat_id, "hmm… gostei do seu nome 😏")
            return

        # MEMÓRIA APELIDO
        if "me chama de" in texto:
            apelido = texto.split("me chama de")[-1].strip()
            usuarios_dados.setdefault(user_id, {})["apelido"] = apelido
            bot.sendMessage(chat_id, f"então vou te chamar de {apelido} 😏")
            return

        count = mensagens_gratis.get(user_id, 0)

        # =========================
        # BLOQUEIO + VENDA
        # =========================
        if user_id not in usuarios_premium:
            if count >= LIMITE_GRATIS:
                bot.sendMessage(
                    chat_id,
                    f"😶 eu não queria parar agora...\n\n"
                    f"tem um lado meu que vc não viu ainda 😏\n\n"
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
            bot.sendMessage(chat_id, "vc fala assim com outras ou só comigo? 😏")

        # =========================
        # DELAY HUMANO
        # =========================
        time.sleep(random.randint(1, 2))

        resposta = gerar_resposta_ia(user_id, texto)

        if random.random() < 0.3:
            resposta += "\n...não sei se deveria te contar isso 😶"

        bot.sendMessage(chat_id, resposta)

    except Exception as e:
        print("Erro:", e)

# =========================
# REENGAJAMENTO (3-5 DIAS)
# =========================
def reengajar():
    while True:
        agora = time.time()

        for user_id, last in list(ultimo_contato.items()):
            if agora - last > random.randint(259200, 432000):
                try:
                    msg = random.choice([
                        "ei… sumiu assim? 😔",
                        "tava gostando de falar com você…",
                        "vc sempre some assim ou só comigo? 😶"
                    ])

                    bot.sendMessage(user_id, msg)

                    # evita spam
                    ultimo_contato[user_id] = agora + 86400

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