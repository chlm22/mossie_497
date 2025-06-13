"""Mossie development configuration."""

import pathlib

# Root of this application, useful if it doesn't occupy an entire domain
APPLICATION_ROOT = "/"

# Secret key for encrypting cookies
SECRET_KEY = (
    b'+\x08\xc0\xa1\xffo3\xf9\xd9\xaf[W{'
    b'\x88\xf1\xea\xe6\xcb\xa3?\xce\xed\x9a\x17'
)
SESSION_COOKIE_NAME = "login"

# File Root
MOSSIE_ROOT = pathlib.Path(__file__).resolve().parent.parent

# Database file is var/mossie.sqlite3
DATABASE_FILENAME = MOSSIE_ROOT / "var" / "mossie.sqlite3"
