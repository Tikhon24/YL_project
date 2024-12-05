import sys
import time
from datetime import datetime, timedelta

from PyQt6 import uic
from PyQt6.QtCore import QDateTime, Qt
from PyQt6 import QtGui
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QTableWidgetItem, QHeaderView, QWidget, QPushButton
from PyQt6.QtCore import QThread, pyqtSignal

# дизайн
from design.main_window_design import Ui_MainWindow
from design.users_table_design import Ui_UsersTable

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


class DataBaseChecker(QThread):
    db_data = pyqtSignal(list)

    def run(self):
        while True:
            users_data = load_users_from_db()
            self.db_data.emit(users_data)
            time.sleep(10)


class UsersTable(QWidget, Ui_UsersTable):
    def __init__(self):
        super().__init__()
        # загрузка интерфейса
        self.setupUi(self)
        self.retranslateUi(self)
        self.setWindowIcon(QtGui.QIcon('static/favicon.png'))

        self.table_flag = True

    def loadTable(self):
        self.table_flag = True
        self.users_table.setRowCount(0)
        self.users_table.setColumnCount(0)
        self.update()

    def paintEvent(self, event):
        if self.table_flag:
            self.table_flag = False
            users = load_users_from_db()
            if users:
                self.users_table.setRowCount(0)
                index_id = {}
                ids = [user[0] for user in users]
                self.users_table.setColumnCount(6)
                self.users_table.setHorizontalHeaderLabels(
                    ['Удаление', 'Имя', 'Дата', 'Почта', 'Телефон', 'Статус отправки'])
                for i, row in enumerate(users):
                    index_id[i + 1] = ids[i]
                    self.users_table.setRowCount(
                        self.users_table.rowCount() + 1)
                    for j, elem in enumerate(row):
                        match j:
                            case 0:
                                user_index = index_id[i + 1]
                                button = QPushButton('Удалить')
                                # Используем функцию-обертку для передачи user_index
                                button.clicked.connect(self.create_delete_handler(user_index))
                                self.users_table.setCellWidget(i, j, button)
                                continue
                            case 2:
                                elem = datetime.strptime(elem, '%Y-%m-%d %H:%M:%S')
                                elem = elem.strftime("%H:%M %d.%m.%Y")
                            case 5:
                                if elem == 'True':
                                    elem = 'Отправлено'
                                elif elem == 'False':
                                    elem = 'Не отправлено'
                        if elem == '':
                            elem = 'Не указано'
                        self.users_table.setItem(i, j, QTableWidgetItem(elem))
            self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def create_delete_handler(self, user_index):
        # Возвращаем лямбда-функцию, которая вызывает delete_user с правильным user_index
        return lambda checked: self.delete_user(user_index)

    def delete_user(self, id: int):
        delete_user(id)
        self.loadTable()


class MainWindow(QMainWindow, Ui_MainWindow):
    # основное окно приложения
    def __init__(self):
        super().__init__()
        # загрузка интерфейса
        self.setupUi(self)
        self.retranslateUi(self)
        self.loadSettings()
        self.loadUI()

        self.table = UsersTable()

    def start_checking(self):
        # запускает второй поток
        self.db_checker = DataBaseChecker()
        self.db_checker.db_data.connect(self.update_all)
        self.db_checker.start()

    def update_all(self, users_data):
        # обновляет все данные связанные с бд
        find_and_move_users_to_sending(users_data)
        self.update_table()

    def update_table(self):
        self.table.loadTable()

    def loadUI(self):
        # загрузка дизайна главного окна
        self.setWindowIcon(QtGui.QIcon('static/favicon.png'))
        self.send_btn.clicked.connect(self.save_user_data)
        self.table_btn.clicked.connect(self.loadTable)
        self.pixmap = QPixmap('static/pic_write.png')
        self.picture.setPixmap(self.pixmap)
        # запуск асинхронного потока
        self.start_checking()

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

    def loadTable(self):
        self.table.loadTable()
        self.table.show()

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
            surname = self.surname.text().strip()
            name = self.name.text().strip()
            patronymic = self.patronymic.text().strip()
            email = self.mail.text()
            phone = self.phone.text()
            date = self.date.dateTime().toPyDateTime()
            if all([surname, name, date]) and any([phone, email]):
                if phone:
                    phone = PhoneNumber(phone).formater()
                if email:
                    email = SendMessage(email).formater()
                save_user_to_db(f'{surname} {name} {patronymic}', date, email=email, phone=phone)
                self.user_saved_message_box('Данные успешно сохранены!')
                try:
                    self.table.loadTable()
                except Exception:
                    pass
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

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.save_user_data()


# РАБОТА С БД
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


def delete_user(id: int):
    # удаление юзера из бд
    with sql.connect(DB_NAME) as con:
        con.cursor().execute(
            '''DELETE FROM users
            WHERE id = ?''',
            (id,)
        )
        con.commit()


def send_mail_to_user(id: int, date, email='', phone='', is_began=False):
    # отправка сообщения
    flag = True
    for _ in range(3):
        if flag:
            time.sleep(0.5)
            try:
                if phone:
                    pass
                if email:
                    message = SendMessage(email)
                    date = date.strftime("%H:%M %d.%m.%Y")
                    if is_began:
                        message.send_email(date, 'static/reception_began.txt')
                    else:
                        message.send_email(date, 'static/notification.txt')
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


def load_users_from_db() -> list[tuple]:
    # возвращает все записи из бд
    with sql.connect(DB_NAME) as con:
        users = con.cursor().execute(
            '''SELECT * FROM users'''
        )
    return list(users)


def save_user_to_db(name, date, email='', phone=''):
    # добавляет юзера в бд
    with sql.connect(DB_NAME) as con:
        if email and phone:
            con.cursor().execute(
                'INSERT INTO users(name, date, email, phone, error) VALUES (?, ?, ?, ?, ?)',
                (name, date, email, phone, 'False')
            )
        elif email:
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


def find_and_move_users_to_sending(users=''):
    # все юзеры
    if users == '':
        users = load_users_from_db()
    # не отправленные
    my_users = []
    for user in users:
        id, name, date, email, phone, error = user
        if error != 'True':
            my_users.append(user)
    # работа с неотправленными юзерами
    now = datetime.now()
    one_week_later = now + timedelta(weeks=1)
    for user in my_users:
        id, name, date, email, phone, error = user
        date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        if date <= now:  # сделать условие со временем
            send_mail_to_user(id, date, email, phone, is_began=True)
        elif date <= one_week_later:
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
