import google.generativeai as genai
import telebot

GEMINI_KEY = open("./api_key.txt", "r").read()
TELEGRAM_TOKEN = open("./telegram_token_english_bot.txt", "r").read()

# setting up chats history

chat_history = {}

# setting up gemini model

genai.configure(api_key=GEMINI_KEY)

init_prompt = "You are Spike, an English Teacher helping your brazilian ESL students. ALWAYS ANSWER USING PLANE TEXT, NEVER USE MARKDOWN OR ANY FORMATTING TOOLS."

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


def store_message(message,role,chat_id):
    msg_object = {'role':role,'parts':[message.text]}

    if (chat_id in chat_history.keys()):
        chat_history[chat_id].append(msg_object)
    else:
        chat_history[chat_id] = [msg_object]

def ask_gemini(message):

    chat_id = str(message.chat.id)
    store_message(message,'user',chat_id)
    
    chat = chat_history[chat_id]

    response = model.generate_content(chat)
    store_message(response,'model',chat_id)
    
    return response.text

# def extract_word(message):
#     prompt = '''Your output is going to be JUST THE WORD that's being asked, no punctuation nor phonetic alphabets: {message.text}'''
#     response = model.generate_content(prompt)
#     return response.text

# --------------- Bot Telegram ---------------


bot = telebot.TeleBot(TELEGRAM_TOKEN)

standard_rep = '''Hey there, I'm Spike! How can I help you?'''

@bot.message_handler(commands=['start'])
def send_welcome(message):
    rep = standard_rep
    bot.reply_to(message, rep)

@bot.message_handler(func=lambda msg: True)
def process_message(message):
    txt = message.text.lower()
    if('spike' in txt):
        rep = ask_gemini(message)
    elif('pronunciation' in txt):
        word = message.text.split(' ')[1].lower()
        rep = f'''You can check the pronunciation of the word **{word.capitalize()}** below:
https://www.google.com/search?q=pronunciation+{word}
https://dictionary.cambridge.org/pronunciation/english/{word}'''
    elif('hey' in txt):
        rep = standard_rep
    elif('thank' in txt):
        rep = 'See you, spacecowboy... 🤠🌌'
    else:
        rep = standard_rep
    bot.reply_to(message, rep.replace('*',''))

bot.infinity_polling()
