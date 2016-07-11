#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base64 import b64encode, b64decode
from getpass import getpass
from sys import exit
from re import sub
import xml.etree.ElementTree as ET
import argparse
import os.path

try:
    from Crypto.Cipher import AES
    from Crypto.Hash import SHA256
    from Crypto import Random
except ImportError as ie:
    print "Error loading Crypto module. Is it installed?"
    exit(1)


class passwd:

    def __init__(self):
        hshPass = SHA256.new()
        fStep = getpass('Type password: ')
        sStep = getpass('Retype password: ')
        if fStep == sStep:
            hshPass.update(fStep)
        else:
            raise ValueError("Passwords don't match")
        self.key = hshPass.digest()
        self.bs = 32
        return

    def crypt(self, text):
        text = self._pad(text)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return b64encode(iv + cipher.encrypt(text))

    def decrypt(self, data):
        data = b64decode(data)
        iv = data[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        text = cipher.decrypt(data[AES.block_size:])
        return self._unpad(text).decode('utf-8')

    def _pad(self, s):
        regardChars = self.bs - len(s) % self.bs
        return s + regardChars * chr(regardChars)

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]


def main():
    hlpDsc = "Encrypt/Decrypt password field into KeyPass XML database file"
    optParser = argparse.ArgumentParser(description=hlpDsc)
    optParser.add_argument("-e", "--encrypt", help="encrypt mode",
                           required=False, action='store_true',
                           dest="encrypt", default=True)
    optParser.add_argument("-d", "--decrypt", help="decrypt mode",
                           required=False, action='store_false',
                           dest="encrypt")
    optParser.add_argument("-o", "--output", help="output file",
                           required=False, metavar='FILE',
                           dest="output", type=str, default=None)
    optParser.add_argument("filename", help="XML-file",
                           metavar="XML-file", nargs=1)
    args = optParser.parse_args()
    if len(args.filename) == 0:
        optParser.print_help()
        exit(2)
    output = args.filename[0] if args.output is None else args.output
    if os.path.isfile(args.filename[0]):
        try:
            aes = passwd()
        except ValueError as ve:
            print(ve)
            exit(3)
        try:
            tree = ET.parse(args.filename[0])
        except ET.ParseError:
            print('Error parsing XML file')
            exit(4)
        root = tree.getroot()
        for password in root.iter('password'):
            if password.text is None:
                password.text = ''
            else:
                try:
                    password.text = aes.crypt(password.text) if args.encrypt \
                        else aes.decrypt(password.text)
                except ValueError:
                        print('Error decrypting data. Is the file encrypted?')
                        exit(5)
        with open(output, 'w') as outFile:
            outFile.write('<!DOCTYPE KEEPASSX_DATABASE>\n')
            outFile.write(sub('<br>', '<br/>', ET.tostring(root,
                                                           encoding='utf-8',
                                                           method='html')))
        # print(ET.tostring(root))
    else:
        print("[%s]: No such file" % args.filename[0])
    return

if __name__ == "__main__":
    main()
