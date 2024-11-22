import smtplib
from email.mime.text import MIMEText


class WrongFile(Exception):
    pass


class LoginError(Exception):
    pass


class SendError(Exception):
    pass


class SMTPServerError(Exception):
    pass


class WrongEmail(Exception):
    pass


class SendMessage:
    def __init__(self, recipient):
        self.recipient = recipient

    def send_email(self, date, filename):
        ''' Принимает на вход дату и имя файла, отправляет письмо на указанный адрес'''
        # данные отправителя
        with open('static/email_settings.txt', 'r', encoding='utf8') as file:
            sender, password = file.read().split('\n')

        # настройка сервера
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
        except BaseException:
            raise SMTPServerError('Ошибка smtp сервера')

        # форматирование текста письма
        try:
            with open("static/email_template.html", encoding='utf8') as file:
                template = file.read()

            with open(filename, 'r', encoding='utf8') as file:
                template = template.format(file.read())
        except BaseException:
            raise WrongFile('Выбран неверный файл')

        template = template.format(date)

        # формирование письма
        msg = MIMEText(template, "html")
        msg["From"] = sender
        msg["To"] = self.recipient

        with open('static/topic.txt', 'r', encoding='utf8') as file:
            msg["Subject"] = file.read()

        # отправка письма
        try:
            server.login(sender, password)
        except BaseException:
            raise LoginError('Регистрация не удалась')
        try:
            server.sendmail(sender, self.recipient, msg.as_string())
        except BaseException:
            raise SendError('Отправка не удалась')

    def formater(self) -> bool:
        ''' Проверяет почту на правильность написания '''
        email = str(self.recipient)
        if email.count('@') == 1 and email.count('.') == 1 and email.index('@') < email.index('.'):
            return email
        raise WrongEmail('Введен неверный адрес почты!')
