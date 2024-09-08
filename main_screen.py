from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QAction, QMenu, QMessageBox, QVBoxLayout, QWidget, QDockWidget, QTreeWidget, QTreeWidgetItem
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from show_result_screen import show_result_screen
from file_open_screen import file_open_screen
from proper_info import analyze_image_file, populate_properties  # proper_info 모듈의 함수들을 import
from hexa_data_anal import get_hexa_data, display_hexa_data_in_textedit, CustomTextEdit
import sys

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ANTI*")
        self.setWindowIcon(QIcon("images/main_icon.png"))
        self.setGeometry(100, 100, 2000, 1200)

        self.open_screen_widget = file_open_screen()
        self.result_screen_widget = show_result_screen()  # show_result_screen 초기화
        self.open_screen_widget.result_screen_widget = self.result_screen_widget  # result_screen_widget 연결
        self.hexa_dock_widget = None  # Hexa Dock Widget 초기화
        self.properties_dock_widget = None  # Properties Dock Widget 초기화

        self.init_ui()

    def init_ui(self):
        self.statusBar()
        menubar = self.menuBar()
        menubar.setStyleSheet("background-color: #FFFFFF; color: #000000;")

        # File Menu
        file_menu = menubar.addMenu('&File')
        open_menu = QMenu('&Open', self)

        load_image_file_action = QAction('&Image File', self)
        load_image_file_action.triggered.connect(self.load_image_file_and_analyze)  # 이미지 파일을 불러오고 분석하는 함수로 연결
        open_menu.addAction(load_image_file_action)

        load_j_file_action = QAction('&$J File', self)
        load_j_file_action.triggered.connect(self.open_screen_widget.open_file_dialog)
        open_menu.addAction(load_j_file_action)

        load_falsify_folder_action = QAction('&Falsify Folder', self)
        load_falsify_folder_action.triggered.connect(self.open_screen_widget.open_folder_dialog2)
        open_menu.addAction(load_falsify_folder_action)

        load_recover_folder_action = QAction('&Recovery Folder', self)
        load_recover_folder_action.triggered.connect(self.open_screen_widget.open_folder_dialog3)
        open_menu.addAction(load_recover_folder_action)

        file_menu.addMenu(open_menu)

        exit_action = QAction(QIcon("images/exit_icon.png"), '&Exit', self)
        exit_action.setShortcut('Ctrl+E')
        exit_action.triggered.connect(self.confirm_exit)
        file_menu.addAction(exit_action)

        # View Menu
        self.view_menu = menubar.addMenu('&Views')

        # Analyze Menu
        analyze_menu = QMenu('&Analyze', self)
        analyze_all_action = QAction('&Analyze All', self)
        analyze_all_action.triggered.connect(self.analyze_all)
        analyze_menu.addAction(analyze_all_action)
        self.view_menu.addMenu(analyze_menu)

        # Tools Menu
        tools_menu = menubar.addMenu('&Tools')

        search_action = QAction('&Search', self)
        search_action.setShortcut('Ctrl+F')
        search_action.triggered.connect(self.search_function)
        tools_menu.addAction(search_action)

        hexa_action = QAction('&Hexa', self)
        hexa_action.setCheckable(True)  # Make the Hexa action checkable
        hexa_action.triggered.connect(self.show_hexa_view)
        tools_menu.addAction(hexa_action)

        properties_action = QAction('&Properties', self)
        properties_action.setCheckable(True)  # Make the Properties action checkable
        properties_action.triggered.connect(self.toggle_properties_view)  # 이 부분이 오류 발생했던 부분
        self.view_menu.addAction(properties_action)

        # Help Menu
        help_menu = menubar.addMenu('&Help')
        help_menu.addAction('&About us')

        # Show File Paths Action
        show_file_paths_action = QAction('Show File Paths', self)
        show_file_paths_action.setCheckable(True)
        show_file_paths_action.triggered.connect(self.toggle_file_paths)
        self.view_menu.addAction(show_file_paths_action)

        self.create_dock_widgets()

    def create_dock_widgets(self):
        # Evidence Tree Dock Widget
        self.evidence_tree_dock = QDockWidget("Evidence Tree", self)
        self.evidence_tree_dock.setWidget(self.open_screen_widget.file_open_area)
        self.evidence_tree_dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.evidence_tree_dock)

        # Detection Results Dock Widget
        self.result_dock_widget = QDockWidget("Detection Results", self)
        self.result_dock_widget.setWidget(self.result_screen_widget)
        self.result_dock_widget.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.addDockWidget(Qt.RightDockWidgetArea, self.result_dock_widget)

        # Hexa View Dock Widget (Initially Hidden)
        self.hexa_dock_widget = QDockWidget("Hexa View", self)
        self.hexa_text_edit = CustomTextEdit(self)
        self.hexa_dock_widget.setWidget(self.hexa_text_edit)
        self.hexa_dock_widget.setAllowedAreas(Qt.AllDockWidgetAreas)

        # Detection Results 바로 아래에 Hexa View 추가
        self.addDockWidget(Qt.BottomDockWidgetArea, self.hexa_dock_widget, Qt.Horizontal)
        self.tabifyDockWidget(self.result_dock_widget, self.hexa_dock_widget)  # 탭으로 결합 가능하게 설정
        self.hexa_dock_widget.hide()  # Initially hidden

        self.result_screen_widget.single_delete_button.clicked.connect(self.open_screen_widget.display_journal_results)
        self.result_screen_widget.signature_mod_button.clicked.connect(self.open_screen_widget.display_falsify_results)
        self.result_screen_widget.wiping_button.clicked.connect(self.result_screen_widget.load_wiping_results)

        # Properties (Evidence Tree 아래에 추가)
        self.properties_dock_widget = QDockWidget("Properties", self)
        self.properties_tree = QTreeWidget()
        self.properties_tree.setHeaderLabels(["Property", "Value"])
        self.properties_dock_widget.setWidget(self.properties_tree)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.properties_dock_widget)
        self.tabifyDockWidget(self.evidence_tree_dock, self.properties_dock_widget)

        # Menubar action to toggle visibility
        self.view_menu.addAction(self.evidence_tree_dock.toggleViewAction())
        self.view_menu.addAction(self.result_dock_widget.toggleViewAction())
        self.view_menu.addAction(self.hexa_dock_widget.toggleViewAction())
        self.view_menu.addAction(self.properties_dock_widget.toggleViewAction())

    def toggle_properties_view(self):
        """
        Properties 뷰를 토글하는 함수.
        """
        action = self.sender()  # Get the action that triggered this function
        if self.properties_dock_widget:
            if self.properties_dock_widget.isVisible():
                self.properties_dock_widget.hide()
                action.setChecked(False)  # Uncheck the action
            else:
                self.properties_dock_widget.show()
                action.setChecked(True)  # Check the action

    def load_image_file_and_analyze(self):
        # 이미지 파일 선택 후 분석 수행
        image_file_path = self.open_screen_widget.load_image_file()  # 이미지 파일 선택
        if image_file_path:
            analyzed_data = analyze_image_file(image_file_path)  # proper_info.py에서 이미지 파일 분석
            if analyzed_data:
                populate_properties(self.properties_tree, analyzed_data, self.open_screen_widget)  # 분석된 데이터로 Properties 채우기
            else:
                QMessageBox.warning(self, "Error", "Failed to analyze the selected image file.")
        else:
            QMessageBox.warning(self, "Error", "No image file was selected.")

    def toggle_file_paths(self):
        sender = self.sender()
        visible = sender.isChecked() if isinstance(sender, QAction) else sender
        self.open_screen_widget.toggle_file_paths(visible)

    def search_function(self):
        print("Search function triggered")

    def properties_function(self):
        print("Properties function triggered")

    def confirm_exit(self):
        reply = QMessageBox.question(self, "Exit", "Are you sure you want to quit?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            QApplication.instance().quit()

    def closeEvent(self, event):
        self.confirm_exit()
        event.ignore()

    def analyze_all(self):
        self.open_screen_widget.execute_analysis()
        self.open_screen_widget.execute_analysis3()

    def show_hexa_view(self):
        action = self.sender()  # Get the action that triggered this function

        if self.hexa_dock_widget:
            if self.hexa_dock_widget.isVisible():
                self.hexa_dock_widget.hide()  # 숨기기
                action.setChecked(False)  # Uncheck the action
            else:
                file_path = self.open_screen_widget.file_path_label.text()
                if file_path and file_path != "No file selected":
                    hexa_data = get_hexa_data(file_path)
                    if hexa_data and not hexa_data.startswith("파일 읽기 오류"):
                        display_hexa_data_in_textedit(self.hexa_text_edit, hexa_data)
                        self.hexa_dock_widget.show()  # Hexa Dock Widget을 표시
                        action.setChecked(True)  # Check the action
                    else:
                        QMessageBox.warning(self, "Error", "Unable to load hexa data. " + hexa_data)
                else:
                    QMessageBox.warning(self, "Error", "No $J file has been analyzed.")
        else:
            QMessageBox.warning(self, "Error", "Hexa view is not available.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyWindow()
    ex.show()
    sys.exit(app.exec_())
