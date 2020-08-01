import requests
from constants import MAIN_BOT_ID, NOTIFY_BOT_ID, GROUPME_BOT_URL

def send_message_to_main_channel(message_text):
  requests.post(url=GROUPME_BOT_URL, json={ 'bot_id': MAIN_BOT_ID, 'text': message_text })

def send_info_message(message_text):
  requests.post(url=GROUPME_BOT_URL, json={ 'bot_id': NOTIFY_BOT_ID, 'text': message_text})
