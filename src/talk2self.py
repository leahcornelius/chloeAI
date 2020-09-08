import discord
from functools import wraps
import configparser
import argparse
import logging
import requests
from urllib.parse import urlencode
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import random
import re

from model import download_model_folder, download_reverse_model_folder, load_model
from decoder import generate_response

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def translate_message_to_gif(message, config):
    # https://engineering.giphy.com/contextually-aware-search-giphy-gets-work-specific/
    params = {
        'api_key': config.get('chatbot', 'giphy_token'),
        's': message,
        'weirdness': config.getint('chatbot', 'giphy_weirdness')
    }
    url = "http://api.giphy.com/v1/gifs/translate?" + urlencode(params)
    response = requests_retry_session().get(url)
    return response.json()['data']['images']['fixed_height']['url']

def gpt_normalize(txt):
    txt = re.sub(r"[^A-Za-z0-9()\[\]:,.!?'“”\"]", " ", txt) # remove illegal chars
    return ' '.join(txt.strip().split()) # remove unnecessary spaces

def message(self, message, context):
    # Parse parameters
    num_samples = self.config.getint('decoder', 'num_samples')
    max_turns_history = self.config.getint('decoder', 'max_turns_history')
    if 'turns' not in context.chat_data:
        context.chat_data['turns'] = []
    turns = context.chat_data['turns']

    user_message = message
    if user_message.lower() == 'bye':
        # Restart chat
        context.chat_data['turns'] = []
        update.message.reply_text("Bye")
        return None
    return_gif = False
    if '@gif' in user_message:
        # Return gif
        return_gif = True
        user_message = user_message.replace('@gif', '').strip()
    if max_turns_history == 0:
        # If you still get different responses then set seed
        context.chat_data['turns'] = []
    # A single turn is a group of user messages and bot responses right after
    turn = {
        'user_messages': [],
        'bot_messages': []
    }
    turns.append(turn)
    turn['user_messages'].append(user_message)
    logger.info(f"{update.effective_message.chat_id} - User >>> {user_message}")
    # Merge turns into a single history (don't forget EOS token)
    history = ""
    from_index = max(len(turns)-max_turns_history-1, 0) if max_turns_history >= 0 else 0
    for turn in turns[from_index:]:
        # Each turn begings with user messages
        for message in turn['user_messages']:
            history += gpt_normalize(message) + self.tokenizer.eos_token
        for message in turn['bot_messages']:
            history += gpt_normalize(message) + self.tokenizer.eos_token

    # Generate bot messages
    bot_messages = generate_response(
        self.model, 
        self.tokenizer, 
        history, 
        self.config, 
        mmi_model=self.mmi_model, 
        mmi_tokenizer=self.mmi_tokenizer
    )
    if num_samples == 1:
        bot_message = bot_messages[0]
    else:
        # TODO: Select a message that is the most appropriate given the context
        # This way you can avoid loops
        bot_message = random.choice(bot_messages)
    turn['bot_messages'].append(bot_message)
    logger.info(f"{update.effective_message.chat_id} - Bot >>> {bot_message}")
    if return_gif:
        # Return response as GIF
        gif_url = translate_message_to_gif(bot_message, self.config)
        context.bot.send_animation(update.effective_message.chat_id, gif_url)
    else:
        # Return response as text
        update.message.reply_text(bot_message)
        

def error(update, context):
    logger.warning(context.error)

class TelegramBot:
    def __init__(self, model, tokenizer, config, mmi_model=None, mmi_tokenizer=None):
        logger.info("Initializing the bot...")

        # Set global variables
        self.model = model
        self.tokenizer = tokenizer
        self.mmi_model = mmi_model
        self.mmi_tokenizer = mmi_tokenizer
        self.config = config

        # Set up Telegram bot
        self.updater = Updater(config.get('chatbot', 'telegram_token'), use_context=True)
        dp = self.updater.dispatcher

        # on different commands - answer in Telegram
        # conversation with bot
        dp.add_handler(MessageHandler(Filters.text, self_decorator(self, message)))

        # chatbot settings
        dp.add_handler(CommandHandler('start', start_command))

        # log all errors
        dp.add_error_handler(error)

    def run_chat(self):
        logger.info("Running the chatbot...")

        # Start the Bot
        self.updater.start_polling()

        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        self.updater.idle()

def main():
    # Script arguments can include path of the config
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--config', type=str, default="chatbot.cfg")
    args = arg_parser.parse_args()

    # Read the config
    config = configparser.ConfigParser(allow_no_value=True)
    with open(args.config) as f:
        config.read_file(f)

    # Download and load main model
    target_folder_name = download_model_folder(config)
    model, tokenizer = load_model(target_folder_name, config)

    # Download and load reverse model
    use_mmi = config.getboolean('model', 'use_mmi')
    if use_mmi:
        mmi_target_folder_name = download_reverse_model_folder(config)
        mmi_model, mmi_tokenizer = load_model(mmi_target_folder_name, config)
    else:
        mmi_model = None
        mmi_tokenizer = None
    
    # Run Telegram bot
    bot = TelegramBot(model, tokenizer, config, mmi_model=mmi_model, mmi_tokenizer=mmi_tokenizer)
    bot.run_chat()
    
if __name__ == '__main__':
    main()

client = discord.Client()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    await message.channel.send("YOYO");

client.run('NzUxNDk0MTE4MTI3MDQyNjAw.X1J5bw.gOcsL79EEOY1bisfLjVulnPguTo')
