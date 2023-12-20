import asyncio
import json
import requests
import frappe
import telegram
from typing import Final
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application,CommandHandler,CallbackContext, MessageHandler, filters, ContextTypes, ApplicationBuilder, CallbackQueryHandler, Updater
import logging


logging.basicConfig(
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
	level=logging.INFO
)

#geting bot token
def get_token(bot_name):
	doc_name = frappe.db.get_value("Telegram Bot Settings", filters={"telegram_bot_name":bot_name}, fieldname ="name")
	return frappe.get_doc("Telegram Bot Settings",doc_name).get_password("telegram_bot_token")

BOT_USERNAME: Final = '@api_testt_bot'
TOKEN = get_token('@api_testt_bot')
bot = telegram.Bot(token=TOKEN)

def remove_webhook():
	bot.removeWebhook()

#verifying user
def is_user(user_id, user_name, verify_user = False):
	if verify_user:
		doc_name = frappe.db.get_value("Telegram User Details", {"telegram_user_id":user_id, "telegram_username":user_name}, "name")
		frappe.db.set_value("Telegram User Details", doc_name, {"verified":1})
		frappe.db.commit()
		return True
	else:
		user_exists = frappe.db.exists("Telegram User Details", {"telegram_user_id":user_id, "telegram_username":user_name, "verified":1})
		if not user_exists:
			if frappe.db.exists("Telegram User Details", {"telegram_user_id":user_id, "telegram_username":user_name}):
				return "User found but not Verified"
			else:
				return "User Not Found"
		else:
			return "Verified"

def build_telegram_message(user_name):
	message = f"A new expense claim has been generated by {user_name} . \nDo you want to approve or reject?"
	return message

def update_doc_status(docname,status,user_id):
<<<<<<< HEAD
	expense_claim_doc = frappe.get_doc("Expense Claim",{"name":docname})
	if status =="Approved":
		expense_claim_doc.docstatus = 1
	elif status == "Rejected":
		expense_claim_doc.docstatus = 0
		expense_claim_doc.workflow_state = status
	expense_claim_doc.approval_status = status
	expense_claim_doc.save()
	frappe.db.commit()
	print(f"Document {docname} has been updated")
	return True
=======
    expense_claim_doc = frappe.get_doc("Expense Claim",{"name":docname})
    if status =="Approved":
        expense_claim_doc.docstatus = 1
    elif status == "Rejected":
        expense_claim_doc.docstatus = 0
        expense_claim_doc.workflow_state = status
    expense_claim_doc.approval_status = status
    expense_claim_doc.save()
    frappe.db.commit()
    print(f"Document {docname} has been updated")
    return True
>>>>>>> 7943c7da36b44efc0cf44bd0608f5b7e119b6e80

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
	try:
		frappe.log_error("entered start")
		user_id = update.message.chat.id
		username = update.message.chat.username
		verify_user = is_user(user_id,username)
		frappe.log_error(verify_user)
		if verify_user == "Verified":
			reply_text = f"Welcome, {username}, You are verified user."
			await update.message.reply_text(reply_text)
		elif verify_user == "User found but not Verified":
			keyboard = [
				[InlineKeyboardButton("Yes", callback_data=json.dumps({"msg":'Yes', "action":"verify"}))],
				[InlineKeyboardButton("No", callback_data=json.dumps({"msg":'No', "action":"verify"}))]
			]
			reply_markup = InlineKeyboardMarkup(keyboard)
			reply_text = f"Sorry, {username}, You are not a verified user. Do you want to verify?"
			await update.message.reply_text(reply_text, reply_markup=reply_markup)
		elif verify_user == "User Not Found":
			keyboard = [
				[InlineKeyboardButton("Yes", callback_data=json.dumps({"msg":'Yes', "action":"register"}))],
				[InlineKeyboardButton("No", callback_data=json.dumps({"msg":'No', "action":"register"}))]
			]
			reply_markup = InlineKeyboardMarkup(keyboard)
			reply_text = "User Not Found. Do you want to register in ERP?"
			await update.message.reply_text(reply_text)
	except Exception as e:
		frappe.log_error(str(e))

