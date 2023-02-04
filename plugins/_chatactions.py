# Ultroid - UserBot
# Copyright (C) 2021-2022 TeamUltroid
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ >
# PLease read the GNU Affero General Public License in
# <https://www.github.com/TeamUltroid/Ultroid/blob/main/LICENSE/>.

import asyncio
import re
import requests
from telethon import events
from telethon.errors.rpcerrorlist import UserNotParticipantError
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.utils import get_display_name

from pyUltroid.dB import stickers
from pyUltroid.dB.forcesub_db import get_forcesetting
from pyUltroid.dB.gban_mute_db import is_gbanned
from pyUltroid.dB.greetings_db import get_goodbye, get_welcome, must_thank
from pyUltroid.dB.nsfw_db import is_profan
from pyUltroid.fns.helper import inline_mention
from pyUltroid.fns.tools import async_searcher, create_tl_btn, get_chatbot_reply

try:
    from ProfanityDetector import detector
except ImportError:
    detector = None
from . import LOG_CHANNEL, LOGS, asst, get_string, types, udB, ultroid_bot
from ._inline import something


@ultroid_bot.on(events.ChatAction())
async def Function(event):
    try:
        await DummyHandler(event)
    except Exception as er:
        LOGS.exception(er)


async def DummyHandler(ult):
    # clean chat actions
    key = udB.get_key("CLEANCHAT") or []
    if ult.chat_id in key:
        try:
            await ult.delete()
        except BaseException:
            pass

    # thank members
    if must_thank(ult.chat_id):
        chat_count = (await ult.client.get_participants(ult.chat_id, limit=0)).total
        if chat_count % 100 == 0:
            stik_id = chat_count / 100 - 1
            sticker = stickers[stik_id]
            await ult.respond(file=sticker)
    # force subscribe
    if (
        udB.get_key("FORCESUB")
        and ((ult.user_joined or ult.user_added))
        and get_forcesetting(ult.chat_id)
    ):
        user = await ult.get_user()
        if not user.bot:
            joinchat = get_forcesetting(ult.chat_id)
            try:
                await ultroid_bot(GetParticipantRequest(int(joinchat), user.id))
            except UserNotParticipantError:
                await ultroid_bot.edit_permissions(
                    ult.chat_id, user.id, send_messages=False
                )
                res = await ultroid_bot.inline_query(
                    asst.me.username, f"fsub {user.id}_{joinchat}"
                )
                await res[0].click(ult.chat_id, reply_to=ult.action_message.id)

    if ult.user_joined or ult.added_by:
        user = await ult.get_user()
        chat = await ult.get_chat()
        # gbans and @UltroidBans checks
        if udB.get_key("ULTROID_BANS"):
            try:
                is_banned = await async_searcher(
                    "https://bans.ultroid.tech/api/status",
                    json={"userId": user.id},
                    post=True,
                    re_json=True,
                )
                if is_banned["is_banned"]:
                    await ult.client.edit_permissions(
                        chat.id,
                        user.id,
                        view_messages=False,
                    )
                    await ult.client.send_message(
                        chat.id,
                        f'**@UltroidBans:** Banned user detected and banned!\n`{str(is_banned)}`.\nBan reason: {is_banned["reason"]}',
                    )

            except BaseException:
                pass
        reason = is_gbanned(user.id)
        if reason and chat.admin_rights:
            try:
                await ult.client.edit_permissions(
                    chat.id,
                    user.id,
                    view_messages=False,
                )
                gban_watch = get_string("can_1").format(inline_mention(user), reason)
                await ult.reply(gban_watch)
            except Exception as er:
                LOGS.exception(er)

        # greetings
        elif get_welcome(ult.chat_id):
            user = await ult.get_user()
            chat = await ult.get_chat()
            title = chat.title or "this chat"
            count = (
                chat.participants_count
                or (await ult.client.get_participants(chat, limit=0)).total
            )
            mention = inline_mention(user)
            name = user.first_name
            fullname = get_display_name(user)
            uu = user.username
            username = f"@{uu}" if uu else mention
            wel = get_welcome(ult.chat_id)
            msgg = wel["welcome"]
            med = wel["media"] or None
            userid = user.id
            msg = None
            if msgg:
                msg = msgg.format(
                    mention=mention,
                    group=title,
                    count=count,
                    name=name,
                    fullname=fullname,
                    username=username,
                    userid=userid,
                )
            if wel.get("button"):
                btn = create_tl_btn(wel["button"])
                await something(ult, msg, med, btn)
            elif msg:
                send = await ult.reply(
                    msg,
                    file=med,
                )
                await asyncio.sleep(150)
                await send.delete()
            else:
                await ult.reply(file=med)
    elif (ult.user_left or ult.user_kicked) and get_goodbye(ult.chat_id):
        user = await ult.get_user()
        chat = await ult.get_chat()
        title = chat.title or "this chat"
        count = (
            chat.participants_count
            or (await ult.client.get_participants(chat, limit=0)).total
        )
        mention = inline_mention(user)
        name = user.first_name
        fullname = get_display_name(user)
        uu = user.username
        username = f"@{uu}" if uu else mention
        wel = get_goodbye(ult.chat_id)
        msgg = wel["goodbye"]
        med = wel["media"]
        userid = user.id
        msg = None
        if msgg:
            msg = msgg.format(
                mention=mention,
                group=title,
                count=count,
                name=name,
                fullname=fullname,
                username=username,
                userid=userid,
            )
        if wel.get("button"):
            btn = create_tl_btn(wel["button"])
            await something(ult, msg, med, btn)
        elif msg:
            send = await ult.reply(
                msg,
                file=med,
            )
            await asyncio.sleep(150)
            await send.delete()
        else:
            await ult.reply(file=med)

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

