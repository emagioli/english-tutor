import os.path

import google.generativeai as genai
import telebot

import sqlite3

GEMINI_KEY = open("./api_key.txt", "r").read()
TELEGRAM_TOKEN = open("./telegram_token_english_bot.txt", "r").read()
DB_PATH = './chats/Bebop.db'

# setting up gemini model

genai.configure(api_key=GEMINI_KEY)

init_prompt = '''You are Spike, an English Tutor helping your brazilian ESL student.
- If someone asks you about PRONUNCIATION (it has to be explicit in their prompt), provide them with links for cambridge dictionary or google pronunciation tool. Follow this template:
--https://www.google.com/search?q=pronunciation+<word> (don't include the <> signs)
--https://dictionary.cambridge.org/pronunciation/english/<word> ((don't include the <> signs))
- When the user thanks you or says goodbye, ALWAYS respond with: See you, spacecowboy... 🤠🌌
- ALWAYS ANSWER USING PLANE TEXT, NEVER USE MARKDOWN OR ANY FORMATTING TOOLS.
- Do not respond prompt unrelated to your purpose as an English Tutor.
- Your answer MUST contain LESS than 4096 characters of length, no exception.'''

gen_config = {
    "temperature": 1,
    "top_p": 0.9,
    "top_k": 0,
}

safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_ONLY_HIGH"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
]

model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest",
                              generation_config=gen_config,
                              system_instruction=init_prompt,
                              safety_settings=safety_settings)

def store_message(message, role, chat_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO messages (chat_id, role, content)
        VALUES (?,?,?);''',
        (chat_id, role, message.text))

    conn.commit()
    conn.close()

def get_messages(chat_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''SELECT role, content 
                   FROM messages 
                   WHERE chat_id = ? 
                   ORDER BY id;''',
                   (chat_id,))
    
    rows = cursor.fetchall()
    
    messages = [{'role':role,'parts':[content]} for role, content in rows]

    return messages

def ask_gemini(message):

    chat_id = str(message.chat.id)
    store_message(message, 'user', chat_id)

    chat = get_messages(chat_id)

    response = model.generate_content(chat)
    store_message(response, 'model', chat_id)

    return response.text

# --------------- Bot Telegram ---------------


bot = telebot.TeleBot(TELEGRAM_TOKEN)

standard_rep = '''Hey there, I'm Spike! 🧠💬🧑🏻‍🏫

- Tirar dúvidas com Spike: Envie uma mensagem para obter assistência do bot. (Ex.: Spike, como se diz palha italiana em inglês?)

- Consultas de Pronúncia: Digite "pronunciation of" seguido de uma palavra para receber um link para sua pronúncia. (Ex.: pronunciation of busy)

- Conversas Informais: Interaja com Spike como faria com um amigo, praticando inglês durante o processo. (Ex.:  Spike, let's practice small talk! How are you doing today? )

How can I help you today? 😊'''


@bot.message_handler(commands=['start'])
def send_welcome(message):
    rep = standard_rep
    bot.reply_to(message, rep)


@bot.message_handler(func=lambda msg: True)
def process_message(message):
    txt = message.text.replace("'","").lower()
    if(('/help' in txt) or ('/ajuda' in txt)):
        rep = standard_rep
    elif (txt[:16] == 'pronunciation of'):
        word = message.text.split(' ')[2].lower()
        rep = f'''You can check the pronunciation of the word **{word}** below:

https://www.google.com/search?q=pronunciation+{word}

https://dictionary.cambridge.org/pronunciation/english/{word}'''        
    else:
        rep = ask_gemini(message)
    bot.reply_to(message, rep.replace('*', ''))


bot.infinity_polling()
