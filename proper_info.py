import pytsk3
import pyewf
from PyQt5.QtWidgets import QTreeWidgetItem

def analyze_image_file(image_path):
    """
    이미지 파일을 분석하여 주요 속성을 반환합니다.
    :param image_path: 분석할 이미지 파일 경로
    :return: dict 형태로 분석된 속성 정보 반환
    """
    try:
        if image_path.lower().endswith('.e01') or image_path.lower().endswith('.001'):
            filenames = pyewf.glob(image_path) if image_path.lower().endswith('.e01') else [image_path]
            ewf_handle = pyewf.handle() if image_path.lower().endswith('.e01') else None

            if ewf_handle:
                ewf_handle.open(filenames)
                img_info = EWFImgInfo(ewf_handle)
            else:
                img_info = pytsk3.Img_Info(image_path)
        else:
            img_info = pytsk3.Img_Info(image_path)

        fs_info = pytsk3.FS_Info(img_info)
        bytes_per_sector = fs_info.info.block_size
        sector_count = fs_info.info.block_count
        image_type = "Raw (dd)"

        return {
            "Evidence Source Path": image_path,
            "Evidence Type": "Forensic Disk Image",
            "Bytes per Sector": str(bytes_per_sector),
            "Sector Count": str(sector_count),
            "Image Type": image_type
        }
    except Exception as e:
        print(f"Error analyzing image file: {str(e)}")
        return {"Error": str(e)}

class EWFImgInfo(pytsk3.Img_Info):
    def __init__(self, ewf_handle):
        self._ewf_handle = ewf_handle
        super().__init__(url="", type=pytsk3.TSK_IMG_TYPE_EXTERNAL)

    def close(self):
        self._ewf_handle.close()

    def read(self, offset, size):
        self._ewf_handle.seek(offset)
        return self._ewf_handle.read(size)

    def get_size(self):
        return self._ewf_handle.get_media_size()

def populate_properties(tree_widget, analyzed_data, open_screen_widget):
    if not analyzed_data:
        print("No analyzed data available.")
        return

    print("Analyzed Data:", analyzed_data)

    tree_widget.clear()

    root_item = QTreeWidgetItem(tree_widget, ["Evidence Source Path", analyzed_data.get("Evidence Source Path", "Unknown")])
    QTreeWidgetItem(root_item, ["Evidence Type", analyzed_data.get("Evidence Type", "Unknown")])

    disk_item = QTreeWidgetItem(tree_widget, ["Disk", ""])
    geometry_item = QTreeWidgetItem(disk_item, ["Drive Geometry", ""])
    QTreeWidgetItem(geometry_item, ["Bytes per Sector", analyzed_data.get("Bytes per Sector", "Unknown")])
    QTreeWidgetItem(geometry_item, ["Sector Count", analyzed_data.get("Sector Count", "Unknown")])

    image_item = QTreeWidgetItem(disk_item, ["Image", ""])
    QTreeWidgetItem(image_item, ["Image Type", analyzed_data.get("Image Type", "Unknown")])

    tree_widget.expandAll()
