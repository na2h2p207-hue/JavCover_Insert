
// --- THEME ---
const toggle = document.getElementById('themeToggle');
const body = document.body;

toggle.addEventListener('click', () => {
    const isDark = body.getAttribute('data-theme') === 'dark';
    if (isDark) {
        body.removeAttribute('data-theme');
    } else {
        body.setAttribute('data-theme', 'dark');
    }
});

// --- UI HELPERS ---
const gel = (id) => document.getElementById(id);

// Called by Python
window.update_progress = function (current, total, msg_file, pct_file) {
    if (total > 0) {
        gel('barTotal').style.width = (current / total * 100) + '%';
        gel('lblTotal').innerText = `Batch Progress: ${current}/${total}`;
    }

    if (pct_file !== null) {
        gel('barFile').style.width = pct_file + '%';
    }

    if (msg_file) {
        gel('lblFile').innerText = msg_file;
        gel('statusL').innerText = msg_file;
    }
};

window.append_log = function (text) {
    const log = gel('logArea');
    log.innerText += text; // or textContent, but innerText handles \n better?
    log.scrollTop = log.scrollHeight;
};

window.set_cover = function (path) {
    const img = gel('coverImg');
    const ph = gel('coverPlaceholder');

    if (path && path.trim() !== "") {
        // Force refresh if same path (cache bust unlikely needed for local file but safe)
        // Note: pywebview might need special handling for local files depending on config.
        // Usually, absolute paths work if scheme is supported, or we use base64.
        // We will try setting src directly.
        img.src = path + "?t=" + new Date().getTime();
        img.style.display = 'block';
        ph.style.display = 'none';
    } else {
        img.style.display = 'none';
        ph.style.display = 'block';
    }
};

window.set_path_input = function (path) {
    gel('pathText').innerText = path;
};

window.reset_ui = function () {
    gel('barTotal').style.width = '0%';
    gel('barFile').style.width = '0%';
    gel('lblTotal').innerText = 'Batch Progress: 0/0';
    gel('lblFile').innerText = 'Ready';
    gel('logArea').innerText = '';
    window.set_cover('');
};

// --- INIT ---
window.addEventListener('pywebviewready', function () {
    console.log('PyWebview Ready');
    // Request initial cover path
    pywebview.api.init_app();
});
