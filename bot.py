import asyncio
import os
import traceback
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from openai import AsyncOpenAI

# --- ТВОИ КЛЮЧИ ---
TELEGRAM_BOT_TOKEN = "8822279040:AAG7CUQhJqHodB8d2N1ANqOQAR9DXJQQaqg"
OPENAI_API_KEY = (
    "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"
)

client = AsyncOpenAI(api_key=OPENAI_API_KEY)
MODEL_NAME = "gpt-4o-mini"

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


async def check_ai_status():
  try:
    response = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": "ping"}],
        max_tokens=10,
    )
    return bool(response.choices[0].message.content)
  except Exception as e:
    print("\n--- ОШИБКА ПРИ ПРОВЕРКЕ OPENAI ---")
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
      "OpenAI ChatGPT bot version\n\nПроверь пожалуйста, работает ли нейросеть"
  )
  await send_branded_message(message, text, reply_markup=get_check_keyboard())


@dp.callback_query(F.data == "check_availability")
async def check_availability_handler(callback: types.CallbackQuery):
  await callback.answer("Проверяем связь...")
  await send_branded_message(callback, "🔄 Идет проверка связи с ChatGPT...")

  is_working = await check_ai_status()

  if is_working:
    text = "ChatGPT проверен на работоспособность\n\nСТАТУС — АКТИВЕН✅"
    await send_branded_message(callback, text, reply_markup=get_active_keyboard())
  else:
    text = "ChatGPT проверен на работоспособность\n\nСТАТУС — НЕАКТИВЕН❌"
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
    response = await asyncio.wait_for(
        client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": message.text}],
        ),
        timeout=20.0,
    )

    answer = response.choices[0].message.content
    if answer:
      await send_branded_message(message, answer)
    else:
      await send_branded_message(
          message, "⚠️ Нейронка пришла пустой, попробуй еще раз."
      )

  except asyncio.TimeoutError:
    await send_branded_message(
        message, "⏳ Превышено время ожидания ответа (таймаут сети)."
    )
  except Exception as e:
    print("\n--- ОШИБКА В ЧАТЕ ---")
    traceback.print_exc()
    print("---------------------\n")
    await send_branded_message(message, f"❌ Ошибка: {e}")


# --- Веб-заглушка для Render ---
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
  print("Бот успешно запущен на OpenAI API!")
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
    
