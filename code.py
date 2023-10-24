import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QTableWidget,
                             QTableWidgetItem, QLabel, QHeaderView, QDialog,
                             QTextEdit, QPushButton, QInputDialog, QHBoxLayout, QListWidget, QAbstractItemView, QAction, QScrollArea, QCheckBox, QGroupBox, QRadioButton, QGridLayout, QLineEdit)
from PyQt5.QtWidgets import QMenu, QApplication
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QSettings
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QMessageBox, QFileDialog
import os
import re
from PyQt5.QtGui import QIcon
import requests
import json
from datetime import datetime
import pytz
from time import sleep
import shutil
import re
import sys
import socket
import json
import os
import platform
import winreg
import hashlib
from PyQt5.QtGui import QColor

class PopupWindow(QDialog):
    def __init__(self, data, parent=None):
        super(PopupWindow, self).__init__(parent)
        self.setWindowTitle("Inventory")

        layout = QVBoxLayout()

        self.text_edit = QTextEdit(self)
        self.text_edit.setPlainText(data)
        self.text_edit.setReadOnly(True)

        self.close_btn = QPushButton("Đóng", self)
        self.close_btn.clicked.connect(self.close)

        layout.addWidget(self.text_edit)
        layout.addWidget(self.close_btn)

        self.setLayout(layout)


class ImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Account")

        layout = QVBoxLayout()

        self.text_edit = QTextEdit(self)
        layout.addWidget(self.text_edit)

        btn_layout = QHBoxLayout()
        self.import_file_btn = QPushButton("Import From File", self)
        self.import_file_btn.clicked.connect(self.import_from_file)
        btn_layout.addWidget(self.import_file_btn)

        self.save_btn = QPushButton("Save", self)
        self.save_btn.clicked.connect(self.save_account)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def import_from_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "", "All Files (*);;Text Files (*.txt)", options=options)
        if file_name:
            with open(file_name, 'r') as file:
                self.text_edit.setText(file.read())

    def save_account(self):
        new_accounts = self.text_edit.toPlainText().strip().split('\n')  # Tách các tài khoản bằng dòng mới

        if not new_accounts:
            return  # Nếu không có dữ liệu, không làm gì cả

        # Đọc tất cả dữ liệu hiện có từ tệp
        with open("accounts.data", "r") as file:
            lines = file.readlines()

        for new_account_data in new_accounts:
            try:
                username_new, password_new, cookie_new = new_account_data.split(':', 2)
            except ValueError:
                # Bỏ qua tài khoản nếu nó không đúng định dạng
                continue

            updated = False  # Biến để kiểm tra xem chúng ta có cập nhật dữ liệu hay không
            for i, line in enumerate(lines):
                if line.strip():  # Kiểm tra xem dòng không trống
                    username_existing, *_ = line.strip().split(':')  # Lấy tên người dùng từ dòng hiện tại
                    if username_existing == username_new:
                        lines[i] = f"{username_new}:{password_new}:{cookie_new}\n"  # Cập nhật dòng với dữ liệu mới nhập
                        updated = True
                        break

            # Nếu chưa cập nhật, thêm dữ liệu mới vào cuối tệp
            if not updated:
                lines.append(f"{username_new}:{password_new}:{cookie_new}\n")

        # Ghi lại nội dung vào tệp
        with open("accounts.data", "w") as file:
            for line in lines:
                file.write(line)

        self.accept()





