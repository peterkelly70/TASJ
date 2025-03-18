import os
import PyQt5.QtCore
from PyQt5.QtCore import QTimer
import multiprocessing
from controller.tasks.download_data_task import download_data_task
from dotenv import load_dotenv

class DataDownloadController:
    def __init__(self, db_instance, progress_queue, cancel_event):
        """Initialize the data download controller with a database instance,
        a progress queue, and a cancel event.
        """
        self.db_instance = db_instance
        self.progress_queue = progress_queue
        self.cancel_event = cancel_event
        self.process = None
        self.progress_timer = None
        self.progress_bar = None
        self.cancel_button = None
    
    def start_download(self, view_widget, progress_bar, cancel_button):
        """Starts the data download in a background process."""
        if self.process and self.process.is_alive():
            view_widget.append("⚠️ Download already in progress.")
            return
        
        # Store UI elements for progress updates.
        self.progress_bar = progress_bar
        self.cancel_button = cancel_button

        # Clear the cancel event before starting.
        self.cancel_event.clear()
        self.process = multiprocessing.Process(
            target=download_data_task,
            args=(self.db_instance.db_type, self.progress_queue, self.cancel_event)
        )
        self.process.start()
        view_widget.append("🚀 Download started.")
        self._monitor_progress(view_widget)

    def cancel_download(self, view_widget):
        """Cancels the download process."""
        if self.process and self.process.is_alive():
            self.cancel_event.set()
            self.process.join()
            view_widget.append("⏹️ Download cancelled.")
        else:
            view_widget.append("⚠️ No active download to cancel.")

    def _monitor_progress(self, view_widget):
        """
        Monitors progress messages from the progress_queue and updates the UI accordingly.
        Uses a QTimer to poll for new messages every 500ms.
        """
        def update_progress():
            message = ""  # Initialize to empty string.
            while not self.progress_queue.empty():
                message = self.progress_queue.get()
                view_widget.append(message)

                # Example: "Progress: 3/10 sectors processed."
                if "Progress:" in message:
                    try:
                        progress_text = message.split(":")[1].strip().split("/")
                        current, total = int(progress_text[0]), int(progress_text[1])
                        percentage = int((current / total) * 100)
                        self.progress_bar.setValue(percentage)
                    except ValueError:
                        pass  # Ignore malformed messages

            if "Download complete" in message:
                self.progress_timer.stop()
                self.progress_bar.setValue(100)
                self.cancel_button.setEnabled(False)

        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(update_progress)
        self.progress_timer.start(500)
