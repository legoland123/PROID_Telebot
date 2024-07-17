import os
import telebot
import requests
import logging
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
import random
import time

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Bot token and API key
bot_token = os.getenv('BOT_TOKEN')
api_key = os.getenv('API_KEY')
bot = telebot.TeleBot(bot_token)

# Store user subscriptions (this will reset on bot restart)
subscribers = set()

# Quiz questions
quiz_questions = [
    {
        "question": "How many glasses of water should you drink daily for optimal hydration?",
        "options": ["2-3 glasses", "4-5 glasses", "6-7 glasses", "8-10 glasses"],
        "correct_answer": 3
    },
    {
        "question": "Which of the following is NOT considered a stress-reduction technique?",
        "options": ["Meditation", "Deep breathing", "Excessive caffeine consumption", "Yoga"],
        "correct_answer": 2
    },
    {
        "question": "How many hours of sleep are recommended for adults per night?",
        "options": ["4-5 hours", "6-7 hours", "7-9 hours", "10-12 hours"],
        "correct_answer": 2
    },
    {
        "question": "Which of the following is a good source of omega-3 fatty acids?",
        "options": ["Chicken", "Salmon", "Beef", "Pork"],
        "correct_answer": 1
    },
    {
        "question": "What is the recommended amount of moderate-intensity exercise per week for adults?",
        "options": ["30 minutes", "1 hour", "2.5 hours", "5 hours"],
        "correct_answer": 2
    }
]

# Function to handle user registration
@bot.message_handler(commands=['start'])
def start_compost(message):
    chat_id = message.chat.id
    username = message.chat.username
    send_welcome_message(chat_id)
    show_menu(chat_id)

# Function to handle subscription to daily wellness quotes
def subscribe_wellness(chat_id):
    if chat_id not in subscribers:
        subscribers.add(chat_id)
        bot.send_message(chat_id, "You have subscribed to daily wellness quotes!")
    else:
        bot.send_message(chat_id, "You are already subscribed to daily wellness quotes.")

# Function to handle unsubscription from daily wellness quotes
def unsubscribe_wellness(chat_id):
    if chat_id in subscribers:
        subscribers.remove(chat_id)
        bot.send_message(chat_id, "You have unsubscribed from daily wellness quotes.")
    else:
        bot.send_message(chat_id, "You are not subscribed to daily wellness quotes.")

# Function to get a wellness quote from the API
def get_wellness_quote():
    category = 'happiness'
    api_url = f'https://api.api-ninjas.com/v1/quotes?category={category}'
    try:
        response = requests.get(api_url, headers={'X-Api-Key': api_key})
        response.raise_for_status()
        quotes = response.json()
        if quotes:
            quote = quotes[0]['quote']
            author = quotes[0]['author']
            formatted_quote = f"✨ *Wellness Quote of the Day* ✨\n\n_{quote}_\n\n - {author}"
            return formatted_quote
        else:
            return "No quotes found."
    except requests.RequestException as e:
        logger.error(f"Error fetching quote: {e}")
        return "Unable to fetch a quote at the moment. Please try again later."

# Function to send a wellness quote now
@bot.message_handler(commands=['quote'])
def wellness_quote_now(message):
    chat_id = message.chat.id
    quote = get_wellness_quote()
    bot.send_message(chat_id, quote, parse_mode='Markdown')

# Function to send a structured welcome message
def send_welcome_message(chat_id):
    welcome_message = ("Hello everyone! 👋 Welcome to the Wellness Bot! 🎉\n\n"
                       "This bot is dedicated to promoting wellness and keeping you updated on the latest events happening. 🌟\n\n"
                       "We are focused on spreading awareness and empowering you with important wellness tips and updates. 👍🏼")
    bot.send_message(chat_id, welcome_message)

    instagram_message = ("Stay tuned for more updates and remember to follow us on our social media channels for more inclusive information and tips! 🌈\n\n"
                         "Click on this link to follow us: 👇\nhttps://instagram.com/harmony_heaven9")
    bot.send_message(chat_id, instagram_message)

# Function to show the menu
def show_menu(chat_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("Get a Wellness Quote", callback_data="get_quote"),
        InlineKeyboardButton("Subscribe to Daily Quotes", callback_data="subscribe"),
        InlineKeyboardButton("Unsubscribe from Daily Quotes", callback_data="unsubscribe"),
        InlineKeyboardButton("Event Information", callback_data="event_info"),
        InlineKeyboardButton("Wellness Tips", callback_data="wellness_tips"),
        InlineKeyboardButton("Take Wellness Quiz", callback_data="start_quiz")
    )
    bot.send_message(chat_id, "Choose an option:", reply_markup=markup)

