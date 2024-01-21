import asyncio
from telegram import Bot, InputFile, InputSticker
from telegram.error import TelegramError

async def check_sticker_set_existence(bot_token, sticker_set_name):
    bot = Bot(bot_token)
    try:
        sticker_set = await bot.get_sticker_set(sticker_set_name)
        return True, sticker_set  # Returns True and the sticker set if it exists
    except TelegramError as e:
        if "Stickerset_invalid" in str(e):
            return False, None  # Returns False if the sticker set does not exist
        else:
            raise 

async def create_sticker_set(bot_token, user_id, sticker_set_name, sticker_details, sticker_format):
    bot = Bot(bot_token,local_mode=True)

    input_stickers = []
    for sticker_path, emoji_list in sticker_details:
        # Use InputFile for local file handling
  
        sticker = InputSticker(sticker=open(sticker_path, 'rb'), emoji_list=emoji_list)
        input_stickers.append(sticker)


    try:
        # Create the sticker set
        await bot.create_new_sticker_set(
            user_id=user_id,
            name=sticker_set_name,
            title="PokeCatDex",
            stickers=input_stickers,
            sticker_format="static",
                connect_timeout =120
        )
        print("Sticker set created successfully.")
    except TelegramError as e:
        print(f"Error creating sticker set: {e}")


async def add_sticker_to_set(bot_token, user_id, sticker_set_name, sticker_png_path, emoji):
    bot = Bot(bot_token)

    sticker = InputSticker(sticker=open(sticker_png_path, 'rb'), emoji_list=[emoji])

    try:
        with open(sticker_png_path, 'rb') as sticker_file:
            await bot.add_sticker_to_set(
                user_id=user_id,
                name=sticker_set_name,
                sticker=sticker
                                        )
        print("Sticker added to set successfully.")
    except TelegramError as e:
        print(f"Error adding sticker to set: {e}")