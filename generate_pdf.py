#!/usr/bin/env python3
"""
Script to generate a comprehensive, professional PDF report for IntelliShell.
"""

from fpdf import FPDF
import datetime

class PDFReport(FPDF):
    def header(self):
        # Header banner on pages after page 1
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(100, 100, 100)
            self.cell(0, 8, "IntelliShell - AI-Powered Terminal Shell | Operating Systems Project Report", 0, 0, "L")
            self.cell(0, 8, f"Page {self.page_no()}", 0, 1, "R")
            self.set_draw_color(200, 200, 200)
            self.line(10, 18, 200, 18)
            self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

    def chapter_title(self, num, label):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(24, 43, 73) # Navy blue
        self.cell(0, 9, f"{num}. {label}", 0, 1, "L")
        self.set_draw_color(24, 43, 73)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def section_subtitle(self, label):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(40, 80, 130)
        self.cell(0, 7, label, 0, 1, "L")
        self.ln(1)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def bullet_point(self, title, desc):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(30, 30, 30)
        self.cell(6, 5.5, "-", 0, 0, "L")
        self.cell(self.get_string_width(title) + 2, 5.5, title, 0, 0, "L")
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 5.5, f" {desc}")
        self.ln(1)

    def code_box(self, code_text):
        self.set_fill_color(245, 247, 250)
        self.set_draw_color(210, 215, 225)
        self.set_font("Courier", "", 9)
        self.set_text_color(30, 30, 30)
        
        # Calculate height roughly
        lines = code_text.strip().split("\n")
        self.set_x(12)
        # Multi_cell inside bounding rect
        for line in lines:
            self.cell(186, 5, "  " + line, 1, 1, "L", fill=True)
        self.ln(3)

