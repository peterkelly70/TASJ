from __future__ import annotations

from typing import Callable, Iterable, List, Dict, Set, Tuple

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QCheckBox,
    QRadioButton,
    QButtonGroup,
    QGroupBox,
    QDialogButtonBox,
    QLineEdit,
)


class DownloadOptionsDialog(QDialog):
    """Dialog allowing the user to configure Traveller Map downloads."""

    def __init__(
        self,
        cached_sectors: Iterable[Dict[str, str]],
        sectors_with_data: Set[str],
        failed_sectors: Set[str],
        fetch_callback: Callable[[], List[Dict[str, str]]],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Download Traveller Map Data")

        screen = parent.screen() if parent and parent.screen() else QApplication.primaryScreen()
        if screen:
            available = screen.availableGeometry()
            suggested_width = min(900, int(available.width() * 0.75))
            suggested_height = min(700, int(available.height() * 0.75))
        else:
            suggested_width, suggested_height = 780, 600

        self.setMinimumSize(560, 420)
        self.resize(suggested_width, suggested_height)

        self._fetch_callback = fetch_callback
        self._sectors_with_data = sectors_with_data
        self._failed_sectors = failed_sectors
        self._cached_sectors = list(cached_sectors)
        self._selected_sector_names: List[str] = []
        self._skip_existing = True
        self._download_mode = "full"

        main_layout = QVBoxLayout(self)

        # Mode selection
        mode_group_box = QGroupBox("Download Scope")
        mode_layout = QVBoxLayout(mode_group_box)
        self.full_mode_radio = QRadioButton("Download entire Traveller universe")
        self.full_mode_radio.setChecked(True)
        self.sector_mode_radio = QRadioButton("Download specific sectors")

        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.full_mode_radio)
        self.mode_group.addButton(self.sector_mode_radio)

        mode_layout.addWidget(self.full_mode_radio)
        mode_layout.addWidget(self.sector_mode_radio)
        main_layout.addWidget(mode_group_box)

        # Sector selection area
        sector_section = QGroupBox("Available Sectors")
        sector_layout = QVBoxLayout(sector_section)
        instructions = QLabel(
            "Red entries indicate sectors that have not been downloaded yet or previously failed."
        )
        instructions.setWordWrap(True)
        sector_layout.addWidget(instructions)

        list_buttons_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter sectors…")
        self.search_input.textChanged.connect(self._apply_filter)
        list_buttons_layout.addWidget(self.search_input)

        self.refresh_button = QPushButton("Refresh list from API")
        self.refresh_button.clicked.connect(self._refresh_sector_list)
        list_buttons_layout.addWidget(self.refresh_button)
        sector_layout.addLayout(list_buttons_layout)

        self.sector_list = QListWidget()
        self.sector_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        sector_layout.addWidget(self.sector_list)

        main_layout.addWidget(sector_section)

        # Options
        self.skip_existing_checkbox = QCheckBox("Skip sectors already downloaded")
        self.skip_existing_checkbox.setChecked(True)
        main_layout.addWidget(self.skip_existing_checkbox)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        self._populate_sector_list(self._cached_sectors)
        self._all_items: List[QListWidgetItem] = [self.sector_list.item(i) for i in range(self.sector_list.count())]
        self.full_mode_radio.toggled.connect(self._update_mode_state)
        self._update_mode_state()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @property
    def download_mode(self) -> str:
        return "sector" if self.sector_mode_radio.isChecked() else "full"

    @property
    def selected_sectors(self) -> List[str]:
        if self.download_mode != "sector":
            return []
        selections = []
        for item in self.sector_list.selectedItems():
            payload = item.data(Qt.ItemDataRole.UserRole) or {}
            abbr = payload.get("abbreviation")
            name = payload.get("name")
            selections.append(abbr or name or item.text())
        return selections

    @property
    def skip_existing(self) -> bool:
        return self.skip_existing_checkbox.isChecked()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _refresh_sector_list(self) -> None:
        sectors = self._fetch_callback()
        if sectors:
            self._cached_sectors = sectors
            self._populate_sector_list(sectors)

    def _populate_sector_list(self, sectors: Iterable[Dict[str, str]]) -> None:
        self.sector_list.clear()
        for entry in sectors:
            name, abbreviation, label, key_tokens = self._derive_sector_identity(entry)

            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, {
                "name": name,
                "abbreviation": abbreviation,
            })

            downloaded = any(token in self._sectors_with_data for token in key_tokens)
            failed = any(token in self._failed_sectors for token in key_tokens)

            if downloaded:
                item.setForeground(QBrush(QColor("darkgreen")))
            else:
                item.setForeground(QBrush(QColor("red")))

            if failed:
                item.setBackground(QBrush(QColor("#ffe6e6")))

            self.sector_list.addItem(item)

        if self.sector_list.count() > 0:
            self.sector_list.setCurrentRow(0)
        self._all_items = [self.sector_list.item(i) for i in range(self.sector_list.count())]
        self._apply_filter(self.search_input.text())

    def _update_mode_state(self) -> None:
        sector_mode = self.sector_mode_radio.isChecked()
        self.sector_list.setEnabled(sector_mode)
        self.refresh_button.setEnabled(sector_mode)
        self.search_input.setEnabled(sector_mode)

    def _apply_filter(self, text: str) -> None:
        text = (text or "").strip().lower()
        for item in self._all_items:
            should_show = True
            if text:
                payload = item.data(Qt.ItemDataRole.UserRole) or {}
                name = (payload.get("name") or "").lower()
                abbr = (payload.get("abbreviation") or "").lower()
                label = item.text().lower()
                should_show = any(
                    text in candidate
                    for candidate in (label, name, abbr)
                    if candidate
                )
            item.setHidden(not should_show)

    def _derive_sector_identity(self, entry: Dict[str, str]) -> Tuple[str, str, str, Set[str]]:
        name = entry.get("Name") or entry.get("name")
        if not name:
            names = entry.get("Names")
            if isinstance(names, list):
                for candidate in names:
                    text = candidate.get("Text") if isinstance(candidate, dict) else None
                    if text:
                        name = text
                        break
        abbreviation = entry.get("Abbreviation") or entry.get("abbr")
        if not name and abbreviation:
            name = abbreviation
        if not name:
            name = "Unknown"
        label = name
        if abbreviation and abbreviation.lower() != name.lower():
            label = f"{name} ({abbreviation})"
        key_tokens = {token.lower() for token in (name, abbreviation) if token}
        return name, abbreviation or "", label, key_tokens
