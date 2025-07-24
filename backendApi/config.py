import os
from dotenv import load_dotenv
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "test")
db_password_file = os.getenv("DB_PASSWORD_FILE", "")
if db_password_file != "":
    f = open(db_password_file, "r")
    DB_PASSWORD = f.read().replace("\n", "")
else:
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_AUTH = os.getenv("DB_AUTH", "mysql_native_password")
