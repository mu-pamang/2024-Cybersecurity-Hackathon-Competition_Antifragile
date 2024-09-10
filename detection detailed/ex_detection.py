from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTextEdit, QPushButton, QFileDialog, QLabel, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QColor, QTextCharFormat, QFont, QTextCursor
from PyQt5.QtCore import Qt
import sys
from simple_delete_detection import read_usn_journal_file, parse_usn_journal, read_usn_record

class CustomTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)  # 텍스트 수정 방지
        self.setMouseTracking(True)  # 마우스 트래킹 활성화
        self.setFont(QFont('Courier', 10))  # 고정폭 폰트 사용
        self.hex_start = 10  # 헥사 값 시작 위치
        self.decoded_start = 60  # 디코드 텍스트 시작 위치

        # 헥사 값과 디코드 텍스트 각각의 색상 설정
        self.hex_highlight_format = QTextCharFormat()
        self.hex_highlight_format.setBackground(QColor("#0078D7"))  # 헥사 값 드래그 색상
        self.hex_highlight_format.setForeground(QColor("white"))  # 드래그 시 헥사 텍스트를 흰색으로 변경

        self.decoded_highlight_format = QTextCharFormat()
        self.decoded_highlight_format.setBackground(QColor("#C2DEF4"))  # 디코드 텍스트 드래그 색상

        # 드래그 해제 후 복원되는 기본 헥사 값 텍스트 색상
        self.default_hex_format = QTextCharFormat()
        self.default_hex_format.setForeground(QColor("black"))  # 헥사 텍스트 기본 색상 (검정색)

        self.offset_highlight_format = QTextCharFormat()
        self.offset_highlight_format.setForeground(QColor("blue"))  # Offset 부분 파란색

        self.is_selecting = False
        self.start_cursor = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_selecting = True
            self.start_cursor = self.cursorForPosition(event.pos())
            # 오프셋 영역은 드래그가 안되도록 처리
            if self.start_cursor.position() >= self.hex_start:
                # 새로운 드래그가 시작되면 이전 선택을 초기화
                self.clear_selection_highlight()
                self.select_hex_and_text(self.start_cursor, self.start_cursor)

    def mouseMoveEvent(self, event):
        if self.is_selecting and event.buttons() == Qt.LeftButton:
            current_cursor = self.cursorForPosition(event.pos())
            if current_cursor.position() >= self.hex_start:  # 오프셋 영역 제외
                self.clear_selection_highlight()
                self.select_hex_and_text(self.start_cursor, current_cursor)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_selecting = False

    def select_hex_and_text(self, start_cursor, end_cursor, reset_colors=False):
        # 시작 및 종료 위치
        start_pos = start_cursor.position()
        end_pos = end_cursor.position()

        if start_pos > end_pos:
            start_pos, end_pos = end_pos, start_pos

        extra_selections = []

        # 선택된 블록 순회
        block = self.document().findBlock(start_pos)
        end_block = self.document().findBlock(end_pos)

        while block.isValid() and block.position() <= end_block.position():
            block_start_pos = block.position()
            block_end_pos = block.position() + block.length() - 1  # 블록의 끝 위치

            selection_start = max(start_pos, block_start_pos)
            selection_end = min(end_pos, block_end_pos)

            start_in_block = selection_start - block_start_pos
            end_in_block = selection_end - block_start_pos

            # 바이트 인덱스 계산 함수
            def position_to_byte_index(pos_in_block):
                if pos_in_block < self.hex_start:
                    return None
                elif self.hex_start <= pos_in_block < self.decoded_start:
                    return (pos_in_block - self.hex_start) // 3
                elif pos_in_block >= self.decoded_start:
                    return pos_in_block - self.decoded_start
                else:
                    return None

            byte_start = position_to_byte_index(start_in_block)
            byte_end = position_to_byte_index(end_in_block)

            if byte_start is None:
                byte_start = 0
            if byte_end is None:
                byte_end = 16  # 최대 바이트 수

            if byte_start > byte_end:
                byte_start, byte_end = byte_end, byte_start

            # 헥사 값 선택
            hex_cursor = QTextCursor(self.document())
            hex_cursor.setPosition(block.position() + self.hex_start + byte_start * 3)
            hex_cursor.setPosition(block.position() + self.hex_start + byte_end * 3, QTextCursor.KeepAnchor)

            # 디코드 텍스트 선택
            text_cursor = QTextCursor(self.document())
            text_cursor.setPosition(block.position() + self.decoded_start + byte_start)
            text_cursor.setPosition(block.position() + self.decoded_start + byte_end, QTextCursor.KeepAnchor)

            # 헥사 값과 디코드 텍스트에 각각 다른 색상 적용
            if reset_colors:
                # 드래그 해제 후 기본 검정색으로 복원
                hex_format = self.default_hex_format
            else:
                # 드래그 중이면 흰색으로 강조
                hex_format = self.hex_highlight_format

            extra_selection_hex = QTextEdit.ExtraSelection()
            extra_selection_hex.cursor = hex_cursor
            extra_selection_hex.format = hex_format
            extra_selections.append(extra_selection_hex)

            extra_selection_decoded = QTextEdit.ExtraSelection()
            extra_selection_decoded.cursor = text_cursor
            extra_selection_decoded.format = self.decoded_highlight_format
            extra_selections.append(extra_selection_decoded)

            if block == end_block:
                break
            block = block.next()

        # 현재 선택된 영역 적용
        self.setExtraSelections(extra_selections)

    def clear_selection_highlight(self):
        # 기존 선택을 완전히 초기화
        self.setExtraSelections([])


