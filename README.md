# upload-automation-client
A desktop automation tool for media upload workflow, built with Python + Selenium + PyQt.

## ✨ Overview
This is a local desktop automation program with GUI.
It reads video files from specified local directory, applies filter rules, respects daily upload quota, and automatically uploads media to the target platform via Chrome.
> The UI is built by PyQt, the browser automation is powered by Selenium.

## 🖼️ Preview
<img width="542" height="482" alt="image" src="https://github.com/user-attachments/assets/ea69418c-75ac-4540-8259-d5ef36dcad53" />


## 📌 Core Features
- Local folder scanning: auto load video files from configured directory
- Keyword filter: remove sensitive words from video title
- Talent ID mapping: assign upload targets by pre-configured talent list
- Daily upload limit: control upload quantity to avoid platform restriction
- Duplicate skip: automatically skip finished/uploaded files
- Runtime log output: view real-time running status inside GUI
- Chrome browser automation: reuse logged-in browser session

## 🧱 Tech Stack
- Python 3.x
- Selenium (Chrome browser automation)
- PyQt5 (Graphical UI)
- File / JSON config driven
- Selenium Manager (Auto match ChromeDriver, no manual driver download)

## 🚀 How to run
1. Install dependencies
```bash
pip install -r requirements.txt
