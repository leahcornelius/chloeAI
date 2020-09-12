# Copyright (c) 2020 Leo Cornelius
#  Licensed under the MIT license.

import configparser
import argparse
import logging
import random

from model import download_model_folder, download_reverse_model_folder, load_model
from decoder import generate_response
import flask
from flask_cors import CORS, cross_origin
from flask_ngrok import run_with_ngrok

app = flask.Flask(__name__)
cors = CORS(app)
run_with_ngrok(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config["DEBUG"] = True
turns = []
model = None
tokenizer = None
config = None
mmi_model = None
mmi_tokenizer = None

admin_users = ['leocornelius', 'nathanarnold']


@app.route('/', methods=['GET'])
@cross_origin()
def home():
    return 'Error: No method defined. Please define a method'


@app.route('/get_response/<user_msg>', methods=['GET'])
@cross_origin()
def get_response(user_msg):
    global config
    global model
    global tokenizer
    global mmi_model
    global mmi_tokenizer
    global turns
    max_turns_history = 5  # config.getint('decoder', 'max_turns_history')
    prompt = user_msg
    print("User >>> {}".format(prompt))
    if (max_turns_history == 0 or prompt.lower() == "reset"):
        # we are not using config, purge the context buffer
        turns = []
    else:
        num_samples = 1  # config.getint('decoder', 'num_samples')
        turn = {
            'user_messages': [],
            'bot_messages': []
        }
        turns.append(turn)
        turn['user_messages'].append(prompt)
        # Merge turns into a single history (don't forget EOS token)
        history = ""
        from_index = max(len(turns)-max_turns_history-1,
                         0) if max_turns_history >= 0 else 0
        for turn in turns[from_index:]:
         # Each turn begings with user messages
            for message in turn['user_messages']:
                history += message + tokenizer.eos_token
            for message in turn['bot_messages']:
                history += message + tokenizer.eos_token
        # Generate bot messages
        bot_messages = generate_response(
            model,
            tokenizer,
            history,
            config,
            mmi_model=mmi_model,
            mmi_tokenizer=mmi_tokenizer
        )
        if num_samples == 1:
            bot_message = bot_messages[0]
        else:
            # TODO: Select a message that is the most appropriate given the context
            # This way you can avoid loops
            bot_message = random.choice(bot_messages)
        print("Bot >>>", bot_message)
        turn['bot_messages'].append(bot_message)
        return bot_message


# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    global config
    global model
    global tokenizer
    global mmi_model
    global mmi_tokenizer
    global turns
    turns = []
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

    app.run()


if __name__ == '__main__':
    main()
