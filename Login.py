import json
import os
import random
import re
import sys
import time

import requests
from bs4 import BeautifulSoup

from EncryptUtils import xEncode, base64_enc, sha1, md5

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36 Edg/94.0.992.38",
}


class Login:
    def __init__(self, username, passwd, alway_online=True, ac_id="1", n="200", type="1", enc_ver="srun_bx1",
                 action="login",
                    domain='@dx-uestc',
                    headers=HEADERS,
                    base_auth_url='http://10.253.0.237/',
                    challenge_url='cgi-bin/get_challenge',
                    login_url='cgi-bin/srun_portal',
                    status_url='cgi-bin/rad_user_info'):
        self.alway_online = alway_online
        self.username = username + domain
        self.domain = domain
        self.password = passwd
        self.ac_id = ac_id
        self.n = n
        self.type = type
        self.action = action
        self.enc_ver = enc_ver
        self.headers = headers
        self.base_auth_url = base_auth_url
        self.challenge_url = os.path.join(base_auth_url, challenge_url)
        self.login_url = os.path.join(base_auth_url, login_url)
        self.status_url = os.path.join(base_auth_url, status_url)
        self.status = 0
        self.tried = 0

    def run(self, tp):
        self.tp = tp
        while self.alway_online:
            self.check_status()
            time.sleep(10)
        else:
            self.check_status()

    def login(self):
        self.callback = self.get_callback()
        self.get_ip()
        challenge = self.get_challenge()
        info = {
            "username": self.username,
            "password": self.password,
            "ip": self.ip,
            "acid": self.ac_id,
            "enc_ver": self.enc_ver
        }
        info = "{SRBX1}" + base64_enc(xEncode(str(info).replace(" ", "").replace("'", '"'), challenge))
        hmd5 = "{MD5}" + md5("", challenge)
        chksum = self.get_chksum(challenge, info)
        self.callback = self.get_callback()
        params = {
            'callback': self.callback,
            'action': self.action,
            'username': self.username,
            'password': hmd5,
            'ac_id': self.ac_id,
            'ip': self.ip,
            'info': info,
            'chksum': chksum,
            'n': self.n,
            'type': self.type
        }
        response = requests.get(self.login_url, params=params, headers=self.headers).text
        content = json.loads(response.replace(self.callback, '')[1:-1])
        print(content)
        if "error_msg" in content and "res" in content and content['error'] == "login_error" and self.tried <= 3:
            self.tp.showMessage(self.username.replace(self.domain, '') + ' 登录失败', content['error_msg'], icon=2)
            self.tried += 1
            self.status = 0

        elif "ploy_msg" in content and "res" in content and content['ploy_msg'] == "E0000: Login is successful.":
            self.tp.showMessage(self.username.replace(self.domain, '') + ' 登录成功', content['ploy_msg'], icon=1)
            self.tried = 0
            self.status = 0

        print("Login: ", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), content['res'], self.ip)
        return content['res'], self.ip

    def get_chksum(self, challenge, info):
        chkstr = challenge + self.username
        chkstr += challenge + md5("", challenge)
        chkstr += challenge + self.ac_id
        chkstr += challenge + self.ip
        chkstr += challenge + self.n
        chkstr += challenge + self.type
        chkstr += challenge + info
        chksum = sha1(chkstr)
        return chksum

    def get_ip(self):
        response = requests.get(self.base_auth_url, headers=self.headers).text
        htmlContent = BeautifulSoup(response, 'html.parser')
        ip = htmlContent.find('input', id='user_ip').attrs['value']
        self.ip = ip
        assert re.match(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$", ip), "Invalid IP or Failed to get IP!"

    def get_random_string(self, length):
        return ''.join(random.sample(
            ['z', 'y', 'x', 'w', 'v', 'u', 't', 's', 'r', 'q', 'p', 'o', 'n', 'm', 'l', 'k', 'j', 'i', 'h', 'g', 'f',
             'e', 'd', 'c', 'b', 'a', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0'], length))

    def get_timestampe(self):
        return str(round(time.time() * 1000))

    def get_callback(self):
        return 'jQuery' + self.get_random_string(21) + '_' + self.get_timestampe()

    def get_challenge(self):
        params = {
            'callback': self.callback,
            'username': self.username,
            'ip': self.ip
        }
        response = requests.get(self.challenge_url, params=params, headers=self.headers).text
        content = json.loads(response.replace(self.callback, '')[1:-1])
        challenge = content['challenge']
        client_ip = content['client_ip']
        assert client_ip == self.ip, "IP doesn't match!"
        self.ip = client_ip if self.ip == "" else self.ip
        return challenge

    def check_status(self):
        params = {
            "callback": "dasdasdsada"
        }
        response = requests.get(self.status_url, params=params, headers=self.headers).text
        content = json.loads(response.replace("dasdasdsada", '')[1:-1])
        print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), content)
        if 'res' not in content and "error" in content and content['error'] == 'ok' and self.status != 0:
            self.tp.showMessage(content['user_name'] + ' 网络正常', "当前IP："+content['online_ip'], icon=1)
            self.status = 0
        if 'res' in content and content['res'] == 'not_online_error':
            if self.status < 3:
                self.tp.showMessage(self.username.replace(self.domain, '') + ' 已离线', "登出IP："+content['online_ip'], icon=2)
                self.status += 1
            self.login()


if __name__ == '__main__':
    username = sys.argv[1]
    passwd = sys.argv[2]
    login = Login(username, passwd)  # For Lab (主楼B1)
    # login = Login(username, passwd, ac_id="3", domain="@cmcc", base_auth_url="http://10.253.0.237/") # For dormitory (硕丰6组团-21栋)
    login.run()
