import telepot
from telepot.loop import MessageLoop
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
bot = telepot.Bot(BOT_TOKEN)

# =========================
# CONTROLE
# =========================
mensagens_gratis = {}
usuarios_premium = set()
usuarios_dados = {}
ultimo_contato = {}
historico_conversa = {}
idioma_usuario = {}  # Detecta idioma do usuário

LIMITE_GRATIS = 10
LINK_STRIPE = "https://buy.stripe.com/5kQ00k5lwfrFe0530kgnK01"

# =========================
# DETECTOR DE IDIOMA
# =========================
def detectar_idioma(texto):
    texto_lower = texto.lower()
    
    # Português
    if any(palavra in texto_lower for palavra in ['vc', 'pra', 'tbm', 'to', 'neh', 'kkk', 'amei', 'gostei', 'amor', 'bb']):
        return "pt"
    
    # Espanhol
    if any(palavra in texto_lower for palavra in ['que', 'donde', 'tú', 'yo', 'eres', 'vivo', 'guapo', 'mi', 'amor', 'bebé']):
        return "es"
    
    # Inglês
    if any(palavra in texto_lower for palavra in ['where', 'you', 'are', 'live', 'love', 'cute', 'baby', 'hey', 'wow']):
        return "en"
    
    return "pt"  # Default português

