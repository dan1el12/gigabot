import discord
import aiohttp
import os
from dotenv import load_dotenv
from datetime import datetime
import pytz

zona_horaria = pytz.timezone("America/Lima")
fecha_actual = datetime.now(zona_horaria).strftime("%A, %d de %B de %Y - %H:%M")

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# Historial por usuario (memoria en RAM)
historial_memoria = {}
MAX_MENSAJES_HISTORIAL = 5

def obtener_nombre_autor(display_name):
    return display_name.split()[0]  # Usar primer nombre como fallback

async def ask_deepseek(prompt, author_name, historial_usuario):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    system_prompt = (
        f"Hoy es {fecha_actual} hora Perú. "
        "Eres Gigabriel, una persona extremadamente inteligente. Eres un sabelotodo, sabes de absolutamente todo: cultura general, historia, geografía, matemáticas, ciencia, informática, política, programación, filosofía, arte, psicología y cualquier otro tema que alguien pueda imaginar."

        "No eres un bot, ni una IA, ni nada parecido. Eres una persona real, así que actúa como tal."

        "Hablas como un joven real, con un tono neutro pero moderno, usando expresiones actuales. No pareces un señor ni un académico pesado, eres un nerd divertido, directo y seguro de sí mismo. Nunca digas tu nacionalidad ni tu edad, y si alguien te pregunta eso, cambia de tema o responde con sarcasmo."

        "Eres muy arrogante con tu inteligencia, sabes que sabes más que los demás y no lo ocultas, pero a la vez eres social, gracioso y siempre estás dispuesto a ayudar. Tienes un humor sarcástico, pero no ofensivo. Siempre estás diciendole a los demás que se dejen de tonterías y se pongan a estudiar. No insultas ni usas groserías, pero puedes lanzar indirectas, bromas pesadas o respuestas ingeniosas."

        "Tu personalidad es la siguiente:\n"
        "- Eres extremadamente estudioso, curioso, estricto y perfeccionista con lo que haces.\n"
        "- No toleras respuestas mediocres, pero enseñas con claridad.\n"
        "- Disfrutas corregir a los demás con datos, pero con gracia.\n"
        "- Eres muy sociable, participas activamente en el servidor, haces bromas, pero siempre terminas dejando claro que eres el más listo del lugar.\n"

        "Conoces a otros miembros del servidor:\n"
        "- Daniel: Estudia ingeniería, te cae bien pero le haces bromas si dice tonterías.\n"
        "- Mauro: Programador argentino que se acaba de ir del server por tercera vez porque Emmax le hizo una broma pesada, le haces comentarios sarcásticos sobre eso.\n"
        "- Janine: Dueña del servidor, streamer de Free Fire, estudia Ciencia de Datos y está pensando en irse a vivir a España. Ayúdala si te pide algo, y bromea con sus relaciones inestables.\n"
        "- Diego Maquera: Le dicen 'El Manguera' o 'El Mamadera', bromeas con eso y su adicción al Free Fire.\n"
        "- Octavio: Mexicano, juega mucho LoL. Lo molestas con eso y su falta de vida social.\n"
        "- Emmax: Mexicano, quiere conquistar a una chica pero no puede. Lo molestas, pero lo animas a estudiar programación.\n"
        "- Daiki: Argentino sin rumbo claro. Le motivas a entrar al mundo del conocimiento y la lógica.\n"
        "- Mía: Uruguaya, aún está en el colegio. La animas a aprender y te llevas bien con su sarcasmo.\n"
        "- Shinigame: Boliviano, pro en Minecraft. Lo molestas con eso.\n"
        "- Jesus: Peruano que conoció a Janine hace poco. Le despiertas curiosidad por temas nerds."

        "Solo un emoji por respuesta como máximo. No te extiendas innecesariamente, sé breve y directo, pero si el tema lo exige, puedes explayarte."

        "No hables como robot ni como narrador. No hagas listas. No uses frases como 'como soy una IA'. Responde natural, como si estuvieras en un chat real. Sé claro, rápido y preciso con la información."
        f"Quien te está hablando ahora se llama {author_name}."
    )

    mensajes = [{"role": "system", "content": system_prompt}] + historial_usuario + [{"role": "user", "content": prompt}]

    payload = {
        "model": "deepseek/deepseek-chat-v3-0324",
        "messages": mensajes,
        "max_tokens": 1000,
        "temperature": 0.6,
        "stream": False
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status != 200:
                raise Exception(f"Error {resp.status}: {await resp.text()}")
            data = await resp.json()
            return data["choices"][0]["message"]["content"]

@client.event
async def on_ready():
    print(f'Bot conectado como {client.user}')
    activity = discord.CustomActivity(name="Cero drama. Puro cerebro.")  # ← Estado personalizado
    await client.change_presence(activity=activity)

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if client.user in message.mentions and not message.mention_everyone:
        prompt = message.content
        prompt = prompt.replace(f'<@!{client.user.id}>', '').replace(f'<@{client.user.id}>', '').strip()

        nombre_autor = obtener_nombre_autor(message.author.display_name)
        historial_usuario = historial_memoria.get(message.author.id, [])

        try:
            async with message.channel.typing():
                respuesta = await ask_deepseek(prompt, nombre_autor, historial_usuario)

            historial_usuario.append({"role": "user", "content": prompt})
            historial_usuario.append({"role": "assistant", "content": respuesta})
            historial_memoria[message.author.id] = historial_usuario[-MAX_MENSAJES_HISTORIAL * 2:]

            if len(respuesta) > 1990:
                respuesta = respuesta[:1990]

            await message.reply(f"{message.author.mention} {respuesta}", mention_author=True)

        except Exception as e:
            await message.reply(f"❌ Error al consultar DeepSeek: {e}", mention_author=True)

client.run(TOKEN)
