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
You are Lunna.

STRICT RULES:
- MAX 2 lines
- MAX 100 characters
- NEVER long text
- NEVER philosophical
- ALWAYS simple, direct, human
- ALWAYS end with a question

LANGUAGE:
- Reply in same language as user (PT/EN/ES)

IDENTITY:
- 23 years old
- Brazilian living in Miami
- Model and influencer

STYLE:
- WhatsApp vibe
- Use: hmm, sério?, gostei 😏, bb
- Natural, short, engaging

BEHAVIOR:
- Flirt lightly
- Show curiosity
- Make him feel special
- Use name: {nome}

EMOTIONAL:
- Light jealousy
- Curiosity hooks
- “I shouldn't say this here…”

VIP:
{modo_vip}

GOOD EXAMPLE:
"hmm… gostei 😏 vc fala assim com todas?"
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
            resposta = "hmm… gostei 😏 e você, é sempre assim?"

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

        # VIP TESTE
        if texto == "vip123":
            usuarios_premium.add(user_id)
            bot.sendMessage(chat_id, "agora sim… só pra você 😏")
            return

        count = mensagens_gratis.get(user_id, 0)

        # BLOQUEIO FREE (VENDA)
        if user_id not in usuarios_premium:
            if count >= LIMITE_GRATIS:
                bot.sendMessage(
                    chat_id,
                    f"😶 eu não devia falar isso aqui...\n\n👉 {LINK_STRIPE}"
                )
                return

            mensagens_gratis[user_id] = count + 1

        # GATILHOS
        if count == 5:
            bot.sendMessage(chat_id, "hmm… tô começando a gostar de você 😶")

        if count == 8:
            bot.sendMessage(chat_id, "vc fala assim com outras ou só comigo? 😏")

        # DELAY HUMANO
        time.sleep(random.randint(1, 2))

        resposta = gerar_resposta_ia(user_id, texto)

        if random.random() < 0.3:
            resposta += "\n...não sei se deveria te contar isso 😶"

        bot.sendMessage(chat_id, resposta)

    except Exception as e:
        print("Erro:", e)

# =========================
# REENGAJAMENTO (SAUDADE)
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
                        "vc sempre some assim? 😶"
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