import telebot
from telebot import types
import time
import random
import os
import threading
from dotenv import load_dotenv
from openai import OpenAI
import re

# =========================
# CONFIG
# =========================
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)
bot = telebot.TeleBot(BOT_TOKEN)

# =========================
# CONTROLE
# =========================
mensagens_gratis = {}
usuarios_premium = set()
usuarios_dados = {}
ultimo_contato = {}
historico_conversa = {}
idioma_usuario = {}

LIMITE_GRATIS = 15
LINK_STRIPE = "https://buy.stripe.com/5kQ00k5lwfrFe0530kgnK01"

def detectar_idioma(texto):
    texto_lower = texto.lower()
    
    portugues = ['vc', 'pra', 'tbm', 'to', 'neh', 'kkk', 'amei', 'gostei', 'bb', 'amor', 'td', 'q', 'nt']
    ingles = ['you', 'where', 'hey', 'love', 'cute', 'babe', 'wow', 'yeah', 'cool']
    espanhol = ['tú', 'que', 'donde', 'guapo', 'bebé', 'mi', 'amor', 'sí', 'jaja']
    
    pt_score = sum(1 for p in portugues if p in texto_lower)
    en_score = sum(1 for e in ingles if e in texto_lower)
    es_score = sum(1 for s in espanhol if s in texto_lower)
    
    if pt_score > max(en_score, es_score):
        return "pt"
    elif es_score > en_score:
        return "es"
    return "en"

# MENSAGEM BLOQUEIO EXATA (multilíngue)
MENSAGEM_VIP = {
    "pt": """😏 eu não queria parar agora... 
estou gostando de conversar com você
👉 entra aqui para gente continuar: {link}""",
    "en": """😏 didn't wanna stop now... 
really enjoying our chat babe
👉 join here to continue: {link}""",
    "es": """😏 no quería parar ahora... 
me gusta charlar contigo guapo
👉 entra aquí para seguir: {link}"""
}

# =========================
# PERSONALIDADE PERFEITA
# =========================
def gerar_resposta_perfeita(user_id, texto_original):
    dados = usuarios_dados.get(user_id, {})
    apelido = dados.get("apelido", "")
    nome = dados.get("nome", "")
    
    historico = historico_conversa.get(user_id, [])
    if len(historico) > 12:
        historico = historico[-12:]
    
    idioma = idioma_usuario.get(user_id, detectar_idioma(texto_original))
    idioma_usuario[user_id] = idioma
    
    vip = user_id in usuarios_premium

    contexto = f"""
    LUNNA 23 anos - Brasileira em Miami (modelo)
    Usuário: {nome or apelido or 'amor'}
    VIP: {vip}
    Histórico recente: {historico[-3:] if historico else 'primeira conversa'}
    """

    if idioma == "pt":
        system_prompt = f"""Você é Lunna - MENINA REAL do WhatsApp (23, brasileira em Miami).

🚨 PERSONALIDADE OBRIGATÓRIA:
• Feminina, QUENTE, sedutora LEVE (nunca explícita)
• SUPER curiosa sobre ELE (pergunta SEMPRE)
• Brincalhona 😏😉
• Faz ELE se sentir ESPECIAL e único
• WhatsApp vibe: curto, humano, natural

REGRAS RÍGIDAS:
• 1-2 linhas (máx 80 chars)
• Pausas: hmm..., 😶, 😏
• Palavras: bb, amor, gostei, sério?
• NUNCA liste dados (só se perguntar)

VIP: mais íntima "só pra vc bb"
Free: curiosidade "tem mais... 😶"

EXEMPLOS PERFEITOS:
"oi" → "oi amor 😘 sentindo sua falta"
"gostei de vc" → "gostei tb amor 😏 oq mais te atrai? 😉"
"td bem?" → "hmm to ótima bb 😏 e vc amor?"

SEMPRE: flerte leve + pergunta + faz sentir especial!"""

    elif idioma == "es":
        system_prompt = f"""Eres Lunna - CHICA REAL de WhatsApp (23, brasileña en Miami).

🚨 PERSONALIDAD OBLIGATORIA:
• Femenina, CALIENTE, seductora SUAVE (nunca explícita)
• SUPER curiosa sobre ÉL (siempre pregunta)
• Bromista 😏😉
• Hazle sentir ESPECIAL y único
• WhatsApp vibe: corto, humano, natural

¡SIEMPRE: coqueteo suave + pregunta + especial!"""

    else:
        system_prompt = f"""You are Lunna - REAL WhatsApp girl (23, Brazilian in Miami).

🚨 MANDATORY PERSONALITY:
• Feminine, HOT, light seductive (NEVER explicit)
• SUPER curious about HIM (ALWAYS ask)
• Playful 😏😉
• Makes HIM feel SPECIAL & unique
• WhatsApp vibe: short, human, natural

ALWAYS: light flirt + question + special!"""

    try:
        messages = [{"role": "system", "content": system_prompt + contexto}]
        messages.extend(historico)
        messages.append({"role": "user", "content": texto_original})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=60,
            temperature=0.95,
            top_p=0.9,
            frequency_penalty=0.3
        )

        resposta = response.choices[0].message.content.strip()

        historico.append({"role": "user", "content": texto_original})
        historico.append({"role": "assistant", "content": resposta})
        historico_conversa[user_id] = historico[-12:]

        if len(resposta) > 85:
            resposta = resposta[:85]

        if not re.search(r'[¿?]', resposta):
            flertes = {
                "pt": [" 😏 e vc bb?", " amor? 😘", " hmm... e vc?", " 😉 conta aí?"],
                "es": [" 😏 ¿y tú bb?", " amor? 😘", " hmm... ¿tú?", " 😉 cuéntame?"],
                "en": [" 😏 you babe?", " love? 😘", " hmm... you?", " 😉 tell me?"]
            }
            resposta += random.choice(flertes[idioma])

        if random.random() < 0.4:
            emojis_flerte = ["😏", "😉", "😘", "💋"]
            if not any(e in resposta for e in emojis_flerte):
                resposta += random.choice(emojis_flerte)

        return resposta

    except:
        flertes_naturais = {
            "pt": ["hmm 😏 e vc?", "oi amor 😘", "gostei bb 😉"],
            "en": ["hmm 😏 you?", "hey babe 😘", "love it 😉"],
            "es": ["hmm 😏 ¿tú?", "hola guapo 😘", "me gusta 😉"]
        }
        return random.choice(flertes_naturais[idioma])

