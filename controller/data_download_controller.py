import os
import PyQt5.QtCore
from PyQt5.QtCore import QTimer
import multiprocessing
from controller.tasks.download_data_task import download_data_task
from dotenv import load_dotenv
import logging
import time
from queue import Empty

class DataDownloadController:
    def __init__(self, db_instance, progress_queue, cancel_event):
        """Initialize the data download controller."""
        self.db_instance = db_instance
        self.queue = progress_queue
        self.cancel_event = cancel_event
        self.progress_bar = None
        self.cancel_button = None
        self.console_view = None  # Will be set later
        self.current_task = None

    def set_console_view(self, console_view):
        """Set the console view for progress and cancel functionality."""
        self.console_view = console_view
        self.progress_bar = console_view.progress_bar
        self.cancel_button = console_view.cancel_button
        self.cancel_button.clicked.connect(self.cancel_event.set)

    def start_download(self):
        """Start the data download process."""
        if self.progress_bar:
            self.progress_bar.setValue(0)
            self.progress_bar.setMaximum(100)
        if self.cancel_button:
            self.cancel_button.setEnabled(True)

        # Clear the cancel event
        self.cancel_event.clear()

        # Start the download process in a separate process
        process = multiprocessing.Process(
            target=download_data_task,
            args=(self.db_instance.db_type, self.queue, self.cancel_event)
        )
        process.start()

        # Start monitoring the queue
        self._monitor_queue()

    def cancel_download(self):
        """Cancel the ongoing download process."""
        if self.cancel_button:
            self.cancel_button.setEnabled(False)
        self.cancel_event.set()

    def update_progress(self, progress: int, message: str):
        """Update the progress bar and status message."""
        if self.progress_bar:
            self.progress_bar.setValue(progress)
        logging.info(message)
        self.console_view.append_text(message)

    def _monitor_queue(self):
        """Monitor the queue for progress updates."""
        while not self.cancel_event.is_set():
            try:
                progress, message = self.queue.get_nowait()
                self.update_progress(progress, message)
            except Empty:
                time.sleep(0.1)

        # Final update
        if not self.queue.empty():
            progress, message = self.queue.get()
            self.update_progress(progress, message)

        if self.cancel_button:
            self.cancel_button.setEnabled(False)
