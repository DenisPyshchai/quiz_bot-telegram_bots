from sqlalchemy import text
from telegram import ReplyKeyboardRemove
from dateutil.parser import parse
from telegram.ext import *
from utils.quiz_utils import *
from utils.db_utils import *
from enums.input_structure import *
from models.bot_models import TelegramBot, QuizBot
from models.manager_models import BotManagerInterface


class QuizTelegramBot(TelegramBot, QuizBot):

    def __init__(self, manager: BotManagerInterface, quiz_json_data: dict,
                 table_name: str, schema_name: str, bot_id=None):
        QuizBot.__init__(self, quiz_json_data, table_name, schema_name)
        TelegramBot.__init__(self, manager, bot_id=bot_id)
        self.dispatcher.add_handler(CommandHandler("start", self.start))
        self.dispatcher.add_handler(MessageHandler(Filters.text, self.handle_message))

    def start(self, update, context):
        sender_id = update.message.from_user.id
        with db.get_engine().connect() as con:
            if not self.multiple_registration and get_objects_by_messenger_id(con, self.table, self.schema, sender_id):
                self.telegram_bot.send_message(
                    update.message.chat.id,
                    self.done_message if self.done_message else "Your have already done this quiz, thank you!",
                    reply_markup=ReplyKeyboardRemove())
            else:
                if self.greeting:
                    self.telegram_bot.send_message(update.message.chat.id, self.greeting,
                                                   reply_markup=ReplyKeyboardRemove())
                first_question = list(self.quiz.keys())[0]
                answers = self.quiz[first_question].get(JSONKeys.answers.value)
                if answers is None:
                    self.telegram_bot.send_message(update.message.chat.id, first_question,
                                                   reply_markup=ReplyKeyboardRemove())
                else:
                    self.telegram_bot.send_message(update.message.chat.id, first_question,
                                                   reply_markup=create_keyboard(answers))
                self.users_answers[sender_id] = {}

    def handle_message(self, update, context):
        sender_id = update.message.from_user.id
        chat_id = update.message.chat.id
        message = update.message.text
        questions = list(self.quiz.keys())
        if sender_id in self.users_answers:
            for index, question in enumerate(questions):
                if question in self.users_answers[sender_id]:
                    continue
                else:
                    answers = self.quiz[question].get(JSONKeys.answers.value, [])
                    custom_answer = self.quiz[question].get(JSONKeys.custom_answer.value)
                    format_message = self.quiz[question].get(JSONKeys.format_message.value)
                    if message in answers:
                        pass
                    elif custom_answer:
                        if not self.__check_custom_answer_format(
                                message, chat_id, formats=custom_answer, format_message=format_message):
                            break
                    elif answers and message not in answers:
                        self.telegram_bot.send_message(chat_id, question, reply_markup=create_keyboard(answers))
                        break
                    else:
                        # This should be impossible to reach
                        raise Exception("Quiz bot has received invalid quiz json!")
                    self.users_answers[sender_id][question] = message
                    if (index + 1) < len(questions):
                        next_question = questions[index + 1]
                        next_answers = self.quiz[next_question].get(JSONKeys.answers.value)
                        if next_answers is None:
                            self.telegram_bot.send_message(chat_id, next_question,
                                                           reply_markup=ReplyKeyboardRemove())
                        else:
                            self.telegram_bot.send_message(chat_id, next_question,
                                                           reply_markup=create_keyboard(next_answers))
                    else:
                        self.__save_in_db(sender_id)
                        del self.users_answers[sender_id]
                        if self.farewell:
                            self.telegram_bot.send_message(chat_id, self.farewell,
                                                           reply_markup=ReplyKeyboardRemove())
                        else:
                            dummy_msg = self.telegram_bot.send_message(chat_id, "1", reply_markup=ReplyKeyboardRemove())
                            dummy_msg.delete()
                    break

        else:
            self.start(update, context)

    def __check_custom_answer_format(self, message, chat_id, formats=None, format_message=None):
        if formats is None:
            formats = [Formats.any.value]
        for format in formats:
            if format == Formats.any.value:
                return True
            elif format == Formats.only_letters.value and message.isalpha():
                return True
            elif format == Formats.integer.value and message.isnumeric():
                return True
            elif format == Formats.date.value and self.__is_date(message):
                return True
            elif format == Formats.name.value and check_person_name(message):
                return True
            elif format == Formats.phone_number.value and check_phone_number(message):
                return True
            elif format == Formats.email_address.value and check_email_address(message):
                return True
        if format_message:
            self.telegram_bot.send_message(chat_id, format_message[0])
        return False

    def __save_in_db(self, sender_id):
        data = {StandardColumns.id.value: uuid.uuid4(),
                StandardColumns.messenger_id.value: sender_id,
                StandardColumns.created.value: datetime.datetime.utcnow(),
                StandardColumns.updated.value: datetime.datetime.utcnow()}
        columns = f'{StandardColumns.id.value}, {StandardColumns.messenger_id.value},' \
                  f' {StandardColumns.created.value}, {StandardColumns.updated.value}, '
        values = f':{StandardColumns.id.value}, :{StandardColumns.messenger_id.value},' \
                 f' :{StandardColumns.created.value}, :{StandardColumns.updated.value}, '
        i = 1
        for question in self.users_answers[sender_id].keys():
            if JSONKeys.table_column.value in self.quiz[question]:
                data[f'param{i}'] = self.users_answers[sender_id][question]
                columns += f'"{self.quiz[question][JSONKeys.table_column.value]}", '
                values += f':param{i}, '
                i += 1
        columns = columns[:-2]
        values = values[:-2]
        statement = text(f'INSERT INTO "{self.schema}"."{self.table}"({columns}) VALUES({values})')
        with db.get_engine().connect() as con:
            con.execute(statement, **data)
            db.session.commit()

    @staticmethod
    def __is_date(string, fuzzy=False):
        try:
            parse(string, fuzzy=fuzzy)
            return True

        except ValueError:
            return False
