#!/usr/bin/python
# -*- coding: utf-8 -*-
#  Copyright (c) leo cornelius
#  Licensed under the MIT license.

import configparser
import argparse
import logging
import random

from model import download_model_folder, download_reverse_model_folder, \
    load_model
from decoder import generate_response

from python_omegle import RandomChat
from python_omegle import ChatEvent

# Enable logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                    , level=logging.INFO)
logger = logging.getLogger(__name__)


def chat_loop(
    chat,
    model,
    tokenizer,
    config,
    mmi_model=None,
    mmi_tokenizer=None,
    spyMode=False
    ):
    file = open('omegleCHAT.txt', 'w+')
    while True:

        # Start a new chat every time the old one ends
        # Parse parameters

        num_samples = config.getint('decoder', 'num_samples')
        max_turns_history = config.getint('decoder', 'max_turns_history'
                )

        logger.info('Running the chatbot...')
        turns = []
        print ('- Starting chat -')
        chat.start()
        while True:
            (event, argument) = chat.get_event()
            if event == ChatEvent.CHAT_WAITING:
                print ('- Waiting for a partner -')
            elif event == ChatEvent.CHAT_READY:
                file.write('- Chat started with user - \r\n')
                print ('- Connected to a partner -')
                if (spyMode):
                    chat.start_typing()
                    response = generate_response(
                        model,
                        tokenizer,
                        argument + tokenizer.eos_token,
                        config,
                        mmi_model=mmi_model,
                        mmi_tokenizer=mmi_tokenizer,
                    )
                    chat.send(response)
                    print("Bot: {}".format(response))
                    file.write("(SPYMODE)Bot: {} \r\n".format(response))
                    chat.stop_typing()
                else:
                    print("Bot: Hey!")
                    chat.send("Hey!")
                    file.write("Bot: Hey \r\n")

                break

        # Connected to a partner

        while True:
            (event, argument) = chat.get_event()
            if event == ChatEvent.GOT_SERVER_NOTICE:
                notice = argument
                print ('- Server notice: {} -'.format(notice))
            elif event == ChatEvent.PARTNER_STARTED_TYPING:

                print ('- Partner started typing -')
            elif event == ChatEvent.PARTNER_STOPPED_TYPING:
                print ('- Partner stopped typing -')
            elif event == ChatEvent.GOT_MESSAGE:
                message = argument
                print ('Partner: {}'.format(message))
                prompt = message
                chat.start_typing()
                if max_turns_history == 0:

                     # If you still get different responses then set seed

                    turns = []
                if prompt.lower() == 'bye':
                    print ('Bot >>>', 'Bye')
                    turns = []
                    continue
                if prompt.lower() == 'quit':
                    break

                # A single turn is a group of user messages and bot responses right after

                turn = {'user_messages': [], 'bot_messages': []}
                turns.append(turn)
                turn['user_messages'].append(prompt)

                # Merge turns into a single history (don't forget EOS token)

                history = ''
                from_index = (max(len(turns) - max_turns_history - 1,
                              0) if max_turns_history >= 0 else 0)
                for turn in turns[from_index:]:

                     # Each turn begings with user messages

                    for message in turn['user_messages']:
                        history += message + tokenizer.eos_token
                    for message in turn['bot_messages']:
                        history += message + tokenizer.eos_token
                print('generating response')

                # Generate bot messages

                bot_messages = generate_response(
                    model,
                    tokenizer,
                    history,
                    config,
                    mmi_model=mmi_model,
                    mmi_tokenizer=mmi_tokenizer,
                    )

                if num_samples == 1:
                    bot_message = bot_messages[0]
                else:

                  # TODO: Select a message that is the most appropriate given the context
                  # This way you can avoid loops

                    bot_message = random.choice(bot_messages)
                chat.stop_typing()
                chat.send(bot_message)
                print('Bot: {}!'.format(bot_message))
                file.write('User: {} \r\n'.format(message))
                file.write('Bot: {} \r\n'.format(bot_message))
                turn['bot_messages'].append(bot_message)
            elif event == ChatEvent.CHAT_ENDED:
                print ('- Chat ended -')
                file.write('- Chat ended with user - \r\n')
                break


def main():
    spymode = False

    # Script arguments can include path of the config

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--config', type=str, default='chatbot.cfg')
    args = arg_parser.parse_args()

    # Read the config

    config = configparser.ConfigParser(allow_no_value=True)
    with open(args.config) as f:
        config.read_file(f)

    # Download and load main model

    target_folder_name = download_model_folder(config)
    (model, tokenizer) = load_model(target_folder_name, config)

    # Download and load reverse model

    use_mmi = config.getboolean('model', 'use_mmi')
    if use_mmi:
        mmi_target_folder_name = download_reverse_model_folder(config)
        (mmi_model, mmi_tokenizer) = load_model(mmi_target_folder_name,
                config)
    else:
        mmi_model = None
        mmi_tokenizer = None

    # Run chatbot with GPT-2
    # run_chat(model, tokenizer, config, mmi_model=mmi_model, mmi_tokenizer=mmi_tokenizer)
    if (spymode):
        chat = SpyeeChat()
        chat_loop(
            chat,
            model,
            tokenizer,
            config,
            mmi_model=mmi_model,
            mmi_tokenizer=mmi_tokenizer,
            spyMode=spymode
            )
    else:
        chat = RandomChat()
        chat_loop(
            chat,
            model,
            tokenizer,
            config,
            mmi_model=mmi_model,
            mmi_tokenizer=mmi_tokenizer,
            spyMode=spymode
            )


if __name__ == '__main__':
    main()

