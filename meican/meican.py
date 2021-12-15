from datetime import datetime, time
import uuid
import requests
from meican.config import Config
from meican import error


class UnauthorizedException(Exception):
    pass

class Meican():

    API_BASE = 'https://api.meican.com'
    AUTH_URL = 'https://api-cn-2.meican.com/v3.0/oauth/token'
    CLIENT_ID = 'TMorVol3uXnalyM7J9s5MMHZdn8HgoM'
    CLIENT_SECRET = 'hQaauYWVcZsJR4zEXMdFY4ogo7lsQOT'

    def __init__(self, config):
        self.__config = config

    def __get_auth_header(self):
        t = self.__config.get('token', 'token_type')
        v = self.__config.get('token', 'access_token')
        if not (t and v):
            return None
        return '%s %s' % (t, v)

    def __default_headers(self):
        headers = {
            'Accept-Charset': 'utf-8',
            'Cache-Control': 'no-cache',
            'Cookie': 'guestId=70a12350-f052-4fa4-84e4-44a4ee209b8d; machineId=93ab1ad4-0a38-40ef-893d-964774641970',
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Meican/ios (main; prod; 3.0.59; 539)',
            'Accept-Language': 'zh',
        }
        auth = self.__get_auth_header()
        if auth:
            headers['Authorization'] = auth
        return headers

    def __make_params(self, params):
        p = {
            'client_id': self.CLIENT_ID,
            'client_secret': self.CLIENT_SECRET,
        }
        if params:
            p.update(params)
        return p

    def __need_login(self):
        auth = self.__get_auth_header()
        if not auth:
            return True
        expires_in = int(self.__config.get('token', 'expires_in'))
        create_at = int(self.__config.get('token', 'create_at'))
        now = int(datetime.now().timestamp())
        return now > create_at + expires_in - 60

    def __save_token(self, resp):
        j = resp.json()
        self.__config.set('token', 'access_token', j['access_token'])
        self.__config.set('token', 'token_type', j['token_type'])
        self.__config.set('token', 'refresh_token', j['refresh_token'])
        self.__config.set('token', 'expires_in', str(j['expires_in']))
        self.__config.set('token', 'create_at', str(int(datetime.now().timestamp())))
        self.__config.write()

    def __clean_token(self):
        self.__config.set('token', 'access_token', '')
        self.__config.set('token', 'token_type', '')
        self.__config.set('token', 'expires_in', '')
        self.__config.set('token', 'create_at', '')
        self.__config.write()

    def login(self):
        if not self.__need_login():
            return

        self.__clean_token()
        # if self.__config.get('token', 'refresh_token'):
        #     # todo login if refresh token is invalid
        #     print('refresh')
        #     self.__refresh_token()
        #     return

        data = {
            'grant_type': 'password',
            'username': self.__config.get('auth', 'username'),
            'password': self.__config.get('auth', 'password'),
            'meican_credential_type': 'password',
            'verifyCode': '',
            'mobile': '',
            'client_secret': self.CLIENT_SECRET,
            'client_id': self.CLIENT_ID,
        }
        resp = requests.post(self.AUTH_URL, data=data, headers=self.__default_headers())
        if resp.status_code == 200:
            self.__save_token(resp)
        elif resp.status_code == 401:
            raise UnauthorizedException(resp.text)
        else:
            raise Exception('request to %s error, code %d, %s' % (resp.request.url, resp.status_code, resp.text))

    def __refresh_token(self):
        data = {
            'grant_type': 'new_token',
            'refresh_token': self.__config.get('token', 'refresh_token'),
            'client_secret': self.CLIENT_SECRET,
            'client_id': self.CLIENT_ID,
        }
        resp = requests.post(self.AUTH_URL, data=data, headers=self.__default_headers())
        if resp.status_code == 200:
            self.__save_token(resp)
        elif resp.status_code == 401:
            print(resp.request.headers)
            raise UnauthorizedException(resp.text)
        else:
            raise Exception('request to %s error, code %d, %s' % (resp.request.url, resp.status_code, resp.text))

    def get_balance(self, total=3000):
        bills = self.list_bill()
        return total - sum([
            b['amountInCent'] - b['userPaidInCent']
            for b in filter(self.__is_today_consume_bill, bills)
        ])

    def __is_today_consume_bill(self, b):
        today = int(datetime.combine(datetime.now(), time.min).timestamp() * 1000)
        return b['billType'] == 'consume' and b['createTime'] >= today

    def list_bill(self, limit=10):
        resp = self.__get('/v2.1/payment/mainTransList', params={'limit': limit})
        return resp.get('list', [])

    def qrpay(self, qrcode, amount_cent):
        data = {
            'qrcode': qrcode,
            'token': str(uuid.uuid4()).upper(),
            'priceInCent': amount_cent,
        }
        resp = self.__post('/v2.1/qrpay/createorder', data=data)
        return resp

    def __get(self, url, params=None):
        return self.__get_response(
            requests.get(self.API_BASE + url, params=self.__make_params(params), headers=self.__default_headers())
        )

    def __post(self, url, params=None, data=None):
        return self.__get_response(
            requests.post(self.API_BASE + url, params=params, data=self.__make_params(data), headers=self.__default_headers())
        )

    def __get_response(self, resp):
        if resp.status_code == 200:
            return resp.json().get('data', {})
        elif resp.status_code == 401:
            raise UnauthorizedException(resp.text)
        else:
            raise Exception('request to %s error, code %d, %s' % (resp.request.url, resp.status_code, resp.text))

def add_meican_command(commands):
    config_parser = commands.add_parser('qrpay', help='qrpay')
    config_parser.add_argument('restaurant', help='restaurant name, aiba or jiduo')
    config_parser.add_argument('-a', '--amount', type=float, help='amount in yuan, like 16 or 16.1')
    config_parser.set_defaults(__command_handler=__command_qrpay)

RESTAURANT_MAP = {
    'aiba': {
        'code': '1b0678',
        'name': '爱吧便利店',
    },
    'jiduo': {
        'code': '59c59e',
        'name': '吉多便利店',
    },
}

def __command_qrpay(restaurant, amount=None):
    if (datetime.now().hour < 15):
        error.fatal(error.ERROR_INVALID_TIME, 'can not pay before 15:00')

    info = RESTAURANT_MAP.get(restaurant)
    if not info:
        error.fatal(error.ERROR_INVALID_RESTAURANT, 'invalid restaurant %s' % restaurant)
    qrcode = 'https://meican.com/qrpay/restaurant/' + info['code']

    m = Meican(Config())
    m.login()

    if amount is None:
        # auto get amount
        amount_cent = m.get_balance()
        amount = amount_cent / 100
    else:
        amount_cent = int(amount * 100)

    print('pay %s yuan to %s' % (amount, restaurant))

    order = m.qrpay(qrcode, amount_cent)
    if order['payStatus'] == 'DONE':
        print('订单金额：%.2f' % (order['total'] / 100))
        print('餐厅名称：' + info['name'])
        print('订单编号：%s' % (order['billNumber']))
        print('下单时间：%s' % (datetime.fromtimestamp(order['paidTime'] / 1000).strftime('%Y.%m.%d %H:%M')))
    else:
        print(order)

if __name__ == "__main__":
    m = Meican(Config())
    m.login()
    b = m.get_balance()
    print(b)
