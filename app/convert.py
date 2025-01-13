import os
import os.path
import shutil
import subprocess
from glob import glob

def write_to_info_file(conversion_id, message):
    with open(f"instance/conversions/{conversion_id}/info.txt", "w") as info_file:
        info_file.write(message)
        info_file.flush()

def preprocess_conversion(conversion_id) -> str:
    """
    a function for preprocessing conversions right after upload\n
    expects a single .py or .zip file inside the conversion folder

    if .zip file is present, it unpacks it and determines the root file\n
    returns the root file that pyinstaller should be started on
    """
    conversion_directory = os.path.join("instance", "conversions", conversion_id)
    files = os.listdir(conversion_directory)
    if len(files) != 1:
        raise Exception(f"Expected only one file in {conversion_directory}, found {len(files)}")
    
    write_to_info_file(conversion_id, "Analyzing file(s)\n")
    filename = files[0]
    if filename.endswith(".py"):
        return filename
    if not filename.endswith(".zip"):
        raise Exception(f"Expected .py or .zip file, got {filename}")
        
    write_to_info_file(conversion_id, "Unpacking zip archive\n")
    shutil.unpack_archive(os.path.join(conversion_directory, filename), conversion_directory, "zip")
    os.remove(os.path.join(conversion_directory, filename)) # removed the zip file - no longer needed
    dir_items = [f for f in os.listdir(conversion_directory) if f != "info.txt"]
    if len(dir_items) == 1 and os.path.isdir(os.path.join(conversion_directory, dir_items[0])): # if there was only one item inside the zip and it is a folder
        try:
            # move everything from the subfolder to the root folder
            for file in os.listdir(os.path.join(conversion_directory, dir_items[0])):
                shutil.move(os.path.join(conversion_directory, dir_items[0], file), conversion_directory)
        except Exception as _e:
            pass
    
    python_files = [f for f in os.listdir(conversion_directory) if f.endswith(".py")]
    if len(python_files) == 0:
        write_to_info_file(conversion_id, f"Conversion failed: No python files found in your zip. Please rename the root file of your project to main.py or run.py and make sure it is located in the root of the zip archive (not in any folder)")
        return False
    if "run.py" in python_files:
        return "run.py"
    if "main.py" in python_files:
        return "main.py"
    if "app.py" in python_files:
        return "app.py"
    if len(python_files) == 1:
        return python_files[0]
    write_to_info_file(conversion_id, f"Conversion failed: Please rename the root file of your project to main.py or run.py and make sure it is located in the root of the zip archive (not in any folder)")
    return False

def create_venv(directory):
    initial_dir = os.getcwd()
    os.chdir(f"instance/conversions/{directory}")
    if os.name == 'nt': # if running on windows
        _ = os.system(f"virtualenv venv")
        _ = os.system(f"venv\Scripts\python.exe -m pip install pyinstaller && venv\Scripts\python.exe -m pip install -r requirements.txt")
    else:
        os.environ["PATH"] = "/usr/bin"
        os.environ["WINEPREFIX"] = initial_dir+"/wine"
        os.environ["WINEPATH"] = initial_dir
        _ = os.system(f"wine {initial_dir}/wine/drive_c/python3.11/python.exe -m virtualenv venv")
        _ = os.system(f"wine venv/Scripts/python.exe -m pip install pyinstaller")
        with open("requirements.txt", "r") as reqs_file: # this is to avoid errors if some packages are not found
            for line in reqs_file.readlines():
                line = line.strip().replace("skimage", "scikit-image").replace("cv2", "opencv-python").replace("==0.0", "")
                try:
                    subprocess.run(["wine", "venv/Scripts/python.exe", "-m", "pip", "install", line], check=True)
                except subprocess.CalledProcessError as e:
                    print(f"Pip install {line} failed: {e}")
    os.chdir(initial_dir)

def run_pyinstaller(directory, filename, venv: bool=False, icon=None):
    """
    run pyinstaller - if venv=True, expect virtual environment in "venv/"\n
    arg icon: filename of icon relative to conversion folder
    """
    initial_dir = os.getcwd()
    os.chdir(f"instance/conversions/{directory}")
    if not icon:
        icon = os.path.join(initial_dir, "app", "static", "img", "favicon.ico")
    if os.name == 'nt': # if running on windows
        if venv:
            _ = os.system(f"venv\Scripts\python.exe -m pyinstaller {filename} --onedir --icon={icon}")
        else:
            _ = os.system(f"pyinstaller {filename} --onedir --icon={icon}")
    else:
        os.environ["PATH"] = "/usr/bin"
        os.environ["WINEPREFIX"] = initial_dir+"/wine"
        os.environ["WINEPATH"] = initial_dir
        if venv:
            _ = os.system(f"wine venv/Scripts/python.exe -m PyInstaller {filename} --onedir --icon={icon}")
        else:
            _ = os.system(f"wine {initial_dir}/wine/drive_c/python3.11/python.exe -m PyInstaller {filename} --onedir --icon={icon}")
    os.chdir(initial_dir)

def convert(conversion_id):
    conversion_directory = os.path.join("instance", "conversions", conversion_id)
    root_file = preprocess_conversion(conversion_id)

    venv = False
    if "requirements.txt" in os.listdir(conversion_directory):
        write_to_info_file(conversion_id, "Creating virtual environment")
        create_venv(conversion_id)
        venv = True

    icon = None
    if "icon.png" in os.listdir(conversion_directory):
        icon = "icon.png"
    if "icon.ico" in os.listdir(conversion_directory):
        icon = "icon.ico"

    write_to_info_file(conversion_id, f"Converting - {root_file}\n")
    run_pyinstaller(conversion_id, root_file, venv=venv, icon=icon)

    if glob(os.path.join(conversion_directory, "dist", "*", "*.exe")):
        write_to_info_file(conversion_id, "Finshed conversion successfully\n")
        write_to_info_file(conversion_id, "Starting zip archive creation\n")
        shutil.make_archive(os.path.join(conversion_directory, "output"), "zip", os.path.join(conversion_directory, "dist"))
        write_to_info_file(conversion_id, "Created zip archive - ready for download")
    else:
        write_to_info_file(conversion_id, "An error occured during conversion - please check that your python files run properly on python 3.11.9 and try again")
        return False
    return True