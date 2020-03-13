from telebot import TeleBot
from threading import Thread
from time import sleep
from requests.exceptions import InvalidSchema, InvalidURL, MissingSchema
import json

from spacebot.app.find_html_components import check, find_subject_name
from spacebot.app.constants import bot_token

bot = TeleBot(bot_token)

urls_to_subjects_dict = {}
user_threads = {}


def get_users_data():
    try:
        with open('users_data.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError as e:
        from os import listdir
        from sys import stderr
        print(listdir(), file=stderr)
        with open('users_data.json', 'w') as f:
            json.dump({}, f)
        with open('users_data.json') as f:
            return json.load(f)


@bot.message_handler(commands=['remove'], func=lambda message: 'https://my.ukma.edu.ua/course/' in message.text)
def remove(message):
    chat_id = message.chat.id
    url_to_remove = ""
    try:
        url_to_remove = message.text.split(' ')[1]
        subject_name = find_subject_name(url_to_remove)
    except IndexError:
        bot.send_message(chat_id, "You must specify a URL to subject after /remove command.")
        return
    except (InvalidURL, InvalidSchema, MissingSchema, AttributeError):
        bot.send_message(chat_id, f"Invalid URL: \"{url_to_remove}\". Cannot find related subject.")
        return

    if urls_to_subjects_dict.get(chat_id) and url_to_remove in urls_to_subjects_dict[chat_id]:
        urls_to_subjects_dict[chat_id].remove(url_to_remove)
        users_data = get_users_data()
        with open('users_data.json', 'w') as f:
            chat_id = str(chat_id)
            if users_data.get(chat_id) and url_to_remove in users_data[chat_id]['subjects']:
                users_data[chat_id]['subjects'].remove(url_to_remove)
            json.dump(users_data, f)

        bot.send_message(chat_id, "Removed subject \"%s\"." % subject_name)
    else:
        bot.send_message(chat_id, "Subject \"%s\" didn't find in your list." % subject_name)


@bot.message_handler(commands=['remove'])
def remove(message):
    bot.send_message(message.chat.id, "To remove the subject from looking for list, types:\n"
                                      "/remove <URL to subject>")


@bot.message_handler(commands=['look_for'])
def look_for_free_space(message):
    users_data = get_users_data()
    user_id = str(message.chat.id)
    if users_data.get(user_id) and users_data[user_id].get('running'):
        bot.send_message(int(user_id), "You are already looking for free space.")
        info(message)
        return
    elif not urls_to_subjects_dict.get(int(user_id)):
        bot.send_message(int(user_id), "Your looking for list is empty. Add some subjects first.")
        info(message)
        return
    try:
        interval = int(message.text.split()[1])
    except ValueError:
        bot.send_message(int(user_id), f"Please, give an integer. "
                                       f"<b>{message.text.split()[1]}</b> cannot be interpreted as an integer.",
                         parse_mode='HTML')
        interval = 120
    except IndexError:
        interval = 120
    chat_id = message.chat.id
    start_thread(chat_id, interval)
    bot.send_message(message.chat.id, f"You are now will receive information about free space every <b>{interval}</b> "
                                      "seconds.", parse_mode='HTML')


@bot.message_handler(commands=['stop_look_for'])
def stop_look_for_free_space(message):
    chat_id = message.chat.id
    if user_threads.get(chat_id):
        user_threads[chat_id].terminate()
        user_threads[chat_id].join()

        users_data = get_users_data()
        with open('users_data.json', 'w') as f:
            user_id = str(message.chat.id)
            if users_data.get(user_id):
                users_data[user_id]['running'] = False
            json.dump(users_data, f)

        bot.send_message(chat_id, "Looking for a free space on subjects was stopped.")
    else:
        bot.send_message(chat_id, "You haven't been looking for free space...")


@bot.message_handler(commands=['list'])
def subjects_list(message):
    user_id = message.chat.id
    if urls_to_subjects_dict.get(user_id):
        bot.send_message(user_id, '\n'.join(
            [f'•<a href="{url}">{find_subject_name(url)}</a>\n' for url in urls_to_subjects_dict[user_id]]),
                         parse_mode='HTML')
    else:
        bot.send_message(user_id, "You haven't got any subjects in the search list yet.")


@bot.message_handler(content_types='text', func=lambda message: 'https://my.ukma.edu.ua/course/' in message.text)
def add_subject(message):
    user_id = message.chat.id
    for url in message.text.split('\n'):
        url = url.strip()
        try:
            subject_name = find_subject_name(url)
        except (InvalidSchema, InvalidURL, MissingSchema, AttributeError):
            bot.send_message(user_id, "Invalid link: \"%s\". Cannot find related subject." % url)
            continue
        if urls_to_subjects_dict.get(user_id):
            if url not in urls_to_subjects_dict[user_id]:
                urls_to_subjects_dict[user_id].append(url)
            else:
                bot.send_message(user_id,
                                 f'The subject <a href="{url}">{subject_name}</a> is already being looking for.',
                                 parse_mode='HTML')
                continue
        else:
            urls_to_subjects_dict[user_id] = []
            urls_to_subjects_dict[user_id].append(url)
        users_data = get_users_data()
        with open('users_data.json', 'w') as f:
            chat_id = str(user_id)
            if users_data.get(chat_id):
                users_data[chat_id]['subjects'].append(url)
            else:
                user_data = {'subjects': []}
                user_data['subjects'].append(url)
                user_data['running'] = False
                users_data[chat_id] = user_data
            json.dump(users_data, f)

        bot.send_message(user_id, "Added subject %s" % subject_name)


@bot.message_handler(content_types='text')
def info(message):
    bot.send_message(message.chat.id,
                     """
To add a subject to searching list, send me its URL in the format
<a href="https://my.ukma.edu.ua/course/242190">https://my.ukma.edu.ua/course/242190</a>
Then type /look_for command and I'll notify you if someone left the group and there is a free space.
Good luck.)😉
    """, parse_mode='HTML')


def start_thread(chat_id, interval):
    if user_threads.get(chat_id):
        user_threads[chat_id].terminate()
        user_threads[chat_id].join()

    thread = LookForFreeSpaceTask(chat_id, interval)
    thread.setDaemon(True)
    thread.start()
    user_threads[chat_id] = thread

    users_data = get_users_data()
    with open('users_data.json', 'w') as f:
        chat_id = str(chat_id)
        if users_data.get(chat_id):
            users_data[chat_id]['running'] = True
            users_data[chat_id]['interval'] = interval
        json.dump(users_data, f)


def restore_users():
    users_data = get_users_data()
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
            if not len(messages):
                continue
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
