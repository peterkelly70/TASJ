from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QMessageBox, QVBoxLayout, QHBoxLayout,
    QLabel, QListWidget, QListWidgetItem, QGroupBox,
    QFormLayout, QTextEdit, QDialogButtonBox, QWidget
)
from PyQt6.QtCore import Qt

class FontDownloadDialog(QDialog):
    """Dialog for confirming font downloads."""
    
    def __init__(self, font_info: dict, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Download Font")
        
        layout = QVBoxLayout()
        
        # Font information
        info_group = QGroupBox("Font Information")
        info_layout = QFormLayout()
        
        info_layout.addRow("Name:", QLabel(font_info['name']))
        info_layout.addRow("Author:", QLabel(font_info['author']))
        info_layout.addRow("License:", QLabel(font_info['license']))
        info_layout.addRow("Usage:", QLabel(font_info['usage']))
        
        description = QLabel(font_info['description'])
        description.setWordWrap(True)
        info_layout.addRow("Description:", description)
        
        source = QLabel(f"<a href='{font_info['source']}'>{font_info['source']}</a>")
        source.setOpenExternalLinks(True)
        info_layout.addRow("Source:", source)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Confirmation message
        msg = QLabel(
            "This font is not currently installed. Would you like to download "
            "and install it now?"
        )
        msg.setWordWrap(True)
        layout.addWidget(msg)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Yes | 
            QDialogButtonBox.StandardButton.No
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)


class FontLicenseDialog(QDialog):
    """Dialog for displaying font licenses."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Font Licenses")
        self.resize(800, 600)
        
        layout = QVBoxLayout()
        
        # Split view
        content = QHBoxLayout()
        
        # Left side - font list
        self.font_list = QListWidget()
        self.font_list.setMaximumWidth(250)
        content.addWidget(self.font_list)
        
        # Right side - details
        details = QWidget()
        details_layout = QVBoxLayout()
        
        # Font info section
        info_group = QGroupBox("Font Information")
        info_layout = QFormLayout()
        
        self.name_label = QLabel()
        self.author_label = QLabel()
        self.description_label = QLabel()
        self.description_label.setWordWrap(True)
        self.usage_label = QLabel()
        self.source_label = QLabel()
        self.source_label.setOpenExternalLinks(True)
        
        info_layout.addRow("Name:", self.name_label)
        info_layout.addRow("Author:", self.author_label)
        info_layout.addRow("Description:", self.description_label)
        info_layout.addRow("Usage:", self.usage_label)
        info_layout.addRow("Source:", self.source_label)
        
        info_group.setLayout(info_layout)
        details_layout.addWidget(info_group)
        
        # License text section
        license_group = QGroupBox("License")
        license_layout = QVBoxLayout()
        self.license_text = QTextEdit()
        self.license_text.setReadOnly(True)
        license_layout.addWidget(self.license_text)
        license_group.setLayout(license_layout)
        details_layout.addWidget(license_group)
        
        details.setLayout(details_layout)
        content.addWidget(details)
        
        layout.addLayout(content)
        
        # Close button
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