class App(QWidget):

    def __init__(self):
        super().__init__()
        self.resize(1130, 600)  # Thay đổi các giá trị kích thước theo ý muốn
        self.allowed_players = self.load_allowed_users()
        self.selected_rows = set()  # Tập hợp lưu trữ các chỉ số dòng được chọn
        # Tải delay từ Config.ini
        self.settings = QSettings("Config.ini", QSettings.IniFormat)
        delay = self.settings.value("delay", 10, int)  # Nếu không tìm thấy trong Config.ini thì mặc định là 10 giây
        self.online_timer_active = True

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.load_data)
        self.timer.start(delay * 1000)  # QTimer hoạt động dựa trên mili giây
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.load_online)
        self.timer.start(60000)  # QTimer hoạt động dựa trên mili giây
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Trackstats-HV - Himve✨#9017 for paid')
        icon_path = os.path.join(os.path.dirname(__file__), "removal.ico")
        app_icon = QIcon(icon_path)  # Sử dụng đường dẫn tương đối
        self.setWindowIcon(app_icon)
        layout = QVBoxLayout()
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        
        self.tableWidget = QTableWidget(self)
        self.tableWidget.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tableWidget.horizontalHeader().setSectionsMovable(False)
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(14)
        self.resize_timer = QTimer(self)
        self.resize_timer.timeout.connect(self.autoscale_columns)
        self.resize_timer.start(5000)  # 20 giây


        font = QFont()
        font.setBold(True)
        header = self.tableWidget.horizontalHeader()
        header.setFont(font)
        header.setDefaultAlignment(Qt.AlignCenter)

        self.tableWidget.setHorizontalHeaderLabels(['Player Name', 'Level', 'Beli / Frag 💲', 'Race 🐺', 'Bounty 📌', 'AwakenSkill', 'Melee', 'CDK', 'SoulGuitar', 'Fruit🍎', 'Materials', 'Accessory', 'Mảnh Mũ', 'Status'])

        layout.addWidget(QLabel('Danh Sách Accounts:'))
        layout.addWidget(self.tableWidget)




        # Thiết kế CSS cho nút
        button_style = """
        QPushButton {
            border: 2px solid black;
            border-radius: 10px;
            padding: 5px;
            background-color: white;
        }
        QPushButton:hover {
            background-color: #ddd;
        }
        """

        # Các nút bạn muốn thêm
        self.update_btn = QPushButton("Delay Setting", self)
        self.import_btn = QPushButton("Import Account", self)
        self.delete_btn = QPushButton("Delete Row", self)
        self.add_script_btn = QPushButton("Script Manager", self)
        self.export_data_btn = QPushButton("Lọc Accounts", self)
        self.disable_status_btn = QPushButton("Stop Timer", self)
        # Kết nối các sự kiện và thiết lập kích thước, kiểu
        buttons = [self.update_btn, self.import_btn, self.delete_btn, self.add_script_btn, self.export_data_btn, self.disable_status_btn,]
        for btn in buttons:
            btn.setStyleSheet(button_style)
            btn.setFixedSize(120, 30)



        # Kết nối sự kiện (giả sử bạn đã có các hàm kết nối trước đây)
        self.update_btn.clicked.connect(self.update_data)
        self.import_btn.clicked.connect(self.show_import_dialog)
        self.delete_btn.clicked.connect(self.delete_selected_row)
        self.add_script_btn.clicked.connect(self.add_script_dialog)
        self.export_data_btn.clicked.connect(self.show_export_dialog)
        self.disable_status_btn.clicked.connect(self.toggle_timer)
        # Sắp xếp các nút ngang nhau
        button_layout = QHBoxLayout()
        for btn in buttons:
            button_layout.addWidget(btn)
            button_layout.addSpacing(10)  # Thêm khoảng cách giữa các nút
        layout.addLayout(button_layout)  # Thêm layout của nút vào layout chính


        self.load_data()
        self.tableWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableWidget.customContextMenuRequested.connect(self.showContextMenu)
        self.tableWidget.resizeColumnsToContents()

        self.tableWidget.cellClicked.connect(self.handleCellClicked)
        self.setLayout(layout)




    def toggle_timer(self):
        if self.online_timer_active:
            self.timer.stop()
            self.disable_status_btn.setText("Start Timer")
        else:
            self.timer.start(60000)
            self.disable_status_btn.setText("Stop Timer")
        self.online_timer_active = not self.online_timer_active



