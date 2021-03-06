import gettext
import logging

import bot.constants as consts
import bot.conv_constants as cc
import bot.keyboards as kbs
import bot.utils as utils

from telegram import Update
from telegram.ext import CallbackContext

_ = gettext.gettext
kb = None

logger = logging.getLogger(__name__)


def pick_survey(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    global _
    global kb
    kb = kbs.Keyboards(context.user_data["settings"]["lang"])
    locale = gettext.translation(
        "poll", localedir="locales", languages=[context.user_data["settings"]["lang"]]
    )
    locale.install()
    _ = locale.gettext
    if "poll_ongoing" not in context.bot_data:
        context.bot_data["poll_ongoing"] = False
    if not context.bot_data["poll_ongoing"]:
        if query.data != "PAGENUM":
            if len(context.bot_data[consts.SURVEYS_KEY]) > 0:
                survey_list = utils.num_list(
                    context.bot_data[consts.SURVEYS_KEY], key="title"
                )
                multipage = context.user_data["settings"]["page_len"] < len(
                    context.bot_data[consts.SURVEYS_KEY]
                )
                if multipage:
                    if "page" not in context.chat_data:
                        context.chat_data["page"] = 1
                    elif query.data == "prev page":
                        context.chat_data["page"] -= 1
                    elif query.data == "next page":
                        context.chat_data["page"] += 1
                else:
                    context.chat_data["page"] = None
                keyboard = kb.populate_keyboard(
                    page_len=context.user_data["settings"]["page_len"],
                    per_row=context.user_data["settings"]["row_len"],
                    length=len(context.bot_data[consts.SURVEYS_KEY]),
                    multipage=multipage,
                    page=context.chat_data["page"],
                )
                query.edit_message_text(
                    text=_("Выберите опрос из существующих\n\n" "{list}").format(
                        list=survey_list
                    ),
                    reply_markup=keyboard,
                )
                return cc.POLL_PICK_STATE
            else:
                query.edit_message_text(
                    text=_("В текущее время идёт опрос, подождите его завершения"),
                    reply_markup=kb.MAIN_MENU_KB,
                )


def preview(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    data = query.data
    idx = int(data)
    context.chat_data["current_survey"] = context.bot_data[consts.SURVEYS_KEY][idx]
    survey = utils.print_survey(context.chat_data["current_survey"])
    query.edit_message_text(
        text=_("Выбранный опрос:\n\n") + survey + _("Выберите действие"),
        reply_markup=kb.POLL_PREVIEW_KB,
    )
    return cc.POLL_PREVIEW_STATE


def pick_chat(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    bot_data = context.bot_data
    if query.data != "PAGENUM":
        if len(bot_data[consts.CHATS_KEY]) > 0:
            chat_names = [
                context.bot.get_chat(chat_id).title
                for chat_id in bot_data[consts.CHATS_KEY]
            ]
            chat_list = utils.num_list(chat_names)
            multipage = context.user_data["settings"]["page_len"] < len(
                context.bot_data[consts.CHATS_KEY]
            )
            if multipage:
                if "page" not in context.chat_data:
                    context.chat_data["page"] = 1
                elif query.data == "prev page":
                    context.chat_data["page"] -= 1
                elif query.data == "next page":
                    context.chat_data["page"] += 1
            else:
                context.chat_data["page"] = None
            keyboard = kb.populate_keyboard(
                page_len=context.user_data["settings"]["page_len"],
                per_row=context.user_data["settings"]["row_len"],
                length=len(context.bot_data[consts.CHATS_KEY]),
                multipage=multipage,
                page=context.chat_data["page"],
            )
            query.edit_message_text(
                text=_("Выберите чат из существующих\n\n" "{list}").format(
                    list=chat_list
                ),
                reply_markup=keyboard,
            )
            return cc.PICK_CHAT_STATE
        else:
            query.edit_message_text(
                text=_(
                    "Пока что не был добавлен ни один чат!\n"
                    "Используйте команду /show_chat_id в нужном чате, затем /add_chat id с полученным числом вместо id"
                    "Бот обязательно должен присутствовать в этом чате!"
                ),
                reply_markup=kb.MAIN_MENU_KB,
            )


def set_cap(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    idx = int(query.data)
    context.chat_data["chat_id"] = context.bot_data[consts.CHATS_KEY][idx]
    target_chat = context.bot.get_chat(context.chat_data["chat_id"])
    context.chat_data["admins"] = len(target_chat.get_administrators())
    context.chat_data["total"] = target_chat.get_members_count()
    context.chat_data["recommended"] = (
        context.chat_data["total"] - context.chat_data["admins"] - 1
    )
    query.edit_message_text(
        text=_(
            "Выбранный чат:\n"
            "{title}\n\n"
            "В чате обнаружено {total} участников, из них {admins} администраторов\n"
            "Для того, чтобы появился следующий вопрос, необходимо, чтобы проголосовало определённое число человек\n"
            "По умолчанию должно проголосовать {rec} человек (все, кроме администраторов и этого бота)\n"
            "Вы можете выбрать рекомендованное значение или установить своё"
        ).format(
            title=target_chat.title,
            total=context.chat_data["total"],
            admins=context.chat_data["admins"],
            rec=context.chat_data["recommended"],
        ),
        reply_markup=kb.SET_CAP_KB,
    )
    return cc.SET_CAP_STATE


def get_cap(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    query.edit_message_text(
        text=_(
            "Введите требуемое число людей для перехода к следующему вопросу\n"
            "Число не может быть меньше 1 и больше {max} (все участники, кроме этого бота)\n"
            "Учтите, что другие боты (если таковые имеются в чате) не смогут голосовать, и голосование останется на первом вопросе при слишком большом значении"
        ).format(max=context.chat_data["total"] - 1)
    )
    return cc.GET_CAP_STATE


def validate_cap(update: Update, context: CallbackContext) -> int:
    try:
        cap = int(update.message.text)
        if cap in range(1, context.chat_data["total"]):
            context.chat_data["custom_cap"] = cap
            update.message.reply_text(
                text=_(
                    "Для перехода к следующему вопросу должно проголосовать {cap} человек\n"
                    "Использовать это значение?"
                ).format(cap=context.chat_data["custom_cap"]),
                reply_markup=kb.CUSTOM_CAP_KB,
            )
            return cc.VALIDATE_CAP_STATE
        elif cap < 1:
            update.message.reply_text(
                text=_("Выбрано слишком маленькое значение! Попробуйте ещё раз"),
            )
            return cc.GET_CAP_STATE
        elif cap >= context.chat_data["total"]:
            update.message.reply_text(
                text=_("Выбрано слишком большое значение! Попробуйте ещё раз"),
            )
            return cc.GET_CAP_STATE
    except ValueError:
        update.message.reply_text(
            text=_("Неправильно введён номер! Попробуйте ещё раз"),
        )
        return cc.GET_CAP_STATE


def confirm(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    data = query.data
    if data == cc.USE_RECOMMENDED_CB:
        context.chat_data["cap"] = context.chat_data["recommended"]
    elif data == cc.USE_CUSTOM_CB:
        context.chat_data["cap"] = context.chat_data["custom_cap"]
    del context.chat_data["recommended"]
    try:
        del context.chat_data["custom_cap"]
    except KeyError:
        pass
    target_chat = context.bot.get_chat(context.chat_data["chat_id"])
    chat_title = target_chat.title
    survey = utils.print_survey(context.chat_data["current_survey"])
    query.edit_message_text(
        text=_(
            "Вы собираетесь провести опрос\n\n"
            "{survey}\n\n"
            "в чате {title}\n\n"
            "Для перехода к следующему вопросу должно ответить {cap} пользователей\n\n"
            "Выберите действие"
        ).format(survey=survey, title=chat_title, cap=context.chat_data["cap"]),
        reply_markup=kb.POLL_CONFIRM_KB,
    )
    return cc.POLL_CONFIRM_STATE


def launch(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    query.edit_message_text(text=_("Опрос запущен!"), reply_markup=kb.MAIN_MENU_KB)
    context.bot_data["poll_ongoing"] = True
    context.bot_data["ongoing"] = {
        "chat_id": context.chat_data["chat_id"],
        "survey": context.chat_data["current_survey"],
        "cap": context.chat_data["cap"],
        "current_question": 0,
        "answers": {},
    }
    del context.chat_data["chat_id"]
    del context.chat_data["current_survey"]
    del context.chat_data["cap"]
    del context.chat_data["page"]
    desc = context.bot_data["ongoing"]["survey"]["desc"]
    chat_id = context.bot_data["ongoing"]["chat_id"]
    delay = round(len(desc.split()) * 60 / 140)
    logger.info(_("Время на чтение описания: {delay} секунд").format(delay=delay))
    context.bot.send_message(chat_id=chat_id, text=desc)
    context.job_queue.run_once(
        step2,
        delay,
        context=context,
        name=context.bot_data["ongoing"]["survey"]["id"] + "_step2",
    )
    return cc.START_STATE


def step2(context):
    context = context.job.context
    context.bot.send_message(
        chat_id=context.bot_data["ongoing"]["chat_id"],
        text=_("Опрос начнётся через 5 секунд"),
    )
    context.job_queue.run_once(
        post_question,
        5,
        context=context,
        name=context.bot_data["ongoing"]["survey"]["id"] + "_post_questions",
    )


def post_question(context):
    if context.job is not None:
        context = context.job.context
    ongoing = context.bot_data["ongoing"]
    current = ongoing["current_question"]
    chat_id = ongoing["chat_id"]
    if current < len(ongoing["survey"]["questions"]):
        question = ongoing["survey"]["questions"][current]
        q = question["question"]
        a = question["answers"]
        multi = question["multi"]
        logger.info(_("Публикуется вопрос №{num}").format(num=current + 1))
        message = context.bot.send_poll(
            chat_id=chat_id,
            question=q,
            options=a,
            is_anonymous=False,
            allows_multiple_answers=multi,
        )
        logger.info(_("Публикуется счётчик к вопросу №{num}").format(num=current + 1))
        counter = context.bot.send_message(
            chat_id=chat_id,
            text=_(
                "Ответили 0 из {cap} участников. Следующий вопрос появится, когда ответят все!"
            ).format(cap=ongoing["cap"]),
            timeout=500,
        )
        payload = {
            message.poll.id: {
                "question": q,
                "message_id": message.message_id,
                "counter_id": counter.message_id,
                "chat_id": chat_id,
                "answered": 0,
            }
        }
        context.bot_data["ongoing"].update(payload)


def collect_answer(update, context):
    answer_upd = update.poll_answer
    poll_answers = answer_upd.option_ids
    name = answer_upd.user.full_name
    uid = answer_upd.user.id
    poll_id = answer_upd.poll_id
    ongoing = context.bot_data["ongoing"]
    chat_id = ongoing[poll_id]["chat_id"]
    current = ongoing["current_question"]
    answers = ongoing["survey"]["questions"][current]["answers"]
    answerstr = ", ".join([answers[i] for i in poll_answers])
    logger.info(
        _("Пользователь {name} ответил на вопрос №{num}:\n\t{answers}.").format(
            name=name, num=current + 1, answers=answerstr
        )
    )
    context.bot_data["ongoing"][poll_id]["answered"] += 1
    if current == 0:
        context.bot_data["ongoing"]["answers"].setdefault(uid, {"name": name})
    context.bot_data["ongoing"]["answers"][uid].setdefault(current, answerstr)
    context.bot.edit_message_text(
        text=_(
            "Ответили {curr} из {cap} участников. Следующий вопрос появится, когда ответят все!"
        ).format(
            curr=context.bot_data["ongoing"][poll_id]["answered"], cap=ongoing["cap"]
        ),
        chat_id=chat_id,
        message_id=ongoing[poll_id]["counter_id"],
    )
    if context.bot_data["ongoing"][poll_id]["answered"] == ongoing["cap"]:
        context.bot.stop_poll(
            chat_id=chat_id,
            message_id=context.bot_data["ongoing"][poll_id]["message_id"],
        )
        context.bot.edit_message_text(
            text=_("Ответили {cap} из {cap} участников.").format(cap=ongoing["cap"]),
            chat_id=chat_id,
            message_id=ongoing[poll_id]["counter_id"],
        )
        context.bot_data["ongoing"]["current_question"] += 1
        if context.bot_data["ongoing"]["current_question"] < len(
            ongoing["survey"]["questions"]
        ):
            post_question(context)
        else:
            logger.info(_("Опрос завершён"))
            context.bot.send_message(
                chat_id=chat_id, text=_("Опрос окончен! Всем спасибо за участие.")
            )
            questions = [
                question["question"]
                for question in context.bot_data["ongoing"]["survey"]["questions"]
            ]
            utils.submit_data(
                answers=context.bot_data["ongoing"]["answers"],
                questions=questions,
                title=ongoing["survey"]["title"],
                file=context.bot_data[consts.SHEETS_KEY]["file"],
                email=context.bot_data[consts.SHEETS_KEY]["email"],
            )
            del context.bot_data["ongoing"]
            context.bot_data["poll_ongoing"] = False
