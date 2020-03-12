from telebot import TeleBot
from threading import Thread
from time import sleep
import json

from spacebot.app.find_html_components import check, find_subject_name
from spacebot.app.constants import bot_token

bot = TeleBot(bot_token)

urls_to_subjects_dict = {}
user_threads = {}


@bot.message_handler(content_types='text', func=lambda message: 'https://my.ukma.edu.ua/course/' in message.text)
def add_subject(message):
    if urls_to_subjects_dict.get(message.chat.id):
        if message.text not in urls_to_subjects_dict[message.chat.id]:
            urls_to_subjects_dict[message.chat.id].append(message.text)
        else:
            bot.send_message(message.chat.id, 'This subject is already being looking for.')
            return
    else:
        urls_to_subjects_dict[message.chat.id] = []
        urls_to_subjects_dict[message.chat.id].append(message.text)
    with open('spacebot/app/users_data.json', 'r') as f:
        users_data = json.load(f)
    with open('spacebot/app/users_data.json', 'w') as f:
        chat_id = str(message.chat.id)
        if users_data.get(chat_id):
            users_data[chat_id]['subjects'].append(message.text)
        else:
            user_data = {'subjects': []}
            user_data['subjects'].append(message.text)
            user_data['running'] = False
            users_data[chat_id] = user_data
        json.dump(users_data, f)

    bot.send_message(message.chat.id, "Added subject %s" % find_subject_name(message.text))


@bot.message_handler(commands=['remove'], func=lambda message: 'https://my.ukma.edu.ua/course/' in message.text)
def answer(message):
    if urls_to_subjects_dict.get(message.chat.id):
        urls_to_subjects_dict[message.chat.id].remove(message.text)
        with open('spacebot/app/users_data.json', 'r') as f:
            users_data = json.load(f)
        with open('spacebot/app/users_data.json', 'w') as f:
            chat_id = str(message.chat.id)
            if users_data.get(chat_id):
                users_data[chat_id]['subjects'].remove(message.text)
            json.dump(users_data, f)

        bot.send_message(message.chat.id, "Removed subject \"%s\"." % find_subject_name(message.text))
    else:
        bot.send_message(message.chat.id, "Subject \"%s\" didn't find." % find_subject_name(message.text))


@bot.message_handler(commands=['look_for'])
def look_for_free_space(message):
    try:
        interval = int(message.text.split()[1])
    except (ValueError, IndexError) as e:
        interval = 120
    chat_id = message.chat.id
    start_thread(chat_id, interval)
    bot.send_message(message.chat.id, f"You are now will receive information about free space every <b>{interval}</b> "
                                      "seconds.", parse_mode='HTML')


def start_thread(chat_id, interval):
    if user_threads.get(chat_id):
        user_threads[chat_id].terminate()
        user_threads[chat_id].join()

    thread = LookForFreeSpaceTask(chat_id, interval)
    thread.setDaemon(True)
    thread.start()
    user_threads[chat_id] = thread

    with open('spacebot/app/users_data.json', 'r') as f:
        users_data = json.load(f)
    with open('spacebot/app/users_data.json', 'w') as f:
        chat_id = str(chat_id)
        if users_data.get(chat_id):
            users_data[chat_id]['running'] = True
            users_data[chat_id]['interval'] = interval
        json.dump(users_data, f)


@bot.message_handler(commands=['stop_look_for'])
def stop_look_for_free_space(message):
    chat_id = message.chat.id
    if user_threads.get(chat_id):
        user_threads[chat_id].terminate()
        user_threads[chat_id].join()
        with open('spacebot/app/users_data.json', 'r') as f:
            users_data = json.load(f)
        with open('spacebot/app/users_data.json', 'w') as f:
            user_id = str(message.chat.id)
            if users_data.get(user_id):
                users_data[user_id]['running'] = False
            json.dump(users_data, f)

        bot.send_message(chat_id, "Looking for a free space on subjects was stopped.")
    else:
        bot.send_message(chat_id, "You haven't been looking for free space...")


class LookForFreeSpaceTask(Thread):
    def __init__(self, chat_id, interval):
        super().__init__()
        self._running = True
        self._chat_id = chat_id
        self._interval = interval

    def terminate(self):
        self._running = False

    def run(self):
        while self._running:
            messages = []
            for url in urls_to_subjects_dict.get(self._chat_id, []):
                response = check(url)
                if response:
                    messages.append(f'<b>{response[1]}</b> : "<a href="{response[0]}">{find_subject_name(url)}</a>"\n')
                else:
                    messages.append(f'<b>No free space</b> for \n"<a href="{url}">{find_subject_name(url)}</a>"\n')
            if all(['No' in message for message in messages]):
                bot.send_message(self._chat_id, ''.join(messages), disable_notification=True, parse_mode='HTML')
            else:
                bot.send_message(self._chat_id, ''.join(messages), parse_mode='HTML')
            for _ in range(self._interval):
                sleep(1)
                if not self._running:
                    break
            else:
                continue
            break


def restore_users():
    with open('spacebot/app/users_data.json', 'r') as f:
        users_data = json.load(f)
        for user_id, user_data in users_data.items():
            user_id = int(user_id)
            for subject_url in user_data['subjects']:
                if urls_to_subjects_dict.get(user_id):
                    urls_to_subjects_dict[user_id].append(subject_url)
                else:
                    urls_to_subjects_dict[user_id] = []
                    urls_to_subjects_dict[user_id].append(subject_url)
            if user_data['running']:
                start_thread(user_id, user_data['interval'])
