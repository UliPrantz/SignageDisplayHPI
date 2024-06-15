import os
import shutil
import time
import subprocess
import pymupdf
from OpenSSL import crypto
from pyudev import Context, Monitor
import logging

##################################################################
#
# Define these ones as needed
# Be aware that the 'TMP_WORKING_DIR' will be erased regularly!!!
#
##################################################################
TMP_WORKING_DIR = '/home/pi/working'
DEFAULT_MOUNT_ROOT_PATH = '/media/pi'
KEY_PATH = '/home/pi/key/somekey_here.pub'
SLIDESHOW_DISPLAY_NUMBER = ":0"
SLIDESHOW_DELAY_SECONDS = 10
##################################################################

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

PROCESS = None

def verify_signature(pdf_path, key_path):
    try:
        with open(key_path, 'r') as key_file:
            public_key = crypto.load_publickey(crypto.FILETYPE_PEM, key_file.read())

        doc = pymupdf.open(pdf_path)
        signature_field = None
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            fields = page.widgets()
            
            for field in fields:
                logging.info(f"Field: {field}")

        signature = bytes.fromhex(signature_field['value'])
        data_to_verify = doc[0].get_text().encode()

        crypto.verify(public_key, signature, data_to_verify, 'sha256')
        return True
    except Exception as e:
        logging.error(f"Verification failed: {e}")
        return False


def find_first_pdf(mount_path):
    for root, _, files in os.walk(mount_path):
        for file in files:
            if file.lower().endswith('.pdf'):
                return os.path.join(root, file)
    return None


def convert_pdf_to_images(pdf_path):
    if os.path.exists(TMP_WORKING_DIR):
        shutil.rmtree(TMP_WORKING_DIR)
    os.makedirs(TMP_WORKING_DIR)
    
    try:
        doc = pymupdf.open(pdf_path)
        page_count = len(doc)
        
        for page_number in range(page_count):
            page = doc.load_page(page_number)
            pagePixmap = page.get_pixmap()
            output_path = os.path.join(TMP_WORKING_DIR, f"page_{page_number:05}.png")
            pagePixmap.save(output_path)
        logging.info(f"PDF ({pdf_path}) converted successfully to image(s) for displaying")
        
        
    except Exception as e:
        logging.error(f"Error converting PDF: {e}")



def start_pdf_slideshow():
    global PROCESS
    
    env_variables = os.environ.copy()
    env_variables["DISPLAY"] = SLIDESHOW_DISPLAY_NUMBER
    PROCESS = subprocess.Popen(
        ["feh", "--fullscreen", "--auto-zoom", "--slideshow-delay", f"{SLIDESHOW_DELAY_SECONDS}", TMP_WORKING_DIR],
        env=env_variables
    )
    logging.info(f"Slideshow started with PID: {PROCESS.pid}")


def process_new_device(mount_path):
    global PROCESS
    
    if PROCESS:
        PROCESS.terminate()
        PROCESS.wait(timeout=10)
        logging.info(f"Old slideshow stopped - PID: {PROCESS.pid}")
    
    pdf_path = find_first_pdf(mount_path)
    if pdf_path:
        logging.info(f"Found PDF: {pdf_path}")
        convert_pdf_to_images(pdf_path)
        start_pdf_slideshow()
    else:
        logging.info("No PDF found")


def is_disk_device(path):
    try:
        result = subprocess.run(['lsblk', '-no', 'TYPE', path], stdout=subprocess.PIPE, text=True)
        types = result.stdout.strip().split()
        return "disk" in types
    except Exception as e:
        logging.error(f"Error getting block type for path: {e}")
        return False


def get_mount_path(path):
    result = subprocess.run(['lsblk', '-no', 'MOUNTPOINT', path], stdout=subprocess.PIPE, text=True)
    mounting_path = result.stdout.strip()
    return mounting_path


def boot_up_check():
    logging.info("Running start up routine")
    
    # waiting for block devices to be mounted
    time.sleep(15)
    entries = os.listdir(DEFAULT_MOUNT_ROOT_PATH)
    
    for entry in entries:
        directory_path = os.path.join(DEFAULT_MOUNT_ROOT_PATH, entry)
        if os.path.isdir(directory_path):
            process_new_device(directory_path)
            break
    logging.info("Finished start up routine")


def monitor_usb():
    boot_up_check()
    
    context = Context()
    monitor = Monitor.from_netlink(context)
    monitor.filter_by(subsystem='block')
    
    logging.info("Starting running routine")
    for device in iter(monitor.poll, None):
        if device.action == 'add':
            device_path = device.device_node
            
            if is_disk_device(device_path):
                time.sleep(5)
                mount_path = get_mount_path(device_path)
                logging.info(f"New device mounted: {mount_path}")
                process_new_device(mount_path)


if __name__ == "__main__":
    monitor_usb()
