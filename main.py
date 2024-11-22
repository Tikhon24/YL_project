# дата, почта, телефон
# нужно собирать приемы с прошедшими сроками или те, у которых срок не неделя а меньше
# отправить заменить на "добавить на отправку"
import datetime

import sys

from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QWidget, QApplication, QLabel, QMainWindow, QMessageBox, QLineEdit

# проверка номеров телефонов
from phone import PhoneNumber
# проверка и отправка почты
from send_email import SendMessage

import sqlite3 as sql

# Errors
from phone import FirstNumber, Staples, Dash, PhoneError, CountOfNumbers, CountryCode, IsNumbers, Operator


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('main_window.ui', self)
        self.loadSettings()
        self.loadUI()

    def loadUI(self):
        # загрузка дизайна главного окна
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

    def error_message_box(self, er):
        QMessageBox.critical(self, 'Error', er)

    def is_filled(self, obj):
        if obj.text():
            return True
        return False

    def save_settings(self):
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
            self.error_message_box('Заполнены не все обязательные поля!')

    def save_user_data(self):
        surname = self.surname.text()
        name = self.name.text()
        patronymic = self.patronymic.text()
        email = self.mail.text()
        phone = self.phone.text()
        date = self.date.dateTime().toString()
        print(date)
        if all([surname, name, patronymic, date]) and any([phone, email]):
            if phone:
                phone = PhoneNumber(phone).formater()
            elif email:
                email = SendMessage(email).formater()
        else:
            self.error_message_box('Заполнены не все обязательные поля!')


if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        ex = MainWindow()
        ex.show()
        sys.exit(app.exec())
    except IsNumbers as i_n:
        print(i_n)
    except FirstNumber as fn:
        print(fn)
    except Staples as s:
        print(s)
    except Dash as d:
        print(d)
    except CountOfNumbers as con:
        print(con)
    except Operator as op:
        print(op)
    except PhoneError as pe:
        print(pe)
    except CountryCode as cc:
        print(cc)
    except Exception as ex:
        print('Произошла ошибка:', ex)

# БД
# id
# name
# date
# email
# phone