#---------------------------------------------------------------------------------------------------------#


    def show_export_dialog(self):
        # Create a new dialog with checkboxes and radio buttons
        dialog = QDialog(self)
        dialog.setWindowTitle("Chọn các loại bạn muốn xuất ra:")
        dialog.resize(800, 600)  # Resize to fit all options

        layout = QVBoxLayout()
        grid_layout = QGridLayout()  # New layout for checkboxes

        # Checkboxes for Melee types, grouped by column
        column_groups = {
            "Godhuman": ["Godhuman", "Godhuman_ManhMu", "Godhuman_CDK", "Godhuman_CDK-ManhMu", 
                        "Godhuman_SG", "Godhuman_SG-ManhMu", "Godhuman_CDK_SG_ManhMu", "Godhuman_CDK_SG"],
            "CDK_SG": ["CDK_SG", "CDK_SG_ManhMu"],
            "SG": ["SG", "SG_ManhMU"],
            "CDK": ["CDK", "CDK_ManhMU"],
            "3-5 Melee": ["Melee_3-5", "Melee_3-5_ManhMu", "3-5_CDK", "3-5_CDK_ManhMu", 
                        "3-5_SG", "3-5_SG_ManhMu", "3-5_CDK_SG_ManhMu", "3-5_CDK_SG"],
        }

        melee_checkboxes = {}
        for col, options in enumerate(column_groups.values()):
            for row, option in enumerate(options):
                checkbox = QCheckBox(option, dialog)
                grid_layout.addWidget(checkbox, row, col)  # Place checkbox in the grid
                melee_checkboxes[option] = checkbox

        layout.addLayout(grid_layout)  # Add the grid layout to the main layout

        # Radio buttons for export format
        format_group = QGroupBox("Format", dialog)
        format_layout = QVBoxLayout()
        username_password_radio = QRadioButton("Username:Password", dialog)
        username_password_cookie_radio = QRadioButton("Username:Password:Cookie", dialog)
        username_password_radio.setChecked(True)
        format_layout.addWidget(username_password_radio)
        format_layout.addWidget(username_password_cookie_radio)
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)

        # OK button to confirm selection
        ok_button = QPushButton("Export", dialog)
        ok_button.clicked.connect(lambda: self.export_selected_data(melee_checkboxes, username_password_radio.isChecked(), username_password_cookie_radio.isChecked()))
        layout.addWidget(ok_button)

        dialog.setLayout(layout)
        dialog.exec_()


    def export_selected_data(self, melee_checkboxes, is_username_password, is_username_password_cookie):
        # This dictionary will store extracted data for each Melee type
        data_per_melee = {}

        # Extract data based on selected Melee types
        for melee_option, checkbox in melee_checkboxes.items():
            if checkbox.isChecked():
                matching_usernames = self.get_matching_usernames_fully_updated(melee_option)
                extracted_data = self.get_extracted_data(matching_usernames, is_username_password, is_username_password_cookie)
                if extracted_data:
                    data_per_melee[melee_option] = extracted_data

        # Save data to respective files or folders
        for melee_option, extracted_data in data_per_melee.items():
            with open(f"{melee_option}.Filter", "w", encoding="utf-8") as output_file:
                output_file.write("\n".join(extracted_data))

        QMessageBox.information(self, "Export Data", "Data exported successfully!")

    def get_matching_usernames_fully_updated(self, option):
        matching_usernames = []

        for row in range(self.tableWidget.rowCount()):
            # Extract the necessary rows
            melee_value = self.tableWidget.item(row, 6).text()
            row7_value = self.tableWidget.item(row, 7).text()
            row8_value = self.tableWidget.item(row, 8).text()
            row12_value = self.tableWidget.item(row, 12).text()

            # Check conditions based on the selected option
            conditions = [
                (option == "Godhuman" and melee_value == "Godhuman" and all([val == "❌" for val in [row7_value, row8_value, row12_value]])),
                (option == "Godhuman_ManhMu" and melee_value == "Godhuman" and row7_value == "❌" and row8_value == "❌" and row12_value == "✅"),
                (option == "Godhuman_CDK" and melee_value == "Godhuman" and row7_value == "✅" and row8_value == "❌" and row12_value == "❌"),
                (option == "Godhuman_CDK-ManhMu" and melee_value == "Godhuman" and row7_value == "✅" and row8_value == "❌" and row12_value == "✅"),
                (option == "Godhuman_SG" and melee_value == "Godhuman" and row7_value == "❌" and row8_value == "✅" and row12_value == "❌"),
                (option == "Godhuman_SG-ManhMu" and melee_value == "Godhuman" and row7_value == "❌" and row8_value == "✅" and row12_value == "✅"),
                (option == "Godhuman_CDK_SG_ManhMu" and melee_value == "Godhuman" and row7_value == "✅" and row8_value == "✅" and row12_value == "✅"),
                (option == "Godhuman_CDK_SG" and melee_value == "Godhuman" and row7_value == "✅" and row8_value == "✅" and row12_value == "❌"),
                (option == "CDK_SG" and row7_value == "✅" and row8_value == "✅" and melee_value != "Godhuman" and melee_value != "3-5 Melee" and row12_value == "❌"),
                (option == "CDK_SG_ManhMu" and row7_value == "✅" and row8_value == "✅" and row12_value == "✅" and melee_value != "Godhuman" and melee_value != "3-5 Melee"),
                (option == "CDK" and row7_value == "✅" and melee_value != "Godhuman" and melee_value != "3-5 Melee" and row8_value == "❌" and row12_value == "❌"),
                (option == "CDK_ManhMU" and row7_value == "✅" and row8_value == "❌" and row12_value == "✅" and melee_value != "Godhuman" and melee_value != "3-5 Melee"),
                (option == "SG" and row8_value == "✅" and melee_value != "Godhuman" and melee_value != "3-5 Melee" and row7_value == "❌" and row12_value == "❌"),
                (option == "SG_ManhMU" and row8_value == "✅" and row7_value == "❌" and row12_value == "✅" and melee_value != "Godhuman" and melee_value != "3-5 Melee"),
                (option == "Melee_3-5" and melee_value == "3-5 Melee" and all([val == "❌" for val in [row7_value, row8_value, row12_value]])),
                (option == "Melee_3-5_ManhMu" and melee_value == "3-5 Melee" and row7_value == "❌" and row8_value == "❌" and row12_value == "✅"),
                (option == "3-5_CDK" and melee_value == "3-5 Melee" and row7_value == "✅" and row8_value == "❌" and row12_value == "❌"),
                (option == "3-5_CDK_ManhMu" and melee_value == "3-5 Melee" and row7_value == "✅" and row8_value == "❌" and row12_value == "✅"),
                (option == "3-5_SG" and melee_value == "3-5 Melee" and row7_value == "❌" and row8_value == "✅" and row12_value == "❌"),
                (option == "3-5_SG_ManhMu" and melee_value == "3-5 Melee" and row7_value == "❌" and row8_value == "✅" and row12_value == "✅"),
                (option == "3-5_CDK_SG_ManhMu" and melee_value == "3-5 Melee" and row7_value == "✅" and row8_value == "✅" and row12_value == "✅"),
                (option == "3-5_CDK_SG" and melee_value == "3-5 Melee" and row7_value == "✅" and row8_value == "✅" and row12_value == "❌"),
            ]

            if any(conditions):
                matching_usernames.append(self.tableWidget.item(row, 0).text())

        return matching_usernames


    def get_extracted_data(self, matching_usernames, is_username_password, is_username_password_cookie):
        extracted_data = []
        with open("accounts.data", "r", encoding="utf-8") as file:
            for account in file.readlines():
                username, password, cookie = account.strip().split(":", 2)
                if username in matching_usernames:
                    if is_username_password:
                        extracted_data.append(f"{username}:{password}")
                    elif is_username_password_cookie:
                        extracted_data.append(f"{username}:{password}:{cookie}")
        return extracted_data
    
