import binascii
from bs4 import BeautifulSoup
from Crypto.Cipher import AES
import hashlib
import json
import re
import requests
import sys
import os

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
            # get login page
            r = self.session.get(f"{self.url}",timeout=self.timeout)
            # parse HTML
            h = BeautifulSoup(r.text, "lxml")
            # get session id from javascript in head
            current_session_id = re.search(r".*var currentSessionId = '(.+)';.*", h.head.text)[1]

            # encrypt password
            iv = re.search(r".*var myIv = '(.+)';.*",h.head.text)[1]
            salt = re.search(r".*var mySalt = '(.+)';.*",h.head.text)[1]
            key = hashlib.pbkdf2_hmac(
                'sha256',
                bytes(self.password.encode("ascii")),
                binascii.unhexlify(salt),
                iterations=1000,
                dklen=16
            )

            secret = { "Password": self.password, "Nonce": current_session_id }
            plaintext = bytes(json.dumps(secret).encode("ascii"))
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
            result = json.loads(r.text)

            # success?
            if result['p_status'] != "AdminMatch":
                self.logger.info("login failure", file=sys.stderr)
                return

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

            # set credentials cookie
            # TODO: get credentials from /base_95x.js'
 
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
            partname = page[5:-4]
            filename = f"simulate/{partname}.txt"
            try:
                with open(filename) as f:
                    result = f.read()
            except FileNotFoundError:
                self.logger.error("FileNotFound:"+filename)

        return result