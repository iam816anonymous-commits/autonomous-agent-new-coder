import os
import time
from .event_bus import bus
from project_creator.core.manifest import ProjectManifest
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class WorkspaceHandler(FileSystemEventHandler):
    def __init__(self, monitor):
        self.monitor = monitor

    def on_modified(self, event):
        if not event.is_directory:
            rel_path = os.path.relpath(event.src_path, self.monitor.workspace_root)
            self.monitor.check_path(rel_path)

class WorkspaceMonitor:
    def __init__(self, workspace_root: str):
        self.workspace_root = workspace_root
        self.manifest = ProjectManifest(workspace_root)
        self.observer = Observer()
        self.handler = WorkspaceHandler(self)

    def start(self):
        print(f"👁️  WorkspaceMonitor: Starting watchdog on {self.workspace_root}")
        self.observer.schedule(self.handler, self.workspace_root, recursive=True)
        self.observer.start()

    def stop(self):
        self.observer.stop()
        self.observer.join()

    def scan_for_deltas(self):
        """Legacy polling method, now just a wrapper for initial check."""
        print("🔍 WorkspaceMonitor: Performing initial delta scan...")
        data = self.manifest.load()
        if not data or 'project' not in data or 'files' not in data['project']:
            return
        for path in data['project']['files'].keys():
            self.check_path(path)

    def check_path(self, path):
        """Checks a specific path for manual edits."""
        data = self.manifest.load()
        if not data or 'project' not in data or 'files' not in data['project']:
            return

        meta = data['project']['files'].get(path)
        if not meta or meta.get('status') != 'applied':
            return

        full_path = os.path.join(self.workspace_root, path)
        if not os.path.exists(full_path):
            return

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                current_content = f.read()

            from project_creator.core.session import SessionManager
            session = SessionManager(self.workspace_root)
            sess_data = session.load_session()

            if sess_data and path in sess_data.get('generated_files', {}):
                jules_version = sess_data['generated_files'][path]

                if current_content != jules_version:
                    bus.publish("MANUAL_EDIT_DETECTED", {
                        "path": path,
                        "jules_code": jules_version,
                        "user_code": current_content
                    })
                    print(f"🕵️  WorkspaceMonitor: Detected manual edit in {path}")
        except Exception as e:
            pass
