# IntelliOS / IntelliShell

**IntelliOS** is an AI-powered interactive terminal and operating system shell built with **C++17**, **Python**, and **Google Gemini AI**. It translates natural-language plain English instructions into precise operating system commands, verifies safety ring restrictions, and executes them with full process synchronization.

It includes both a **native C++ terminal shell** and a **modern Glassmorphic Web UI**.

---

## Key Features

* **Natural Language Command Translation**: Type what you want to do in plain English (e.g., *"show all files in current folder"*, *"check free disk space"*, *"show my ip address"*), and the AI translates it to native shell commands.
* **Cross-Platform**: Full native support for **Windows (PowerShell/CMD)** and **Linux (/bin/sh)**.
* **Core Operating System Concepts Demonstrated**:
  * **Inter-Process Communication (IPC)**: Streams JSON across anonymous OS pipes between C++ and Python.
  * **Process Lifecycle**: Spawns and supervises child processes via `CreateProcessA` (Windows) / `fork()` & `exec()` (Linux).
  * **Standard I/O Redirection**: Remaps `STDIN` and `STDOUT` handles.
  * **Process Synchronization**: Parent process waits for child termination via `WaitForSingleObject` / `waitpid()` to avoid zombie processes.
  * **System Calls**: Direct filesystem kernel calls (`_chdir()`, `_getcwd()`, etc.).
  * **Protection Ring & Safety Interception**: Real-time regex interception for dangerous operations (e.g. fork bombs, disk wipe attempts).
* **Modern Web Console UI**:
  * Dark-mode glassmorphic interface with interactive terminal chrome.
  * Quick suggestion chips for common admin and OS tasks.
  * Live **OS Concepts Tracker** that highlights active system components in real time.
  * Command inspection & interactive edit modal before execution.
  * Instant offline rule-based fallback engine.

---

## Quick Start

### 1. Configure API Key (Optional)
Copy `.env.example` to `.env` and add your Gemini API key:
```bash
cp .env.example .env
```
*(Note: If no API key is provided or if network times out, the built-in offline engine will seamlessly handle common commands!)*

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

---

## Running the Application

### Option A: Modern Web UI (Recommended)
Double-click or run:
```cmd
launch_ui.bat
```
Or start manually via Python:
```bash
python web_server.py
```
Then navigate to **http://localhost:5000** in your browser.

### Option B: Native C++ Console Shell
Compile and run the native shell:

**Windows (MinGW / GCC):**
```cmd
g++ -std=c++17 -I. ai_shell.cpp -o ai_shell.exe
ai_shell.exe ai_adapter.py
```
*(Or simply double-click `run.bat`)*

**Linux / macOS:**
```bash
make
./ai_shell ./ai_adapter.py
```

---

## Project Structure

```text
├── ai_shell.cpp            # Core C++ interactive shell engine (Win32 & POSIX)
├── ai_adapter.py           # Python AI adapter (Gemini API + local fallback engine)
├── web_server.py           # Lightweight backend & REST API server
├── launch_ui.bat           # 1-click launcher for Web UI
├── run.bat                 # 1-click launcher for C++ CLI
├── ui/
│   ├── index.html          # Futuristic Glassmorphic Terminal Web UI
│   ├── style.css           # Modern dark mode design tokens & animations
│   └── app.js              # Client-side controller & real-time OS tracker
├── nlohmann/               # C++ header-only JSON library
├── .env.example            # Environment template
└── requirements.txt        # Python package dependencies
```

---

## License
MIT License.
