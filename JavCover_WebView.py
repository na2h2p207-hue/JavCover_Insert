import webview
import threading
import os
import sys
import time
import json
from io import StringIO

# --- SETUP PATHS ---
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

rename_dir = os.path.join(base_path, "rename")
if rename_dir not in sys.path:
    sys.path.insert(0, rename_dir)

try:
    import rename_movies
    import manual_fix
except ImportError as e:
    print(f"Error importing modules: {e}")
    rename_movies = None
    manual_fix = None

# --- API ---
class Api:
    def __init__(self):
        self._window = None
        self.cover_save_path = ""
        self.default_cover_path = self._get_default_cover_path()

    def set_window(self, window):
        self._window = window

    def _get_default_cover_path(self):
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
            return os.path.join(exe_dir, "cover")
        return os.path.join(os.path.dirname(base_path), "cover")

    def init_app(self):
        # Called by JS on load
        self.cover_save_path = self.default_cover_path
        # Send initial path to JS
        if self._window:
            self._window.evaluate_js(f"window.set_path_input('{self.cover_save_path.replace(os.sep, '/')}')")
        return "OK"

    def minimize(self):
        if self._window: self._window.minimize()

    def toggle_maximize(self):
        if self._window: self._window.toggle_fullscreen()

    def close(self):
        if self._window: self._window.destroy()
    
    def select_folder(self):
        if not self._window: return
        result = self._window.create_file_dialog(webview.FileDialog.FOLDER)
        if result and len(result) > 0:
            self.cover_save_path = result[0]
            self._window.evaluate_js(f"window.set_path_input('{self.cover_save_path.replace(os.sep, '/')}')")

    def start_javcover(self):
        if not self._window: return
        result = self._window.create_file_dialog(webview.FileDialog.OPEN, allow_multiple=True, file_types=('Video Files (*.mp4;*.mkv;*.avi)', 'All files (*.*)'))
        if result:
            threading.Thread(target=self._run_worker, args=(result, True), daemon=True).start()

    def start_manual(self):
        if not self._window: return
        result = self._window.create_file_dialog(webview.FileDialog.OPEN, allow_multiple=True, file_types=('Video Files (*.mp4;*.mkv;*.avi)', 'All files (*.*)'))
        if result:
            threading.Thread(target=self._run_worker, args=(result, False), daemon=True).start()

    def _run_worker(self, files, is_javcover):
        total = len(files)
        
        # Reset UI
        self._window.evaluate_js("window.reset_ui()")
        time.sleep(0.1)

        for i, f in enumerate(files):
            filename = os.path.basename(f)
            parent = os.path.dirname(f)
            
            # Update Total Progress
            self._window.evaluate_js(f"window.update_progress({i}, {total}, 'Processing {filename}', 0)")
            
            def progress_cb(idx_ignored, pct, msg):
                # Escape msg for JS
                safe_msg = msg.replace("'", "\\'").replace("\n", " ")
                self._window.evaluate_js(f"window.update_progress({i}, {total}, '{safe_msg}', {pct})")

            try:
                if is_javcover and rename_movies:
                    rename_movies.process_directory(
                        parent, False, target_file=filename,
                        progress_callback=progress_cb,
                        custom_cover_dir=self.cover_save_path
                    )
                elif not is_javcover and manual_fix:
                    # Manual Fix Wrapper
                    def man_cb(pct, msg):
                        progress_cb(0, pct, msg)
                    manual_fix.process_file(f, progress_callback=man_cb)
            except Exception as e:
                print(f"Error: {e}")

        self._window.evaluate_js(f"window.update_progress({total}, {total}, 'All Done.', 100)")


# --- LOGGER ---
class BridgeLogger:
    def __init__(self, api):
        self.api = api
        self.buffer = ""
        self._orig_stdout = sys.__stdout__  # May be None in windowed exe

    def write(self, message):
        if not message: return
        
        # Intercept Cover Path
        if message.startswith("[COVER_PATH]"):
            path = message.replace("[COVER_PATH]", "").strip()
            js_path = path.replace(os.sep, '/')
            if self.api._window:
                try:
                    self.api._window.evaluate_js(f"window.set_cover('{js_path}')")
                except Exception:
                    pass
            return

        # Send to Log Area
        safe_msg = message.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "")
        if self.api._window:
            try:
                self.api._window.evaluate_js(f"window.append_log('{safe_msg}')")
            except Exception:
                pass
        
        # Also print to console for debug (only if console exists)
        if self._orig_stdout:
            try:
                self._orig_stdout.write(message)
            except Exception:
                pass

    def flush(self):
        if self._orig_stdout:
            try:
                self._orig_stdout.flush()
            except Exception:
                pass

if __name__ == '__main__':
    api = Api()
    
    # Redirect Stdout
    sys.stdout = BridgeLogger(api)
    sys.stderr = BridgeLogger(api)

    # Resolve index.html path
    gui_dir = os.path.join(base_path, "gui")
    index_path = os.path.join(gui_dir, "index.html")
    # Must use file:// protocol for local file
    url_path = os.path.abspath(index_path).replace("\\", "/")
    url = f"file:///{url_path}"

    window = webview.create_window(
        'JavCover', 
        url, 
        js_api=api,
        width=737, 
        height=640, 
        frameless=True,
        resizable=True,
        min_size=(737, 560),
        background_color='#FFFFFF'
    )
    api.set_window(window)
    
    # Enable EasyDrag to drag the window by title bar (defined in CSS with -webkit-app-region: drag)
    webview.start(debug=False, gui="edgechromium")