def register_telegram_user(user_id, username, email):
	if frappe.db.exists("User", {"name":email}):
		parent_name = frappe.db.get_value("Telegram Bot Settings", filters = {"telegram_bot_name":BOT_USERNAME}, fieldname =  "name")
		parent_doc = frappe.get_doc("Telegram Bot Settings", parent_name)
		parent_doc.append("user_details", {
			"user":email,
			"telegram_user_id":user_id,
			"telegram_username":username,
			"verified":1
		})
		parent_doc.save()
		frappe.db.commit()
		return True
	else:
		return False


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
	user_data = context.user_data
	user_id= update.message.chat.id
	username = update.message.chat.username
	text = update.message.text
	state = user_data.get("state", None)
	if state == "EMAIL_REGISTER_STATE":
		register_telegram_user(user_id=user_id, username=username, email=text)
		print(f"User ID {update.message.chat.id} sends message as {text} in {update.message.chat.type}")
		await update.message.reply_text("User registered succesfully")

async def send_notification(user_id,username,from_user,doc_name):
	message = build_telegram_message(from_user)
	callback_data_approve = json.dumps({"status":"Approved","docname":doc_name})
	callback_data_reject = json.dumps({"status":"Rejected","docname":doc_name})
	keyboard = [
		[InlineKeyboardButton("Approve", callback_data= callback_data_approve)],
		[InlineKeyboardButton("Reject", callback_data=callback_data_reject)]
	]
	reply_markup = InlineKeyboardMarkup(keyboard)
	await bot.send_message(chat_id=user_id, text=message,reply_markup=reply_markup)

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
	frappe.log_error("entered test")
	# Create an inline keyboard with "Approve" and "Decline" buttons
	keyboard = [
		[InlineKeyboardButton("Approve", callback_data='approve')],
		[InlineKeyboardButton("Reject", callback_data='reject')]
	]
	reply_markup = InlineKeyboardMarkup(keyboard)

	# Send the message with the inline keyboard
	await update.message.reply_text("Do you approve or decline?", reply_markup=reply_markup)

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
	await update.message.reply_text("Enter your email address")
	context.user_data['state'] = "EMAIL_REGISTER_STATE"

async def button_click(update, context):
<<<<<<< HEAD
	try:
		query = update.callback_query
		callback_data =json.loads(query.data)
		user_id=query.from_user.id
		username = query.from_user.username
		query.answer()
		text_message = ''
		if callback_data.get('status') == 'Approved':
			if update_doc_status(docname=callback_data.get('docname'),status=callback_data.get('status')):
				text_message = "Expense claim has been approved"
			else:
				print("error occured on update_doc_status")
		elif callback_data.get('status') == 'Rejected':
			if update_doc_status(docname=callback_data.get('docname'),status=callback_data.get('status')):
				text_message = "Expense claim has been rejected"
		# Handle button clicks here
		if query.data == 'approve':
			query.edit_message_text(text="You approved!")
			text_message = f"User {user_id} has approved."
		elif query.data == 'reject':
			query.edit_message_text(text="You declined!")
			text_message = f"User {user_id} has declined."
		if callback_data.get('msg') == 'Yes' & callback_data.get("action") == 'verify':
			if is_user(user_id, username, verify_user=True):
				query.edit_message_text(text="You are verified!")
				text_message = f"User {user_id} has verified."
			else:
				text_message = is_user(user_id, username, verify_user=True)
		elif callback_data.get('msg') == 'No' & callback_data.get("action") == 'verify':
			query.edit_message_text(text="Okay, Thank you")
			text_message = "Okay, Thank you"
		if callback_data.get('msg') == 'Yes' & callback_data.get("action") == 'register':
			query.edit_message_text(text = "Enter `/register` command")
		elif callback_data.get('msg') == 'No' & callback_data.get("action") == 'register':
			query.edit_message_text(text="Okay, Thank you")
			text_message = "Okay, Thank you"
		# if not text_message:
		#     text_message = "Default message or handle this case appropriately"
