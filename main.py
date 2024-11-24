# дата, почта, телефон
# нужно собирать приемы со сроками <= неделя

import sys
import time

from PyQt6.QtCore import QDateTime
from PyQt6 import QtGui
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox

# дизайн
from static.design import Ui_MainWindow

# проверка номеров телефонов
from phone import PhoneNumber
# проверка и отправка почты
from send_email import SendMessage

import sqlite3 as sql

# Errors
from phone import FirstNumber, Staples, Dash, PhoneError, CountOfNumbers, CountryCode, IsNumbers, Operator
from send_email import WrongFile, WrongEmail, LoginError, SendError, SMTPServerError

DB_NAME = 'db/users_db.sqlite'


class WrongDate(Exception):
    pass


def error_message_box(obj, er):
    QMessageBox.critical(obj, 'Error', er)


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.retranslateUi(self)
        self.loadSettings()
        self.loadUI()

    def loadUI(self):
        # загрузка дизайна главного окна
        self.setWindowIcon(QtGui.QIcon('static/favicon.png'))
        self.send_btn.clicked.connect(self.save_user_data)

    def loadSettings(self):
        # загрузка значений в окно настроек
        with open('static/email_settings.txt', 'r', encoding='utf8') as file:
            email, password = file.read().split('\n')
        with open('static/topic.txt', 'r', encoding='utf8') as file:
            topic = file.read()
        with open('static/notification.txt', 'r', encoding='utf8') as file:
            notification = file.read()
        with open('static/reception_began.txt', 'r', encoding='utf8') as file:
            reception_began = file.read()
        # поля ввода
        self.set_email.setText(email)
        self.set_password.setText(password)
        self.set_topic.setText(topic)
        self.set_notification.setText(notification)
        self.set_reception_began.setText(reception_began)
        # кнопки
        self.save_settings_btn.clicked.connect(self.save_settings)

    def user_saved_message_box(self, s):
        dlg = QMessageBox(self)
        dlg.setWindowTitle('Сообщение')
        dlg.setText(s)
        button = dlg.exec()
        if button == QMessageBox.StandardButton.Ok:
            self.surname.setText('')
            self.name.setText('')
            self.patronymic.setText('')
            self.mail.setText('')
            self.phone.setText('')
            self.date.setDateTime(QDateTime(2000, 1, 1, 0, 0, 0))

    def is_filled(self, obj):
        if obj.text():
            return True
        return False

    def save_settings(self):
        # сохранение настроек
        if all([self.is_filled(self.set_email), self.is_filled(self.set_password), self.is_filled(self.set_topic),
                self.is_filled(self.set_notification), self.is_filled(self.set_reception_began)]):
            email = self.set_email.text()
            password = self.set_password.text()
            topic = self.set_topic.text()
            notification = self.set_notification.text()
            reception_began = self.set_reception_began.text()
            # запись в файлы
            with open('static/email_settings.txt', 'w', encoding='utf8') as file:
                file.write('{}\n{}'.format(email, password))
            with open('static/topic.txt', 'w', encoding='utf8') as file:
                file.write(topic)
            with open('static/notification.txt', 'w', encoding='utf8') as file:
                file.write(notification)
            with open('static/reception_began.txt', 'w', encoding='utf8') as file:
                file.write(reception_began)
        else:
            error_message_box(self, 'Заполнены не все обязательные поля!')

    def save_user_data(self):
        # сохранение данных пользователя в бд
        try:
            surname = self.surname.text()
            name = self.name.text()
            patronymic = self.patronymic.text()
            email = self.mail.text()
            phone = self.phone.text()
            date = self.date.dateTime().toString()
            if all([surname, name, patronymic, date]) and any([phone, email]):
                if phone:
                    phone = PhoneNumber(phone).formater()
                    save_user_to_db(f'{surname} {name} {patronymic}', date, phone=phone)
                elif email:
                    email = SendMessage(email).formater()
                    save_user_to_db(f'{surname} {name} {patronymic}', date, email=email)
                self.user_saved_message_box('Данные успешно сохранены!')
            else:
                error_message_box(self, 'Заполнены не все обязательные поля!')
        except WrongDate as wd:
            error_message_box(self, str(wd))
        except WrongEmail as we:
            error_message_box(self, str(we))
        except IsNumbers as i_n:
            error_message_box(self, str(i_n))
        except FirstNumber as fn:
            error_message_box(self, str(fn))
        except Staples as s:
            error_message_box(self, str(s))
        except Dash as d:
            error_message_box(self, str(d))
        except CountOfNumbers as con:
            error_message_box(self, str(con))
        except Operator as op:
            error_message_box(self, str(op))
        except PhoneError as pe:
            error_message_box(self, str(pe))
        except CountryCode as cc:
            error_message_box(self, str(cc))
        except Exception as ex:
            print('Произошла ошибка:', ex)


def update_error(id, er) -> None:
    # обновляет поле error в бд
    with sql.connect(DB_NAME) as con:
        con.cursor().execute(
            '''UPDATE users
            SET error = ?
            WHERE id = ?''',
            (er, id)
        )
        con.commit()


def delete_user(id):
    with sql.connect(DB_NAME) as con:
        con.cursor().execute(
            '''DELETE FROM users
            WHERE id = ?''',
            (id,)
        )
        con.commit()


def send_mail_to_user(id: int, date, email='', phone=''):
    flag = True
    for _ in range(3):
        if flag:
            time.sleep(0.5)
            try:
                if phone:
                    pass
                if email:
                    message = SendMessage(email)
                    message.send_email(date, 'static/notification.txt')
                print('Email successfully sent!')
                update_error(id, 'True')
                flag = False
            except WrongFile as wf:
                update_error(id, str(wf))
            except LoginError as le:
                update_error(id, str(le))
            except SendError as se:
                update_error(id, str(se))
            except SMTPServerError as smtpe:
                update_error(id, str(smtpe))
            except Exception as ex:
                update_error(id, str(ex))


def load_users_from_db():
    with sql.connect(DB_NAME) as con:
        users = con.cursor().execute(
            '''SELECT * FROM users'''
        )
    return users


def save_user_to_db(name, date, email='', phone=''):
    with sql.connect(DB_NAME) as con:
        if email:
            con.cursor().execute(
                'INSERT INTO users(name, date, email, phone, error) VALUES (?, ?, ?, ?, ?)',
                (name, date, email, '', 'False')
            )
        elif phone:
            con.cursor().execute(
                'INSERT INTO users(name, date, email, phone, error) VALUES (?, ?, ?, ?, ?)',
                (name, date, '', phone, 'False')
            )
        con.commit()


def find_and_move_users_to_sending():
    # все юзеры
    users = load_users_from_db()
    # не отправленные
    my_users = []
    for user in users:
        id, name, date, email, phone, error = user
        if error != 'True':
            my_users.append(user)
    # работа с неотправленными юзерами
    for user in my_users:
        id, name, date, email, phone, error = user
        if True:  # сделать условие со временем
            send_mail_to_user(id, date, email, phone)


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    find_and_move_users_to_sending()
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())

# БД
# id
# name
# date
# email
# phone
# error
