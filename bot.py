import asyncio
import os
import traceback
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import google.generativeai as genai
import requests

# --- ТВОИ КЛЮЧИ ---
TELEGRAM_BOT_TOKEN = "8822279040:AAG7CUQhJqHodB8d2N1ANqOQAR9DXJQQaqg"
GEMINI_API_KEY = "AQ.Ab8RN6JqQOWi4NLLaI_qkVhl8R3Ld5vbpGx3j_vmHWqqt8iuKw"

os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY
genai.configure(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-2.5-flash"

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()


async def send_branded_message(
    message_or_callback, text: str, reply_markup=None
):
  branded_text = f"{text}\n\n<b>by @ghshuy 🔥</b>"
  parse_mode = "HTML"

  try:
    if isinstance(message_or_callback, types.CallbackQuery):
      await message_or_callback.message.edit_text(
          branded_text, reply_markup=reply_markup, parse_mode=parse_mode
      )
    else:
      await message_or_callback.answer(
          branded_text, reply_markup=reply_markup, parse_mode=parse_mode
      )
  except Exception as e:
    print("Ошибка отправки:", e)
    fallback_text = f"{text}\n\nby @ghshuy 🔥"
    if isinstance(message_or_callback, types.CallbackQuery):
      await message_or_callback.message.edit_text(
          fallback_text, reply_markup=reply_markup
      )
    else:
      await message_or_callback.answer(fallback_text, reply_markup=fallback_text)


def direct_rest_generate(prompt: str):
  url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent"
  headers = {
      "Authorization": f"Bearer {GEMINI_API_KEY}",
      "Content-Type": "application/json",
  }
  data = {"contents": [{"parts": [{"text": prompt}]}]}

  response = requests.post(url, headers=headers, json=data, timeout=15)
  if response.status_code == 200:
    res_json = response.json()
    try:
      return res_json["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
      return "⚠️ Ответ пришел в странном формате."
  else:
    raise Exception(f"API Error {response.status_code}: {response.text}")


async def check_gemini_status():
  try:
    response = await asyncio.to_thread(direct_rest_generate, "ping")
    return bool(response)
  except Exception as e:
    print("\n--- ОШИБКА ПРИ ПРОВЕРКЕ GEMINI ---")
    traceback.print_exc()
    print("----------------------------------\n")
    return False


def get_check_keyboard():
  return InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="Проверка работоспособности",
                  callback_data="check_availability",
              )
          ]
      ]
  )


def get_active_keyboard():
  return InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="Начало работы", callback_data="start_chatting"
              )
          ]
      ]
  )


def get_inactive_keyboard():
  return InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="Повторная проверка", callback_data="check_availability"
              )
          ]
      ]
  )


@dp.message(Command("start"))
async def start_handler(message: types.Message):
  text = (
      "Google Gemini bot version\n\n"
      "Проверь пожалуйста, работет ли Gemini"
  )
  await send_branded_message(message, text, reply_markup=get_check_keyboard())


@dp.callback_query(F.data == "check_availability")
async def check_availability_handler(callback: types.CallbackQuery):
  await callback.answer("Проверяем связь...")
  await send_branded_message(callback, "🔄 Идет проверка связи с Gemini...")

  is_working = await check_gemini_status()

  if is_working:
    text = "Gemini проверен на работоспособность\n\nСТАТУС — АКТИВЕН✅"
    await send_branded_message(callback, text, reply_markup=get_active_keyboard())
  else:
    text = "Gemini проверен на работоспособность\n\nСТАТУС — НЕАКТИВЕН❌"
    await send_branded_message(
        callback, text, reply_markup=get_inactive_keyboard()
    )


@dp.callback_query(F.data == "start_chatting")
async def start_chatting_handler(callback: types.CallbackQuery):
  await callback.answer()
  text = "Что хотите узнать\n\n<i>(Пиши любые вопросы прямо сюда!)</i>"
  await send_branded_message(callback.message, text)


@dp.message()
async def chat_handler(message: types.Message):
  if message.text and message.text.startswith("/"):
    return
  if not message.text:
    return

  try:
    response_text = await asyncio.wait_for(
        asyncio.to_thread(direct_rest_generate, message.text),
        timeout=15.0,
    )

    if response_text:
      await send_branded_message(message, response_text)
    else:
      await send_branded_message(
          message, "⚠️ Нейронка пришла пустой, попробуй еще раз."
      )

  except asyncio.TimeoutError:
    await send_branded_message(
        message, "⏳ Превышено время ожидания ответа от Gemini (таймаут сети)."
    )
  except Exception as e:
    print("\n--- ОШИБКА В ЧАТЕ ---")
    traceback.print_exc()
    print("---------------------\n")
    await send_branded_message(message, f"❌ Ошибка: {e}")


async def handle(request):
  return web.Response(text="Bot is running!")


async def web_server():
  app = web.Application()
  app.router.add_get("/", handle)
  runner = web.AppRunner(app)
  await runner.setup()
  port = int(os.environ.get("PORT", 10000))
  site = web.TCPSite(runner, "0.0.0.0", port)
  await site.start()
  print(f"Веб-заглушка запущена на порту {port}")


async def main():
  await web_server()
  print("Бот успешно запущен!")
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
    
