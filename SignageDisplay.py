import os, signal
import shutil
import subprocess
import pymupdf
from pyudev import Context, Monitor
import logging

##################################################################
#
# Define these ones as needed
# Be aware that the 'TMP_WORKING_DIR' will be erased regularly!!!
#
##################################################################
TMP_MOUNT_PATH = "/media/root/SignageDisplayMountPoint"
TMP_WORKING_DIR = "/root/SignageDisplay/tmp_working_directory"
ALLOWED_FILE_NAMES = ["E-School-TV.pdf"] # PDFs must have one of these file names to be displayed
SLIDESHOW_DELAY_SECONDS = 10
SLIDESHOW_BLENDING_SECONDS = 1
SCALE_FACTOR = 6 # is used when transforming the PDF to images and should be sufficient for 4k
##################################################################

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def find_first_pdf():
    for root, _, files in os.walk(TMP_MOUNT_PATH):
        for file in files:
            
            # filter for PDF files that are not hidden or otherwise special files
            if file.lower().endswith(".pdf") and not file.lower().startswith(('.', '$', '~')):
                return os.path.join(root, file)
    return None


def convert_pdf_to_images(pdf_path):
    if os.path.exists(TMP_WORKING_DIR):
        shutil.rmtree(TMP_WORKING_DIR)
    os.makedirs(TMP_WORKING_DIR)
    
    try:
        doc = pymupdf.open(pdf_path)
        page_count = len(doc)
        
        scale_matrix = pymupdf.Matrix(SCALE_FACTOR, SCALE_FACTOR)
        for page_number in range(page_count):
            page = doc.load_page(page_number)
            page_pixmap = page.get_pixmap(matrix=scale_matrix)
            output_path = os.path.join(TMP_WORKING_DIR, f"page_{page_number:05}.png")
            page_pixmap.save(output_path)
        logging.info(f"PDF ()'{pdf_path}') converted successfully to {page_count} image(s) for displaying")
        
    except Exception as e:
        logging.error(f"Error converting PDF: {e}")


def start_pdf_slideshow():    
    files = os.listdir(TMP_WORKING_DIR)
    files = [f"{TMP_WORKING_DIR}/{file_name}" for file_name in files]
    subprocess.Popen(
        ["fbi", "-T", "1", "-a", "--noverbose", "--blend", f"{SLIDESHOW_BLENDING_SECONDS * 1000}", "-t", f"{SLIDESHOW_DELAY_SECONDS}", *files],
    )
    logging.info(f"Slideshow started")


def kill_all_previous_slideshows():
    try: 
        result = subprocess.run(["ps", "-C", "fbi", "-o", "pid="], capture_output=True, text=True)
        pids = [int(pid) for pid in result.stdout.split()]
        
        for pid in pids:
            os.kill(pid, signal.SIGTERM)
            
    except Exception as e:
        logging.info(f"Encountered the following error when tyring to kill all previous slideshows: {e}")

def process_new_device():
    kill_all_previous_slideshows()
    
    pdf_path = find_first_pdf()
    if pdf_path:
        
        pdf_file_name = os.path.basename(pdf_path)
        if pdf_file_name not in ALLOWED_FILE_NAMES:
            logging.info(f"Found PDF file: '{pdf_file_name}' is not matching any allowed pdf file names. It will not be displayed!")
            return
        
        logging.info(f"Found PDF: '{pdf_path}'")
        convert_pdf_to_images(pdf_path)
        start_pdf_slideshow()
    else:
        logging.info("No PDF found")


def is_disk_device(path):
    try:
        result = subprocess.run(["lsblk", "-no", "TYPE", path], stdout=subprocess.PIPE, text=True)
        types = result.stdout.strip().split()
        return "disk" in types
    except Exception as e:
        logging.error(f"Error getting block type for path: {e}")
        return False


def is_disk_part(path):
    try:
        result = subprocess.run(["lsblk", "-no", "TYPE", path], stdout=subprocess.PIPE, text=True)
        types = result.stdout.strip().split()
        return "part" in types and "disk" not in types
    except Exception as e:
        logging.error(f"Error getting block type for path: {e}")
        return False


def mount_device(device_path):
    """
    Mount the device to `/media/pi/...` and return the right path

    Args:
        device_path (string): path to the device that should be mounted
    """
    if not os.path.exists(TMP_MOUNT_PATH):
        os.makedirs(TMP_MOUNT_PATH)
        logging.info(f"Created mount path: '{TMP_MOUNT_PATH}'")

    mount_output = subprocess.run(["mount"], capture_output=True, text=True).stdout
    if TMP_MOUNT_PATH in mount_output:
        subprocess.run(["umount", TMP_MOUNT_PATH], check=True)
        logging.info(f"Unmounted existing device at: '{TMP_MOUNT_PATH}'")

    subprocess.run(["mount", device_path, TMP_MOUNT_PATH], check=True)
    logging.info(f"New device mounted '{device_path}' at '{TMP_MOUNT_PATH}'")


def boot_up_check():    
    if not os.path.exists(TMP_WORKING_DIR):
            return
    start_pdf_slideshow()


def monitor_usb():
    logging.info("Running start up routine")
    boot_up_check()
    logging.info("Finished start up routine")
    
    context = Context()
    monitor = Monitor.from_netlink(context)
    monitor.filter_by(subsystem="block")
    
    logging.info("Starting running routine")
    for device in iter(monitor.poll, None):
        if device.action == "add":
            device_path = device.device_node
            
            if is_disk_part(device_path):
                mount_device(device_path)
                process_new_device()


if __name__ == "__main__":
    monitor_usb()
