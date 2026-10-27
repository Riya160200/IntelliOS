#!/usr/bin/env python3
"""
IntelliShell Web Server
Lightweight, zero-dependency HTTP server with REST API endpoints for:
1. Serving static UI files (HTML, CSS, JS, PDF)
2. /api/suggest: Natural Language -> Shell Command (Gemini API + Rule Engine)
3. /api/execute: Executes commands on Windows/PowerShell and returns output
"""

import http.server
import socketserver
import os
import sys
import json
import subprocess
import platform
import re
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from dotenv import load_dotenv

# Load environment variables
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

PORT = 5000
UI_DIR = os.path.join(BASE_DIR, "ui")
API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
is_valid_key = bool(API_KEY and API_KEY != "your_api_key_here")

# Initialize Gemini if available
gemini_model = None
executor = ThreadPoolExecutor(max_workers=2)
if is_valid_key:
    try:
        import google.generativeai as genai
        genai.configure(api_key=API_KEY)
        for m_name in ["gemini-3.8-flash", "gemini-2.5-flash", "gemini-1.5-flash"]:
            try:
                gemini_model = genai.GenerativeModel(m_name)
                break
            except Exception:
                continue
    except Exception as e:
        print(f"[WARN] Gemini initialization failed: {e}")

def call_gemini_sync(sys_prompt):
    res = gemini_model.generate_content(
        sys_prompt,
        generation_config={"temperature": 0.1, "max_output_tokens": 200}
    )
    return res.text

def detect_os_concept(cmd_str, prompt_str):
    """Categorizes the command into an operating system concept for live visualizer."""
    c = (cmd_str + " " + prompt_str).lower()
    if any(k in c for k in ["delete", "remove", "rm", "erase", "format", "wipe", "danger", "drop"]):
        return "card-security"
    elif any(k in c for k in ["process", "task", "ps", "get-process", "tasklist", "kill"]):
        return "card-proc"
    elif any(k in c for k in ["pipe", "|", "json", "stream", "grep", "select-string"]):
        return "card-ipc"
    elif any(k in c for k in ["location", "pwd", "get-location", "cd", "chdir", "mkdir", "new-item"]):
        return "card-syscalls"
    elif any(k in c for k in [">", "<", "2>&1", "out-file", "write-output"]):
        return "card-redirection"
    elif any(k in c for k in ["wait", "sleep", "start-sleep", "test-connection", "ping"]):
        return "card-sync"
    return "card-proc"

