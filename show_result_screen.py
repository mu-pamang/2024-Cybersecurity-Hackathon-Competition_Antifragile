from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem,
    QLineEdit, QLabel, QHeaderView, QAbstractItemView, QComboBox, QFrame, QSplitter, QTextEdit, QSpacerItem,
    QSizePolicy, QStackedWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPixmap, QIcon, QTextCursor
import subprocess
import sys


class show_result_screen(QWidget):
    def __init__(self):
        super().__init__()

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 버튼 레이아웃
        self.button_layout = QHBoxLayout()
        self.wiping_button = QPushButton("와이핑")
        self.single_delete_button = QPushButton("완전 삭제")
        self.signature_mod_button = QPushButton("데이터 변조")

        self.button_layout.addWidget(self.wiping_button)
        self.button_layout.addWidget(self.single_delete_button)
        self.button_layout.addWidget(self.signature_mod_button)

        self.main_layout.addLayout(self.button_layout)

        # 테이블 위젯들
        self.wiping_table = self.create_table(2, ['와이핑된 파일', '와이핑 흔적 발견'])
        self.single_delete_table = self.create_table(3, ['파일 명', '삭제 유형', '시간'])
        self.signature_mod_table = self.create_table(4, ['파일 명', '변조 가능성', '복구 경로', '시간'])

        # 스택 위젯을 사용하여 테이블들을 관리
        self.table_stack = QStackedWidget()
        self.table_stack.addWidget(self.wiping_table)
        self.table_stack.addWidget(self.single_delete_table)
        self.table_stack.addWidget(self.signature_mod_table)

        # 테이블 스택을 메인 레이아웃에 추가
        self.main_layout.addWidget(self.table_stack)

        # 검색 레이아웃
        self.search_layout = QHBoxLayout()

        self.search_label = QLabel()
        pixmap = QPixmap("images/analyze_icon.png")
        scaled_pixmap = pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.search_label.setPixmap(scaled_pixmap)

        self.search_bar = QLineEdit()
        #self.search_bar.setFixedWidth(150)  # 글 넣는 부분 가로 크기를 줄임
        self.search_bar.setAlignment(Qt.AlignCenter) # 추가됨
        
        self.search_options = QComboBox()
        self.search_options.setFixedWidth(150)  # 콤보박스의 가로 크기를 늘림
        self.center_align_combobox_text(self.search_options) 

        self.search_button = QPushButton("Search")
        self.search_button.setIcon(QIcon("images/analyze_icon_2.png"))

        self.clear_search_button = QPushButton()
        self.clear_search_button.setIcon(QIcon("images/x_icon.png"))

        self.search_layout.addWidget(self.search_label)
        self.search_layout.addWidget(self.search_bar)
        self.search_layout.addWidget(self.search_options)
        self.search_layout.addWidget(self.search_button)
        self.search_layout.addWidget(self.clear_search_button)

        # 검색 레이아웃을 메인 레이아웃에 추가
        self.main_layout.addLayout(self.search_layout)

        # 헥사 뷰
        self.hexa_view = QTextEdit()
        self.hexa_view.setReadOnly(True)
        self.hexa_view.hide()  # 초기에는 숨겨둡니다

        # 헥사 뷰를 메인 레이아웃에 추가
        self.main_layout.addWidget(self.hexa_view)

        # 버튼 연결
        self.wiping_button.clicked.connect(lambda: self.display_table(self.wiping_table))
        self.single_delete_button.clicked.connect(lambda: self.display_table(self.single_delete_table))
        self.signature_mod_button.clicked.connect(lambda: self.display_table(self.signature_mod_table))
        self.search_button.clicked.connect(self.search_records)
        self.clear_search_button.clicked.connect(self.clear_search)

        # 초기 설정
        self.display_table(self.wiping_table)

    def create_table(self, columns, headers):
        table = QTableWidget()
        table.setRowCount(0)
        table.setColumnCount(columns)
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        table.setFrameShape(QFrame.Box)
        table.setStyleSheet("""
            QHeaderView::section {
            text-align: center;
            }
            QTableWidget::item {
            text-align: center;
            }
            background-color: #FFFFFF;
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 15px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #888888;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        return table

    def display_wiping_records(self):
        self.search_options.clear()
        self.search_options.addItems(["공통", "파일", "흔적"])
        self.center_align_combobox_text(self.search_options)
        if self.wiping_results is None:
            self.load_wiping_results()
        self.display_table(self.wiping_table)

    def display_single_delete_records(self):
        self.search_options.clear()
        self.search_options.addItems(["공통", "파일명", "삭제유형", "시간"])
        self.center_align_combobox_text(self.search_options)
        self.display_table(self.single_delete_table)

    def display_signature_mod_records(self):
        self.search_options.clear()
        self.search_options.addItems(["공통", "파일명", "변조가능성", "복구경로", "시간"])
        self.center_align_combobox_text(self.search_options)
        self.display_table(self.signature_mod_table)

    def update_search_options(self, table):
        self.search_options.clear()
        if table == self.wiping_table:
            self.search_options.addItems(["공통", "파일", "흔적"])
        elif table == self.single_delete_table:
            self.search_options.addItems(["공통", "파일명", "삭제유형", "시간"])
        elif table == self.signature_mod_table:
            self.search_options.addItems(["공통", "파일명", "변조가능성", "복구경로", "시간"])
        
    def display_table(self, table):
        self.table_stack.setCurrentWidget(table)
        self.update_search_options(table)

    def hide_all_tables(self):
        self.wiping_table.hide()
        self.single_delete_table.hide()
        self.signature_mod_table.hide()
        self.placeholder.hide()

    def show_placeholder(self):
        self.hide_all_tables()
        self.placeholder.show()

    def add_wiping_record(self, file_name, wiping_trace):
        self.add_table_row(self.wiping_table, [file_name, wiping_trace])

    def add_single_delete_record(self, file_name, delete_type, timestamp):
        self.add_table_row(self.single_delete_table, [file_name, delete_type, timestamp])

    def add_signature_mod_record(self, file_name, falsify_type, recovery_path, formatted_timestamp):
        self.add_table_row(self.signature_mod_table, [file_name, falsify_type, recovery_path, formatted_timestamp])

    def add_table_row(self, table, data):
        row_position = table.rowCount()
        table.insertRow(row_position)
        for i, value in enumerate(data):
            item = QTableWidgetItem(value)
            item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row_position, i, item)
        self.adjust_table_columns(table)

    def clear_tables(self):
        self.wiping_table.setRowCount(0)
        self.single_delete_table.setRowCount(0)
        self.signature_mod_table.setRowCount(0)

    def analyze_file(self, file_path):
        self.clear_tables()

        deletion_records = self.get_deletion_records(file_path)
        for record in deletion_records:
            if record.strip():
                try:
                    file_name, delete_type, timestamp = map(str.strip, record.split(","))
                    self.add_single_delete_record(file_name, delete_type, timestamp)
                except ValueError:
                    print(f"Skipping invalid record: {record}")

        wiping_records = self.get_wiping_records(file_path)
        for record in wiping_records:
            if record.strip():
                try:
                    file_name, wiping_trace = map(str.strip, record.split(","))
                    self.add_wiping_record(file_name, wiping_trace)
                except ValueError:
                    print(f"Skipping invalid record: {record}")

        signature_mod_records = self.get_signature_mod_records(file_path)
        for record in signature_mod_records:
            if record.strip():
                fields = record.split(",")
                if len(fields) >= 4:
                    file_name = fields[0].strip()
                    falsify_type = ",".join(fields[1:-2]).strip()
                    recovery_path = fields[-2].strip()
                    formatted_timestamp = fields[-1].strip()
                    self.add_signature_mod_record(file_name, falsify_type, recovery_path, formatted_timestamp)
                else:
                    print(f"Skipping invalid record: {record}")

    def load_records(self):
        self.clear_tables()

        deletion_records = self.get_deletion_records("default_file_path")
        for record in deletion_records:
            if record.strip():
                try:
                    file_name, delete_type, timestamp = map(str.strip, record.split(","))
                    self.add_single_delete_record(file_name, delete_type, timestamp)
                except ValueError:
                    print(f"Skipping invalid record: {record}")

        wiping_records = self.get_wiping_records("default_file_path")
        for record in wiping_records:
            if record.strip():
                try:
                    file_name, wiping_trace = map(str.strip, record.split(","))
                    self.add_wiping_record(file_name, wiping_trace)
                except ValueError:
                    print(f"Skipping invalid record: {record}")

        signature_mod_records = self.get_signature_mod_records("default_file_path")
        for record in signature_mod_records:
            if record.strip():
                fields = record.split(",")
                if len(fields) >= 4:
                    file_name = fields[0].strip()
                    falsify_type = ",".join(fields[1:-2]).strip()
                    recovery_path = fields[-2].strip()
                    formatted_timestamp = fields[-1].strip()
                    self.add_signature_mod_record(file_name, falsify_type, recovery_path, formatted_timestamp)
                else:
                    print(f"Skipping invalid record: {record}")

    def get_deletion_records(self, file_path):
        result = subprocess.run([sys.executable, "simple_delete_detection.py", file_path], capture_output=True, text=True, encoding='utf-8', errors='ignore')
        return result.stdout.splitlines()

    def get_wiping_records(self, _):
        result = subprocess.run([sys.executable, "print_wiping.py"], capture_output=True, text=True, encoding='cp949', errors='ignore')
        self.wiping_results = result.stdout.splitlines()
        return self.wiping_results

    def get_signature_mod_records(self, file_path):
        result = subprocess.run([sys.executable, "detect_data_falsify.py", file_path], capture_output=True, text=True, encoding='cp949', errors='ignore')
        return result.stdout.splitlines()

    def load_wiping_results(self):
        self.clear_tables()
        wiping_records = self.get_wiping_records("default_file_path")
        for record in wiping_records:
            if record.strip():
                try:
                    file_name, wiping_trace = map(str.strip, record.split(","))
                    self.add_wiping_record(file_name, wiping_trace)
                except ValueError:
                    print(f"Skipping invalid record: {record}")

    def search_records(self):
        search_term = self.search_bar.text()
        search_option = self.search_options.currentText()
        if self.wiping_table.isVisible():
            self.filter_table(self.wiping_table, search_term, search_option)
        elif self.single_delete_table.isVisible():
            self.filter_table(self.single_delete_table, search_term, search_option)
        elif self.signature_mod_table.isVisible():
            self.filter_table(self.signature_mod_table, search_term, search_option)

    def filter_table(self, table, search_term, search_option):
        for row in range(table.rowCount()):
            match = False
            for column in range(table.columnCount()):
                item = table.item(row, column)
                if search_option == "공통" or \
                   (search_option == "파일" and column == 1 and self.wiping_table.isVisible()) or \
                   (search_option == "흔적" and column == 0 and self.wiping_table.isVisible()) or \
                   (search_option == "파일명" and column == 0) or \
                   (search_option == "삭제유형" and column == 1 and self.single_delete_table.isVisible()) or \
                   (search_option == "시간" and column == table.columnCount() - 1) or \
                   (search_option == "변조가능성" and column == 1 and self.signature_mod_table.isVisible()) or \
                   (search_option == "복구경로" and column == 2 and self.signature_mod_table.isVisible()):
                    if search_term.lower() in item.text().lower():
                        match = True
                        break
            table.setRowHidden(row, not match)

    def clear_search(self):
        self.search_bar.clear()
        if self.wiping_table.isVisible():
            self.reset_table_filter(self.wiping_table)
        elif self.single_delete_table.isVisible():
            self.reset_table_filter(self.single_delete_table)
        elif self.signature_mod_table.isVisible():
            self.reset_table_filter(self.signature_mod_table)

    def reset_table_filter(self, table):
        for row in range(table.rowCount()):
            for column in range(table.columnCount()):
                item = table.item(row, column)
                item.setBackground(QColor("white"))  
            table.setRowHidden(row, False)

    def adjust_table_columns(self, table):
        table.resizeColumnsToContents()
        header = table.horizontalHeader()
        if table == self.signature_mod_table:
            header.setSectionResizeMode(QHeaderView.ResizeToContents)
            for column in range(table.columnCount()):
                if table.columnWidth(column) > 300:
                    header.setSectionResizeMode(column, QHeaderView.Interactive)
                    table.setColumnWidth(column, 300)
                else:
                    header.setSectionResizeMode(column, QHeaderView.Stretch)
        else:
            header.setSectionResizeMode(QHeaderView.Stretch)

    def center_align_combobox_text(self, combobox):
        for i in range(combobox.count()):
            combobox.setItemData(i, Qt.AlignCenter, Qt.TextAlignmentRole)

    def toggle_hexa_view(self):
        if self.hexa_view.isVisible():
            self.hexa_view.hide()
        else:
            self.hexa_view.show()
            self.adjust_hexa_view_size()  # 헥사 뷰 크기 조정

    def adjust_hexa_view_size(self):
        # 헥사 뷰의 크기를 조정하는 메소드 추가
        if self.hexa_view.isVisible():
            self.main_layout.setStretchFactor(self.hexa_view, 1)
            self.main_layout.setStretchFactor(self.table_stack, 1)
        else:
            self.main_layout.setStretchFactor(self.hexa_view, 0)
            self.main_layout.setStretchFactor(self.table_stack, 1)
