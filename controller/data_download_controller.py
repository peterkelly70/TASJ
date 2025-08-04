import os
from PyQt6.QtCore import QThread, QTimer, pyqtSignal
import queue
import threading
from controller.tasks.download_data_task import download_data_task
from dotenv import load_dotenv
import logging
from PyQt6.QtWidgets import QApplication

# Set up file-based logging
logging.basicConfig(filename='/tmp/tasj_debug.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')
debug_logger = logging.getLogger('tasj_controller')

class DownloadWorkerThread(QThread):
    """Worker thread for downloading data."""
    progress_update = pyqtSignal(int, str)
    
    def __init__(self, db_type, cancel_event):
        super().__init__()
        self.db_type = db_type
        self.cancel_event = cancel_event
        self.progress_queue = queue.Queue()
        self.timer = QTimer()
        self.timer.timeout.connect(self._process_queue)
        self.timer.moveToThread(self)  # Move timer to this thread
    
    def run(self):
        """Run the download task in the thread."""
        # Start queue processing timer in this thread
        self.timer.start(100)
        download_data_task(self.db_type, self.progress_queue, self.cancel_event)
        self.timer.stop()
    
    def _process_queue(self):
        """Process messages from the queue and emit signals."""
        try:
            while True:
                progress, message = self.progress_queue.get_nowait()
                self.progress_update.emit(progress, message)
        except queue.Empty:
            pass

class DataDownloadController:
    def __init__(self, db_instance):
        """Initialize the data download controller."""
        self.db_instance = db_instance
        self.cancel_event = threading.Event()
        self.console_view = None  # Will be set later
        self.worker_thread = None

    def set_console_view(self, console_view):
        """Set the console view for progress and cancel functionality."""
        self.console_view = console_view
        self.cancel_button = console_view.cancel_button
        self.cancel_button.clicked.connect(self.cancel_download)
        self.progress_bar = console_view.progress_bar

    def start_download(self):
        """Start the data download process."""
        if self.console_view:
            self.console_view.clear_text()
            self.console_view.append_text("Starting download...\n")
            self.console_view.show_progress_bar(True)
            self.console_view.update_progress_bar(0)
            self.console_view.enable_cancel_button(True)
        
        # Clear the cancel event
        self.cancel_event.clear()

        # Create and start the worker thread
        self.worker_thread = DownloadWorkerThread(
            self.db_instance.db_type, 
            self.cancel_event
        )
        self.worker_thread.finished.connect(self._on_download_finished)
        self.worker_thread.progress_update.connect(self.update_progress)
        self.worker_thread.start()
        
        print("DEBUG: Worker thread started with signal connections")

    def cancel_download(self):
        """Cancel the ongoing download process."""
        if self.console_view:
            self.console_view.enable_cancel_button(False)
        self.cancel_event.set()
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.wait(5000)  # Wait up to 5 seconds for thread to finish

    def update_progress(self, progress: int, message: str) -> None:
        """Update the progress bar and console with the current progress."""
        # Log all messages for debugging (file only, no console)
        debug_logger.info(f"CONTROLLER RECEIVED: '{message}' (progress: {progress})")
        
        if self.console_view:
            # Make sure the console view is visible
            self.console_view.show()
            self.console_view.raise_()
            
            # Update progress bar
            self.console_view.update_progress_bar(progress)
            
            # Special handling for different message types
            if message.startswith("    ") or message.startswith("        "):
                # Indented messages (relationship links, etc.)
                debug_logger.info(f"CONTROLLER INDENTED: '{message}'")
                self.console_view.append_text(f"{message}\n")
            # Check for system and planet messages
            elif message.startswith("SYSTEM:") or message.startswith("PLANET:") or \
                 message.startswith("---------") or message.startswith("- - - - -"):
                # System and planet updates - display without progress prefix
                debug_logger.info(f"CONTROLLER ENTITY: '{message}'")
                self.console_view.append_text(f"{message}\n")
            else:
                # Normal progress messages
                debug_logger.info(f"CONTROLLER NORMAL: '{message}'")
                formatted_msg = f"Progress: {progress}% - {message}\n"
                self.console_view.append_text(formatted_msg)
                
            # Process any pending events to ensure UI updates (only once)
            QApplication.processEvents()
        else:
            debug_logger.error("console_view is None!")
            print("ERROR: console_view is None!")
            
        # Also print to stdout for debugging
        if message.startswith("    ") or message.startswith("        "):
            print("INDENTED OUTPUT: " + message)
        elif message.startswith("[SYSTEM]") or message.startswith("[PLANET]"):
            print("ENTITY OUTPUT: " + message)
        else:
            print(f"NORMAL OUTPUT: Progress: {progress}% - {message}")

    def _on_download_finished(self):
        """Called when the download thread finishes."""
        if self.console_view:
            self.console_view.enable_cancel_button(False)
            self.console_view.show_progress_bar(False)
            self.console_view.append_text("Download process completed.\n")
        print("DEBUG: Download thread finished")
