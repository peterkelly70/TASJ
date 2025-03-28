"""Dialog to browse and install available fonts."""

import logging
from typing import Optional, Dict, Any, List
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton, 
    QDialogButtonBox, QLabel, QTextBrowser, QSplitter, QProgressDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from controller.font_controller import FontController

logger = logging.getLogger(__name__)

class FontInstallWorker(QThread):
    """Worker thread to install fonts in the background."""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(str, bool, str) # font_id, success, message

    def __init__(self, font_controller: FontController, font_id: str, config: Dict[str, Any]):
        super().__init__()
        self.font_controller = font_controller
        self.font_id = font_id
        self.config = config

    def run(self) -> None:
        """Perform the font installation."""
        self.progress.emit(0, f"Starting installation for {self.config.get('name', self.font_id)}...")
        try:
            # Use the existing ensure_font_available logic which handles download/install
            font_path = self.font_controller.ensure_font_available(self.font_id, parent_widget=None, show_dialogs=False)
            if font_path:
                self.progress.emit(100, f"{self.config.get('name', self.font_id)} installed successfully.")
                self.finished.emit(self.font_id, True, f"{self.config.get('name', self.font_id)} installed successfully.")
            else:
                # Try to get a more specific error from the model/controller if possible
                error_msg = f"Installation failed for {self.config.get('name', self.font_id)}." # Generic message
                self.progress.emit(100, error_msg)
                self.finished.emit(self.font_id, False, error_msg)
        except Exception as e:
            logger.error(f"Error installing font {self.font_id}: {e}", exc_info=True)
            error_msg = f"Error installing {self.config.get('name', self.font_id)}: {e}"
            self.progress.emit(100, error_msg)
            self.finished.emit(self.font_id, False, error_msg)


