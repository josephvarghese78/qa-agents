import os
import time
#import requests  # Assuming your QE team will call the Flask API
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class BusinessFileHandler(FileSystemEventHandler):
    """Custom event handler to process incoming business requirement documents."""

    def on_created(self, event):
        # Ignore directory creation events
        if event.is_directory:
            return

        file_path = event.src_path
        file_name = os.path.basename(file_path)

        # Ignore system/hidden/temporary files (like Mac .DS_Store or Windows temp files)
        if file_name.startswith('.') or file_name.startswith('~'):
            return

        print(f"\n[DETECTED] New file dropped: {file_name}")
        self.process_file(file_path)

    def process_file(self, file_path):
        # ⚠️ CRITICAL QA GUARDRAIL: Wait for large files to finish writing
        # If a business user is copying a large PDF/Word file, 'on_created' fires instantly.
        # We check the file size until it stops growing before handing it off to the Agent.
        historical_size = -1
        while True:
            print(1)
            try:
                current_size = os.path.getsize(file_path)
                if current_size == historical_size:
                    break
                historical_size = current_size
                time.sleep(0.5)  # Wait half a second and check again
            except FileNotFoundError:
                # Handle edge case where file was dropped and immediately deleted/moved
                return

        print(f"[READY] File transfer complete. Size: {os.path.getsize(file_path)} bytes.")
        print(f"[HANDOFF] Passing {os.path.basename(file_path)} to Agent 1 (Readiness Check)...")

        # --- QE HOOK: Trigger your Flask API / Agent 1 Engine ---
        # Example API Trigger logic:
        # try:
        #     api_url = "http://localhost:5000/api/v1/intake"
        #     payload = {"file_path": os.path.abspath(file_path)}
        #     response = requests.post(api_url, json=payload, timeout=30)
        #     if response.status_code == 200:
        #         print("[SUCCESS] Agent 1 successfully accepted the job context.")
        #     else:
        #         print(f"[ERROR] API responded with status code: {response.status_code}")
        # except Exception as e:
        #     print(f"[CRITICAL] Failed to communicate with Agent API: {str(e)}")


if __name__ == "__main__":
    # Define target path to watch relative to script execution path
    WATCH_DIRECTORY = "./Incoming"

    # Bootstrap the directory if it doesn't exist yet
    if not os.path.exists(WATCH_DIRECTORY):
        os.makedirs(WATCH_DIRECTORY)

    # Initialize the architecture components
    event_handler = BusinessFileHandler()
    observer = Observer()

    # Schedule the handler (recursive=False ensures it only checks the root of /Incoming)
    observer.schedule(event_handler, path=WATCH_DIRECTORY, recursive=True)

    print(f"🚀 pipeline listener active. Monitoring: '{os.path.abspath(WATCH_DIRECTORY)}'")
    print("Press Ctrl+C to terminate.")

    observer.start()

    try:
        while True:
            print(2)
            time.sleep(1)  # Keeps the main thread alive running the daemon
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Stopping file system observer daemon...")
        observer.stop()

    observer.join()