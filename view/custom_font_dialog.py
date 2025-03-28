"""Custom Font Selection Dialog for TASJ Application."""

import logging
from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QLabel, QPushButton,
    QDialogButtonBox, QSplitter, QListWidgetItem, QScrollArea, QWidget
)
from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtCore import Qt

from controller.font_controller import FontController
from view.get_more_fonts_dialog import GetMoreFontsDialog

logger = logging.getLogger(__name__)

class CustomFontDialog(QDialog):
    """A custom dialog for selecting application-installed fonts."""

    def __init__(
        self,
        font_controller: FontController,
        current_font: Optional[QFont] = None,
        parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self.font_controller = font_controller
        self.selected_font: Optional[QFont] = current_font or QFont() # Start with current or default

        self.setWindowTitle("Select Application Font")
        self.setMinimumSize(600, 400)

        # Main layout
        layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # --- Left Pane: Font List ---
        left_pane = QWidget()
        left_layout = QVBoxLayout(left_pane)
        self.font_list_widget = QListWidget()
        self.font_list_widget.currentItemChanged.connect(self._update_preview)
        left_layout.addWidget(QLabel("Installed Fonts:"))
        left_layout.addWidget(self.font_list_widget)
        
        # Get More Fonts button (placeholder)
        self.get_more_button = QPushButton("Get More Fonts...")
        self.get_more_button.clicked.connect(self._get_more_fonts)
        left_layout.addWidget(self.get_more_button)
        
        splitter.addWidget(left_pane)

        # --- Right Pane: Preview ---
        right_pane = QWidget()
        right_layout = QVBoxLayout(right_pane)
        self.preview_label = QLabel("AaBbCcDdEeFfGg HhIiJjKkLlMmNn OoPpQqRrSsTtUuVvWwXxYyZz\n0123456789")
        self.preview_label.setWordWrap(True)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        # Use QScrollArea for potentially large previews
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.preview_label)
        
        right_layout.addWidget(QLabel("Preview:"))
        right_layout.addWidget(scroll_area)
        splitter.addWidget(right_pane)
        
        splitter.setSizes([200, 400]) # Initial sizes for left/right panes

        # --- Dialog Buttons ---
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self._populate_font_list()
        self._select_initial_font()

    def _populate_font_list(self) -> None:
        """Populate the list with fonts installed by the application."""
        self.font_list_widget.clear()
        installed_families = self.font_controller.get_installed_app_font_families()
        
        logger.info(f"Populating custom font dialog with: {installed_families}")
        
        for family in sorted(installed_families):
            item = QListWidgetItem(family)
            # Store the family name in the item's data
            item.setData(Qt.ItemDataRole.UserRole, family)
            self.font_list_widget.addItem(item)

    def _select_initial_font(self) -> None:
        """Select the current font in the list if it exists."""
        if self.selected_font:
            initial_family = self.selected_font.family()
            items = self.font_list_widget.findItems(initial_family, Qt.MatchFlag.MatchExactly)
            if items:
                self.font_list_widget.setCurrentItem(items[0])
                # Trigger preview update manually if selection didn't change currentItem
                if self.font_list_widget.currentItem() == items[0]:
                    self._update_preview(items[0])
            else:
                 # If current font isn't in the list, select the first item if available
                 if self.font_list_widget.count() > 0:
                     self.font_list_widget.setCurrentRow(0)
                 else: # No fonts, clear preview
                     self._update_preview(None)
        elif self.font_list_widget.count() > 0:
            self.font_list_widget.setCurrentRow(0)
        else: # No fonts, clear preview
            self._update_preview(None)


    def _update_preview(self, current_item: Optional[QListWidgetItem]) -> None:
        """Update the preview label with the selected font."""
        if current_item:
            family = current_item.data(Qt.ItemDataRole.UserRole)
            if family:
                # Use a reasonable default size for preview
                preview_font = QFont(family, 24)
                self.preview_label.setFont(preview_font)
                # Update the font we'll return on OK
                # Keep original size if possible, otherwise default
                original_size = self.selected_font.pointSize() if self.selected_font else -1
                self.selected_font = QFont(family, original_size if original_size > 0 else QFont().pointSize())
                logger.debug(f"Previewing font: {family}, Size: {self.selected_font.pointSize()}")
            else:
                 # Clear preview if item has no family data
                 self.preview_label.setFont(QFont())
                 self.selected_font = QFont()
        else:
            # Clear preview if no item is selected
            self.preview_label.setFont(QFont())
            self.selected_font = QFont()
            
    def _get_more_fonts(self) -> None:
        """Launch the 'Get More Fonts' dialog/process."""
        logger.info("'Get More Fonts' clicked. Launching dialog.")
        # Create and execute the GetMoreFontsDialog
        get_fonts_dialog = GetMoreFontsDialog(self.font_controller, self)
        # Connect the signal to refresh this dialog's list when installation finishes
        get_fonts_dialog.fonts_installed_signal.connect(self._on_fonts_installed)
        get_fonts_dialog.exec()
        
    def _on_fonts_installed(self) -> None:
        """Slot to handle signal from GetMoreFontsDialog when fonts are installed."""
        logger.info("Received signal that new fonts were installed. Refreshing list.")
        # Remember current selection if possible
        current_selection_text = self.font_list_widget.currentItem().text() if self.font_list_widget.currentItem() else None
        
        self._populate_font_list()
        
        # Try to re-select the previously selected font
        if current_selection_text:
            items = self.font_list_widget.findItems(current_selection_text, Qt.MatchFlag.MatchExactly)
            if items:
                self.font_list_widget.setCurrentItem(items[0])
            else:
                # Fallback if previously selected is no longer available or name changed
                self._select_initial_font()
        else:
             self._select_initial_font()

    def get_selected_font(self) -> Optional[QFont]:
        """Return the font selected by the user."""
        if self.result() == QDialog.DialogCode.Accepted:
            return self.selected_font
        return None

    @staticmethod
    def get_font(
        font_controller: FontController,
        current_font: Optional[QFont] = None,
        parent: Optional[QWidget] = None
    ) -> tuple[Optional[QFont], bool]:
        """Static method to create, show dialog, and return result."""
        dialog = CustomFontDialog(font_controller, current_font, parent)
        result = dialog.exec()
        font = dialog.get_selected_font()
        return font, result == QDialog.DialogCode.Accepted
