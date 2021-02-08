from uuid import uuid4

from telegram.ext import CallbackContext
from telegram import Update


from bot.constants import SURVEYS_NONE, SURVEYS_KEY

import bot.keyboards as kb
import bot.conv_constants as cc

def start(update: Update, context: CallbackContext)	-> int:
	query = update.callback_query
	user = update.effective_user
	query.answer()
	query.edit_message_text(
        	'Добро пожаловать, {}!'.format(user.first_name), reply_markup = kb.INITIAL_STATE_KB
    )	
	context.chat_data['last_handler'] = 'start'
	context.chat_data['last_state'] = cc.START_STATE
	return cc.START_STATE

def start_survey(update: Update, context: CallbackContext) -> int:
	query = update.callback_query
	query.answer()
	bot_data = context.bot_data
	if len(context.bot_data[SURVEYS_KEY].items()) > 0:
		return
	else:
		query.edit_message_text(
        	text = SURVEYS_NONE, reply_markup = START_SURVEY_NONE_KB
    	)
	context.chat_data['last_handler'] = 'start_survey'
	context.chat_data['last_state'] = cc.START_SURVEY_STATE
	return cc.START_SURVEY_STATE

def manage_surveys(update: Update, context: CallbackContext) -> int:
	update.message.reply_text('Выберите действие', reply_markup = kb.MANAGE_SURVEYS_KB)
	return cc.MANAGE_SURVEYS_STATE

def choose_survey(update: Update, context: CallbackContext) -> int:
	return

def load_survey(update: Update, context: CallbackContext) -> int:
	return

def to_prev_step(update: Update, context: CallbackContext) -> int:
	argsdict = {'update': update, 'context': context}
	globals()[context.chat_data['last_handler']](**argsdict)
	return context.chat_data['last_state']

def confirm_start_over(update: Update, context: CallbackContext) -> int:
	query = update.callback_query
	query.answer()
	update.message.reply_text(cc.CONFIRM_START_OVER, reply_markup = kb.YES_NO_KB)
	return cc.START_OVER_STATE

def confirm_return_to_main(update: Update, context: CallbackContext) -> int:
	query = update.callback_query
	query.answer()
	update.message.reply_text(cc.CONFIRM_RETURN_TO_MAIN, reply_markup = kb.YES_NO_KB)
	return cc.MAIN_MENU_STATE


