# Standard Library Imports
import asyncio
from logging import Logger
from telegram import Bot, InputFile, Update
import telegram
from telegram.error import TelegramError
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler,ContextTypes, CallbackContext, ConversationHandler
from telegram.ext import filters
from dotenv import load_dotenv
from io import BytesIO
import os
import sys
sys.path.insert(0, './DB')
import json

# Third-Party Library Imports
from telegram import Bot, InputFile, Update
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import TelegramError
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler,ContextTypes, CallbackContext, ConversationHandler, CallbackQueryHandler
from telegram.ext import filters

from Source.Handler.stickerHandler import check_sticker_set_existence, add_sticker_to_set, create_sticker_set

# Local Imports
from db_insert import insert_photo
import db_query
import pixel_art_api
from db_insert import insert_photo, insert_user

NAME, DESCRIPTION = range(2)  # Define states
load_dotenv()

# User ID of the bot owner and name for the new sticker set
sticker_set_name = ""
user_states = {}
cat_data = {}

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')

async def cancel(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    await update.message.reply_text('Operation cancelled.')

    return ConversationHandler.END

async def cancel_Approval(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    if user_id in user_states:
        related_user_id = user_states[user_id].get('recipient_id') or user_states[user_id].get('initiator_id')
        
        # Remove both entries from the dictionary
        user_states.pop(user_id, None)
        user_states.pop(related_user_id, None)

        await update.message.reply_text("You have successfully cancelled the approval process.")
    else:
        await update.message.reply_text("You don't have any ongoing approval process to cancel.")


"""
init_command: This method initialises important states and adds handlers and entry points
"""
def init_command(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cats", view_cats))
    app.add_handler(CommandHandler("help", get_help))
    app.add_handler(CallbackQueryHandler(view_cat))

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.PHOTO, handle_photo)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_description)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    app.add_handler(conv_handler)
    # app.add_handler(CommandHandler("battle", start_approval))
    # app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_approval))
    # app.add_handler(CommandHandler("cancel_Approval",cancel_Approval))
    conv_handler_battle = ConversationHandler(
        entry_points=[CommandHandler('battle', start_approval)],
        states={
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username)],
        },
        fallbacks=[CommandHandler('cancel', cancel_Approval)],
    )
    app.add_handler(conv_handler_battle)

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_approval))
    



"""
These are handlers for available commans.
/start: Print welcome message and send a link to the user's personalised sticker pack
/cats: View an interface allowing users to see the cats they've collected
/cancel: Exits the interface
"""

"""/start command handler"""
async def start(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    sticker_set_name = "PokeCatDex_" + str(user['id']) +"_by_PokeCat_Bot"

    await update.message.reply_text('Welcome to PokeCat! Start your journey by taking pictures of cats.')
    set_exist, _ = await check_sticker_set_existence(os.getenv("BOT_TOKEN"), sticker_set_name=sticker_set_name)

    if(not set_exist):

        sticker_set_details = [("Photo/initial.jpg", ["🙂"])]
        await create_sticker_set(os.getenv("BOT_TOKEN"),user['id'],sticker_set_name=sticker_set_name,sticker_details=sticker_set_details,sticker_format='static')
    print(update)
    await update.message.reply_text("This is your catMondex " + "https://t.me/addstickers/" + sticker_set_name )

"""/cats command handler"""
async def view_cats(update: Update, context: CallbackContext) -> int:
    user = str((update.message.from_user)['id'])
    all_records = db_query.view_cats(user)

    # Create a list to store buttons users can click on, each button will show cat's details when clicked on
    keyboard = []

    # Iterate through each record
    for record in all_records:
        record_attributes = {}
        # For each name and set of attributes 
        record_attributes["_id"] = str(record["_id"])
        record_attributes["name"] = record["name"]
        keyboard.append([InlineKeyboardButton(record["name"], callback_data=record_attributes["_id"])])

    # Return a keyboard of all the buttons
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Choose a cat to view:', reply_markup=reply_markup)

async def select_cats(chatid, update: Update, context: CallbackContext) -> int:
    user = str((update.message.from_user)['id'])
    all_records = db_query.view_cats(user)

    # Create a list to store buttons users can click on, each button will show cat's details when clicked on
    keyboard = []

    # Iterate through each record
    for record in all_records:
        record_attributes = {}
        # For each name and set of attributes 
        record_attributes["_id"] = str(record["_id"])
        record_attributes["name"] = record["name"]
        keyboard.append([InlineKeyboardButton(record["name"], callback_data=record_attributes["_id"])])

    # Return a keyboard of all the buttons
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id = chatid,text='Choose a cat to battle:',reply_markup=reply_markup)

