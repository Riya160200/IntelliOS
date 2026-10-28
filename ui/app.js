/**
 * IntelliShell Frontend Controller
 * Handles terminal interaction, AI suggestion cards, OS concept live tracking,
 * command editing modal, and real-time command execution.
 */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const terminalFeed = document.getElementById('terminal-feed');
    const promptForm = document.getElementById('prompt-form');
    const userInput = document.getElementById('user-input');
    const btnSubmit = document.getElementById('btn-submit');
    const btnClearTerm = document.getElementById('btn-clear-term');
    const btnClearHistory = document.getElementById('btn-clear-history');
    const historyList = document.getElementById('history-list');
    const osWinBtn = document.getElementById('os-win');
    const osLinuxBtn = document.getElementById('os-linux');
    const quickChips = document.querySelectorAll('.chip');

    // Modal Elements
    const editModal = document.getElementById('edit-modal');
    const modalInput = document.getElementById('modal-command-input');
    const btnCloseModal = document.getElementById('btn-close-modal');
    const btnModalCancel = document.getElementById('btn-modal-cancel');
    const btnModalRun = document.getElementById('btn-modal-run');

    // State
    let currentOS = 'windows';
    let currentCardContext = null;
    let commandHistory = [];

    // ================= OS Selector =================
    osWinBtn.addEventListener('click', () => {
        currentOS = 'windows';
        osWinBtn.classList.add('active');
        osLinuxBtn.classList.remove('active');
        userInput.placeholder = "Type in English... (e.g. 'show all files in current folder')";
    });

    osLinuxBtn.addEventListener('click', () => {
        currentOS = 'linux';
        osLinuxBtn.classList.add('active');
        osWinBtn.classList.remove('active');
        userInput.placeholder = "Type in English... (e.g. 'find large files in /var')";
    });

    // ================= Quick Suggestion Chips =================
    quickChips.forEach(chip => {
        chip.addEventListener('click', () => {
            const prompt = chip.getAttribute('data-prompt');
            if (prompt) {
                userInput.value = prompt;
                promptForm.dispatchEvent(new Event('submit'));
            }
        });
    });

    // ================= Clear Actions =================
    btnClearTerm.addEventListener('click', () => {
        // Keep only the welcome ASCII art
        const welcome = terminalFeed.querySelector('.terminal-welcome');
        terminalFeed.innerHTML = '';
        if (welcome) terminalFeed.appendChild(welcome);
    });

    btnClearHistory.addEventListener('click', () => {
        commandHistory = [];
        renderHistory();
    });

    // ================= Form Submission =================
    promptForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const prompt = userInput.value.trim();
        if (!prompt) return;

        userInput.value = '';
        userInput.disabled = true;
        btnSubmit.disabled = true;

        // 1. Render User Input Row
        appendUserMessage(prompt);

        // 2. Render Loading Indicator
        const loadingId = appendLoadingIndicator();

        try {
            // 3. Request Suggestion from Backend or Fallback
            const suggestion = await fetchSuggestion(prompt, currentOS);
            removeLoadingIndicator(loadingId);

            // 4. Highlight Relevant OS Concept
            highlightOSConcept(suggestion.os_concept || 'card-proc');

            // 5. Render AI Suggestion Card
            appendSuggestionCard(suggestion, prompt);

        } catch (err) {
            removeLoadingIndicator(loadingId);
            appendErrorCard(err.message || 'Error communicating with AI kernel.');
        } finally {
            userInput.disabled = false;
            btnSubmit.disabled = false;
            userInput.focus();
            scrollToBottom();
        }
    });

    // ================= API Communication =================
    async function fetchSuggestion(prompt, targetOS) {
        try {
            const res = await fetch('/api/suggest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt, os: targetOS })
            });
            if (res.ok) {
                return await res.json();
            }
        } catch (e) {
            console.warn('[Network Notice] Server not reachable, running client-side AI kernel fallback.');
        }

        // Client-side fallback if server offline or running directly from file://
        return clientSideFallback(prompt, targetOS);
    }

    async function executeCommand(command, targetOS) {
        try {
            const res = await fetch('/api/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command, os: targetOS })
            });
            if (res.ok) {
                return await res.json();
            }
        } catch (e) {
            console.warn('[Network Notice] Direct server unavailable.');
        }

        // Simulated output if running purely in static browser mode
        return {
            output: `[SIMULATED EXECUTION (${targetOS})]\n$ ${command}\nOutput: Process spawned with PID 4182.\nReturn code: 0 (STATUS_SUCCESS)`,
            returncode: 0,
            executed_command: command
        };
    }

    // ================= Client-side Fallback Generator =================
    function clientSideFallback(prompt, targetOS) {
        const p = prompt.toLowerCase();
        const isWin = targetOS === 'windows';
        const osName = isWin ? 'Windows (PowerShell)' : 'Linux (/bin/sh)';

        if (/delete|remove|rm|erase|format|wipe/.test(p)) {
            const m = p.match(/(?:delete|remove|rm|erase)\s+(?:file|folder)?\s*['"]?([a-zA-Z0-9_\-\.]+)?['"]?/);
            const target = (m && m[1] && !['a', 'the', 'file', 'folder'].includes(m[1])) ? m[1] : 'target_file.txt';
            const cmd = isWin ? `Remove-Item '${target}'` : `rm '${target}'`;
            return {
                command: cmd,
                explanation: `Deletes '${target}' from current directory on ${osName}.`,
                confirm: true,
                os_concept: 'card-security',
                source: 'AI Safety Kernel (Offline)'
            };
        } else if (/file|folder|dir|ls|list|show all|show files/.test(p)) {
            const cmd = isWin ? 'Get-ChildItem' : 'ls -la';
            return {
                command: cmd,
                explanation: `Lists files and subdirectories in the current workspace.`,
                confirm: false,
                os_concept: 'card-syscalls',
                source: 'AI Kernel Fast Engine'
            };
        } else if (/where|pwd|location|current dir/.test(p)) {
            const cmd = isWin ? 'Get-Location' : 'pwd';
            return {
                command: cmd,
                explanation: `Prints current working directory using kernel filesystem calls.`,
                confirm: false,
                os_concept: 'card-syscalls',
                source: 'AI Kernel Fast Engine'
            };
        } else if (/ip|network|ifconfig|ipconfig|wifi|ethernet/.test(p)) {
            const cmd = isWin ? 'ipconfig' : 'ip a';
            return {
                command: cmd,
                explanation: `Queries network stack adapters and assigned IPv4/IPv6 addresses.`,
                confirm: false,
                os_concept: 'card-proc',
                source: 'AI Kernel Fast Engine'
            };
        } else if (/disk|space|storage|capacity/.test(p)) {
            const cmd = isWin ? 'Get-PSDrive -PSProvider FileSystem' : 'df -h';
            return {
                command: cmd,
                explanation: `Inspects filesystem superblock for free and allocated storage sectors.`,
                confirm: false,
                os_concept: 'card-syscalls',
                source: 'AI Kernel Fast Engine'
            };
        } else if (/process|task|running|ps|cpu|ram/.test(p)) {
            const cmd = isWin ? 'Get-Process | Select-Object -First 15' : 'ps aux | head -n 15';
            return {
                command: cmd,
                explanation: `Inspects Process Control Blocks (PCBs) and resource consumption.`,
                confirm: false,
                os_concept: 'card-proc',
                source: 'AI Kernel Fast Engine'
            };
        }

        return {
            command: isWin ? 'Get-ChildItem' : 'ls',
            explanation: `Default safe directory listing on ${osName}.`,
            confirm: false,
            os_concept: 'card-syscalls',
            source: 'AI Kernel Fast Engine'
        };
    }

    // ================= DOM Append Functions =================
    function appendUserMessage(prompt) {
        const row = document.createElement('div');
        row.className = 'msg-row';
        row.innerHTML = `
            <div class="user-query-line">
                <span class="query-symbol">❯</span>
                <span class="query-text">${escapeHtml(prompt)}</span>
            </div>
        `;
        terminalFeed.appendChild(row);
    }

    function appendLoadingIndicator() {
        const id = 'loading-' + Date.now();
        const row = document.createElement('div');
        row.id = id;
        row.className = 'msg-row';
        row.innerHTML = `
            <div style="display:flex; align-items:center; gap:8px; font-family:var(--font-mono); font-size:0.8rem; color:var(--accent-cyan);">
                <span class="icon-pulse" style="width:8px; height:8px;"></span>
                <span>AI Kernel is analyzing intent & mapping OS system calls...</span>
            </div>
        `;
        terminalFeed.appendChild(row);
        scrollToBottom();
        return id;
    }

    function removeLoadingIndicator(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    function appendSuggestionCard(suggestion, prompt) {
        const row = document.createElement('div');
        row.className = 'msg-row';

        const isDanger = suggestion.confirm === true;
        const tagText = currentOS === 'windows' ? 'PowerShell' : 'POSIX sh';
        const sourceBadge = suggestion.source || 'AI Kernel';

        row.innerHTML = `
            <div class="suggestion-card">
                <div class="card-header-badge">
                    <span class="badge-suggestion">Recommended Command</span>
                    <div style="display:flex; gap:6px;">
                        <span class="badge-tag">${sourceBadge}</span>
                        <span class="badge-tag">${tagText}</span>
                    </div>
                </div>

                <div class="command-preview">
                    <span class="cmd-text">$ ${escapeHtml(suggestion.command)}</span>
                </div>

                <div class="explanation-text">
                    <span class="label">Why:</span>${escapeHtml(suggestion.explanation)}
                </div>

                ${isDanger ? `
                    <div class="warning-banner">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                        <span>CAUTION: Destructive operation detected. Review command before executing.</span>
                    </div>
                ` : ''}

                <div class="action-controls">
                    <button class="btn-action btn-run" data-cmd="${escapeAttr(suggestion.command)}">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
                        <span>Execute Command</span>
                    </button>
                    <button class="btn-action btn-edit" data-cmd="${escapeAttr(suggestion.command)}">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>
                        <span>Edit</span>
                    </button>
                    <button class="btn-action btn-cancel">Cancel</button>
                </div>
            </div>
        `;

        terminalFeed.appendChild(row);

        // Bind Action Buttons
        const btnRun = row.querySelector('.btn-run');
        const btnEdit = row.querySelector('.btn-edit');
        const btnCancel = row.querySelector('.btn-cancel');

        btnRun.addEventListener('click', () => {
            handleExecute(suggestion.command, row);
        });

        btnEdit.addEventListener('click', () => {
            openEditModal(suggestion.command, row);
        });

        btnCancel.addEventListener('click', () => {
            row.querySelector('.action-controls').innerHTML = `
                <span style="font-family:var(--font-mono); font-size:0.78rem; color:var(--text-muted);">
                    [Command discarded by user]
                </span>
            `;
        });
    }

    function appendErrorCard(msg) {
        const row = document.createElement('div');
        row.className = 'msg-row';
        row.innerHTML = `
            <div class="suggestion-card" style="border-left-color: #ef4444;">
                <div style="color: #f87171; font-weight:600; font-size:0.85rem;">Engine Notice</div>
                <div style="font-size:0.82rem; color:var(--text-secondary);">${escapeHtml(msg)}</div>
            </div>
        `;
        terminalFeed.appendChild(row);
    }

    async function handleExecute(command, cardRow) {
        // Update controls to spinner state
        const controls = cardRow.querySelector('.action-controls');
        if (controls) {
            controls.innerHTML = `
                <div style="display:flex; align-items:center; gap:8px; font-family:var(--font-mono); font-size:0.8rem; color:var(--accent-emerald);">
                    <span class="icon-pulse" style="background:var(--accent-emerald);"></span>
                    <span>Spawning child process and streaming I/O...</span>
                </div>
            `;
        }

        // Highlight Execution OS Concepts (Process Lifecycle, Redirection, Synchronization)
        highlightOSConcept('card-proc');
        setTimeout(() => highlightOSConcept('card-redirection'), 300);
        setTimeout(() => highlightOSConcept('card-sync'), 600);

        const result = await executeCommand(command, currentOS);

        // Replace controls with done badge
        if (controls) {
            controls.innerHTML = `
                <span style="font-family:var(--font-mono); font-size:0.75rem; color:var(--accent-emerald); font-weight:600; display:inline-flex; align-items:center; gap:5px;">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
                    Executed with exit code ${result.returncode}
                </span>
            `;
        }

        // Append output terminal block
        const outRow = document.createElement('div');
        outRow.className = 'msg-row';
        outRow.innerHTML = `
            <div class="terminal-output">${escapeHtml(result.output)}</div>
        `;
        terminalFeed.appendChild(outRow);

        // Add to history
        addToHistory(command);
        scrollToBottom();
    }

    // ================= Modal Edit Flow =================
    function openEditModal(command, sourceCardRow) {
        currentCardContext = { command, row: sourceCardRow };
        modalInput.value = command;
        editModal.classList.remove('hidden');
        modalInput.focus();
    }

    function closeEditModal() {
        editModal.classList.add('hidden');
        currentCardContext = null;
    }

    btnCloseModal.addEventListener('click', closeEditModal);
    btnModalCancel.addEventListener('click', closeEditModal);

    btnModalRun.addEventListener('click', () => {
        const editedCmd = modalInput.value.trim();
        if (editedCmd && currentCardContext) {
            const row = currentCardContext.row;
            // Update preview in card
            const cmdText = row.querySelector('.command-preview .cmd-text');
            if (cmdText) cmdText.textContent = '$ ' + editedCmd;

            closeEditModal();
            handleExecute(editedCmd, row);
        }
    });

    modalInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            btnModalRun.click();
        } else if (e.key === 'Escape') {
            closeEditModal();
        }
    });

    // Close modal on backdrop click
    editModal.addEventListener('click', (e) => {
        if (e.target === editModal) closeEditModal();
    });

    // ================= OS Concept Highlight Animation =================
    function highlightOSConcept(cardId) {
        // Remove existing highlights
        document.querySelectorAll('.os-card').forEach(c => c.classList.remove('highlight'));

        const target = document.getElementById(cardId);
        if (target) {
            target.classList.add('highlight');
            target.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            setTimeout(() => {
                target.classList.remove('highlight');
            }, 3500);
        }
    }

    // ================= History Management =================
    function addToHistory(cmd) {
        commandHistory.unshift({ cmd, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) });
        if (commandHistory.length > 20) commandHistory.pop();
        renderHistory();
    }

    function renderHistory() {
        const countBadge = document.getElementById('history-count');
        if (countBadge) countBadge.textContent = commandHistory.length > 0 ? (commandHistory.length + ' / 8') : 'Active';
        if (commandHistory.length === 0) {
            historyList.innerHTML = `<li class="history-empty">No commands executed yet</li>`;
            return;
        }

        historyList.innerHTML = '';
        commandHistory.forEach(item => {
            const li = document.createElement('li');
            li.className = 'history-item';
            li.innerHTML = `
                <span title="${escapeAttr(item.cmd)}">${escapeHtml(truncate(item.cmd, 28))}</span>
                <span style="color:var(--text-muted); font-size:0.65rem;">${item.time}</span>
            `;
            li.addEventListener('click', () => {
                userInput.value = item.cmd;
                userInput.focus();
            });
            historyList.appendChild(li);
        });
    }

    // ================= Utilities =================
    function scrollToBottom() {
        terminalFeed.scrollTop = terminalFeed.scrollHeight;
    }

    function escapeHtml(text) {
        if (!text) return '';
        return String(text)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function escapeAttr(text) {
        if (!text) return '';
        return String(text).replace(/"/g, '&quot;');
    }

    function truncate(str, maxLen) {
        return str.length > maxLen ? str.slice(0, maxLen) + '...' : str;
    }
});
