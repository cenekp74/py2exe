from app import app
from flask import flash, render_template, redirect, url_for, jsonify, abort, request, send_file, send_from_directory
from .utils import allowed_file, random_hex_token, start_conversion, delete_conversion
from werkzeug.utils import secure_filename
import os

@app.route('/favicon.ico')
def send_favicon():
    return send_from_directory('static/img', 'favicon.ico')

@app.route('/')
@app.route('/index')
def index():
    return redirect(url_for('convert'))

@app.route('/convert', methods=["POST", "GET"])
def convert():
    if request.method == "GET":
        return render_template("convert.html")
    file = request.files.get('filepond')
    if not allowed_file(file.filename): abort(400)
    filename = secure_filename(file.filename)
    token = random_hex_token()
    
    os.mkdir(f"instance/conversions/{token}")
    file.save(f"instance/conversions/{token}/{filename}")

    start_conversion.delay(token)
    delete_conversion.apply_async(args=[token], countdown=2*60*60)

    return token

@app.route('/convert/<conversion_id>/download')
def download_conversion(conversion_id):
    if not os.path.exists(f"instance/conversions/{conversion_id}/output.zip"):
        abort(404)
    return send_file(f"../instance/conversions/{conversion_id}/output.zip")

@app.route('/convert/<conversion_id>')
def view_conversion(conversion_id):
    if not os.path.exists(f"instance/conversions/{conversion_id}"):
        return render_template("conversion_not_found.html")
    original_files = [fn for fn in os.listdir(f"instance/conversions/{conversion_id}") if fn.endswith(".py") or fn.endswith(".zip")]
    if not os.path.exists(f"instance/conversions/{conversion_id}/info.txt"):
        return render_template("view_conversion.html", status="Your conversion is in queue", download=None, filenames=original_files)
    with open(f"instance/conversions/{conversion_id}/info.txt", "r") as info_file:
        status = list(info_file.readlines())[-1]
        download = None
        if "download" in status:
            download = url_for('download_conversion', conversion_id=conversion_id)
    return render_template("view_conversion.html", status=status, download=download, filenames=original_files)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/how-to')
def how_to():
    return render_template('how_to.html')