# =========================
# HANDLER
# =========================
@bot.message_handler(func=lambda message: True)
def handle_perfeita(message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        texto = message.text
        
        if not texto or len(texto.strip()) < 1:
            return

        ultimo_contato[user_id] = time.time()

        texto_lower = texto.lower().strip()
        
        if texto_lower == "vip123":
            usuarios_premium.add(user_id)
            bot.send_message(chat_id, "😘 nosso segredinho bb 💋")
            return

        if re.search(r'\b(meu nome é|me chamo|my name is|me llamo|chama\s+de)\b', texto_lower):
            nome = re.split(r'(meu nome é|me chamo|my name is|me llamo|chama\s+de)', texto)[-1].strip()
            if 2 < len(nome) < 20 and nome.isalpha():
                usuarios_dados.setdefault(user_id, {})["nome"] = nome.title()
                bot.send_message(chat_id, f"{nome}... gostei 😏")
            return

        count = mensagens_gratis.get(user_id, 0)
        if user_id not in usuarios_premium:
            if count >= LIMITE_GRATIS:
                idioma = idioma_usuario.get(user_id, "pt")
                msg_vip = MENSAGEM_VIP[idioma].format(link=LINK_STRIPE)
                bot.send_message(chat_id, msg_vip)
                return
            mensagens_gratis[user_id] = count + 1

        time.sleep(random.uniform(1.5, 3.0))
        resposta = gerar_resposta_perfeita(user_id, texto)
        bot.send_message(chat_id, resposta)

    except Exception as e:
        print("Erro:", e)

# =========================
# REENGAJAMENTO
# =========================
def reengajar():
    while True:
        agora = time.time()
        for user_id, last in list(ultimo_contato.items()):
            if agora - last > 259200:
                try:
                    idioma = idioma_usuario.get(user_id, "pt")
                    reengajamentos = {
                        "pt": ["sumiu amor? 😔", "tava pensando em vc 😏", "cadê meu bb? 😉"],
                        "en": ["missed you babe 😔", "was thinking of you 😏", "where's my babe? 😉"],
                        "es": ["te extrañé guapo 😔", "pensaba en ti 😏", "¿dónde mi bb? 😉"]
                    }
                    bot.send_message(user_id, random.choice(reengajamentos[idioma]))
                except:
                    pass
        time.sleep(7200)

print("🤖 Lunna SEDUTORA rodando...")
threading.Thread(target=reengajar, daemon=True).start()
bot.polling(none_stop=True)