"""/cancel command handler"""
async def cancel(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    await update.message.reply_text('Operation cancelled.')

    return ConversationHandler.END

async def get_help(update: Update, context: CallbackContext):
    helplist = """List of Commands:\n
/start - starts the bot\n
/cats - view all the documented cats\n
/cancel - cancel the current operations\n
/help - prints the commands that is available\n
Upload a cat photo to start the saving process\n"""
    await update.message.reply_text(helplist)

"""
This handler is triggered when the user submits a new photograph.
If the photograph contains a cat, the cat's attributes will be initialised and saved.
"""
def craft_usersupplied_file_path(user):
    return 'Photo/' + user + '-user.jpg'

def craft_bitimage_file_path(user):
    return 'Photo/8bit-' + user + '.png'

def craft_sticker_link(user):
    return "PokeCatDex_" + user +"_by_PokeCat_Bot"

# Handles the photo that is to be uploaded to the database
async def handle_photo(update: Update, context: CallbackContext) -> int:
    user = str((update.message.from_user)['id'])
    photo_file = await update.message.photo[-1].get_file()
    await update.message.reply_text("Processing...")
    await photo_file.download_to_drive(craft_usersupplied_file_path(user))
    # Generate a pixel avatar and replace the original image
    output, original, bit = pixel_art_api.img2img(craft_usersupplied_file_path(user), user)
    if(not output):
        await update.message.reply_text("Not a cat")
        return
    await update.message.reply_text("Got your photo! Now, please enter a name for the cat photo.")
    return NAME

# Handles the name for the cat photo that is being uploaded
async def handle_name(update: Update, context: CallbackContext) -> int:
    user = str((update.message.from_user)['id'])
    context.user_data['name'] = update.message.text
    cat_data[user] = {"name" : update.message.text}
    await update.message.reply_text("Name received!")
    sticker_set_name = "PokeCatDex_" + user +"_by_PokeCat_Bot"
    print(sticker_set_name)
    await add_sticker_to_set(os.getenv("BOT_TOKEN"),user, craft_sticker_link(user), craft_bitimage_file_path(user), "😄") #test
    await update.message.reply_text("Got the name! Now, please enter how you met the cat.")
    return DESCRIPTION

"""
These are helper handlers called by the handlers documented above.
"""

"""Send the user a greeting"""
async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')


"""Add a new sticker and save attributes for new cat entries"""
async def handle_description(update: Update, context: CallbackContext) -> int:
    user = str((update.message.from_user)['id'])
    context.user_data['description'] = update.message.text
    await update.message.reply_text("Description received!")
    insert_photo(craft_usersupplied_file_path(user), craft_bitimage_file_path(user), cat_data[user]['name'], update.message.text, user)
    await update.message.reply_text("Sucessfully uploaded!")
    await update.message.reply_text("Please resave the sticker pack with this link: " + "https://t.me/addstickers/"+ craft_sticker_link(user) )
    return ConversationHandler.END

# Define a callback query handler
async def view_cat(update: Update, context: CallbackContext):
    # Extract chat ID from the CallbackQuery
    chat_id = update.callback_query.message.chat_id

    # Access the CallbackQuery object
    query = update.callback_query

    if query:
        # Access the data attribute of the CallbackQuery object
        cat_id = query.data
        cat_attributes = db_query.get_cat(cat_id)
        cat_name = cat_attributes["name"]
        
        # Attack and Defence might be initialised to none
        if ("attack" not in cat_attributes or "defend" not in cat_attributes):
            cat_attributes["attack"] = "Innocent Cat"
            cat_attributes["defend"] = "Innocent Cat"

        await context.bot.send_message(chat_id=chat_id, text=f'''*Cat ID:* {cat_id}\n*Name:* {cat_attributes["name"]}\n*Attack:* {cat_attributes["attack"]}\n*Defence:* {cat_attributes["defend"]}''', parse_mode='Markdown')
        await context.bot.send_photo(chat_id=chat_id, photo=BytesIO(cat_attributes["8bit"]), caption=f"*Pixel art of {cat_name}*", parse_mode='Markdown')
        await context.bot.send_photo(chat_id=chat_id, photo=BytesIO(cat_attributes["data"]), caption=f"*This is the picture you took of {cat_name}*", parse_mode='Markdown')
    else:
        print("No valid CallbackQuery found")


USERNAME = 0
async def start_approval(update: Update, context: CallbackContext) -> int:
    initiator_user_id = update.effective_user.id
    await update.message.reply_text("Please enter the username.")

    # Store the initiator's ID and await the username response
    user_states[initiator_user_id] = {'awaiting_username': True}
    return USERNAME


async def handle_username(update: Update, context: CallbackContext) -> int:
    initiator_user_id = update.effective_user.id
    received_username = update.message.text

    # Process the received username
    # Example: Resolve the username to a user ID (target_user_id)
    target_user_id = int(db_query.get_telegram_id(received_username))  # Implement this function

    # Store both the initiator's and recipient's IDs
    user_states[initiator_user_id] = {'recipient_id': target_user_id}
    user_states[target_user_id] = {'initiator_id': initiator_user_id}

    # Send approval request to the target user
    await context.bot.send_message(chat_id=target_user_id, text="Please approve this action by replying 'approve'.")
    return ConversationHandler.END

async def handle_approval(update: Update, context: CallbackContext):
    from_user_id = update.effective_user.id
    message_text = update.message.text.lower()

    print(from_user_id in user_states)
    print(user_states)
    print(from_user_id)
    if from_user_id in user_states and message_text == 'approve':
        print('hit')

        initiator_user_id = user_states[from_user_id]

        try:
            await context.bot.send_message(chat_id=initiator_user_id['initiator_id'], text="Your request has been approved.")
            # Clear the state after sending the message
            #BATTLE MODE
            await context.bot.send_message(chat_id=initiator_user_id['initiator_id'], text="Battle Starts")
            await context.bot.send_message(chat_id=from_user_id, text="Battle Starts")

            await select_cats(initiator_user_id['initiator_id'],update,context)
            await select_cats(from_user_id,update,context)

            del user_states[from_user_id]
        except telegram.error.BadRequest:
            Logger.error(f"Cannot send message to user {initiator_user_id}. Chat not found.")
            # Optionally, inform the user who tried to approve
            await update.message.reply_text("Unable to notify the requester. They might not have started the bot.")

        return


# Define a command handler (e.g., for the /start command)
async def start(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    sticker_set_name = "PokeCatDex_" + str(user['id']) +"_by_PokeCat_Bot"
    insert_user(str(user['username']), str(user['id']))
    await update.message.reply_text('Welcome to PokeCat! Start your journey by taking pictures of cats.')
    set_exist, _ = await check_sticker_set_existence(os.getenv("BOT_TOKEN"), sticker_set_name=sticker_set_name)

    if(not set_exist):
        sticker_set_details = [("Photo/initial.jpg", ["🙂"])]
        await create_sticker_set(os.getenv("BOT_TOKEN"),user['id'],sticker_set_name=sticker_set_name,sticker_details=sticker_set_details,sticker_format='static')
    
    await update.message.reply_text("This is your catMondex " + "https://t.me/addstickers/"+sticker_set_name )

if __name__ == "__main__":
    # Replace with your bot token, user ID, sticker set name, and sticker details
    print("Bot is starting")
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
    print("Bot has started")
    init_command(app)
    app.run_polling()