def build_pdf():
    pdf = PDFReport(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(10, 15, 10)

    # ================= PAGE 1: TITLE & COVER =================
    pdf.add_page()
    pdf.ln(10)

    # Title Box
    pdf.set_fill_color(24, 43, 73)
    pdf.rect(10, 20, 190, 40, "F")
    
    pdf.set_xy(10, 26)
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 12, "IntelliShell", 0, 1, "C")

    pdf.set_font("Helvetica", "I", 12)
    pdf.set_text_color(200, 220, 245)
    pdf.cell(190, 8, "AI-Powered Natural Language Terminal Shell", 0, 1, "C")

    pdf.set_xy(10, 68)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(0, 6, "OPERATING SYSTEMS COURSE PROJECT REPORT", 0, 1, "C")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, f"Generated: {datetime.datetime.now().strftime('%B %d, %Y')}", 0, 1, "C")
    pdf.ln(8)

    # 1. Executive Summary & Overview
    pdf.chapter_title("1", "Executive Summary & Project Overview")
    pdf.body_text(
        "IntelliShell is an intelligent, interactive command-line shell written in C++ that integrates "
        "Artificial Intelligence (Google Gemini) to bridge the gap between human natural language and low-level "
        "operating system commands. Instead of memorizing obscure terminal syntax, flags, or utility names, "
        "users express their intent in plain English (e.g., 'show all files in the current folder' or 'check network ip')."
    )
    pdf.body_text(
        "The project demonstrates a dual-process architecture where a high-performance compiled C++ shell "
        "manages the terminal interface, process lifecycle, and kernel execution, while a decoupled Python "
        "adapter interfaces with cloud LLM endpoints and structured JSON validation."
    )

    pdf.section_subtitle("Core Architectural Objectives:")
    pdf.bullet_point("Interactive C++ Terminal Interface:", "Renders dynamic colored prompts ([user@host] - [cwd]), handles user input, command history, and custom execution loops.")
    pdf.bullet_point("AI Natural Language Translation:", "Converts English instructions into precise operating system commands (PowerShell/CMD on Windows, POSIX /bin/sh on Linux).")
    pdf.bullet_point("Human-in-the-Loop Safeguard:", "Displays the AI-generated command alongside an explanation. Users can Run (r), Edit (e), or Cancel (c) before execution.")
    pdf.bullet_point("Proactive Security Filter:", "Scans commands for destructive patterns (e.g., fork bombs, recursive deletes, partition wipes) and enforces explicit confirmation.")
    pdf.bullet_point("Resilient Offline Fallback:", "Includes local keyword/regex translation so that network timeouts or missing API keys never crash the shell.")

    # ================= PAGE 2: OS CONCEPTS MAPPING =================
    pdf.add_page()
    pdf.chapter_title("2", "Operating System Concepts Applied in IntelliShell")
    pdf.body_text(
        "This project implements core Operating System principles studied in computer science courses. "
        "Below is a direct mapping of each theoretical concept to its concrete implementation in the codebase:"
    )

    pdf.section_subtitle("2.1 Process Creation and Lifecycle Management")
    pdf.body_text(
        "In modern operating systems, processes run in isolated address spaces. The C++ shell creates and "
        "manages child processes dynamically using native kernel APIs:"
    )
    pdf.bullet_point("Windows (CreateProcessA):", "Spawns python.exe as a child process with custom STARTUPINFO.")
    pdf.bullet_point("Linux (fork + exec):", "Uses fork() to duplicate the parent process and execlp() to overwrite the child's address space with the Python interpreter image.")
    pdf.code_box(
        "// Windows Process Creation in ai_shell.cpp\n"
        "CreateProcessA(NULL, cmdVec.data(), NULL, NULL, TRUE, 0, NULL, NULL, &siStartInfo, &piProcInfo);"
    )

    pdf.section_subtitle("2.2 Inter-Process Communication (IPC) via Anonymous Pipes")
    pdf.body_text(
        "Because the C++ shell and the Python AI adapter are distinct processes with independent memory spaces, "
        "they communicate across kernel-managed anonymous pipes (unnamed byte streams):"
    )
    pdf.bullet_point("Anonymous Pipes:", "C++ creates dual unidirectional pipes (one for STDIN and one for STDOUT). The parent writes JSON requests to the child's STDIN pipe and reads structured JSON responses from the child's STDOUT pipe.")
    pdf.code_box(
        "// Creating kernel pipe buffers in ai_shell.cpp\n"
        "CreatePipe(&hChildStd_OUT_Rd, &hChildStd_OUT_Wr, &saAttr, 0);\n"
        "CreatePipe(&hChildStd_IN_Rd,  &hChildStd_IN_Wr,  &saAttr, 0);"
    )

    pdf.section_subtitle("2.3 Standard I/O Redirection (File Descriptors & Handles)")
    pdf.body_text(
        "Normally, standard streams point to the console keyboard and display. The shell programmatically "
        "redirects standard handles prior to child execution:"
    )
    pdf.bullet_point("Handle Remapping:", "Configures STARTUPINFO with STARTF_USESTDHANDLES, routing Python's stdin/stdout to the pipe endpoints rather than the terminal.")
    pdf.code_box(
        "siStartInfo.hStdInput  = hChildStd_IN_Rd;   // Redirect STDIN\n"
        "siStartInfo.hStdOutput = hChildStd_OUT_Wr;  // Redirect STDOUT\n"
        "siStartInfo.dwFlags   |= STARTF_USESTDHANDLES;"
    )

    # ================= PAGE 3: OS CONCEPTS (CONT.) & DEMO =================
    pdf.add_page()
    pdf.section_subtitle("2.4 Process Synchronization & Zombie Prevention")
    pdf.body_text(
        "A well-behaved shell must synchronize with child processes to prevent race conditions and zombie entries "
        "in the operating system's process table:"
    )
    pdf.bullet_point("Blocking Wait:", "WaitForSingleObject (Windows) or waitpid (Linux) halts parent execution until the child signals termination, after which handles are safely closed.")
    pdf.code_box(
        "WaitForSingleObject(piProcInfo.hProcess, INFINITE);\n"
        "CloseHandle(piProcInfo.hProcess);\n"
        "CloseHandle(piProcInfo.hThread);"
    )

    pdf.section_subtitle("2.5 Working Directory & Environment Block System Calls")
    pdf.body_text(
        "The shell interacts directly with the Process Environment Block (PEB) and OS directory tables:"
    )
    pdf.bullet_point("System Calls:", "Queries getenv() for USER/HOME context, calls _getcwd() to locate the current directory, and executes _chdir() system calls when handling directory navigation.")

    pdf.section_subtitle("2.6 OS Security & Protection Guard")
    pdf.body_text(
        "To protect host system integrity, IntelliShell acts as a security filter before issuing commands to the OS:"
    )
    pdf.bullet_point("Safety Interception:", "Matches regular expressions against dangerous signatures (fork bombs ':(){ :|:& };:', recursive wipe 'Remove-Item -Recurse', volume formatting) to enforce explicit user confirmation.")

    # 3. Demo Walkthrough
    pdf.chapter_title("3", "Step-by-Step Execution Demo")
    pdf.body_text(
        "The following sequence demonstrates how a user instruction is processed through the entire pipeline:"
    )

    pdf.section_subtitle("Live Execution Trace: 'show all files in the current folder'")
    pdf.code_box(
        "[Riya gupta@LAPTOP-Q5R8L2TO] - [~\\Downloads\\OS CP 2\\IntelliShell]\n"
        "> show all files in the current folder\n\n"
        "[AI Suggestion] [Command]\n"
        "$ Get-ChildItem\n\n"
        "[Explanation]\n"
        "Lists all files and folders in the current directory on Windows (PowerShell/CMD).\n\n"
        "[Action] Run as-is (r), edit (e), or cancel (c)? r\n\n"
        "[Output]\n"
        "    Directory: C:\\Users\\Riya gupta\\Downloads\\OS CP 2\\IntelliShell\n"
        "Mode                 LastWriteTime         Length Name\n"
        "----                 -------------         ------ ----\n"
        "d-----        27-10-2026  10.49 PM                nlohmann\n"
        "-a----        27-10-2026  11.34 PM             69 .env\n"
        "-a----        27-10-2026  11.50 PM           4457 ai_adapter.py\n"
        "-a----        27-10-2026  11.26 PM          12240 ai_shell.cpp\n"
        "-a----        27-10-2026  11.27 PM        2304195 ai_shell.exe\n"
        "-a----        27-10-2026  11.30 PM            301 run.bat"
    )

    # ================= PAGE 4: FUTURE SCOPE & THREADS =================
    pdf.add_page()
    pdf.chapter_title("4", "Future Scope & Advanced OS Extensions (Threads & Concurrency)")
    pdf.body_text(
        "To further elevate the project's academic and practical standing, several advanced Operating Systems "
        "concepts can be integrated into future versions:"
    )

    pdf.section_subtitle("4.1 Multithreading and Asynchronous AI Worker Threads (Priority)")
    pdf.body_text(
        "Currently, when the shell queries the AI adapter, the main process waits synchronously. "
        "Introducing native C++ multithreading (std::thread, std::mutex, condition variables) provides enormous architectural benefits:"
    )
    pdf.bullet_point("Non-Blocking UI Thread:", "The main thread remains fully responsive, handling user keystrokes, window resizing, or immediate command cancellation.")
    pdf.bullet_point("Asynchronous Worker Thread:", "A dedicated background thread manages pipe I/O and network latency with the AI adapter, signaling the main thread via thread-safe queues.")
    pdf.bullet_point("Real-Time Visual Feedback:", "Enables the main thread to render an animated console progress indicator (spinner) while waiting for the cloud AI response.")
    pdf.code_box(
        "// Conceptual Multithreaded Architecture\n"
        "std::mutex mtx;\n"
        "std::condition_variable cv;\n"
        "bool ai_ready = false;\n"
        "std::string ai_response;\n\n"
        "void worker_thread(std::string prompt) {\n"
        "    std::string result = run_adapter(\"./ai_adapter.py\", prompt);\n"
        "    std::lock_guard<std::mutex> lock(mtx);\n"
        "    ai_response = result;\n"
        "    ai_ready = true;\n"
        "    cv.notify_one();\n"
        "}"
    )

    pdf.section_subtitle("4.2 Native Job Control & Background Execution ('&', jobs, fg, bg)")
    pdf.body_text(
        "Classic shells support asynchronous process execution via the '&' operator. Future iterations will implement:"
    )
    pdf.bullet_point("Job Table Management:", "Tracking process groups, PIDs, and process states (Running, Stopped, Done).")
    pdf.bullet_point("Built-in Job Commands:", "Adding 'jobs' to inspect background tasks and 'fg <PID>' / 'bg <PID>' to transfer processes between foreground and background terminal control.")

    pdf.section_subtitle("4.3 Asynchronous Signal Handling (SIGINT, Ctrl+C)")
    pdf.body_text(
        "Intercepting hardware interrupts via OS signal handlers (SetConsoleCtrlHandler on Windows / sigaction on Linux) "
        "ensures that typing Ctrl+C cleanly terminates a runaway child process without killing the shell itself."
    )

    pdf.section_subtitle("4.4 Process Resource Accounting & Profiling")
    pdf.body_text(
        "Querying kernel accounting metrics (GetProcessTimes / getrusage) after each command to report exact "
        "User-mode CPU time, Kernel-mode CPU time, and peak memory working set."
    )

    pdf.ln(4)
    pdf.set_fill_color(240, 245, 255)
    pdf.set_draw_color(180, 200, 230)
    pdf.rect(10, pdf.get_y(), 190, 18, "DF")
    pdf.set_xy(12, pdf.get_y() + 3)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(0, 5, "Conclusion:", 0, 1, "L")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 5, "IntelliShell effectively combines systems programming, OS system calls, IPC, and artificial", 0, 1, "L")
    pdf.cell(0, 5, "intelligence to deliver a modern, secure, and user-friendly command-line experience.", 0, 1, "L")

    # Output to disk
    pdf.output("IntelliShell_Project_Report.pdf")
    print("PDF generated successfully: IntelliShell_Project_Report.pdf")

if __name__ == "__main__":
    build_pdf()
