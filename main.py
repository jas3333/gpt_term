#!/usr/bin/env python
import os
import json
from rich import print
from rich.markdown import Markdown
from dotenv import load_dotenv
from lib.openlib import OpenAI


from tools.functions import handle_user_input, save_conversation

# Get API key
load_dotenv()
api_key = os.getenv("open_ai_key")
brave_api = os.getenv("brave_api")
assistant_id = os.getenv("assistant_id")

client = OpenAI(api_key=api_key, brave_api=brave_api)
client.assistant_id = str(assistant_id)
client.load_thread()
assistants = client.list_assistants()


conversation = []


while True:
    if client.debug_mode == True:
        user_input = input("Debug mode enabled: ")
    else:
        user_input = input(f"\n[{client.assistant_name}]: ")

    print("-------------------------------------------------------------------------")

    if user_input == "quit" or user_input == "q":
        break
    elif user_input == "save":
        save_conversation(conversation)
    elif handle_user_input(user_input, client):
        gpt_output = client.output()
        conversation.append(gpt_output)
        markdown = Markdown(gpt_output, code_theme="one-dark")
        print(markdown)

    print("-------------------------------------------------------------------------")
