import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QPushButton, QFileDialog, QHeaderView
import sqlite3
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QValidator



class SANZoningApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # ... Existing code ...

        # Create a button to toggle colons in the WWPN column
        self.toggle_button = QPushButton("Toggle Colons")
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(True)
        self.toggle_button.clicked.connect(self.toggle_colons)

        # Create a validator for the WWPN column
        self.wwpn_validator = WWPNValidator()

        # Create a layout and add the table widget, import button, and toggle button
        layout = QVBoxLayout()
        layout.addWidget(self.table_widget)
        layout.addWidget(import_button)
        layout.addWidget(self.toggle_button)

        # Create a central widget and set the layout
        central_widget = QWidget()
        central_widget.setLayout(layout)

        # Set the central widget for the main window
        self.setCentralWidget(central_widget)

        # Load existing data from the database
        self.load_data()

    def toggle_colons(self):
        # Toggle the display of colons in the WWPN column
        if self.toggle_button.isChecked():
            self.table_widget.itemDelegateForColumn(2).setDisplayFormat(":")
        else:
            self.table_widget.itemDelegateForColumn(2).setDisplayFormat("")

    def load_data(self):
        # ... Existing code ...

        for row_number, row_data in enumerate(data):
            for column_number, column_data in enumerate(row_data[1:]):
                item = QTableWidgetItem(column_data)
                if column_number == 2:  # WWPN column
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Disable editing for WWPN
                    item.setValidator(self.wwpn_validator)  # Apply WWPN validator
                self.table_widget.setItem(row_number, column_number, item)


class WWPNValidator(QValidator):
    def validate(self, input_string, position):
        # Validate the format of the WWPN
        if ":" in input_string:
            # WWPN with colons
            valid, _ = self.validate_wwpn_with_colons(input_string)
        else:
            # WWPN without colons
            valid, _ = self.validate_wwpn_without_colons(input_string)

        if valid:
            return self.Acceptable, input_string, position
        else:
            return self.Invalid, input_string, position

    def validate_wwpn_with_colons(self, input_string):
        # Validate the format of the WWPN with colons
        # Example format: XX:XX:XX:XX:XX:XX:XX:XX
        # Implement your custom validation logic here
        # For simplicity, the code below assumes a valid WWPN with colons has 23 characters
        return len(input_string) == 23, input_string

    def validate_wwpn_without_colons(self, input_string):
        # Validate the format of the WWPN without colons
        # Example format: XXXXXXXXXXXXXXXX
        # Implement your custom validation logic here
        # For simplicity, the code below assumes a valid WWPN without colons has 16 characters
        return len(input_string) == 16, input_string

    def fixup(self, input_string):
        pass
        # Provide a suggestion for fixing an invalid WWPN
       



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SANZoningApp()
    window.show()
    sys.exit(app.exec_())
