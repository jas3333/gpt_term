#!/usr/bin/env python
import os
import logging

from rich import print
from rich.markdown import Markdown
from dotenv import load_dotenv
from lib.openlib import OpenAI


from tools.functions import handle_user_input, save_conversation, truncate

# Get API key
load_dotenv()
api_key = os.getenv("open_ai_key")
brave_api = os.getenv("brave_api")
assistant_id = os.getenv("assistant_id")

client = OpenAI(api_key=api_key, brave_api=brave_api)
client.assistant_id = str(assistant_id)
client.load_thread()
assistants = client.list_assistants()

# Logging
FORMAT = "%(message)s - %(levelname)s - %(message)s"

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    filename="logs.log",
    level=logging.INFO,
    format=FORMAT,
    filemode="w",
)

conversation = []


while True:
    user_input = input(f"\n[{client.assistant_name} | {truncate(client.thread_title, 5)}]: ")

    print("-------------------------------------------------------------------------")

    if user_input == "quit" or user_input == "q":
        break
    elif user_input == "save":
        save_conversation(conversation)
    elif handle_user_input(user_input, client):
        gpt_output = client.output()
        conversation.append(gpt_output)
        markdown = Markdown(gpt_output, code_theme="one-dark")
        print()
        print(markdown)

    print("-------------------------------------------------------------------------")