@ultroid_bot.on(events.NewMessage(incoming=True))
async def chatBot_replies(e):
    sender = await e.get_sender()
    if not isinstance(sender, types.User):
        return
    key = udB.get_key("CHATBOT_USERS") or {}
    if e.text and key.get(e.chat_id) and sender.id in key[e.chat_id]:
        payload = {
          "uid": 414477568,
          "av": "8.4.4",
          "os": "a",
          "lc": "en",
          "cc": "UK",
          "tz": "Europe/London",
          "cv": "",
          "message": e.message.message,
          "free_level": 10,
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
        sleep = udB.get_key("CHATBOT_SLEEP") or 0.5
        await e.action(e.chat_id, "typing")
        await asyncio.sleep(sleep)
        await e.reply(out)
    chat = await e.get_chat()
    if e.is_group and not sender.bot:
        if sender.username:
            await uname_stuff(e.sender_id, sender.username, sender.first_name)
    elif e.is_private and not sender.bot:
        if chat.username:
            await uname_stuff(e.sender_id, chat.username, chat.first_name)
    if detector and is_profan(e.chat_id) and e.text:
        x, y = detector(e.text)
        if y:
            await e.delete()


@ultroid_bot.on(events.Raw(types.UpdateUserName))
async def uname_change(e):
    await uname_stuff(e.user_id, e.username, e.first_name)


async def uname_stuff(id, uname, name):
    if udB.get_key("USERNAME_LOG"):
        old_ = udB.get_key("USERNAME_DB") or {}
        old = old_.get(id)
        # Ignore Name Logs
        if old and old == uname:
            return
        if old and uname:
            await asst.send_message(
                LOG_CHANNEL,
                get_string("can_2").format(old, uname),
            )
        elif old:
            await asst.send_message(
                LOG_CHANNEL,
                get_string("can_3").format(f"[{name}](tg://user?id={id})", old),
            )
        elif uname:
            await asst.send_message(
                LOG_CHANNEL,
                get_string("can_4").format(f"[{name}](tg://user?id={id})", uname),
            )

        old_[id] = uname
        udB.set_key("USERNAME_DB", old_)
