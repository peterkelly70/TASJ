# view/sql_query_view.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QTextEdit, QPushButton

class SQLQueryView(QDialog):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("SQL Query")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # List of tables
        table_label = QLabel("Select Table:")
        layout.addWidget(table_label)

        self.table_combo = QComboBox()
        tables = self.controller.get_table_names()
        self.table_combo.addItems(tables)
        layout.addWidget(self.table_combo)

        # SQL Query input
        query_label = QLabel("SQL Query:")
        layout.addWidget(query_label)

        self.sql_input = QTextEdit()
        layout.addWidget(self.sql_input)

        # Run Query button
        run_button = QPushButton("Run Query")
        layout.addWidget(run_button)

        # Output area for query results
        self.results_output = QTextEdit()
        self.results_output.setReadOnly(True)
        layout.addWidget(self.results_output)

        # Connect the button to execute the query
        run_button.clicked.connect(self.execute_query)

        self.setLayout(layout)

    def execute_query(self):
        query = self.sql_input.toPlainText()
        results = self.controller.run_query(query)
        self.results_output.setText(str(results))
