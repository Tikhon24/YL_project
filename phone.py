ERROR_FORMAT = 'Неверный формат'
ERROR_COUNT = 'Неверное количество цифр'


class FirstNumber(Exception):
    pass


class Staples(Exception):
    pass


class Dash(Exception):
    pass


class PhoneError(Exception):
    pass


class CountOfNumbers(Exception):
    pass


class IsNumbers(Exception):
    pass


class Operator(Exception):
    pass


class CountryCode(Exception):
    pass


class CheckPhone:

    def is_numbers(self, number):
        # проверка на лишние символы(буквы и т.д.)
        for i in number:
            try:
                if i in ['(', ')', '-', '+', ' ', '\t', '\n']:
                    continue
                int(i)
            except ValueError:
                raise IsNumbers(ERROR_FORMAT)
        return True

    def staples(self, number):
        # скобки
        count_left_staples = 0
        count_right_staples = 0
        for i in number:
            if i == ')' and count_left_staples == 0:
                raise Staples(ERROR_FORMAT)
            if i == '(':
                count_left_staples += 1
            elif i == ')':
                count_right_staples += 1
        if (count_right_staples == 1 and count_left_staples == 1) or (
                count_right_staples == 0 and count_left_staples == 0):
            return True
        raise Staples(ERROR_FORMAT)

    def dashes(self, number):
        # проверка знака "-"
        if number[0] == '-' or number[-1] == '-':
            raise Dash(ERROR_FORMAT)
        j = ''
        for i in number:
            if j == '-' and i == '-':
                raise Dash(ERROR_FORMAT)
            j = i
        return True

    def count_numbers(self, number, code):
        # длина номера телефона
        if len(number) == 12:
            return True
        raise CountOfNumbers(ERROR_COUNT)

    def right_operator(self, number, code='+7'):
        # проверка на корректного оператора
        # сюда телефон подается с корректным кодом
        if code == '+7':
            if int(number[len(code):len(code) + 3]) in (
                    list(range(910, 920)) + list(range(980, 990)) + list(range(920, 940)) +
                    list(range(902, 907)) + list(range(960, 970))):
                return True
            raise Operator('Не определяется оператор сотовой связи!')
        else:
            return True


class PhoneNumber(CheckPhone):
    ''' Принимает номер телефона и проверяет его на достоверность '''

    def __init__(self, number: str):
        self.number = number

    def _get_phone(self):
        if all([self.staples(self.number), self.dashes(self.number), self.is_numbers(self.number)]):
            return self.number

    def formater(self):
        ''' Если номер верный, возвращает его отфармотированным '''
        phone_number = self._get_phone()
        if phone_number:
            for i in ['(', ')', '-']:
                phone_number = phone_number.replace(i, '')
            phone_number = ''.join(phone_number.strip().split())
            code = '+7'
            if phone_number[:2] == '+7':
                code = '+7'
            elif phone_number[0] == '8':
                phone_number = '+7' + phone_number[1:]
                code = '+7'
            elif phone_number[:4] == '+359':
                code = '+359'
            elif phone_number[:3] == '+55':
                code = '+55'
            elif phone_number[:2] == '+1':
                code = '+1'
            else:
                raise CountryCode('Не определяется код страны')
            if self.count_numbers(phone_number, code) and self.right_operator(phone_number, code):
                return str(phone_number)
        raise PhoneError(ERROR_FORMAT)
