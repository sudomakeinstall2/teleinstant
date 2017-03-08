import hmac
import os

basedir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(basedir, 'secret_key.txt')) as f:
    key = f.read().strip()


def hash_str(s):
    return hmac.new(key, s).hexdigest()


def make_secure(s):
    return "%s|%s"%(s, hash_str(s))


def check_secure_val(h):
    val = h.split('|')[0]
    if h == make_secure(val):
        return val
    return None
