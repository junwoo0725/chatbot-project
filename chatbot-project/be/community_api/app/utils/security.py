import hashlib
import re

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PW_RE = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^\w\s]).{8,20}$")

def valid_email(email: str) -> bool:
    return bool(email and EMAIL_RE.match(email))

def valid_password(pw: str) -> bool:
    return bool(pw and PW_RE.match(pw))

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()
