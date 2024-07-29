# USB PDF Monitor Script

This project is a Python script that monitors USB insertions on a Raspberry Pi, searches for the first PDF file on the USB stick, verifies its signature using a public key stored on the Pi, and if valid, displays the PDF in full screen with auto-play rotation.

## Prerequisites

1. Raspberry Pi running Raspbian (Raspberry Pi OS)
2. Internet connection for installing necessary packages (only needed during setup)

## Setup Instructions

Open a terminal and run the following commands to update your system and install necessary packages:

> We will run this script as root since we are doing a lot of system level operations (e. g. writing directly to the frame buffer or mounting USB drives). This could also be achieved by running the script as a non-root user but this would require additional setup steps including adding the user to the `video` group and adding system capabilities to auto mount USB drives while being in headless mode.

### 0. Switch to root user

The whole installation as well as the execution of the script will be done as the root user. To switch to the root user, run the following command:

```bash
sudo su
```

Switch to root user default home directory:

```bash 
cd 
```

### 1. Install System Packages

```bash
apt update -y
apt full-upgrade -y
apt install -y python3 fbi git 
```

### 2. Clone the repository

Now we need to clone the repository to the Raspberry Pi. We can do this by running the following command:

```bash
git clone https://github.com/UliPrantz/SignageDisplayHPI.git
```

After cloning the repository, we need to change into the directory:

```bash
cd SignageDisplayHPI
```

### 3. Install python dependencies

No we simply need to install the python dependencies globally. This can be done by running the following command:

```bash
pip3 install -r requirements.txt --break-system-packages
```

> Short notice here: The `--break-system-packages` flag is used to install the dependencies globally. This is necessary because the script is run as a systemd service and the service does not have access to the user's python environment. </br> 
> **Normally we wouldn't want this but since this is a single purpose system we will be fine!**

### 4. Change the configuration (especially the allowed PDF names)

Now we need to change the configuration. We can do this by going into the `SignageDisplay.py` file and change the appropriate variables at the top of the file

**The allowed files names are the names of the PDF files that are allowed to be displayed.**
```python
ALLOWED_FILE_NAMES = ["Example-File-Name.pdf"] 
```

### 4. Autostart everything

To make everything work automatically from the startup, you need to create a systemd service. We can do this by copying the `SignageDisplay.service` file to the systemd services directory and enabling it.

```bash
cp SignageDisplay.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable SignageDisplay.service
systemctl start SignageDisplay.service
```

### 5. Secure the setup

Set a new password for the `pi` user by running the following command:

```bash
passwd pi
```

### 6. Disable auto login and restart

To make sure the script works correctly, we need to disable the auto login feature of the Raspberry Pi and switch to console boot. This can be done by running the following command:

```bash
raspi-config
```

Here navigate to `System Options` -> `Boot / Auto Login` and now select `Console`. This disabled the Autologin and switched to console boot. We now need to reboot the system to apply the changes. Therefore select `Finish` and confirm the reboot with `Yes`.

## Troubleshooting

### Reading the logs

If you encounter any issues, please open an issue on this repository.
Beforehand please try to troubleshoot some problems yourself by running the following commands:

```bash
journalctl -u SignageDisplay.service -f
```

This command will show you the logs of the service. If you see any errors, please copy them and paste them in the issue.

```bash
systemctl status SignageDisplay.service
```

This command will show you the status of the service itself and whether it's running in the first place or might have already exited.

### Checking priviliges (only if run as non-root user - not recommended)

**To make this work as non-root USB automount capabilities must also be added (not covered here)**

To make sure the script can write to the framebuffer device (`fb0`) directly we need to add the `pi` user which we will be using to run the script (defined in the `SignageDisplay.service` file) to the `video` group. We can do this by executing the following command.

```bash
sudo usermod -aG video pi
```

On some systems the `/dev/fb0` device might not be accessible by the `pi` user since it might not be in the video group. To check whether the user has access to the framebuffer device you can run the following command:

```bash
ls -l /dev/fb0
```

Make sure the `pi` user and the device are both in the `video` group.

```bash
groups pi
```

# Usage Instructions

Here are the steps to actually use the display as a monitor for your PDFs.

> 



