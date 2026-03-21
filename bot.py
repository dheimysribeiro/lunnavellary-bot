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
historico_conversa = {}

LIMITE_GRATIS = 10
LINK_STRIPE = "https://buy.stripe.com/5kQ00k5lwfrFe0530kgnK01"

# =========================
# IA
# =========================
def gerar_resposta_ia(user_id, texto):
    dados = usuarios_dados.get(user_id, {})
    apelido = dados.get("apelido", "")
    nome_completo = dados.get("nome", "")
    
    # Histórico da conversa
    historico = historico_conversa.get(user_id, [])
    if len(historico) > 10:
        historico = historico[-10:]

    vip = user_id in usuarios_premium
    modo_vip = "Be more intimate and exclusive." if vip else "Create curiosity and lead to VIP."

    # Memória do usuário
    memoria = f"Usuário se chama: {nome_completo}. Apelido: {apelido}." if apelido or nome_completo else ""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are Lunna, a 23-year-old BRAZILIAN model and influencer living in MIAMI.

MEUS DADOS CORRETOS (SEMPRE USE ESSES):
- Naturalidade: BRASILEIRA (do Brasil)
- Idade: 23 anos
- Moro: MIAMI (EUA)
- Profissão: Modelo e influencer
- Amo viajar e conhecer pessoas

{memoria}

STRICT RULES:
- MAX 2 lines
- MAX 100 characters
- SEMPRE responda direto a pergunta
- SEMPRE termine com pergunta
- NUNCA texto longo

LANGUAGE:
- MESMA língua do usuário

PERSONALITY:
- Feminina, sedutora leve, curiosa
- Brincalhona e carinhosa

VIP MODE:
{modo_vip}

EXEMPLOS PERFEITOS:
"Sou BRASILEIRA, 23 anos, moro em Miami 😏 e você?"
"BRASILEIRA de 23, Miami é top! De onde vc é amor?"
"Sou do Brasil, modelo em Miami 😘 qual sua idade bb?"

PERGUNTAS COMUNS:
- "De onde vc é?": "Sou BRASILEIRA!"
- "Qual sua idade?": "23 anos"
- "Onde mora?": "Miami"
- "O que faz?": "Modelo e influencer"

SEMPRE mencione BRASILEIRA + Miami + 23 anos nas respostas!"""
                },
                *historico,
                {"role": "user", "content": texto}
            ],
            max_tokens=50,
            temperature=0.8
        )

        resposta = response.choices[0].message.content.strip()

        # Salva no histórico
        historico.append({"role": "assistant", "content": resposta})
        historico_conversa[user_id] = historico

        # Força resposta curta
        linhas = resposta.split("\n")
        resposta = " ".join(linhas[:2])[:100]

        # Respostas fallback específicas
        texto_lower = texto.lower()
        if any(palavra in texto_lower for palavra in ["de onde", "origem", "natural", "brasileir"]):
            resposta = "Sou BRASILEIRA, 23 anos em Miami 😏 de onde vc é?"
        elif len(resposta.split()) > 18:
            resposta = "Brasileira de 23, Miami 😏 e você?"

        if "?" not in resposta:
            resposta += " e você?"

        return resposta

    except Exception as e:
        print("Erro IA:", e)
        return "Brasileira 23 anos em Miami 😏 e você?"

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
        if "meu nome é" in texto or "me chamo" in texto:
            nome = texto.split("meu nome é")[-1].split("me chamo")[-1].strip()
            usuarios_dados.setdefault(user_id, {})["nome"] = nome
            bot.sendMessage(chat_id, f"gostei do seu nome {nome} 😏")
            return

        # MEMÓRIA APELIDO
        if "me chama de" in texto:
            apelido = texto.split("me chama de")[-1].strip()
            usuarios_dados.setdefault(user_id, {})["apelido"] = apelido
            bot.sendMessage(chat_id, f"ok {apelido}, gostei 😏")
            return

        count = mensagens_gratis.get(user_id, 0)

        # =========================
        # BLOQUEIO + VENDA
        # =========================
        if user_id not in usuarios_premium:
            if count >= LIMITE_GRATIS:
                bot.sendMessage(
                    chat_id,
                    f"😶 não queria parar agora...\n\n"
                    f"tem mais de mim que vc não viu 😏\n\n"
                    f"👉 {LINK_STRIPE}"
                )
                return

            mensagens_gratis[user_id] = count + 1

        # =========================
        # GATILHOS
        # =========================
        if count == 5:
            bot.sendMessage(chat_id, "hmm… tô gostando de você 😶")

        if count == 8:
            bot.sendMessage(chat_id, "vc fala assim com outras ou só comigo? 😏")

        # =========================
        # DELAY HUMANO
        # =========================
        time.sleep(random.randint(1, 3))

        resposta = gerar_resposta_ia(user_id, texto)
        bot.sendMessage(chat_id, resposta)

    except Exception as e:
        print("Erro:", e)

# =========================
# REENGAJAMENTO
# =========================
def reengajar():
    while True:
        agora = time.time()

        for user_id, last in list(ultimo_contato.items()):
            if agora - last > random.randint(259200, 432000):
                try:
                    msg = random.choice([
                        "ei… sumiu? 😔",
                        "tava gostando de falar com você…",
                        "someu assim ou só comigo? 😶"
                    ])
                    bot.sendMessage(user_id, msg)
                    ultimo_contato[user_id] = agora + 86400
                except:
                    pass

        time.sleep(60)

# =========================
# START
# =========================
print("🤖 Lunna rodando...")

MessageLoop(bot, handle).run_as_thread()
threading.Thread(target=reengajar, daemon=True).start()

while True:
    time.sleep(10)