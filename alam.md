

  

#@markdown
#@markdown jlesage/firefox, firefox-esr
#@markdown The GUI of the application is accessed through a modern web browser (no installation or configuration needed on the client side) via HTTP
#@markdown Firefox download directory = `CONFIG_DIRECTORY`/downloads

import os, tarfile
import urllib.request
from IPython.display import clear_output
import subprocess
import socket
import time

#####################################
USE_FREE_TOKEN = True  # @param {type:"boolean"}

TOKEN = ""  # @param {type:"string"}
REGION = "AP" #@param ["US", "EU", "AP", "AU", "SA", "JP", "IN"]
PORT_FORWARD = "argotunnel" #@param ["ngrok", "localhost", "argotunnel"]
TYPE = "firefox" #@param ["firefox", "firefox-esr"]
CONFIG_DIRECTORY = "/content/tools/firefox"  # @param {type:"string"}
HOME = os.path.expanduser("~")

if not os.path.exists(f"{HOME}/.ipython/ocr.py"):
    hCode = "https://raw.githubusercontent.com/biplobsd/" \
                "OneClickRun/master/res/ocr.py"
    urllib.request.urlretrieve(hCode, f"{HOME}/.ipython/ocr.py")


from ocr import (
    loadingAn,
    PortForward_wrapper,
    findProcess,
    read_subprocess_output,
    textAn
)

def is_port_open(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            s.connect(("localhost", port))
        return True
    except (socket.timeout, ConnectionRefusedError):
        return False

def in_output(command, output):
    try:
        result = subprocess.run(command.split(), capture_output=True, text=True, check=True)
        return output in result.stdout
    except subprocess.CalledProcessError:
        return False

def check_log_until_line_appears(command, line_to_check):
    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    while True:
        line = process.stdout.readline().decode('utf-8')
        if line_to_check in line:
            return True
        elif line == '':
            return False
        else:
            time.sleep(0.1)

def popen(cmd, description=None):
    try:
        if description:
          clear_output()
          loadingAn()
          textAn(description, 'twg')
        subprocess.Popen(cmd.split()).wait()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}")
        print(f"Error message: {e}")
        raise

loadingAn()
os.makedirs(CONFIG_DIRECTORY, exist_ok=True)

if not os.path.exists("/usr/local/bin/udocker"):
    popen('pip install udocker', "Installing udocker ...")
    popen('udocker --allow-root install', 'Setuping udocker ...')

if not in_output('udocker --allow-root images', f'jlesage/{TYPE}:latest'):
    popen(f'udocker --allow-root pull jlesage/{TYPE}', f"Pulling jlesage/{TYPE} image ...")

if not in_output('udocker --allow-root ps', TYPE):
    popen(f'udocker --allow-root create --name={TYPE} jlesage/{TYPE}', f"Creating {TYPE} container ...")

command = f'udocker --allow-root run -v {CONFIG_DIRECTORY}:/config -p 5800:5800 {TYPE}'.split()
line_to_check = '[supervisor  ] all services started.'

done = True
if (not findProcess(TYPE, '/config/profile')) or (not is_port_open(5800)):
    popen('fuser -k -n tcp 5900')
    clear_output()
    loadingAn()
    textAn("Waiting for all services started ...", 'twg')
    done = check_log_until_line_appears(command, line_to_check)

# START_SERVER
# Ngrok region 'us','eu','ap','au','sa','jp','in'
clear_output()
if done:
    server = PortForward_wrapper(
        PORT_FORWARD, TOKEN, USE_FREE_TOKEN, [['firefox', '5800', 'http']],
        REGION.lower(),
        [f"{HOME}/.ngrok2/firefox.yml", 58009]
    ).start('firefox', displayB=True)
else:
    print("Error: Please delete the runtime and run again.")