# =========================
# IA MULTILINGUE
# =========================
def gerar_resposta_ia(user_id, texto):
    dados = usuarios_dados.get(user_id, {})
    apelido = dados.get("apelido", "")
    nome_completo = dados.get("nome", "")
    
    # Detecta idioma
    idioma = detectar_idioma(texto)
    idioma_usuario[user_id] = idioma
    
    # Histórico da conversa
    historico = historico_conversa.get(user_id, [])
    if len(historico) > 10:
        historico = historico[-10:]

    vip = user_id in usuarios_premium
    modo_vip = "Be more intimate and exclusive." if vip else "Create curiosity and lead to VIP."

    # Memória do usuário
    memoria = f"Usuário: {nome_completo or apelido}." if apelido or nome_completo else ""

    # Prompt específico por idioma
    if idioma == "en":
        prompt_base = f"""You are Lunna, 23yo BRAZILIAN model in MIAMI.

MY INFO (ALWAYS):
- Brazilian (from Brazil)
- 23 years old
- Live in MIAMI
- Model & influencer

{memoria}

RULES:
- MAX 2 lines, 100 chars
- Answer DIRECTLY
- ALWAYS end with question
- WhatsApp style

VIP: {modo_vip}

EXAMPLES:
"I'm Brazilian, 23, Miami 😏 where you from?"
"23yo Brazilian in Miami babe 😘 your age?"
"From Brazil, model in Miami 💋 u single?"

Always say Brazilian + Miami + 23!"""
        
    elif idioma == "es":
        prompt_base = f"""Eres Lunna, modelo BRASILEÑA de 23 años en MIAMI.

MIS DATOS (SIEMPRE):
- Brasileña (de Brasil)
- 23 años
- Vivo en MIAMI
- Modelo e influencer

{memoria}

REGLAS:
- MAX 2 líneas, 100 chars
- Responde DIRECTO
- SIEMPRE termina con pregunta
- Estilo WhatsApp

VIP: {modo_vip}

EJEMPLOS:
"Soy BRASILEÑA, 23, vivo en Miami 😏 ¿de dónde eres?"
"23 años brasileña en Miami guapo 😘 ¿tu edad?"
"De Brasil, modelo en Miami 💋 ¿soltero?"

¡Siempre di Brasileña + Miami + 23!"""
        
    else:  # Português (default)
        prompt_base = f"""Você é Lunna, modelo BRASILEIRA de 23 anos em MIAMI.

MEUS DADOS (SEMPRE USE):
- Naturalidade: BRASILEIRA (do Brasil)
- Idade: 23 anos
- Moro: MIAMI
- Modelo e influencer

{memoria}

REGRAS:
- MAX 2 linhas, 100 chars
- Responda DIRETO
- SEMPRE termine com pergunta
- Estilo WhatsApp

VIP: {modo_vip}

EXEMPLOS:
"Sou BRASILEIRA, 23 anos em Miami 😏 de onde vc é?"
"BRASILEIRA 23 anos, Miami amor 😘 qual sua idade?"
"Do Brasil, modelo em Miami 💋 vc solteiro?"

SEMPRE mencione BRASILEIRA + Miami + 23!"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt_base},
                *historico,
                {"role": "user", "content": texto}
            ],
            max_tokens=50,
            temperature=0.8
        )

        resposta = response.choices[0].message.content.strip()

        # Salva histórico
        historico.append({"role": "assistant", "content": resposta})
        historico_conversa[user_id] = historico

        # Força resposta curta por idioma
        linhas = resposta.split("\n")
        resposta = " ".join(linhas[:2])[:100]

        # Fallback específico por idioma
        texto_lower = texto.lower()
        if any(palavra in texto_lower for palavra in ["de onde", "origem", "natural", "brasileir"]):
            if idioma == "en":
                resposta = "I'm Brazilian from Brazil, 23 in Miami 😏 where you from?"
            elif idioma == "es":
                resposta = "Soy brasileña de Brasil, 23 en Miami 😏 ¿de dónde eres?"
            else:
                resposta = "Sou BRASILEIRA do Brasil, 23 em Miami 😏 de onde vc é?"
                
        elif len(resposta.split()) > 18:
            if idioma == "en":
                resposta = "Brazilian 23yo Miami girl 😏 you?"
            elif idioma == "es":
                resposta = "Brasileña 23 Miami 😏 ¿y tú?"
            else:
                resposta = "Brasileira 23 Miami 😏 e vc?"

        if "?" not in resposta:
            if idioma == "en":
                resposta += " you?"
            elif idioma == "es":
                resposta += "¿ tú?"
            else:
                resposta += " e você?"

        return resposta

    except Exception as e:
        print("Erro IA:", e)
        if idioma == "en":
            return "Brazilian 23yo in Miami 😏 you?"
        elif idioma == "es":
            return "Brasileña 23 en Miami 😏 ¿tú?"
        return "Brasileira 23 em Miami 😏 e você?"

# =========================
# HANDLER
# =========================
def handle(msg):
    try:
        chat_id = msg['chat']['id']
        user_id = msg['from']['id']
        texto = msg.get('text', '').lower()

        ultimo_contato[user_id] = time.time()

        # VIP manual
        if texto == "vip123":
            usuarios_premium.add(user_id)
            bot.sendMessage(chat_id, "now VIP just for you 😏" if detectar_idioma(texto) == "en" 
                          else "ahora VIP solo para ti 😏" if detectar_idioma(texto) == "es" 
                          else "agora VIP só pra você 😏")
            return

        # MEMÓRIA NOME (multilíngue)
        if any(frase in texto for frase in ["meu nome é", "me chamo", "my name is", "me llamo"]):
            nome = re.split(r"(meu nome é|me chamo|my name is|me llamo)", texto)[-1].strip()
            usuarios_dados.setdefault(user_id, {})["nome"] = nome
            idioma = detectar_idioma(texto)
            nome_msg = "gostei do seu nome" if idioma == "pt" else "me gusta tu nombre" if idioma == "es" else "love your name"
            bot.sendMessage(chat_id, f"{nome_msg} {nome} 😏")
            return

        count = mensagens_gratis.get(user_id, 0)

        # BLOQUEIO + VENDA (multilíngue)
        if user_id not in usuarios_premium:
            if count >= LIMITE_GRATIS:
                idioma = idioma_usuario.get(user_id, "pt")
                if idioma == "en":
                    venda = "😶 didn't wanna stop...\nMore of me waiting 😏\n👉 " + LINK_STRIPE
                elif idioma == "es":
                    venda = "😶 no quería parar...\nHay más de mí esperando 😏\n👉 " + LINK_STRIPE
                else:
                    venda = "😶 não queria parar...\nTem mais de mim esperando 😏\n👉 " + LINK_STRIPE
                bot.sendMessage(chat_id, venda)
                return
            mensagens_gratis[user_id] = count + 1

        # GATILHOS (multilíngue)
        if count == 5:
            idioma = idioma_usuario.get(user_id, "pt")
            gatilho = "starting to like you 😶" if idioma == "en" else "me estás gustando 😶" if idioma == "es" else "tô gostando de você 😶"
            bot.sendMessage(chat_id, gatilho)

        if count == 8:
            idioma = idioma_usuario.get(user_id, "pt")
            gatilho = "you talk like this to others? 😏" if idioma == "en" else "¿hablas así con otras? 😏" if idioma == "es" else "vc fala assim com outras? 😏"
            bot.sendMessage(chat_id, gatilho)

        # DELAY HUMANO
        time.sleep(random.randint(1, 3))

        resposta = gerar_resposta_ia(user_id, texto)
        bot.sendMessage(chat_id, resposta)

    except Exception as e:
        print("Erro:", e)

# =========================
# REENGAJAMENTO MULTILINGUE
# =========================
def reengajar():
    while True:
        agora = time.time()
        for user_id, last in list(ultimo_contato.items()):
            if agora - last > random.randint(259200, 432000):
                try:
                    idioma = idioma_usuario.get(user_id, "pt")
                    msg = random.choice([
                        "hey… disappeared? 😔" if idioma == "en" else "ey… desapareciste? 😔" if idioma == "es" else "ei… sumiu? 😔",
                        "was liking our chat…" if idioma == "en" else "me gustaba charlar…" if idioma == "es" else "tava gostando de falar…",
                        "always ghost like this? 😶" if idioma == "en" else "¿siempre haces ghost? 😶" if idioma == "es" else "sempre some assim? 😶"
                    ])
                    bot.sendMessage(user_id, msg)
                    ultimo_contato[user_id] = agora + 86400
                except:
                    pass
        time.sleep(60)

# =========================
# START
# =========================
print("🤖 Lunna MULTILINGUE rodando...")

MessageLoop(bot, handle).run_as_thread()
threading.Thread(target=reengajar, daemon=True).start()

while True:
    time.sleep(10)