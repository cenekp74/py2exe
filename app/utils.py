from . import app
import random
from celery import shared_task
from .convert import convert
import shutil

def allowed_file(filename, allowed_extensions=app.config["ALLOWED_EXTENSIONS"]):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def random_hex_token(length=16):
    return ''.join(random.choice('0123456789abcdef') for _ in range(length))

@shared_task
def start_conversion(conversion_id):
    convert(conversion_id)
    return True

@shared_task
def delete_conversion(conversion_id):
    shutil.rmtree(f"instance/conversions/{conversion_id}")
    return True