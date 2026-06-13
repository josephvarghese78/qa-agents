import os
import json
import time
import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, DirModifiedEvent, FileModifiedEvent
from concurrent.futures import ThreadPoolExecutor
from testcase_agent import TestCaseAgent
from testplan_agent import TestPlanAgent
from helperfunctions import InputParser
import threading
from collections import defaultdict


# Global worker pool (LIMIT concurrency here)
executor = ThreadPoolExecutor(max_workers=5)

in_progress_files = set()
lock = threading.Lock()
remaining_agents = defaultdict(int)

def run_agent(agent_type, file_path):
    """Runs async agent safely inside a thread."""

    agent=None
    print(f"Starting agent of type '{agent_type}' for file: {file_path}")
    if agent_type =="testplan":
        agent = TestPlanAgent(file_path)
    elif agent_type =="testcase":
        agent = TestCaseAgent(file_path)
    elif agent_type =="precheck":
        print(f"Precheck agent: dev in progress...")
        return
    elif agent_type =="scripting":
        print(f"Scripting agent: dev in progress...")
        return
    else:
        print(f"Unknown agent type: {agent_type}")
        return

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(agent.start())
    finally:
        loop.close()
        with lock:
            count = remaining_agents.get(file_path)

            if count is None:
                return

            count = max(0, count - 1)

            if count <= 0:
                print(f"[DONE] {file_path}")

                in_progress_files.discard(file_path)
                remaining_agents.pop(file_path, None)
            else:
                remaining_agents[file_path] = count




def submit_agent(file_path):
    """Non-blocking submission"""
    with lock:
        if file_path in in_progress_files:
            print(f"File already being processed: {file_path}")
            return
        in_progress_files.add(file_path)

    agent_types = InputParser(file_path).agents()
    remaining_agents[file_path] = len(agent_types)

    for agent_type in agent_types:
        executor.submit(run_agent, agent_type, file_path)


class FileHandler(FileSystemEventHandler):


    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent):
        self.process_file(event)

    def on_created(self, event):
        self.process_file(event)

    def process_file(self, event):
        if event.is_directory:
            return

        file_path = event.src_path
        file_name = os.path.basename(file_path)

        if file_name.startswith('.') or file_name.startswith('~'):
            return

        print(f"\n[DETECTED] New file: {file_name}")
        # Wait until file is fully written
        last_size = -1

        while True:
            try:
                current_size = os.path.getsize(file_path)

                if current_size == last_size:
                    break

                last_size = current_size
                time.sleep(0.5)

            except FileNotFoundError:
                return

        #print(f"[READY] File stable: {file_path}")
        #print(f"[HANDOFF] Sending to agent (NON-BLOCKING)")

        # 🚀 IMPORTANT: NO waiting
        submit_agent(file_path)


if __name__ == "__main__":

    WATCH_DIRECTORY = "./documents/input"
    os.makedirs(WATCH_DIRECTORY, exist_ok=True)
    event_handler = FileHandler()
    observer = Observer()
    observer.schedule(event_handler, path=WATCH_DIRECTORY, recursive=True)
    print(f"🚀 Watching: {os.path.abspath(WATCH_DIRECTORY)}")
    observer.start()

    try:
        while True:
            time.sleep(1)  # keep main thread alive

    except KeyboardInterrupt:
        print("\nStopping...")
        observer.stop()

    observer.join()