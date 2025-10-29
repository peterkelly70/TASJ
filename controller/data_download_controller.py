import os
import PyQt6.QtCore
from PyQt6.QtCore import QTimer
import multiprocessing
from controller.tasks.download_data_task import download_data_task
from dotenv import load_dotenv
import logging
import time
from queue import Empty

class DataDownloadController:
    def __init__(self, db_instance, queue: multiprocessing.Queue, cancel_event: multiprocessing.Event):
        """Initialize the data download controller."""
        self.db_instance = db_instance
        self.queue = queue
        self.cancel_event = cancel_event
        self.console_view = None  # Will be set later
        self.current_process = None  # Track the current download process

    def set_console_view(self, console_view):
        """Set the console view for progress and cancel functionality."""
        self.console_view = console_view
        self.cancel_button = console_view.cancel_button
        self.cancel_button.clicked.connect(self.cancel_event.set)
        self.progress_bar = console_view.progress_bar

    def start_download(self, download_options=None):
        """Start the data download process."""
        # Cancel any existing download
        if self.current_process and self.current_process.is_alive():
            self.cancel_download()
            self.current_process.join(timeout=1.0)
        
        if self.console_view:
            self.console_view.clear_text()
            self.console_view.append_text("Starting download...\n")
            self.console_view.show_progress_bar(True)
            self.console_view.update_progress_bar(0)
            self.console_view.enable_cancel_button(True)
        
        # Clear the cancel event
        self.cancel_event.clear()

        download_options = download_options or {}
        mode = download_options.get("mode", "full")
        target_sectors = download_options.get("selected_sectors") if mode == "sector" else None
        skip_existing = download_options.get("skip_existing", True)

        # Start the download process in a separate process
        self.current_process = multiprocessing.Process(
            target=download_data_task,
            args=(
                self.db_instance.db_type,
                self.queue,
                self.cancel_event,
                target_sectors,
                skip_existing,
            )
        )
        self.current_process.start()
        
        # Note: Queue monitoring is now handled by the main application's QTimer

    def cancel_download(self):
        """Cancel the ongoing download process."""
        if self.console_view:
            self.console_view.enable_cancel_button(False)
        self.cancel_event.set()

    def update_progress(self, payload):
        """Update the progress bar and console output with queue payload."""
        if not self.console_view:
            return

        progress = None
        message = ""

        if isinstance(payload, tuple) and len(payload) == 2:
            progress, message = payload
        else:
            message = str(payload)

        if progress is not None:
            self.console_view.update_progress_bar(progress)

        if message:
            self.console_view.append_text(f"{message}\n")

    def _monitor_queue(self):
        """Monitor the queue for progress updates."""
        while not self.cancel_event.is_set():
            try:
                payload = self.queue.get_nowait()
                self.update_progress(payload)
            except Empty:
                time.sleep(0.1)

        # Final update
        if not self.queue.empty():
            payload = self.queue.get()
            self.update_progress(payload)

        if self.console_view:
            self.console_view.enable_cancel_button(False)
            self.console_view.show_progress_bar(False)