def hexdump(data, length=16):
    result = []

    # Header 설정
    header = "Offset(h) " + " ".join(f"{i:02X}" for i in range(length)) + "   Decoded text"
    result.append(header)

    for i in range(0, len(data), length):
        # Offset 값
        line = f'{i:08X}  '

        # 16진수 값
        hex_values = ' '.join(f'{b:02X}' for b in data[i:i + length])
        hex_part = f'{hex_values:<{length * 3}}'

        # ASCII 값
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i + length])

        # 라인 조합
        result.append(f'{line}{hex_part}  {ascii_part}')

    return '\n'.join(result)


def get_hexa_data(file_path):
    try:
        with open(file_path, 'rb') as file:
            data = file.read()
            return hexdump(data)
    except Exception as e:
        return f"파일 읽기 오류: {str(e)}"


def display_hexa_data_in_textedit(textedit: QTextEdit, hexa_data: str):
    textedit.clear()

    # 오프셋에 파란색 적용
    header_format = QTextCharFormat()
    header_format.setForeground(QColor("blue"))
    header_format.setFontWeight(QFont.Bold)

    blue_format = QTextCharFormat()
    blue_format.setForeground(QColor("blue"))

    default_format = QTextCharFormat()

    lines = hexa_data.splitlines()

    if len(lines) > 0:
        # 헤더 처리
        textedit.setCurrentCharFormat(header_format)
        textedit.append(lines[0])  # 헤더 추가
        textedit.insertPlainText("\n")

        # 본문 처리
        for line in lines[1:]:
            offset_end_index = line.index("  ")
            offset_text = line[:offset_end_index]
            remainder_text = line[offset_end_index:]

            textedit.setCurrentCharFormat(blue_format)
            textedit.insertPlainText(offset_text)  # 오프셋 부분은 파란색

            textedit.setCurrentCharFormat(default_format)
            textedit.insertPlainText(remainder_text + "\n")  # 나머지 부분은 기본 텍스트

        textedit.moveCursor(QTextCursor.Start)
    else:
        textedit.setPlainText("No data to display.")


class HexViewerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Hex Viewer 및 탐지 결과')

        self.main_layout = QVBoxLayout()

        # 헥사 데이터를 보여줄 텍스트 에디터
        self.text_edit = CustomTextEdit(self)
        self.main_layout.addWidget(self.text_edit)

        # 결과 테이블
        self.result_table = QTableWidget(0, 3)
        self.result_table.setHorizontalHeaderLabels(["Filename", "Deletion Type", "Timestamp"])
        self.result_table.cellClicked.connect(self.on_record_selected)
        self.main_layout.addWidget(self.result_table)

        # 파일 열기 버튼
        self.open_button = QPushButton('파일 열기', self)
        self.open_button.clicked.connect(self.open_file)
        self.main_layout.addWidget(self.open_button)

        # 중앙 위젯 설정
        container = QWidget()
        container.setLayout(self.main_layout)
        self.setCentralWidget(container)

    def open_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open $J File", "", "All Files (*)")
        if file_name:
            self.process_usn_journal(file_name)

    def process_usn_journal(self, file_path):
        """$J 파일 읽고 분석"""
        try:
            # $J 파일에서 헥사 데이터를 읽음
            hexa_data = get_hexa_data(file_path)
            display_hexa_data_in_textedit(self.text_edit, hexa_data)  # 헥사 데이터를 텍스트 에디터에 표시

            # 탐지 결과 처리
            journal_data = read_usn_journal_file(file_path)
            self.journal_data = journal_data  # 헥사 데이터를 저장

            # 탐지 결과 추가
            results, _ = parse_usn_journal(journal_data)
            self.result_table.setRowCount(0)
            for result in results:
                file_name, deletion_type, timestamp = result.split(', ')
                row_position = self.result_table.rowCount()
                self.result_table.insertRow(row_position)
                self.result_table.setItem(row_position, 0, QTableWidgetItem(file_name))
                self.result_table.setItem(row_position, 1, QTableWidgetItem(deletion_type))
                self.result_table.setItem(row_position, 2, QTableWidgetItem(timestamp))
        except Exception as e:
            print(f"파일 처리 오류: {str(e)}")

    def on_record_selected(self, row, column):
        """테이블에서 특정 기록 선택 시 호출"""
        print(f"선택된 행: {row}, 열: {column}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = HexViewerApp()
    viewer.show()
    sys.exit(app.exec_())