#---------------------------------------------------------------------------------

    def update_folder_list(self):
        base_dir = os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'Packages')
        
        roblox_folders = [f for f in os.listdir(base_dir) if re.match(r'^ROBLOXCORPORATION.', f)]

        def extract_number(folder_name):
            match = re.search(r'ROBLOXCORPORATION\..*\.(\d+)_', folder_name)
            return int(match.group(1)) if match else 0

        roblox_folders.sort(key=extract_number)

        # Check if 'HV-TOOL.lua' exists in the 'autoexec' folder and update folder names accordingly
        for i in range(len(roblox_folders)):
            target_file_path = os.path.join(base_dir, roblox_folders[i], "AC", "autoexec", "HV-TOOL.lua")
            if os.path.exists(target_file_path):
                roblox_folders[i] += " | Ready"

        self.list_widget.clear()
        self.list_widget.addItems(roblox_folders)


    def add_script_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Script")
        dialog.resize(500, 500)

        layout = QVBoxLayout()

        # List widget
        self.list_widget = QListWidget(dialog)
        self.list_widget.setSelectionMode(QAbstractItemView.MultiSelection)
        base_dir = os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'Packages')
        roblox_folders = [f for f in os.listdir(base_dir) if f.startswith('ROBLOXCORPORATION.')]

        # Extract the number part and sort based on it
        def extract_number(folder_name):
            match = re.search(r'ROBLOXCORPORATION.(\d+)_', folder_name)
            return int(match.group(1)) if match else 0

        roblox_folders.sort(key=extract_number)

        # Check if 'HV-TOOL.lua' exists in the 'autoexec' folder and update folder names accordingly
        for i in range(len(roblox_folders)):
            target_file_path = os.path.join(base_dir, roblox_folders[i], "AC", "autoexec", "HV-TOOL.lua")
            if os.path.exists(target_file_path):
                roblox_folders[i] += " | Ready"

        self.list_widget.addItems(roblox_folders)
        layout.addWidget(self.list_widget)

        # Buttons
        add_selected_btn = QPushButton("Add Selected", dialog)
        add_selected_btn.clicked.connect(self.add_selected_script)
        layout.addWidget(add_selected_btn)

        add_all_btn = QPushButton("Add All", dialog)
        add_all_btn.clicked.connect(self.add_all_scripts)
        layout.addWidget(add_all_btn)
        delete_selected_btn = QPushButton("Delete from Selected", dialog)
        delete_selected_btn.clicked.connect(self.delete_selected_scripts)
        layout.addWidget(delete_selected_btn)

        # Button to delete script from all folders
        delete_all_btn = QPushButton("Delete from All", dialog)
        delete_all_btn.clicked.connect(self.delete_all_scripts)
        layout.addWidget(delete_all_btn)


        dialog.setLayout(layout)
        dialog.exec_()

    def add_selected_script(self):
        selected_folders = [item.text() for item in self.list_widget.selectedItems()]
        base_dir = os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'Packages')
        
        success_count = 0
        for folder in selected_folders:
            if self.copy_script_to_folder(base_dir, folder):
                success_count += 1

        QMessageBox.information(self, "Result", f"Added script to {success_count}/{len(selected_folders)} selected folders successfully!")
        self.update_folder_list()

    def add_all_scripts(self):
        base_dir = os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'Packages')
        roblox_folders = [f for f in os.listdir(base_dir) if f.startswith('ROBLOXCORPORATION.')]

        success_count = 0
        for folder in roblox_folders:
            if self.copy_script_to_folder(base_dir, folder):
                success_count += 1

        QMessageBox.information(self, "Result", f"Added script to {success_count}/{len(roblox_folders)} total folders successfully!")
        self.update_folder_list()

    def copy_script_to_folder(self, base_dir, folder_name):
        # Check if the script is running as a packaged executable
        if getattr(sys, 'frozen', False):
            current_dir = os.path.dirname(sys.executable)
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Look for the HV-TOOL.lua script in the "script" subdirectory of the current directory
        script_path = os.path.join(current_dir, "script", "HV-TOOL.lua")
        
        target_folder_path = os.path.join(base_dir, folder_name, "AC", "autoexec")
        
        # Check and create the autoexec folder if it doesn't exist
        if not os.path.exists(target_folder_path):
            os.makedirs(target_folder_path)

        target_file_path = os.path.join(target_folder_path, "HV-TOOL.lua")
        
        if os.path.exists(target_file_path):
            return False  # File already exists, don't copy

        # Copy the script file
        shutil.copy2(script_path, target_file_path)
        return True  # File was successfully copied
    
    def delete_all_scripts(self):
        base_dir = os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'Packages')
        roblox_folders = [f for f in os.listdir(base_dir) if f.startswith('ROBLOXCORPORATION.')]

        success_count = 0
        for folder in roblox_folders:
            if self.delete_script_from_folder(base_dir, folder):
                success_count += 1

        QMessageBox.information(self, "Result", f"Deleted script from {success_count}/{len(roblox_folders)} total folders successfully!")
        self.update_folder_list()

    def delete_selected_scripts(self):
        selected_folders = [item.text() for item in self.list_widget.selectedItems()]
        base_dir = os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'Packages')
        
        success_count = 0
        for folder in selected_folders:
            if self.delete_script_from_folder(base_dir, folder):
                success_count += 1

        QMessageBox.information(self, "Result", f"Deleted script from {success_count}/{len(selected_folders)} selected folders successfully!")
        self.update_folder_list()

    def delete_script_from_folder(self, base_dir, folder_name):
        target_file_path = os.path.join(base_dir, folder_name, "AC", "autoexec", "HV-TOOL.lua")
        
        # Kiểm tra xem file script có tồn tại không
        if not os.path.exists(target_file_path):
            return False  # File không tồn tại, không thể xóa

        # Xóa file script
        os.remove(target_file_path)
        return True  # File được xóa thành công

    def showContextMenu(self, position):
        # Lấy các dòng đã được chọn
        selected_rows = list({index.row() for index in self.tableWidget.selectedIndexes()})
        
        # Kiểm tra nếu không có dòng nào được chọn thì không làm gì
        if not selected_rows:
            return

        # Tạo menu và các tùy chọn
        contextMenu = QMenu(self)
        copyUsernameAction = contextMenu.addAction("Copy Username")
        copyPasswordAction = contextMenu.addAction("Copy Password")
        copyCookieAction = contextMenu.addAction("Copy Cookie")
        copyUserPassAction = contextMenu.addAction("Copy Username:Password")
        copyFullAction = contextMenu.addAction("Copy Username:Password:Cookie")

        # Kết nối sự kiện khi chọn một tùy chọn
        copyUsernameAction.triggered.connect(lambda: self.copy_data(selected_rows, "username"))
        copyPasswordAction.triggered.connect(lambda: self.copy_data(selected_rows, "password"))
        copyCookieAction.triggered.connect(lambda: self.copy_data(selected_rows, "cookie"))
        copyUserPassAction.triggered.connect(lambda: self.copy_data(selected_rows, "userpass"))
        copyFullAction.triggered.connect(lambda: self.copy_data(selected_rows, "full"))
        
        # Hiển thị menu
        contextMenu.exec_(self.tableWidget.viewport().mapToGlobal(position))

    def copy_data(self, selected_rows, data_type):
        clipboard = QApplication.clipboard()
        data_to_copy = []
        
        if os.path.exists("accounts.data"):
            with open("accounts.data", "r") as file:
                accounts = {account.split(':', 2)[0]: account.strip().split(':', 2)[1:] for account in file.readlines()}
                
            for row in selected_rows:
                username = self.tableWidget.item(row, 0).text()
                
                if username in accounts:
                    password, cookie = accounts[username]
                    if data_type == "username":
                        data_to_copy.append(username)
                    elif data_type == "password":
                        data_to_copy.append(password)
                    elif data_type == "cookie":
                        data_to_copy.append(cookie)
                    elif data_type == "userpass":
                        data_to_copy.append(f"{username}:{password}")
                    elif data_type == "full":
                        data_to_copy.append(f"{username}:{password}:{cookie}")

        clipboard.setText("\n".join(data_to_copy))

    def autoscale_columns(self):
        self.tableWidget.resizeColumnsToContents()

    def show_import_dialog(self):
        dialog = ImportDialog(self)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            # Tải lại dữ liệu từ file (hoặc thực hiện bất kỳ thao tác nào bạn muốn khi dữ liệu được nhập)
            self.load_data()    

    def handleCellClicked(self, row, column):
        if column in [9, 10, 11]:  # Fruit, Materials, and Accessory
            data = self.tableWidget.item(row, column).data(Qt.UserRole)
            if data:
                if column == 9:  # Fruit column
                    tiered_data = self.organize_fruits_by_tier(data)
                else:
                    tiered_data = data
                popup = PopupWindow(tiered_data, self)
                popup.exec_()
        if column == 0:
            # Kiểm tra xem dòng đã được chọn trước đó chưa
            if row in self.selected_rows:
                self.selected_rows.remove(row)  # Nếu đã chọn rồi, thì bỏ chọn
            else:
                self.selected_rows.add(row)  # Nếu chưa chọn, thì thêm vào tập hợp

    
    def delete_selected_row(self):
        # Xóa các dòng được chọn khỏi giao diện và cập nhật file
        if self.selected_rows:
            player_names_to_delete = set()

            for row in self.selected_rows:
                player_name = self.tableWidget.item(row, 0).text()
                player_names_to_delete.add(player_name)

            # Cập nhật file accounts.data
            with open("accounts.data", "r") as file:
                accounts = file.readlines()

            # Xóa account tương ứng từ danh sách
            updated_accounts = [account for account in accounts if not any(name in account for name in player_names_to_delete)]

            with open("accounts.data", "w") as file:
                file.writelines(updated_accounts)

            # Xóa các dòng khỏi QTableWidget
            for row in sorted(self.selected_rows, reverse=True):
                self.tableWidget.removeRow(row)

            self.selected_rows.clear()  # Xóa tất cả các dòng được chọn sau khi xóa


    

    def organize_fruits_by_tier(self, fruit_data):
        tiers = {
            'Legend': ['Leopard', 'Dragon', 'Venom', 'Rumble', 'Budda', 'Spider', 'Dough', 'Shadow', 'Soul', 'Dark', 'Blizzard'],
            'Epic': ['Phoenix', 'Rumble', 'Control', 'Light', 'Magma', 'Flame', 'Quake', 'String', 'Barrier'],
            'Rare': ['Ice', 'Sand', 'Paw', 'Door', 'Gravity Revive', 'Diamond'],
            'Medium': ['Love', 'Rubber', 'Spring', 'Smoke', 'Falcon'],
            'Common': ['Spin', 'Spike', 'Kilo', 'Chop', 'Bomb']
        }

        organized_data = ''
        for tier, fruits in tiers.items():
            matched_fruits = [fruit for fruit in fruits if fruit in fruit_data]
            if matched_fruits:
                organized_data += f"Tier {tier}: " + ', '.join(matched_fruits) + '\n'

        return organized_data

    def find_row_by_player_name(self, player_name):
        for row in range(self.tableWidget.rowCount()):
            item = self.tableWidget.item(row, 0)  # Assuming Player Name is in column 0
            if item and item.text() == player_name:
                return row
        return None
    
    def extract_materials(self, content):
        match = re.search(r"Materials\(s\):([\s\S]*?)(?=\w+\(s\):|$)", content)
        if match:
            materials_content = match.group(1).strip()
            # Loại bỏ khoảng trắng đầu mỗi dòng
            cleaned_content = '\n'.join(line.strip() for line in materials_content.split('\n'))
            return cleaned_content
        return ""




    def load_allowed_users(self):
        with open("accounts.data", "r") as file:
            lines = file.readlines()
        usernames = [line.split(":")[0] for line in lines if ":" in line]
        return usernames

    def load_online(self):
        # API endpoints for querying player information and checking game status
        users_api_url = 'https://users.roblox.com/v1/usernames/users'
        presence_api_url = 'https://presence.roblox.com/v1/presence/users'
        exclude_banned_users = True

        headers = {
            'Content-Type': 'application/json'
        }
        
        def get_usernames_from_file():
            usernames = []

            # Check if the file exists
            if not os.path.exists('accounts.data'):
                return usernames  # Return an empty list if the file doesn't exist

            with open('accounts.data', 'r') as file:
                for line in file:
                    parts = line.strip().split(':')
                    if len(parts) >= 1:
                        username = parts[0]
                        usernames.append(username)
            return usernames


        usernames = get_usernames_from_file()
        if not usernames:  # Check if the list is empty
            return



        def elapsed_time_str(last_online):
            vietnam_timezone = pytz.timezone('Asia/Ho_Chi_Minh')
            last_online_datetime = datetime.strptime(last_online, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.utc)
            last_online_vietnam = last_online_datetime.astimezone(vietnam_timezone)
            current_time = datetime.now(vietnam_timezone)           
            time_elapsed = current_time - last_online_vietnam

            seconds_elapsed = time_elapsed.total_seconds()
            if seconds_elapsed < 60:
                return f"{int(seconds_elapsed)} giây"
            elif seconds_elapsed < 3600:
                return f"{int(seconds_elapsed / 60)} phút"
            elif seconds_elapsed < 24 * 3600:
                return f"{int(seconds_elapsed / 3600)} giờ"
            elif seconds_elapsed < 30 * 24 * 3600:
                return f"{int(seconds_elapsed / (24 * 3600))} ngày"
            elif seconds_elapsed < 360 * 24 * 3600:
                return f"{int(seconds_elapsed / (30 * 24 * 3600))} tháng"
            else:
                return f"{int(seconds_elapsed / (365 * 24 * 3600))} năm"

        usernames = get_usernames_from_file()

        users_request_data = {
            "usernames": usernames,
            "excludeBannedUsers": exclude_banned_users
        }

        response = requests.post(users_api_url, data=json.dumps(users_request_data), headers=headers)
        results = []

        if response.status_code == 200:
            data = response.json()
            user_ids = [user['id'] for user in data['data']]
            
            presence_request_data = {
                "userIds": user_ids
            }
            presence_response = requests.post(presence_api_url, headers=headers, data=json.dumps(presence_request_data))
            
            if presence_response.status_code == 200:
                presence_data = presence_response.json()
                for user_presence in presence_data.get('userPresences', []):
                    user_id = user_presence.get('userId')
                    user_name = next((user['name'] for user in data['data'] if user['id'] == user_id), "Loading...❕")
                    user_presence_type = user_presence.get('userPresenceType')
                    last_online = user_presence.get('lastOnline')

                    if user_presence_type == 2:
                        results.append(f"{user_name}:Playing Blox Fruit  🟢")
                    else:
                        elapsed_str = elapsed_time_str(last_online)
                        results.append(f"{user_name}:Disconnect {elapsed_str} Trước 🔴")
            else:
                results.append(f"Yêu cầu presence không thành công. Mã trạng thái: {presence_response.status_code}")
        else:
            results.append(f"Lỗi khi gửi yêu cầu usernames. Mã lỗi: {response.status_code}")

        # Write results to a file
        with open('OnlineCheck.data', 'w', encoding='utf-8') as file:
            for result in results:
                file.write(result + '\n')

    def load_online_statuses(self):
        status_dict = {}
        try:
            with open("OnlineCheck.data", "r", encoding="utf-8") as file:
                lines = file.readlines()
                for line in lines:
                    parts = line.split(":")
                    if len(parts) > 1:
                        username = parts[0].strip()
                        status = ":".join(parts[1:]).strip()
                        status_dict[username] = status
        except FileNotFoundError:
            pass
        return status_dict

    def check_helm_fragment(self, accessory_content, materials_content):
        if "Valkyrie Helm" in accessory_content:
            mirror_fractal_match = re.search(r"Mirror Fractal:\s*(\d+)", materials_content)
            if mirror_fractal_match and int(mirror_fractal_match.group(1)) >= 1:
                return "✅"
        return "❌"




    def load_data(self):
        self.allowed_players = self.load_allowed_users()
        online_statuses = self.load_online_statuses()
        processed_usernames = []  # Danh sách chứa tất cả username đã được xử lý

        base_dir = os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'Packages')

        melee_options = ['Superhuman', 'ElectricClaw', 'DragonTalon', 'SharkmanKarate', 'DeathStep', 'Godhuman']

        # Existing players with valid data.yummybeo files
        existing_players_with_data = []

        for folder_name in os.listdir(base_dir):
            if folder_name.startswith('ROBLOXCORPORATION.'):
                ac_dir = os.path.join(base_dir, folder_name, 'AC')

                if os.path.exists(ac_dir):
                    workspace_dir = os.path.join(ac_dir, 'workspace')
                    if os.path.exists(workspace_dir):
                        file_path = os.path.join(workspace_dir, 'data.yummybeo')
                        if os.path.exists(file_path):
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                player_name = self.extract_value(r"Player Name\s*:\s*([^\n]+)", content)
                                if player_name not in self.allowed_players:
                                    continue
                                existing_players_with_data.append(player_name)    
                                                    
                                level = self.extract_value(r"Level\s*:\s*([^\n]+)", content)
                                beli = self.extract_value(r"Beli\s*:\s*([^\n]+)", content)
                                fragment = self.extract_value(r"Frag\s*:\s*([^\n]+)", content)
                                bounty = self.extract_value(r"Bounty/Honor:\s*([^\n]+)", content)
                                beli_frag = f"{beli}  /  {fragment}"
                                awaken_skill = self.extract_value(r"Awakened Skills:\s*([^\n]+)(?=\s*Melee\s*\(s\):)", content)






                                swords = self.extract_value(r"Sword\(s\):\s*([^\n]+)", content)
                                cdk = "✅" if swords and "Cursed Dual Katana" in swords else "❌"
                                race = self.extract_value("Race:\s*([^\n]+)", content)
                                guns = self.extract_value(r"Gun\(s\):\s*([^\n]+)", content)
                                soulguitar = "✅" if guns and "SoulGuitar" in guns else "❌"
                                melee_str = self.extract_value(r"Melee\(s\):\s*([^\n]+)", content)

                                if melee_str:
                                    melee_list = [melee for melee in melee_options if melee in melee_str]
                                    if 'Godhuman' in melee_list:
                                        melee = 'Godhuman'
                                    elif len(melee_list) > 2:
                                        melee = '3-5 Melee'
                                    else:
                                        melee = ', '.join(melee_list)
                                else:
                                    melee = ""

                                fruit = self.extract_value(r"Fruit\(s\):\s*([^\n]+)", content)
                                accessory_raw = self.extract_value(r"Accessory\(s\):\s*((?:(?!\w+\(s\):)[^\n]*\n?)+)", content)


                                if accessory_raw:
                                    accessory_items = [item.strip() for item in accessory_raw.split(',')]
                                    accessory = '\n'.join(accessory_items)
                                else:
                                    accessory = ""

                                materials_content = self.extract_value(r"Material\(s\):\s*((?:.+\n)+)", content)
                                if materials_content:
                                    # Loại bỏ khoảng trắng thừa từ mỗi dòng
                                    materials_items = [item.strip() for item in materials_content.split('\n')]
                                    materials_content = '\n'.join(materials_items)
                                else:
                                    materials_content = ""


                                helm_fragment_status = self.check_helm_fragment(accessory, materials_content)
                                
                                status = online_statuses.get(player_name, "Loading...❕")
                                existing_row = self.find_row_by_player_name(player_name)
                                if existing_row is not None:
                                    values = [player_name, level, beli_frag, race, bounty, awaken_skill, melee, cdk, soulguitar, fruit, materials_content, accessory, helm_fragment_status, status]  # Đảm bảo thêm helm_fragment_status
                                    for col, value in enumerate(values):
                                        item = QTableWidgetItem(value if value else '')
                                        item.setTextAlignment(Qt.AlignCenter)
                                        if col in [9, 10, 11]:  # Fruit, Materials, and Accessory
                                            item.setText("🎒")
                                            item.setData(Qt.UserRole, value)
                                        self.tableWidget.setItem(existing_row, col, item)
                                else:
                                    current_row = self.tableWidget.rowCount()
                                    self.tableWidget.insertRow(current_row)
                                    values = [player_name, level, beli_frag, race, bounty, awaken_skill, melee, cdk, soulguitar, fruit, materials_content, accessory, helm_fragment_status, status]
                                    for col, value in enumerate(values):
                                        item = QTableWidgetItem(value if value else '')
                                        item.setTextAlignment(Qt.AlignCenter)
                                        if col in [9, 10, 11]:  # Fruit, Materials, and Accessory
                                            item.setText("🎒")
                                            item.setData(Qt.UserRole, value)
                                        self.tableWidget.setItem(current_row, col, item)
                                processed_usernames.append(player_name)



        for row in range(self.tableWidget.rowCount() - 1, -1, -1):
            item = self.tableWidget.item(row, 0)
            if item and item.text() not in processed_usernames:
                self.tableWidget.removeRow(row)


    def update_data(self):
        delay, ok = QInputDialog.getInt(self, "Setting Delay", "Delay Time (giây):", 10, 1, 3600, 1)
        if ok:
            # Cập nhật giá trị delay trong Config.ini
            self.settings.setValue("delay", delay)
            self.timer.start(delay * 1000)  # QTimer hoạt động dựa trên mili giây

    def extract_value(self, pattern, content):
        match = re.search(pattern, content)
        return match.group(1) if match else None

