import os
import multiprocessing
from controller.tasks.download_data_task import download_data_task
from dotenv import load_dotenv

class DataDownloadController:
    def __init__(self, db_instance):
        """Initialize the data download controller with a database instance."""
        self.db_instance = db_instance  # ✅ Use `TravellerDatabase` instead of hardcoding SQLite
        self.process = None
        self.cancel_event = multiprocessing.Event()
        self.progress_queue = multiprocessing.Queue()
    
    def start_download(self, view_widget):
        """Starts the data download in a background process."""
        if self.process and self.process.is_alive():
            view_widget.append("⚠️ Download already in progress.")
            return
        
        self.cancel_event.clear()
        self.process = multiprocessing.Process(
            target=download_data_task,
            args=(self.db_instance.db_type, self.progress_queue, self.cancel_event)  # ✅ Pass `db_type`
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
        Monitors progress messages and updates the progress bar in real-time.
        This method is called in a loop to check for new progress messages.
        """
        def update_progress():
            while not self.progress_queue.empty():
                message = self.progress_queue.get()
                view_widget.append(message)
    
                # ✅ Extract numbers from "Progress: X/Y sectors processed."
                if "Progress:" in message:
                    try:
                        progress_text = message.split(":")[1].strip().split("/")
                        current, total = int(progress_text[0]), int(progress_text[1])
                        percentage = int((current / total) * 100)
                        self.progress_bar.setValue(percentage)  # ✅ Now updates the progress bar
                    except ValueError:
                        pass  # Skip malformed progress messages
                    
            # ✅ Stop the timer when done
            if "Download complete" in message:
                self.progress_timer.stop()
                self.progress_bar.setValue(100)
                self.cancel_button.setEnabled(False)
    
        # ✅ Use QTimer to check for updates every 500ms
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(update_progress)
        self.progress_timer.start(500)  # Check progress every 500ms
