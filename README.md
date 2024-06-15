# USB PDF Monitor Script

This project is a Python script that monitors USB insertions on a Raspberry Pi, searches for the first PDF file on the USB stick, verifies its signature using a public key stored on the Pi, and if valid, displays the PDF in full screen with auto-play rotation.

## Prerequisites

1. Raspberry Pi running Raspbian (Raspberry Pi OS)
2. Internet connection for installing necessary packages

## Setup Instructions

Open a terminal and run the following commands to update your system and install necessary packages:

### Install System Packages

```bash
sudo apt-get update
sudo apt-get install python3 feh
```

### Install python dependencies

```bash
pip3 install -r requirements.txt
```

## Usage

### Generate 



# Debug

journalctl -u SignageDisplay.service -f