def get_hwid():
    if platform.system() == "Windows":
        try:
            HwProfileGuid = winreg.QueryValueEx(winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\\CurrentControlSet\\Control\\IDConfigDB\\Hardware Profiles\\0001"), "HwProfileGuid")[0].replace("{", "").replace("}", "").replace("-", "")
        except Exception as e:
            HwProfileGuid = ""

        try:
            SystemManufacturer = winreg.QueryValueEx(winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\\CurrentControlSet\\Control\\SystemInformation"), "SystemManufacturer")[0]
        except Exception as e:
            SystemManufacturer = ""

        return HwProfileGuid + hashlib.md5(SystemManufacturer.encode()).hexdigest()
    elif platform.system() == "Linux":
        return os.popen('cat /var/lib/dbus/machine-id').read().strip()
    else:
        return "UNKNOWN_HWID"

class KeyVerificationApp(QWidget):
    def __init__(self):
        super().__init__()
        self.key_verified = False
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        icon_path = os.path.join(os.path.dirname(__file__), "removal.ico")
        app_icon = QIcon(icon_path)
        self.setWindowIcon(app_icon)

        self.key_input = QLineEdit(self)
        self.key_input.setPlaceholderText('Nhập key của bạn')
        layout.addWidget(self.key_input)

        button_layout = QHBoxLayout()

        self.send_button = QPushButton('Xác minh Key', self)
        self.send_button.clicked.connect(self.verify_key)
        button_layout.addWidget(self.send_button)

        self.load_button = QPushButton('Load Key', self)
        self.load_button.clicked.connect(self.load_key_from_file)
        button_layout.addWidget(self.load_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)
        self.setWindowTitle('Xác minh Key')
        self.resize(300, 100)

    def load_key_from_file(self):
        if os.path.exists('auth.data'):
            with open('auth.data', 'r') as file:
                data = json.load(file)
                stored_key = data.get('key')
                if stored_key:
                    response_message = self.send_key_to_server(stored_key)
                    if response_message == "Key successfully!":
                        self.key_verified = True
                        self.close()
                    else:
                        QMessageBox.warning(self, "Lỗi", "Key không chính xác. Vui lòng nhập lại.")
        else:
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy file auth.data. Vui lòng nhập key.")

    def verify_key(self):
        key = self.key_input.text().strip()
        if key:
            response_message = self.send_key_to_server(key)
            QMessageBox.information(self, "Thông báo từ máy chủ", response_message)
            if response_message == "Key successfully!":
                self.key_verified = True
                # Save the key to auth.data
                with open('auth.data', 'w') as file:
                    json.dump({"key": key}, file)
                self.close()
        else:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập key trước khi xác minh.")

    def send_key_to_server(self, key):
        hwid = get_hwid()
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('116.111.9.47', 2818))
                data = {"key": key, "hwid": hwid}
                s.sendall(json.dumps(data).encode())
                response = s.recv(1024)
                return response.decode()
        except Exception as e:
            return str(e)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    key_verification = KeyVerificationApp()
    key_verification.show()
    app.exec_()

    if key_verification.key_verified:
        main_window = App()
        main_window.show()
        sys.exit(app.exec_())