def rule_based_suggest(user_prompt, target_os="windows"):
    """Rule-based shell command suggestion matching ai_adapter.py."""
    p = user_prompt.lower()
    is_win = (target_os == "windows")
    os_name = "Windows (PowerShell)" if is_win else "Linux (/bin/sh)"

    # 1. Destructive actions
    if any(k in p for k in ["delete", "remove", "rm", "erase", "format", "wipe"]):
        m = re.search(r"(?:delete|remove|rm|erase)\s+(?:file|folder)?\s*['\"]?([a-zA-Z0-9_\-\.]+)?['\"]?", p)
        target = m.group(1) if m and m.group(1) and m.group(1) not in ["a", "the", "file", "folder"] else "target_file.txt"
        cmd = f"Remove-Item '{target}'" if is_win else f"rm '{target}'"
        return {
            "command": cmd,
            "explanation": f"Deletes '{target}' from current directory on {os_name}.",
            "confirm": True,
            "os_concept": "card-security",
            "source": "AI Kernel Safety Engine"
        }

    # 2. Directory Listing
    elif any(k in p for k in ["file", "folder", "dir", "ls", "list", "content", "show all", "show files"]):
        if "hidden" in p or "-a" in p or "-force" in p:
            cmd = "Get-ChildItem -Force" if is_win else "ls -la"
            return {"command": cmd, "explanation": f"Lists all files and directories including hidden items on {os_name}.", "confirm": False, "os_concept": "card-syscalls", "source": "AI Kernel Fast Engine"}
        else:
            cmd = "Get-ChildItem" if is_win else "ls"
            return {"command": cmd, "explanation": f"Lists all files and folders in the current directory on {os_name}.", "confirm": False, "os_concept": "card-syscalls", "source": "AI Kernel Fast Engine"}

    # 3. Location / Current Dir
    elif any(k in p for k in ["where", "pwd", "current path", "current dir", "location"]):
        cmd = "Get-Location" if is_win else "pwd"
        return {"command": cmd, "explanation": f"Displays the current working directory path on {os_name}.", "confirm": False, "os_concept": "card-syscalls", "source": "AI Kernel Fast Engine"}

    # 4. IP / Network
    elif any(k in p for k in ["ip", "network", "ifconfig", "ipconfig", "adapter", "wifi", "ethernet"]):
        cmd = "ipconfig" if is_win else "ip a"
        return {"command": cmd, "explanation": f"Displays network adapter and IP configuration on {os_name}.", "confirm": False, "os_concept": "card-proc", "source": "AI Kernel Fast Engine"}

    # 5. Disk Space
    elif any(k in p for k in ["disk", "drive", "space", "storage", "free space", "capacity"]):
        cmd = "Get-PSDrive -PSProvider FileSystem" if is_win else "df -h"
        return {"command": cmd, "explanation": f"Displays available free storage space across drives on {os_name}.", "confirm": False, "os_concept": "card-syscalls", "source": "AI Kernel Fast Engine"}

    # 6. Running Processes
    elif any(k in p for k in ["process", "task", "ps", "running", "cpu", "ram", "memory"]):
        cmd = "Get-Process | Select-Object -First 15" if is_win else "ps aux | head -n 15"
        return {"command": cmd, "explanation": f"Lists currently running processes and system resource usage on {os_name}.", "confirm": False, "os_concept": "card-proc", "source": "AI Kernel Fast Engine"}

    # 7. Create Folder
    elif any(k in p for k in ["create folder", "make folder", "mkdir", "new folder", "create directory"]):
        m = re.search(r"(?:folder|directory|named|called)\s+['\"]?([a-zA-Z0-9_\-]+)['\"]?", p)
        fname = m.group(1) if m else "new_folder"
        cmd = f"New-Item -ItemType Directory -Name '{fname}'" if is_win else f"mkdir '{fname}'"
        return {"command": cmd, "explanation": f"Creates a new directory named '{fname}' on {os_name}.", "confirm": False, "os_concept": "card-syscalls", "source": "AI Kernel Fast Engine"}

    # 8. Date and Time
    elif any(k in p for k in ["date", "time", "clock", "today"]):
        cmd = "Get-Date" if is_win else "date"
        return {"command": cmd, "explanation": f"Displays current date and time on {os_name}.", "confirm": False, "os_concept": "card-syscalls", "source": "AI Kernel Fast Engine"}

    # 9. Clear Screen
    elif any(k in p for k in ["clear", "cls", "clean screen"]):
        cmd = "Clear-Host" if is_win else "clear"
        return {"command": cmd, "explanation": "Clears the terminal screen.", "confirm": False, "os_concept": "card-redirection", "source": "AI Kernel Fast Engine"}

    # 10. Ping
    elif "ping" in p or "test connection" in p:
        cmd = "Test-Connection 8.8.8.8 -Count 2" if is_win else "ping -c 2 8.8.8.8"
        return {"command": cmd, "explanation": f"Tests network reachability to Google DNS on {os_name}.", "confirm": False, "os_concept": "card-sync", "source": "AI Kernel Fast Engine"}

    # Default
    cmd = "Get-ChildItem" if is_win else "ls"
    return {
        "command": cmd,
        "explanation": f"Lists directory contents on {os_name}.",
        "confirm": False,
        "os_concept": "card-syscalls",
        "source": "AI Kernel Fast Engine"
    }

class IntelliShellHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=UI_DIR, **kwargs)

    def end_headers(self):
        # Enable CORS and disable aggressive caching for dev
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        # Serve the PDF report if requested
        if parsed.path == "/IntelliShell_Project_Report.pdf" or parsed.path == "/report.pdf":
            pdf_path = os.path.join(BASE_DIR, "IntelliShell_Project_Report.pdf")
            if os.path.exists(pdf_path):
                self.send_response(200)
                self.send_header("Content-Type", "application/pdf")
                self.send_header("Content-Disposition", "inline; filename=IntelliShell_Project_Report.pdf")
                with open(pdf_path, "rb") as f:
                    content = f.read()
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            req_data = json.loads(post_data.decode("utf-8"))
        except Exception:
            req_data = {}

        if parsed.path == "/api/suggest":
            prompt = req_data.get("prompt", "").strip()
            target_os = req_data.get("os", "windows").lower()

            result = None
            if gemini_model:
                try:
                    os_str = "Windows (PowerShell)" if target_os == "windows" else "Linux (/bin/sh)"
                    sys_prompt = f"""
You are an intelligent OS command translator for {os_str}.
Given the user's natural language request: "{prompt}"
Return ONLY a valid JSON object with keys:
- "command": the exact shell command to execute
- "explanation": a concise 1-sentence explanation of what the command does
- "confirm": true if the command is destructive (delete, remove, wipe, format, drop), false otherwise
Do not wrap in markdown quotes. Return raw JSON.
"""
                    future = executor.submit(call_gemini_sync, sys_prompt)
                    raw_text = future.result(timeout=2.0)
                    text = raw_text.strip()
                    # Strip any markdown code fences if present
                    if text.startswith("```"):
                        text = re.sub(r"^```(?:json)?\s*", "", text)
                        text = re.sub(r"\s*```$", "", text)
                    parsed_res = json.loads(text)
                    parsed_res["os_concept"] = detect_os_concept(parsed_res.get("command", ""), prompt)
                    parsed_res["source"] = "Gemini AI"
                    result = parsed_res
                except Exception as ex:
                    print(f"[Fast Fallback Triggered]: {ex}")

            if not result:
                result = rule_based_suggest(prompt, target_os)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode("utf-8"))
            return

        elif parsed.path == "/api/execute":
            cmd = req_data.get("command", "").strip()
            target_os = req_data.get("os", "windows").lower()

            # Security ring check
            danger_patterns = [r"\bformat\b", r"\brmdir\s+/[sS]", r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;", r"\brm\s+-rf\s+/\b"]
            is_danger = any(re.search(pat, cmd, re.IGNORECASE) for pat in danger_patterns)

            if is_danger:
                resp = {
                    "output": f"[SECURITY INTERCEPTION] Command rejected by Operating System Protection Ring!\nCommand contains dangerous signature: {cmd}",
                    "returncode": -1,
                    "executed_command": cmd
                }
            else:
                try:
                    # Execute via powershell on Windows, or bash/sh on Unix
                    if platform.system() == "Windows":
                        proc = subprocess.run(
                            ["powershell.exe", "-NoProfile", "-Command", cmd],
                            capture_output=True,
                            text=True,
                            timeout=10,
                            cwd=BASE_DIR
                        )
                    else:
                        proc = subprocess.run(
                            cmd,
                            shell=True,
                            capture_output=True,
                            text=True,
                            timeout=10,
                            cwd=BASE_DIR
                        )
                    
                    stdout = proc.stdout.strip()
                    stderr = proc.stderr.strip()
                    out = stdout if stdout else ""
                    if stderr:
                        out = out + ("\n[STDERR]\n" if out else "") + stderr
                    if not out:
                        out = f"[Command executed successfully with exit code {proc.returncode}]"

                    resp = {
                        "output": out,
                        "returncode": proc.returncode,
                        "executed_command": cmd
                    }
                except subprocess.TimeoutExpired:
                    resp = {
                        "output": "[EXECUTION TIMEOUT] Process took longer than 10 seconds and was terminated by parent supervisor.",
                        "returncode": 124,
                        "executed_command": cmd
                    }
                except Exception as e:
                    resp = {
                        "output": f"[EXECUTION ERROR] Failed to spawn process: {str(e)}",
                        "returncode": 1,
                        "executed_command": cmd
                    }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(resp).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

def main():
    print(f"=" * 60)
    print(f"  IntelliShell Web Console Server")
    print(f"  Serving UI from: {UI_DIR}")
    print(f"  URL: http://localhost:{PORT}")
    print(f"  Gemini API Status: {'ACTIVE' if is_valid_key else 'OFFLINE (Fallback Active)'}")
    print(f"=" * 60)

    # Allow address reuse so quick restarts don't hit "Address already in use"
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), IntelliShellHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down IntelliShell server.")
            httpd.server_close()

if __name__ == "__main__":
    main()
