import os
import re 
import sys
import asyncio 
import logging 
from database import Db, db
from config import Config, temp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message 
from pyrogram.errors.exceptions.bad_request_400 import AccessTokenExpired, AccessTokenInvalid
from pyrogram.errors import FloodWait
from config import Config
from script import Script
from typing import Union, Optional, AsyncGenerator
from pyrogram.errors import (
    ApiIdInvalid,
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

BTN_URL_REGEX = re.compile(r"(\[([^\[]+?)]\[buttonurl:/{0,2}(.+?)(:same)?])")
BOT_TOKEN_TEXT = "<b><b>1) צור בוט באמצעות @BotFather\n2) לאחר מכן תקבל הודעה עם אסימון בוט\n3) העבר את ההודעה הזו אליי</b>"
SESSION_STRING_SIZE = 351


class CLIENT: 
  def __init__(self):
     self.api_id = Config.API_ID
     self.api_hash = Config.API_HASH

  def user_session(self, data):
      return Client("USERBOT", self.api_id, self.api_hash, session_string=data)
     
  async def add_bot(self, bot, message):
     user_id = int(message.from_user.id)
     msg = await bot.ask(chat_id=user_id, text=BOT_TOKEN_TEXT)
     if msg.text=='/cancel':
        return await msg.reply('<b>process cancelled !</b>')
     elif not msg.forward_date:
       return await msg.reply_text("<b>זו לא הודעה קדימה</b>")
     elif str(msg.forward_from.id) != "93372553":
       return await msg.reply_text("<b>הודעה זו לא הועברה מ @botfather</b>")
     bot_token = re.findall(r'\d[0-9]{8,10}:[0-9A-Za-z_-]{35}', msg.text, re.IGNORECASE)
     bot_token = bot_token[0] if bot_token else None
     if not bot_token:
       return await msg.reply_text("<b>אין אסימון בוט בהודעה הזו</b>")
     try:
       _client = Client("BOT", Config.API_ID, Config.API_HASH, bot_token=bot_token, in_memory=True)
       client = await _client.start()
     except Exception as e:
       await msg.reply_text(f"<b>שגיאה:</b> `{e}`")
       return
     _bot = _client.me
     details = {
       'id': _bot.id,
       'is_bot': True,
       'user_id': user_id,
       'name': _bot.first_name,
       'token': bot_token,
       'username': _bot.username 
     }
     await db.add_bot(details)
     return True

  async def add_session(self, bot, message):
     user_id = int(message.from_user.id)
     text = "<b>⚠️ כתב ויתור ⚠️</b>\n\n<code>אתה יכול להשתמש בהפעלה שלך להעברת הודעה מצ'אט פרטי לצ'אט אחר.\nאנא הוסף את הפעלת הפירוגרמה שלך באחריותך בלבד.  יש להם הזדמנות לחסום את החשבון שלך.  המפתח שלי אינו אחראי אם חשבונך עלול להיחסם.</code>"
     await bot.send_message(user_id, text=text)
     phone_number_msg = await bot.ask(chat_id=user_id, text="<b>אנא שלח את מספר הטלפון שלך הכולל קוד מדינה</b>\n<b>לדוגמא:</b> <code>+13124562345</code>")
     if phone_number_msg.text=='/cancel':
        return await phone_number_msg.reply('<b>התהליך בוטל !</b>')
     phone_number = phone_number_msg.text
     client = Client(":memory:", Config.API_ID, Config.API_HASH)
     await client.connect()
     await phone_number_msg.reply("שולח OTP...")
     try:
        code = await client.send_code(phone_number)
        phone_code_msg = await bot.ask(user_id, "אנא בדוק אם יש OTP בחשבון הטלגרם הרשמי.  אם קיבלת את זה, שלח כאן OTP לאחר קריאת הפורמט שלהלן. \n\nאם OTP נראה כ `12345`, **אז שלח אותו בתור** `1 2 3 4 5`.\n\n**שלח /cancel כדי לבטל את התהליך**", filters=filters.text, timeout=600)
     except PhoneNumberInvalid:
        await phone_number_msg.reply('`PHONE_NUMBER` **אינו חוקי.**')
        return
     if phone_code_msg.text=='/cancel':
        return await phone_code_msg.reply('<b>התהליך בוטל !</b>')
     try:
        phone_code = phone_code_msg.text.replace(" ", "")
        await client.sign_in(phone_number, code.phone_code_hash, phone_code)
     except PhoneCodeInvalid:
        await phone_code_msg.reply('**OTP לא חוקי.**')
        return
     except PhoneCodeExpired:
        await phone_code_msg.reply('**פג תוקף ה-OTP.**')
        return
     except SessionPasswordNeeded:
        two_step_msg = await bot.ask(user_id, '**החשבון שלך איפשר אימות דו-שלבי. אנא ספק את הסיסמה.\n\nשלח /cancel כדי לבטל את התהליכים‌‌**', filters=filters.text, timeout=300)
        if two_step_msg.text=='/cancel':
            return await two_step_msg.reply('<b>התהליך בוטל !</b>')
        try:
           password = two_step_msg.text
           await client.check_password(password=password)
        except PasswordHashInvalid:
           await two_step_msg.reply('**סיסמה לא חוקית סופקה**')
           return
     string_session = await client.export_session_string()
     await client.disconnect()
     if len(string_session) < SESSION_STRING_SIZE:
        return await msg.reply('<b>invalid session sring</b>')
     try:
       _client = Client("USERBOT", self.api_id, self.api_hash, session_string=string_session)
       client = await _client.start()
     except Exception as e:
       return await msg.reply_text(f"<b>שגיאת יוזרבוט:</b> `{e}`")
     user = _client.me
     details = {
       'id': user.id,
       'is_bot': False,
       'user_id': user_id,
       'name': user.first_name,
       'session': string_session,
       'username': user.username
     }
     await db.add_userbot(details)
     return True


@Client.on_message(filters.private & filters.command('reset'))
async def forward_tag(bot, m):
   default = await db.get_configs("01")
   await db.update_configs(m.from_user.id, default)
   await m.reply("successfully settings reseted ✔️")


@Client.on_message(filters.command('resetall') & filters.user(Config.BOT_OWNER))
async def resetall(bot, message):
  users = await db.get_all_users()
  sts = await message.reply("**processing**")
  TEXT = "total: {}\nsuccess: {}\nfailed: {}\nexcept: {}"
  total = success = failed = already = 0
  ERRORS = []
  async for user in users:
      user_id = user['id']
      default = await get_configs(user_id)
      default['db_uri'] = None
      total += 1
      if total %10 == 0:
         await sts.edit(TEXT.format(total, success, failed, already))
      try: 
         await db.update_configs(user_id, default)
         success += 1
      except Exception as e:
         ERRORS.append(e)
         failed += 1
  if ERRORS:
     await message.reply(ERRORS[:100])
  await sts.edit("completed\n" + TEXT.format(total, success, failed, already))


async def get_configs(user_id):
  configs = await db.get_configs(user_id)
  return configs


async def update_configs(user_id, key, value):
  current = await db.get_configs(user_id)
  if key in ['caption', 'duplicate', 'db_uri', 'forward_tag', 'protect', 'min_size', 'max_size', 'extension', 'keywords', 'button']:
     current[key] = value
  else: 
     current['filters'][key] = value
  await db.update_configs(user_id, current)


async def iter_messages(
    self,
    chat_id: Union[int, str],
    limit: int,
    offset: int = 0,
    filters: dict = None,
    max_size: int = None,
) -> Optional[AsyncGenerator["types.Message", None]]:
        current = offset
        dup_files = []
        while True:
            new_diff = min(200, limit - current)
            if new_diff <= 0:
                return

            messages = await self.get_messages(chat_id, list(range(current, current + new_diff + 1)))
            for message in messages:
                if any(getattr(message, media_type, False) for media_type in filters):
                    yield "FILTERED"
                else:
                    yield message
                    
                current += 1


async def get_client(bot_token, is_bot=True):
  if is_bot:
    return Client("BOT", Config.API_ID, Config.API_HASH, bot_token=bot_token, in_memory=True)
  else:
    return Client("USERBOT", Config.API_ID, Config.API_HASH, session_string=bot_token)


def parse_buttons(text, markup=True):
    buttons = []
    for match in BTN_URL_REGEX.finditer(text):
        n_escapes = 0
        to_check = match.start(1) - 1
        while to_check > 0 and text[to_check] == "\\":
            n_escapes += 1
            to_check -= 1

        if n_escapes % 2 == 0:
            if bool(match.group(4)) and buttons:
                buttons[-1].append(InlineKeyboardButton(
                    text=match.group(2),
                    url=match.group(3).replace(" ", "")))
            else:
                buttons.append([InlineKeyboardButton(
                    text=match.group(2),
                    url=match.group(3).replace(" ", ""))])
    if markup and buttons:
       buttons = InlineKeyboardMarkup(buttons)
    return buttons if buttons else None
