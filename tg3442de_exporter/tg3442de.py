import binascii
from Crypto.Cipher import AES
import hashlib
import json
import re
import requests
import sys

class TG3442DE():
    def __init__(self,logger, address, key, timeout,simulate=False):
        self.logger = logger
        self.logger.debug("__init__")        
        self.ip_address = address
        self.url = 'http://' + address
        self.username = 'admin'
        self.password = key
        self.timeout = timeout
        self.simulate = simulate
        self.session = requests.Session()
        if (self.simulate):
            self.logger.info("Simulating Device Access")
        

    def login(self):
        self.logger.debug("TG3442DE Logging in at " + self.ip_address)
        if self.simulate == False:
            # the web UI sends this on every request; firmware 01.05.069.14 needs it for the login too
            self.session.headers.update({"X-Requested-With": "XMLHttpRequest"})
            # get login page
            r = self.session.get(f"{self.url}",timeout=self.timeout)
            # parse HTML
            # get session id from javascript in head
            current_session_id = re.search(r".*var currentSessionId = '(.+)';.*", r.text)[1]

            # encrypt password
            iv = re.search(r".*var myIv = '(.+)';.*",r.text)[1]
            salt = re.search(r".*var mySalt = '(.+)';.*",r.text)[1]
            key = hashlib.pbkdf2_hmac(
                'sha256',
                bytes(self.password.encode("utf-8")),
                binascii.unhexlify(salt),
                iterations=1000,
                dklen=16
            )

            # build the plaintext like the web UI's JavaScript does (plain concatenation, no JSON escaping)
            plaintext = ('{"Password": "' + self.password + '", "Nonce": "' + current_session_id + '"}').encode("utf-8")
            associated_data = "loginPassword"
            
            # initialize cipher
            cipher = AES.new(key, AES.MODE_CCM, binascii.unhexlify(iv))
            # set associated data
            cipher.update(bytes(associated_data.encode("ascii")))
            # encrypt plaintext
            encrypt_data = cipher.encrypt(plaintext)
            # append digest
            encrypt_data += cipher.digest()
            # return
            login_data = {
                'EncryptData': binascii.hexlify(encrypt_data).decode("ascii"),
                'Name': self.username,
                'AuthData': associated_data
            }

            # login
            r = self.session.post(
                f"{self.url}/php/ajaxSet_Password.php",
                headers={
                    "Content-Type": "application/json",
                },
                data=json.dumps(login_data),
                timeout=self.timeout
            )

            # parse result
            # success? newer firmware does not always say "AdminMatch", so look for the encrypted nonce instead
            try:
                result = json.loads(r.text)
            except ValueError:
                result = {}
            if 'encryptData' not in result:
                self.logger.info(f"login failure: HTTP {r.status_code}, p_status={result.get('p_status')!r}")
                return
            self.logger.debug(f"login ok: p_status={result.get('p_status')!r}")

            # remember CSRF nonce
            encryptData = result['encryptData']
            cipher = AES.new(key, AES.MODE_CCM, binascii.unhexlify(iv))
            plain_data = cipher.decrypt(binascii.unhexlify(encryptData))
            csrf_nonce = plain_data[:32]

            # prepare headers
            self.session.headers.update({
                "X-Requested-With": "XMLHttpRequest",
                "csrfNonce": csrf_nonce,
                "Origin": f"{self.url}/",
            })

            # set credentials cookie from /base_95x.js, as the web UI and vodafone-station-cli do
            r = self.session.get(f"{self.url}/base_95x.js", timeout=self.timeout)
            m = re.search(r'createCookie\(\s*"credential"\s*,\s*["\'](.*?)["\']', r.text, re.S)
            if m:
                self.session.cookies.set("credential", m[1])

            # set session
            r = self.session.post(f"{self.url}/php/ajaxSet_Session.php",timeout=self.timeout)



    def logout(self):
        self.logger.debug("TG3442DE Logging out ")
        if self.simulate == False:
            r = self.session.post(
                f"{self.url}/php/logout.php",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                },timeout=self.timeout
            )

    def html_getter(self, page, result):
        self.logger.debug("TG3442DE Page :" + page)
        result = ''
        if self.simulate == False:
            r = self.session.get(f"{self.url}{page}",timeout=self.timeout)
            if r != None:
                if int(r.status_code) == 200:
                    result = r.text
        else:
            partname = page[5:page.find('.php')]
            filename = f"simulate/{partname}.txt"
            try:
                with open(filename) as f:
                    result = f.read()
            except FileNotFoundError:
                self.logger.error("FileNotFound:"+filename)

        return result