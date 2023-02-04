# Ultroid - UserBot
# Copyright (C) 2021-2022 TeamUltroid
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ >
# PLease read the GNU Affero General Public License in
# <https://www.github.com/TeamUltroid/Ultroid/blob/main/LICENSE/>.

from . import get_help

__doc__ = get_help("help_chatbot")


from pyUltroid.fns.tools import get_chatbot_reply

from . import eod, get_string, inline_mention, udB, ultroid_cmd, LOGS

import requests
import re


url = "https://bumcomingo.simsimi.com/simtalk/get_talk_set"
headers = {
    'accept': 'application/json, text/plain, */*',
    'os': 'a',
    'av': '8.4.4',
    'appcheck': '',
    'Content-Type': 'application/json',
    'Content-Length': '159',
    'Host': 'bumcomingo.simsimi.com',
    'Connection': 'Keep-Alive',
    'Accept-Encoding': 'gzip',
    'User-Agent': 'okhttp/4.9.1'
}

@ultroid_cmd(pattern="repai")
async def im_lonely_chat_with_me(event):
    if event.reply_to:
        message = (await event.get_reply_message()).message
    else:
        try:
            message = event.text.split(" ", 1)[1]
        except IndexError:
            return await eod(event, get_string("tban_1"), time=10)
    payload = {
          "uid": 414477568,
          "av": "8.4.4",
          "os": "a",
          "lc": "en",
          "cc": "UK",
          "tz": "Europe/London",
          "cv": "",
          "message": message,
          "free_level": 1,
          "logUID": "414477568",
          "reg_now_days": 0
        }
    response = requests.post(url, json=payload, headers=headers)
    try:
         out = response.json()['sentence']
    except:
         out = response.json()['detail']
    out = re.sub('@[a-zA-Z]{3,}', '،', out)
    out = re.sub(r'[0-9]+', '', out)
    await event.eor(out)


@ultroid_cmd(pattern="addai")
async def add_chatBot(event):
    await chat_bot_fn(event, type_="add")


@ultroid_cmd(pattern="remai")
async def rem_chatBot(event):
    await chat_bot_fn(event, type_="remov")


@ultroid_cmd(pattern="listai")
async def lister(event):
    key = udB.get_key("CHATBOT_USERS") or {}
    users = key.get(event.chat_id, [])
    if not users:
        return await event.eor(get_string("chab_2"), time=5)
    msg = "**Total List Of AI Enabled Users In This Chat :**\n\n"
    for i in users:
        try:
            user = await event.client.get_entity(int(i))
            user = inline_mention(user)
        except BaseException:
            user = f"`{i}`"
        msg += f"• {user}\n"
    await event.eor(msg, link_preview=False)


async def chat_bot_fn(event, type_):
    if event.reply_to:
        user_ = (await event.get_reply_message()).sender
    else:
        temp = event.text.split(maxsplit=1)
        try:
            user_ = await event.client.get_entity(await event.client.parse_id(temp[1]))
        except BaseException as er:
            LOGS.exception(er)
            user_ = event.chat if event.is_private else None
    if not user_:
        return await eod(
                event,
                get_string("chab_1"),
        )
    key = udB.get_key("CHATBOT_USERS") or {}
    chat = event.chat_id
    user = user_.id
    if type_ == "add":
        if key.get(chat):
            if user not in key[chat]:
                key[chat].append(user)
        else:
            key.update({chat: [user]})
    elif type_ == "remov":
        if key.get(chat):
            if user in key[chat]:
                key[chat].remove(user)
            if chat in key and not key[chat]:
                del key[chat]
    udB.set_key("CHATBOT_USERS", key)
    await event.eor(f"**ChatBot:**\n{type_}ed {inline_mention(user_)}")