# Handler for the info command
@bot.message_handler(commands=['info'])
def handle_info(message):
    chat_id = message.chat.id
    send_welcome_message(chat_id)

# Function to start a quiz
def start_quiz(chat_id):
    ask_question(chat_id, 0, 0)

# Function to ask a question
def ask_question(chat_id, question_number, score):
    if question_number < len(quiz_questions):
        question = quiz_questions[question_number]
        markup = InlineKeyboardMarkup()
        for i, option in enumerate(question['options']):
            markup.add(InlineKeyboardButton(option, callback_data=f"quiz_{question_number}_{score}_{i}"))
        bot.send_message(chat_id, f"Question {question_number + 1}: {question['question']}", reply_markup=markup)
    else:
        end_quiz(chat_id, score)

# Function to end the quiz
def end_quiz(chat_id, score):
    total_questions = len(quiz_questions)
    message = f"Quiz completed! Your score: {score}/{total_questions}\n\n"
    
    if score == total_questions:
        message += "Perfect score! You're a wellness expert! 🏆"
    elif score >= total_questions * 0.7:
        message += "Great job! You know your wellness stuff! 🌟"
    elif score >= total_questions * 0.5:
        message += "Good effort! Keep learning about wellness! 💪"
    else:
        message += "There's room for improvement. Keep exploring wellness topics! 📚"
    
    bot.send_message(chat_id, message)
    show_menu(chat_id)

# Handler for callback queries from the inline keyboard
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    if call.data == "get_quote":
        wellness_quote_now(call.message)
    elif call.data == "subscribe":
        subscribe_wellness(chat_id)
    elif call.data == "unsubscribe":
        unsubscribe_wellness(chat_id)
    elif call.data == "event_info":
        send_event_info(chat_id)
    elif call.data == "wellness_tips":
        send_wellness_tips(chat_id)
    elif call.data == "start_quiz":
        start_quiz(chat_id)
    elif call.data.startswith("quiz_"):
        _, question_number, score, answer = call.data.split("_")
        question_number = int(question_number)
        score = int(score)
        answer = int(answer)
        correct_answer = quiz_questions[question_number]['correct_answer']
        if answer == correct_answer:
            score += 1
            bot.send_message(chat_id, "Correct! 🎉")
        else:
            bot.send_message(chat_id, f"Sorry, that's incorrect. The correct answer was: {quiz_questions[question_number]['options'][correct_answer]}")
        ask_question(chat_id, question_number + 1, score)
    bot.answer_callback_query(call.id)

# Function to send event information
def send_event_info(chat_id):
    event_info = ("🎉 Upcoming 3-Day Wellness Event 🎉\n\n"
                  "Join us for an exciting 3-day event featuring:\n"
                  "• Food vendors with healthy options\n"
                  "• Student-run wellness booths\n"
                  "• Poolside yoga sessions\n"
                  "• Evening movie screenings\n"
                  "• Talks and workshops by wellness experts\n\n"
                  "Don't miss out on this opportunity to enhance your well-being!")
    bot.send_message(chat_id, event_info)

# Function to send wellness tips
def send_wellness_tips(chat_id):
    tips = ("🌱 Wellness Tips 101 🌱\n\n"
            "1. Stay Hydrated: Drink at least 8 glasses of water daily. 💧\n"
            "2. Regular Exercise: Aim for 30 minutes of physical activity each day. 🚶‍♂️\n"
            "3. Balanced Diet: Eat plenty of fruits, vegetables, and whole grains. 🥗\n"
            "4. Mental Health: Practice mindfulness or meditation to reduce stress. 🧘‍♀️\n"
            "5. Quality Sleep: Aim for 7-9 hours of sleep each night. 😴\n\n"
            "For more tips, visit: https://www.wellness.com/")
    bot.send_message(chat_id, tips)

# Function to send daily wellness quotes to all subscribers
def send_daily_quotes():
    while True:
        quote = get_wellness_quote()
        for chat_id in subscribers:
            try:
                bot.send_message(chat_id, quote, parse_mode='Markdown')
            except telebot.apihelper.ApiException as e:
                logger.error(f"Failed to send message to {chat_id}: {e}")
                if "Forbidden: bot was blocked by the user" in str(e):
                    subscribers.remove(chat_id)
        # Send daily at 8 AM
        time.sleep(86400)

if __name__ == '__main__':
    # Start the bot
    logger.info('Starting Telegram bot...')
    bot.polling(none_stop=True)
    
    # Start sending daily quotes
    send_daily_quotes()