=======
    try:
        query = update.callback_query
        callback_data =json.loads(query.data)
        user_id=query.from_user.id
        username = query.from_user.username
        query.answer()
        text_message = ''
        if callback_data.get('status') == 'Approved':
            if update_doc_status(docname=callback_data.get('docname'),status=callback_data.get('status'), user_id = user_id):
                text_message = "Expense claim has been approved"
            else:
                print("error occured on update_doc-status")
        elif callback_data.get('status') == 'Rejected':
            if update_doc_status(docname=callback_data.get('docname'),status=callback_data.get('status'), user_id = user_id):
                text_message = "Expense claim has been rejected"
        # Handle button clicks here
        if query.data == 'approve':
            query.edit_message_text(text="You approved!")
            text_message = f"User {user_id} has approved."
        elif query.data == 'reject':
            query.edit_message_text(text="You declined!")
            text_message = f"User {user_id} has declined."
        if callback_data.get('msg') == 'Yes':
            if is_user(user_id, username, verify_user=True):
                query.edit_message_text(text="You are verified!")
                text_message = f"User {user_id} has verified."
            else:
                text_message = is_user(user_id, username, verify_user=True)
        elif callback_data.get('msg') == 'No':
            query.edit_message_text(text="Okay, Thank you")
            text_message = "Okay, Thank you"
        # if not text_message:
        #     text_message = "Default message or handle this case appropriately"
>>>>>>> 7943c7da36b44efc0cf44bd0608f5b7e119b6e80

		# You can also edit the original message if needed
		await context.bot.edit_message_text(
			chat_id=user_id,
			message_id=query.message.message_id,
			text=text_message
		)
	except Exception as e:
		frappe.log_error(str(e))

# application = ApplicationBuilder().token(TOKEN).build()
# frappe.log_error("Application instance created")
# #Commands
# application.add_handler(CommandHandler("start", start_command))
# application.add_handler(CommandHandler("test", test_command))
# application.add_handler(CallbackQueryHandler(button_click))

# #Messages
# application.add_handler(MessageHandler(filters.TEXT, handle_message))

def process_telegram_update(update: Update) -> None:
	# Extract information from the update
	user_id = update.message.from_user.id
	user_name = update.message.from_user.username
	user_message = update.message.text

	if user_message == "/start":
		asyncio.run(start_command(update))
	elif user_message == "/test":
		asyncio.run(test_command(update))
	else:
		asyncio.run(handle_message(update))

	# Your custom processing logic here...
	processed_message = f"Hello, {user_name}! You said: {user_message}"
	frappe.log_error("Processsed telgram update successfully")
	# Send a response back to the user
	# await update.message.reply_text(text=processed_message)

def process_callback_query(update: Update):
	try:
		query = update.callback_query
		data = query.data
		message  = ''
		if data == 'approve':
			message = "You're approveed"
		elif data == 'reject':
			message = "You're rejected"

	   # bot.answer_callback_query(callback_query_id = query.id,text = message)
		 # Send a reply message
		bot.send_message(
			chat_id=query.from_user.id,
			text=message,
			reply_to_message_id=query.message.id,
			)
	except Exception as e:
		frappe.log_error(str(e))


@frappe.whitelist(allow_guest=True)
def webhook():
	try:
		if frappe.request.data:
			update = Update.de_json(json.loads(frappe.request.data), bot)
			frappe.log_error("Telegram Webhook", f"Update object: {update}")
			# frappe.log_error(application)
			if update.message:
				process_telegram_update(update)
			if update.callback_query:
				process_callback_query(update)
			frappe.response["status"] = "OK"
			return "OK"
	except Exception as e:
		frappe.log_error(str(e))
		frappe.response["error"] = str(e)
		frappe.response["status"] ="ERROR"
		return "500"


@frappe.whitelist(allow_guest=True)
def set_webhook_url():
	webhook_url = 'https://alfarsi.aerele.in/api/method/telegram_productivity.telegram_productivity.utils.telegram_bot.webhook'

	api_url = f'https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_url}'

	response = requests.get(api_url)

	# Check the response to ensure the webhook was set up successfully
	if response.ok:
		print(f'Webhook URL set successfully: {webhook_url}')
	else:
		print(f'Failed to set webhook URL. Response: {response.text}')

@frappe.whitelist()
def start():
	print("Starting bot...")
	application = ApplicationBuilder().token(token=TOKEN).build()

	#Commands
	application.add_handler(CommandHandler("start", start_command))
	application.add_handler(CommandHandler("test", test_command))
	application.add_handler(CommandHandler("register", register))
	application.add_handler(CallbackQueryHandler(button_click))

	#Messages
	application.add_handler(MessageHandler(filters.TEXT, handle_message))

	application.run_polling(poll_interval= 3)
