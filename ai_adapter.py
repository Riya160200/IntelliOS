#!/usr/bin/env python3
# Simple adapter: read JSON payload from stdin { "prompt": "...", "history": [...] }
# Call Gemini (gemini-3.8-flash) and print JSON {command, explanation, confirm}

import os, sys, json, platform, re, warnings

# Suppress noisy library warnings
warnings.filterwarnings("ignore")

from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
is_valid_key = bool(API_KEY and API_KEY != "your_api_key_here")

# Read stdin
data = sys.stdin.read()
try:
    payload = json.loads(data)
except Exception:
    payload = {"prompt": data}

prompt = payload.get("prompt", "").strip()
history = payload.get("history", [])

is_windows = (platform.system() == "Windows")
os_name = "Windows (PowerShell/CMD)" if is_windows else "Linux (/bin/sh)"

def fallback_generator(user_prompt):
    """Robust rule-based fallback when Gemini API key is missing or timing out."""
    p = user_prompt.lower()

    # 1. Destructive actions (delete, remove, rm, erase, wipe, format) -> Must be evaluated FIRST!
    if any(k in p for k in ["delete", "remove", "rm", "erase", "format", "wipe"]):
        m = re.search(r"(?:delete|remove|rm|erase)\s+(?:file|folder)?\s*['\"]?([a-zA-Z0-9_\-\.]+)?['\"]?", p)
        target = m.group(1) if m and m.group(1) and m.group(1) not in ["a", "the", "file", "folder"] else "target_file.txt"
        cmd = f"Remove-Item '{target}'" if is_windows else f"rm '{target}'"
        return {
            "command": cmd,
            "explanation": f"Deletes '{target}' from the current directory on {os_name}.",
            "confirm": True
        }

    # 2. Directory & File Listing
    elif any(k in p for k in ["file", "folder", "dir", "ls", "list", "content", "show all", "show files"]):
        if "hidden" in p or "-a" in p or "-force" in p:
            cmd = "Get-ChildItem -Force" if is_windows else "ls -la"
            return {"command": cmd, "explanation": f"Lists all files and directories including hidden items on {os_name}.", "confirm": False}
        else:
            cmd = "Get-ChildItem" if is_windows else "ls"
            return {"command": cmd, "explanation": f"Lists all files and folders in the current directory on {os_name}.", "confirm": False}

    # 3. Current Directory / Location
    elif any(k in p for k in ["where", "pwd", "current path", "current dir", "location"]):
        cmd = "Get-Location" if is_windows else "pwd"
        return {"command": cmd, "explanation": f"Displays the current working directory path on {os_name}.", "confirm": False}

    # 4. IP and Network
    elif any(k in p for k in ["ip", "network", "ifconfig", "ipconfig", "adapter", "wifi", "ethernet"]):
        cmd = "ipconfig" if is_windows else "ip a"
        return {"command": cmd, "explanation": f"Displays network adapter and IP configuration on {os_name}.", "confirm": False}

    # 5. Disk space / Storage
    elif any(k in p for k in ["disk", "drive", "space", "storage", "free space", "capacity"]):
        cmd = "Get-PSDrive -PSProvider FileSystem" if is_windows else "df -h"
        return {"command": cmd, "explanation": f"Displays available free storage space across drives on {os_name}.", "confirm": False}

    # 6. Process / Tasks
    elif any(k in p for k in ["process", "task", "ps", "running", "cpu", "ram", "memory"]):
        cmd = "Get-Process" if is_windows else "ps aux"
        return {"command": cmd, "explanation": f"Lists currently running processes and system resource usage on {os_name}.", "confirm": False}

    # 7. Create folder
    elif any(k in p for k in ["create folder", "make folder", "mkdir", "new folder", "create directory"]):
        m = re.search(r"(?:folder|directory|named|called)\s+['\"]?([a-zA-Z0-9_\-]+)['\"]?", p)
        fname = m.group(1) if m else "new_folder"
        cmd = f"New-Item -ItemType Directory -Name '{fname}'" if is_windows else f"mkdir '{fname}'"
        return {"command": cmd, "explanation": f"Creates a new directory named '{fname}' on {os_name}.", "confirm": False}

    # 8. Date and Time
    elif any(k in p for k in ["date", "time", "clock", "today"]):
        cmd = "Get-Date" if is_windows else "date"
        return {"command": cmd, "explanation": f"Displays current date and time on {os_name}.", "confirm": False}

    # 9. Clear screen
    elif any(k in p for k in ["clear", "cls", "clean screen"]):
        cmd = "Clear-Host" if is_windows else "clear"
        return {"command": cmd, "explanation": "Clears the terminal screen.", "confirm": False}

    # 10. Ping / Connection test
    elif "ping" in p or "test connection" in p:
        cmd = "Test-Connection 8.8.8.8 -Count 2" if is_windows else "ping -c 2 8.8.8.8"
        return {"command": cmd, "explanation": f"Tests network reachability to Google DNS on {os_name}.", "confirm": False}

    # 11. Echo / Print
    elif p.startswith("echo ") or p.startswith("print "):
        text = user_prompt.split(" ", 1)[1] if " " in user_prompt else ""
        return {"command": f"Write-Output '{text}'" if is_windows else f"echo '{text}'", "explanation": "Echoes text.", "confirm": False}

    # 12. Default safe fallback
    else:
        return {
            "command": "Get-ChildItem" if is_windows else "ls",
            "explanation": f"Lists directory contents on {os_name}.",
            "confirm": False
        }

if not is_valid_key:
    result = fallback_generator(prompt)
    print(json.dumps(result))
    sys.exit(0)

try:
    import google.generativeai as genai
    genai.configure(api_key=API_KEY)

    instruction = f"""
You are an intelligent shell command generator for {os_name}.

Given the user's natural language request, produce only a JSON object with fields:
{{ "command":"...", "explanation":"short explanation", "confirm": true|false }}

User request: {prompt}

History (most recent first):
{json.dumps(history[-5:], indent=2)}

Rules:
- produce a single-line shell command suitable for execution on {os_name}
- if the command may be destructive (delete, format, terminate important process, change permissions), set confirm=true
- output only valid JSON, nothing else.
"""

    model = genai.GenerativeModel("gemini-3.8-flash")
    resp = model.generate_content(instruction, request_options={"timeout": 4})
    text = resp.text

    m = re.search(r"(\{[\s\S]*\})", text)
    if m:
        out = m.group(1)
    else:
        out = text.strip()

    try:
        parsed = json.loads(out)
    except Exception:
        first = text.strip().splitlines()[0]
        parsed = {"command": first, "explanation": "Autogenerated command.", "confirm": False}

    print(json.dumps(parsed))
except Exception as e:
    err_str = str(e)
    fb = fallback_generator(prompt)
    if "504" in err_str or "deadline" in err_str.lower():
        fb["explanation"] = fb["explanation"] + " (Gemini server timed out; used fast local translation)."
    elif "429" in err_str or "quota" in err_str.lower():
        fb["explanation"] = fb["explanation"] + " (Gemini rate-limited; used fast local translation)."
    print(json.dumps(fb))
