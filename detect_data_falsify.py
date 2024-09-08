import os
from datetime import datetime

file_header_signatures = {
    "JPEG": b"\xFF\xD8\xFF",
    "PNG": b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A",
    "PDF": b"%PDF",
    "ZIP": b"\x50\x4B\x03\x04",
    "GIF": b"\x47\x49\x46\x38",
    "BMP": b"\x42\x4D"
}

file_footer_signatures = {
    "JPEG": b"\xFF\xD9",
    "PNG": b"\x49\x45\x4E\x44\xAE\x42\x60\x82",
    "GIF": b"\x00\x3B",
    "ZIP": b"\x50\x4B"
}

file_extensions = {
    "JPEG": [".jpg", ".jpeg"],
    "PNG": [".png"],
    "PDF": [".pdf"],
    "ZIP": [".zip"],
    "GIF": [".gif"],
    "BMP": [".bmp"]
}

sos_marker = b"\xFF\xDA"
sos_marker_behind = b"\x00\x0C\x03\x01\x00\x02\x11\x03\x11\x00\x3F\x00"

def detect_file_type(file_path):
    with open(file_path, "rb") as file:
        header = file.read(16)

        file.seek(-16, 2)
        footer = file.read(16)

        detected_type = None
        for file_type, signature in file_header_signatures.items():
            if header.startswith(signature):
                detected_type = file_type
                break

        footer_match = False
        if detected_type in file_footer_signatures:
            footer_signature = file_footer_signatures[detected_type]
            if footer.endswith(footer_signature):
                footer_match = True

        return detected_type, footer_match

def check_file_extension(file_path, detected_type):
    _, file_extension = os.path.splitext(file_path)
    file_extension = file_extension.lower()
    
    if detected_type in file_extensions:
        return file_extension in file_extensions[detected_type]
    return False

def hidden_data_detect(file_path, detected_type, recover_directory):
    if not os.path.exists(recover_directory):
        os.makedirs(recover_directory)

    with open(file_path, "rb") as file:
        full_data = file.read()

    footer_signature = file_footer_signatures[detected_type]
    hidden_data_start = full_data.find(footer_signature) + len(footer_signature)
    hidden_data = full_data[hidden_data_start:]

    if len(hidden_data) == 0:
        return None

    index = len(os.listdir(recover_directory)) + 1

    if hidden_data.startswith(b'\xFF\xD8'):
        file_out = os.path.join(recover_directory, f"복구파일_{index}.jpg")
    elif hidden_data.startswith(b'%PDF'):
        file_out = os.path.join(recover_directory, f"복구파일_{index}.pdf")
    elif hidden_data.startswith(b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'):
        file_out = os.path.join(recover_directory, f"복구파일_{index}.png")
    else:
        file_out = os.path.join(recover_directory, f"복구파일_{index}.txt")

    with open(file_out, 'wb') as hidden_file:
        hidden_file.write(hidden_data)
        
    return file_out

def check_sos_marker(file_path):
    with open(file_path, "rb") as file:
        data = file.read()

    sos_marker_position = data.find(sos_marker)
    if sos_marker_position == -1:
        print(f"{file_path}: SOS 마커를 찾을 수 없습니다.")
        return False

    sos_data = data[sos_marker_position + len(sos_marker):sos_marker_position + len(sos_marker) + len(sos_marker_behind)]

    if sos_data != sos_marker_behind:
        repair_data = (data[:sos_marker_position + len(sos_marker)] +
                         sos_marker_behind +
                         data[sos_marker_position + len(sos_marker) + len(sos_marker_behind):])
        return False, repair_data

    return True, None

def process_file(file_path, recover_directory):
    filename = os.path.basename(file_path)
    falsify_types = []
    recovery_path = "없음"

    detected_type, footer_match = detect_file_type(file_path)

    if detected_type:
        extension_match = check_file_extension(file_path, detected_type)
        if not extension_match:
            falsify_types.append("파일 확장자 불일치")
        
        if not footer_match:
            falsify_types.append("푸터 시그니처 변조")
        
        hidden_data_path = hidden_data_detect(file_path, detected_type, recover_directory)
        if hidden_data_path:
            falsify_types.append("숨겨진 데이터 탐지")
            recovery_path = hidden_data_path
        
        if detected_type == "JPEG":
            sos_correct, repair_data = check_sos_marker(file_path)
            if not sos_correct:
                falsify_types.append("SOS 마커 변조")
                index = len(os.listdir(recover_directory)) + 1
                repaired_file_path = os.path.join(recover_directory, f"복구파일_{index}.jpg")
                with open(repaired_file_path, "wb") as file:
                    file.write(repair_data)
                recovery_path = repaired_file_path
    else:
        falsify_types.append("변조 가능성 또는 알 수 없는 파일 형식")

    falsify_type = ", ".join(falsify_types) if falsify_types else "정상"

    formatted_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{filename}, {falsify_type}, {recovery_path}, {formatted_timestamp}")

def main(directory, recover_directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            process_file(file_path, recover_directory)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        directory = sys.argv[1]
        recover_directory = sys.argv[2]
        main(directory, recover_directory)
    else:
        print("This script should be imported and used within the file_open_screen.py interface.")