class GetMoreFontsDialog(QDialog):
    """Dialog to browse and install available fonts."""
    # Signal emitted when fonts have been installed, prompting parent dialog to refresh
    fonts_installed_signal = pyqtSignal()
    
    def __init__(self, font_controller: FontController, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.font_controller = font_controller
        self.available_fonts: Dict[str, Dict[str, Any]] = {}
        self.install_workers: Dict[str, FontInstallWorker] = {}
        self.progress_dialog: Optional[QProgressDialog] = None

        self.setWindowTitle("Get More Fonts")
        self.setMinimumSize(700, 500)

        # Main Layout
        layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Left Pane: Available Fonts List
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(QLabel("Available Fonts:"))
        self.font_list = QListWidget()
        self.font_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.font_list.currentItemChanged.connect(self._show_font_details)
        left_layout.addWidget(self.font_list)
        splitter.addWidget(left_widget)

        # Right Pane: Font Details and Install Button
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.addWidget(QLabel("Details:"))
        self.details_browser = QTextBrowser()
        self.details_browser.setOpenExternalLinks(True)
        right_layout.addWidget(self.details_browser)
        
        self.install_button = QPushButton("Install Selected")
        self.install_button.clicked.connect(self._install_selected_fonts)
        self.install_button.setEnabled(False) # Enabled when a font is selected
        right_layout.addWidget(self.install_button)
        splitter.addWidget(right_widget)
        
        splitter.setSizes([250, 450])

        # Dialog Buttons (Close)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self._populate_available_fonts()

    def _populate_available_fonts(self) -> None:
        """Fill the list with fonts available for download."""
        self.font_list.clear()
        self.available_fonts = self.font_controller.get_available_uninstalled_fonts()
        
        if not self.available_fonts:
            self.font_list.addItem("No new fonts available.")
            self.install_button.setEnabled(False)
            return

        for font_id, config in sorted(self.available_fonts.items(), key=lambda item: item[1].get('name', item[0])):
            item = QListWidgetItem(config.get('name', font_id))
            item.setData(Qt.ItemDataRole.UserRole, font_id) # Store font_id
            self.font_list.addItem(item)
            
        # Select first item automatically to show details
        if self.font_list.count() > 0:
            self.font_list.setCurrentRow(0)

    def _show_font_details(self, current: Optional[QListWidgetItem], previous: Optional[QListWidgetItem]) -> None:
        """Display details of the currently selected font."""
        if not current:
            self.details_browser.clear()
            self.install_button.setEnabled(False)
            return

        font_id = current.data(Qt.ItemDataRole.UserRole)
        if not font_id or font_id not in self.available_fonts:
             self.details_browser.clear()
             self.install_button.setEnabled(False)
             return

        config = self.available_fonts[font_id]
        details_html = f"""
        <h3>{config.get('name', font_id)}</h3>
        <p><b>Author:</b> {config.get('author', 'N/A')}</p>
        <p><b>Description:</b> {config.get('description', 'N/A')}</p>
        <p><b>Usage:</b> {config.get('usage', 'N/A')}</p>
        <p><a href=\"{config.get('source_url', '#')}\">Source Link</a></p>
        <p><i>License details should be reviewed before installation.</i></p>
        """
        self.details_browser.setHtml(details_html)
        self.install_button.setEnabled(True)

    def _install_selected_fonts(self) -> None:
        """Start installing the selected fonts using worker threads."""
        selected_items = self.font_list.selectedItems()
        if not selected_items:
            return

        fonts_to_install = [
            item.data(Qt.ItemDataRole.UserRole) for item in selected_items 
            if item.data(Qt.ItemDataRole.UserRole) in self.available_fonts
        ]
        
        if not fonts_to_install:
            return

        self.install_button.setEnabled(False) # Disable while installing

        # Setup progress dialog
        self.progress_dialog = QProgressDialog("Installing fonts...", "Cancel", 0, len(fonts_to_install), self)
        self.progress_dialog.setWindowTitle("Font Installation")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setAutoClose(False)
        self.progress_dialog.setAutoReset(False)
        self.progress_dialog.setValue(0)
        self.progress_dialog.canceled.connect(self._cancel_installation)
        
        self.install_workers = {}
        self.install_results: Dict[str, tuple[bool, str]] = {}
        self._installed_count = 0
        
        logger.info(f"Starting installation for fonts: {fonts_to_install}")

        for i, font_id in enumerate(fonts_to_install):
            config = self.available_fonts[font_id]
            worker = FontInstallWorker(self.font_controller, font_id, config)
            worker.finished.connect(self._on_worker_finished)
            # worker.progress can be connected if more detailed progress is needed
            self.install_workers[font_id] = worker
            worker.start()
            
        self.progress_dialog.show()

    def _on_worker_finished(self, font_id: str, success: bool, message: str) -> None:
        """Handle completion of a single font installation worker."""
        logger.info(f"Worker finished for {font_id}: Success={success}, Message={message}")
        if font_id in self.install_workers:
            self.install_results[font_id] = (success, message)
            del self.install_workers[font_id] # Remove finished worker
        
        self._installed_count += 1
        if self.progress_dialog:
            self.progress_dialog.setValue(self._installed_count)
            self.progress_dialog.setLabelText(message) # Show last message

        # Check if all workers are done
        if not self.install_workers and self.progress_dialog:
            self._finalize_installation()
            
    def _finalize_installation(self) -> None:
        """Called when all font installation workers have finished."""
        logger.info("All font installation workers finished.")
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
            
        # Process results (e.g., show summary message)
        successful_installs = [fid for fid, (s, m) in self.install_results.items() if s]
        failed_installs = [(fid, m) for fid, (s, m) in self.install_results.items() if not s]
        
        if successful_installs:
             logger.info(f"Successfully installed: {successful_installs}")
             self.fonts_installed_signal.emit() # Signal parent to refresh
             self._populate_available_fonts() # Refresh list in this dialog
             
        if failed_installs:
             logger.error(f"Failed installs: {failed_installs}")
             # Optionally show an error message dialog here

        # Re-enable install button if there are still available fonts
        self.install_button.setEnabled(self.font_list.count() > 0 and self.available_fonts)
        
    def _cancel_installation(self) -> None:
        """Attempt to cancel ongoing installations."""
        logger.warning("Font installation cancellation requested.")
        for font_id, worker in list(self.install_workers.items()):
            if worker.isRunning():
                # QThread termination is not always clean, especially during network ops
                # A more robust implementation might require flags within the worker run method
                logger.info(f"Requesting termination for worker {font_id}")
                worker.terminate() # Forceful termination
                worker.wait(1000) # Wait a bit for termination
                self.install_results[font_id] = (False, "Installation cancelled.")
                del self.install_workers[font_id]

        if self.progress_dialog:
             self.progress_dialog.setLabelText("Cancelling...")
        self._finalize_installation() # Clean up even if cancelled
        
    def reject(self) -> None:
        """Ensure threads are stopped if dialog is closed prematurely."""
        self._cancel_installation()
        super().reject()
