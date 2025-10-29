from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QTextEdit,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
)


class AdventureHooksView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QHBoxLayout(self)

        left_layout = QVBoxLayout()

        filters_layout = QHBoxLayout()

        self.sector_combo = QComboBox()
        self.sector_combo.addItem("Any Sector", userData=None)
        filters_layout.addWidget(QLabel("Sector:"))
        filters_layout.addWidget(self.sector_combo)

        self.system_combo = QComboBox()
        self.system_combo.addItem("Any System", userData=None)
        filters_layout.addWidget(QLabel("System:"))
        filters_layout.addWidget(self.system_combo)

        self.planet_combo = QComboBox()
        self.planet_combo.addItem("Any World", userData=None)
        filters_layout.addWidget(QLabel("Planet:"))
        filters_layout.addWidget(self.planet_combo)

        left_layout.addLayout(filters_layout)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Adventure Title")
        left_layout.addWidget(self.title_edit)

        controls_layout = QHBoxLayout()
        self.generate_button = QPushButton("Generate Adventure Hook")
        controls_layout.addWidget(self.generate_button)
        self.enhance_button = QPushButton("Enhance via ChatGPT")
        controls_layout.addWidget(self.enhance_button)
        self.save_button = QPushButton("Save/Update")
        controls_layout.addWidget(self.save_button)
        self.delete_button = QPushButton("Delete")
        self.delete_button.setEnabled(False)
        controls_layout.addWidget(self.delete_button)
        controls_layout.addStretch()
        left_layout.addLayout(controls_layout)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        left_layout.addWidget(self.output)

        main_layout.addLayout(left_layout, stretch=3)

        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Saved Adventure Hooks"))
        self.saved_hooks_list = QListWidget()
        right_layout.addWidget(self.saved_hooks_list)
        main_layout.addLayout(right_layout, stretch=1)

        self.setLayout(main_layout)
