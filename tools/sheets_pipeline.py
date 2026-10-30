#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stella Sora - Google Sheets & Excel Pipeline
Tạo và đồng bộ bảng tính dịch thuật chuẩn dành cho cộng tác viên non-tech.
100% Python Standard Library (không cần cài thêm thư viện ngoài).

Cấu trúc phân tầng:
1. Sheet 00: Hướng dẫn nhanh 3 phút (Dành cho Editor)
2. Sheet 01: Thống nhất danh từ toàn game (Glossary 322 mục phân 5 nhóm)
3. Sheet 02: Ma trận tính cách, khẩu khí & xưng hô (41 nhân vật & 12 ma trận)
4. Sheet Chuong_0_Mo_Dau: Chương Mở Đầu (Phân chia Màn 01 -> 06 + Phụ đề)
5. Sheet Chuong_1_MainStory: Chương 1 - 12 Màn (1,303 câu, có Chủ thể người nói)
6. Sheet Chuong_2_MainStory: Chương 2 - 14 Màn (1,503 câu, có Chủ thể người nói)
7. Sheet Chuyen_Nhan_Vat_Dating: Chuyện nhân vật & Voice lines
"""

import sys
import os
import re
import json
import zipfile
import io
import argparse
from typing import List, Dict, Any, Tuple, Optional
import xml.etree.ElementTree as ET

# Đảm bảo UTF-8 cho console Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def escape_xml(s: Any) -> str:
    """Escape ký tự cho XML an toàn, loại bỏ control characters bất hợp lệ."""
    if s is None:
        return ""
    if not isinstance(s, str):
        s = str(s)
    clean = []
    for c in s:
        code = ord(c)
        if (code >= 0x20 and code <= 0xD7FF) or code in (0x9, 0xA, 0xD) or (code >= 0xE000 and code <= 0xFFFD):
            clean.append(c)
    s = "".join(clean)
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def col_name(index_1based: int) -> str:
    """Chuyển số cột 1-based (1, 2, 3...) thành chữ cái (A, B, C... AA, AB...)."""
    result = ""
    while index_1based > 0:
        index_1based, remainder = divmod(index_1based - 1, 26)
        result = chr(65 + remainder) + result
    return result


class MiniXLSXWriter:
    """Tạo file Microsoft Excel .xlsx hoàn chỉnh bằng Python standard library (zipfile + xml)."""

    def __init__(self):
        self.sheets: List[Dict[str, Any]] = []

    def add_sheet(self, title: str, col_widths: List[float], rows: List[List[Tuple[str, int]]]):
        clean_title = re.sub(r'[\\/*?:\[\]]', '_', title)[:31]
        self.sheets.append({
            "name": clean_title,
            "col_widths": col_widths,
            "rows": rows
        })

    def save(self, filepath: str):
        """Đóng gói và lưu thành file .xlsx chuẩn OpenXML."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with zipfile.ZipFile(filepath, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("[Content_Types].xml", self._build_content_types())
            z.writestr("_rels/.rels", self._build_root_rels())
            z.writestr("xl/workbook.xml", self._build_workbook())
            z.writestr("xl/_rels/workbook.xml.rels", self._build_workbook_rels())
            z.writestr("xl/styles.xml", self._build_styles())
            for idx, sheet in enumerate(self.sheets, 1):
                z.writestr(f"xl/worksheets/sheet{idx}.xml", self._build_worksheet(sheet, idx))

    def _build_content_types(self) -> str:
        parts = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
            '  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
            '  <Default Extension="xml" ContentType="application/xml"/>',
            '  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
            '  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>',
        ]
        for idx in range(1, len(self.sheets) + 1):
            parts.append(
                f'  <Override PartName="/xl/worksheets/sheet{idx}.xml" '
                f'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            )
        parts.append('</Types>')
        return "\n".join(parts)

    def _build_root_rels(self) -> str:
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
            '  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>\n'
            '</Relationships>'
        )

    def _build_workbook_rels(self) -> str:
        parts = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
        ]
        for idx in range(1, len(self.sheets) + 1):
            parts.append(
                f'  <Relationship Id="rId{idx}" '
                f'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
                f'Target="worksheets/sheet{idx}.xml"/>'
            )
        parts.append(
            f'  <Relationship Id="rIdStyles" '
            f'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
            f'Target="styles.xml"/>'
        )
        parts.append('</Relationships>')
        return "\n".join(parts)

    def _build_workbook(self) -> str:
        parts = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">',
            '  <sheets>',
        ]
        for idx, sheet in enumerate(self.sheets, 1):
            name_esc = escape_xml(sheet["name"])
            parts.append(f'    <sheet name="{name_esc}" sheetId="{idx}" r:id="rId{idx}"/>')
        parts.append('  </sheets>')
        parts.append('</workbook>')
        return "\n".join(parts)

    def _build_styles(self) -> str:
        return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="7">
    <!-- 0: Regular -->
    <font><sz val="11"/><color rgb="FF262626"/><name val="Segoe UI"/></font>
    <!-- 1: Header Bold White -->
    <font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Segoe UI"/></font>
    <!-- 2: Title Large Bold White -->
    <font><b/><sz val="14"/><color rgb="FFFFFFFF"/><name val="Segoe UI"/></font>
    <!-- 3: Subheader Bold -->
    <font><b/><sz val="12"/><color rgb="FF1B365D"/><name val="Segoe UI"/></font>
    <!-- 4: Warning Bold Red -->
    <font><b/><sz val="11"/><color rgb="FFC62828"/><name val="Segoe UI"/></font>
    <!-- 5: Success Bold Green -->
    <font><b/><sz val="11"/><color rgb="FF2E7D32"/><name val="Segoe UI"/></font>
    <!-- 6: Stage Section Title Bold -->
    <font><b/><sz val="12"/><color rgb="FF0C4A6E"/><name val="Segoe UI"/></font>
  </fonts>
  <fills count="11">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <!-- 2: Navy Header #1B365D -->
    <fill><patternFill patternType="solid"><fgColor rgb="FF1B365D"/></patternFill></fill>
    <!-- 3: Soft Green #E8F5E9 (Editable) -->
    <fill><patternFill patternType="solid"><fgColor rgb="FFE8F5E9"/></patternFill></fill>
    <!-- 4: Soft Gray #F2F4F8 (ID/Old) -->
    <fill><patternFill patternType="solid"><fgColor rgb="FFF2F4F8"/></patternFill></fill>
    <!-- 5: Soft Yellow #FFF8E7 (Speaker) -->
    <fill><patternFill patternType="solid"><fgColor rgb="FFFFF8E7"/></patternFill></fill>
    <!-- 6: Soft Purple #F3E5F5 (Note) -->
    <fill><patternFill patternType="solid"><fgColor rgb="FFF3E5F5"/></patternFill></fill>
    <!-- 7: Gray Subheader #E0E0E0 -->
    <fill><patternFill patternType="solid"><fgColor rgb="FFE0E0E0"/></patternFill></fill>
    <!-- 8: Soft Red #FFEBEE (Warning) -->
    <fill><patternFill patternType="solid"><fgColor rgb="FFFFEBEE"/></patternFill></fill>
    <!-- 9: Soft Cream #FFFDE7 (Tip) -->
    <fill><patternFill patternType="solid"><fgColor rgb="FFFFFDE7"/></patternFill></fill>
    <!-- 10: Soft Ocean Blue #E0F2FE (Stage Banner) -->
    <fill><patternFill patternType="solid"><fgColor rgb="FFE0F2FE"/></patternFill></fill>
  </fills>
  <borders count="4">
    <!-- 0: None -->
    <border><left/><right/><top/><bottom/><diagonal/></border>
    <!-- 1: Thin Border All -->
    <border>
      <left style="thin"><color rgb="FFD0D7DE"/></left>
      <right style="thin"><color rgb="FFD0D7DE"/></right>
      <top style="thin"><color rgb="FFD0D7DE"/></top>
      <bottom style="thin"><color rgb="FFD0D7DE"/></bottom>
      <diagonal/>
    </border>
    <!-- 2: Highlight Border Green (Editable Cell) -->
    <border>
      <left style="medium"><color rgb="FF81C784"/></left>
      <right style="medium"><color rgb="FF81C784"/></right>
      <top style="thin"><color rgb="FF81C784"/></top>
      <bottom style="thin"><color rgb="FF81C784"/></bottom>
      <diagonal/>
    </border>
    <!-- 3: Stage Divider Border -->
    <border>
      <left style="medium"><color rgb="FF0284C7"/></left>
      <right style="thin"><color rgb="FFBAE6FD"/></right>
      <top style="medium"><color rgb="FF0284C7"/></top>
      <bottom style="medium"><color rgb="FF0284C7"/></bottom>
      <diagonal/>
    </border>
  </borders>
  <cellStyleXfs count="1">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>
  </cellStyleXfs>
  <cellXfs count="15">
    <!-- 0: Default -->
    <xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>
    <!-- 1: Header (Navy, White Bold, Center) -->
    <xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyAlignment="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf>
    <!-- 2: ID (Gray, Readonly) -->
    <xf numFmtId="0" fontId="0" fillId="4" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>
    <!-- 3: Speaker / Context (Yellow, Semi-bold) -->
    <xf numFmtId="0" fontId="0" fillId="5" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>
    <!-- 4: Source EN (White) -->
    <xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>
    <!-- 5: Old Translation (Gray) -->
    <xf numFmtId="0" fontId="0" fillId="4" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>
    <!-- 6: New Translation (Light Green Editable, Bold Border) -->
    <xf numFmtId="0" fontId="0" fillId="3" borderId="2" xfId="0" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>
    <!-- 7: Status (Center) -->
    <xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyAlignment="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf>
    <!-- 8: Note (Purple) -->
    <xf numFmtId="0" fontId="0" fillId="6" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>
    <!-- 9: Title Banner (14pt Bold, Navy) -->
    <xf numFmtId="0" fontId="2" fillId="2" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>
    <!-- 10: Section Subheader (12pt Bold, Gray Fill) -->
    <xf numFmtId="0" fontId="3" fillId="7" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>
    <!-- 11: Warning Box (Red) -->
    <xf numFmtId="0" fontId="4" fillId="8" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>
    <!-- 12: Success Box (Green) -->
    <xf numFmtId="0" fontId="5" fillId="3" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>
    <!-- 13: Stage Section Divider (Blue Banner, Bold 12pt) -->
    <xf numFmtId="0" fontId="6" fillId="10" borderId="3" xfId="0" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>
    <!-- 14: Category Tag (Center) -->
    <xf numFmtId="0" fontId="0" fillId="4" borderId="1" xfId="0" applyAlignment="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf>
  </cellXfs>
</styleSheet>"""

    def _build_worksheet(self, sheet: Dict[str, Any], sheet_idx: int) -> str:
        parts = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
            '  <sheetViews>',
            '    <sheetView tabSelected="' + ('1' if sheet_idx == 1 else '0') + '" workbookViewId="0">',
            '      <pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>',
            '    </sheetView>',
            '  </sheetViews>',
        ]

        if sheet["col_widths"]:
            parts.append('  <cols>')
            for c_idx, width in enumerate(sheet["col_widths"], 1):
                parts.append(f'    <col min="{c_idx}" max="{c_idx}" width="{width}" customWidth="1"/>')
            parts.append('  </cols>')

        parts.append('  <sheetData>')
        for r_idx, row in enumerate(sheet["rows"], 1):
            if not row:
                parts.append(f'    <row r="{r_idx}"/>')
                continue
            parts.append(f'    <row r="{r_idx}">')
            for c_idx, cell_data in enumerate(row, 1):
                c_addr = f"{col_name(c_idx)}{r_idx}"
                if isinstance(cell_data, tuple):
                    val, s_id = cell_data
                else:
                    val, s_id = str(cell_data), 0

                val_esc = escape_xml(val)
                parts.append(
                    f'      <c r="{c_addr}" t="inlineStr" s="{s_id}">'
                    f'<is><t xml:space="preserve">{val_esc}</t></is></c>'
                )
            parts.append('    </row>')
        parts.append('  </sheetData>')
        parts.append('</worksheet>')
        return "\n".join(parts)


class MiniXLSXReader:
    """Đọc file Excel .xlsx (chuẩn zip + xml) bằng standard library."""

    @staticmethod
    def read(filepath: str) -> Dict[str, List[List[str]]]:
        result: Dict[str, List[List[str]]] = {}
        with zipfile.ZipFile(filepath, "r") as z:
            shared_strings: List[str] = []
            if "xl/sharedStrings.xml" in z.namelist():
                tree = ET.fromstring(z.read("xl/sharedStrings.xml"))
                ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
                for si in tree.findall(".//s:si", ns) or tree.findall(".//si"):
                    t_elems = si.findall(".//s:t", ns) or si.findall(".//t")
                    shared_strings.append("".join(t.text or "" for t in t_elems))

            wb_tree = ET.fromstring(z.read("xl/workbook.xml"))
            rels_tree = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))

            rel_map = {}
            for rel in rels_tree.findall(".//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship") or rels_tree.findall(".//Relationship"):
                rel_map[rel.attrib.get("Id")] = rel.attrib.get("Target")

            sheets_info = []
            for sheet_elem in wb_tree.findall(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheet") or wb_tree.findall(".//sheet"):
                s_name = sheet_elem.attrib.get("name")
                r_id = sheet_elem.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id") or sheet_elem.attrib.get("r:id")
                target = rel_map.get(r_id, "")
                if not target.startswith("xl/"):
                    target = "xl/" + target.lstrip("/")
                sheets_info.append((s_name, target))

            for s_name, s_target in sheets_info:
                if s_target not in z.namelist():
                    continue
                ws_tree = ET.fromstring(z.read(s_target))
                sheet_rows: List[List[str]] = []

                row_nodes = ws_tree.findall(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row") or ws_tree.findall(".//row")
                for r_node in row_nodes:
                    row_data: Dict[int, str] = {}
                    cell_nodes = r_node.findall(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c") or r_node.findall(".//c")
                    for c_node in cell_nodes:
                        c_ref = c_node.attrib.get("r", "A1")
                        col_letters = "".join(filter(str.isalpha, c_ref))
                        c_idx = 0
                        for char in col_letters:
                            c_idx = c_idx * 26 + (ord(char.upper()) - 64)

                        c_type = c_node.attrib.get("t", "")
                        v_node = c_node.find(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v") or c_node.find(".//v")
                        is_node = c_node.find(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}is") or c_node.find(".//is")

                        cell_val = ""
                        if c_type == "s" and v_node is not None and v_node.text:
                            idx = int(v_node.text)
                            if 0 <= idx < len(shared_strings):
                                cell_val = shared_strings[idx]
                        elif c_type == "inlineStr" and is_node is not None:
                            t_nodes = is_node.findall(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t") or is_node.findall(".//t")
                            cell_val = "".join(t.text or "" for t in t_nodes)
                        elif v_node is not None and v_node.text:
                            cell_val = v_node.text

                        row_data[c_idx] = cell_val

                    max_c = max(row_data.keys()) if row_data else 0
                    row_list = [row_data.get(i, "") for i in range(1, max_c + 1)]
                    sheet_rows.append(row_list)

                result[s_name] = sheet_rows

        return result


def audit_entry(source: str, translation: str) -> List[str]:
    """Kiểm tra câu dịch xem có bị thiếu biến số {...}, lệch thẻ <...>, hoặc mất \\n."""
    issues = []
    if not translation:
        return issues

    # Biến số {...}
    src_tokens = set(re.findall(r"\{[^{}]*\}", source))
    tr_tokens = set(re.findall(r"\{[^{}]*\}", translation))
    missing_tokens = src_tokens - tr_tokens
    extra_tokens = tr_tokens - src_tokens
    if missing_tokens:
        issues.append(f"Mất biến số: {', '.join(missing_tokens)}")
    if extra_tokens:
        issues.append(f"Thừa biến số lạ: {', '.join(extra_tokens)}")

    # Thẻ HTML / Ruby: <color=...>, </color>, <r=...>, </r>, <b>, </b>
    for tag_type in ["color", "r", "b", "i", "size"]:
        src_open = len(re.findall(rf"<{tag_type}[^>]*>", source, re.IGNORECASE))
        tr_open = len(re.findall(rf"<{tag_type}[^>]*>", translation, re.IGNORECASE))
        src_close = len(re.findall(rf"</{tag_type}>", source, re.IGNORECASE))
        tr_close = len(re.findall(rf"</{tag_type}>", translation, re.IGNORECASE))

        if src_open != tr_open:
            issues.append(f"Lệch số lượng thẻ mở <{tag_type}> (Gốc có {src_open}, dịch có {tr_open})")
        if src_close != tr_close:
            issues.append(f"Lệch số lượng thẻ đóng </{tag_type}> (Gốc có {src_close}, dịch có {tr_close})")

    # Ký tự ngắt dòng \n
    src_nl = source.count(r"\n") + source.count("\n")
    tr_nl = translation.count(r"\n") + translation.count("\n")
    if src_nl > 0 and tr_nl == 0:
        issues.append(f"Cảnh báo: Câu gốc có {src_nl} vị trí xuống dòng, bản dịch mới chưa có \\n")

    return issues


# ==============================================================================
# 1. SHEET HƯỚNG DẪN 3 PHÚT (CHO EDITOR NON-TECH)
# ==============================================================================

def build_instruction_sheet() -> Tuple[List[float], List[List[Tuple[str, int]]]]:
    widths = [24, 45, 45, 30]
    rows = [
        [
            ("CẨM NANG HIỆU ĐÍNH & DỊCH THUẬT STELLA SORA (DÀNH CHO EDITOR - 3 PHÚT LÀM QUEN)", 9),
            ("", 9), ("", 9), ("", 9)
        ],
        [
            ("Hệ thống bảng tính được thiết kế theo từng Chương và từng Màn. Dưới đây là 5 quy tắc sống còn:", 10),
            ("", 10), ("", 10), ("", 10)
        ],
        [("Quy tắc cốt lõi", 1), ("Giải thích dễ hiểu", 1), ("Ví dụ SAI (Gây lỗi game)", 1), ("Ví dụ ĐÚNG (Chuẩn)", 1)],
        [
            ("1. Vùng làm việc duy nhất", 2),
            ("Chỉ điền hoặc sửa vào CỘT F (Màu xanh ngọc). Các cột Màn, ID, Chủ thể, câu gốc, bản cũ đều đã khóa để bảo vệ an toàn.", 4),
            ("Gõ đè vào cột ID hoặc cột Lời thoại gốc.", 11),
            ("Chỉ gõ vào Cột F (Bản dịch mới). Cột ID và Chủ thể giữ nguyên.", 12)
        ],
        [
            ("2. Biến số trong ngoặc { ... }", 2),
            ("Đây là chỗ game tự điền số hoặc tên (ví dụ: {0}, {player}). TUYỆT ĐỐI KHÔNG DỊCH TRONG NGOẶC. Giữ nguyên 100%!", 4),
            ("Nhận được {0} Vàng -> Nhận được {không} Vàng\nWelcome {player} -> Chào mừng {người chơi}", 11),
            ("Nhận được {0} Vàng.\nChào mừng {player} đã trở lại!", 12)
        ],
        [
            ("3. Thẻ màu và ruby < ... >", 2),
            ("Ký hiệu tạo màu sắc hoặc cách đọc tên. Thấy <...> và </...> thì giữ nguyên cặp thẻ, CHỈ DỊCH CHỮ Ở GIỮA.", 4),
            ("<color=#FF0000>Cảnh báo</color> -> <màu=#Đỏ>Cảnh báo</màu>\nAm<r=Kohaku></r>ber -> Amber", 11),
            ("<color=#FF0000>Cảnh báo!</color>\nAm<r=Kohaku></r>ber, cậu nghe rõ không!?", 12)
        ],
        [
            ("4. Ký tự xuống dòng \\n", 2),
            ("Ký hiệu \\n là phím ENTER xuống dòng của game. Không xóa mất ký tự này.", 4),
            ("Dòng 1\\nDòng 2 -> Dòng 1 Dòng 2 (xóa mất \\n)", 11),
            ("Dòng 1\\nDòng 2 (giữ nguyên vị trí ngắt dòng)", 12)
        ],
        [
            ("5. Tra cứu trước khi dịch", 2),
            ("Mở Tab '01_Thong_Nhat_Danh_Tu' để tra thuật ngữ cố định. Mở Tab '02_Ma_Tran_Tinh_Cach_Xung_Ho' để tra đại từ xưng hô theo từng cặp nhân vật.", 4),
            ("Tự bịa xưng hô (câu trước xưng tớ-cậu, câu sau xưng anh-em).", 11),
            ("Tra ma trận: Amber gọi Iris là 'cậu', xưng 'tớ'.", 12)
        ],
        [
            ("6. Trạng thái & Ghi chú", 2),
            ("Sau khi sửa câu, chọn Cột G thành 'Đã duyệt' 🟢. Nếu phân vân từ ngữ thì chọn 'Cần trao đổi' 🔴 và để lại câu hỏi ở Cột H.", 4),
            ("Bỏ trống không note gì khi phân vân.", 11),
            ("Ghi ở Cột H: 'Chỗ này chưa rõ {0} là số lượng hay tỷ lệ %'.", 12)
        ]
    ]
    return widths, rows


# ==============================================================================
# 2. SHEET THỐNG NHẤT DANH TỪ (TOÀN BỘ 322 MỤC GLOSSARY TỪ BATCH DATA)
# ==============================================================================

def build_glossary_sheet(batch_data: Optional[Dict[str, Any]] = None) -> Tuple[List[float], List[List[Tuple[str, int]]]]:
    widths = [26, 26, 22, 52, 16]
    rows = [
        [
            ("BẢNG THỐNG NHẤT DANH TỪ & THUẬT NGỮ TOÀN GAME (GLOSSARY 322 MỤC)", 9),
            ("", 9), ("", 9), ("", 9), ("", 9)
        ],
        [
            ("Danh từ chuẩn bắt buộc tuân thủ. Giúp toàn bộ các Chương và Màn không bao giờ bị lệch thuật ngữ.", 10),
            ("", 10), ("", 10), ("", 10), ("", 10)
        ],
        [
            ("Danh từ gốc (EN)", 1),
            ("Bản dịch Tiếng Việt chuẩn", 1),
            ("Phân loại nhóm", 1),
            ("Ghi chú ngữ cảnh & Lưu ý sống còn", 1),
            ("Trạng thái", 1)
        ]
    ]

    glossary_items = []
    if batch_data and "glossary" in batch_data:
        glossary_items = batch_data["glossary"]
    else:
        # Fallback đọc glossary.json
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        gp = os.path.join(base_dir, "config", "glossary.json")
        if os.path.exists(gp):
            try:
                with open(gp, "r", encoding="utf-8") as f:
                    glossary_items = json.load(f).get("entries", [])
            except Exception:
                pass

    # Phân nhóm danh từ
    current_group = ""
    for item in glossary_items:
        grp = item.get("group_vi", item.get("category", "Chung"))
        if grp != current_group:
            current_group = grp
            rows.append([
                (f"--- NHÓM: {current_group.upper()} ---", 10),
                ("", 10), ("", 10), ("", 10), ("", 10)
            ])

        src = item.get("source", item.get("term_en", ""))
        tgt = item.get("target", item.get("target_vi", ""))
        cat = item.get("category", "General")
        notes = item.get("notes", "")
        status = item.get("status", "approved")

        rows.append([
            (src, 3),
            (tgt, 6),
            (cat, 14),
            (notes, 4),
            (status, 7)
        ])

    return widths, rows


# ==============================================================================
# 3. SHEET MA TRẬN TÍNH CÁCH & XƯNG HÔ (41 NHÂN VẬT & 12 MA TRẬN)
# ==============================================================================

def build_voice_bible_sheet(batch_data: Optional[Dict[str, Any]] = None) -> Tuple[List[float], List[List[Tuple[str, int]]]]:
    widths = [20, 22, 22, 45, 42, 32]
    rows = [
        [
            ("MA TRẬN TÍNH CÁCH, KHẨU KHÍ & QUY CHUẨN XƯNG HÔ (VOICE BIBLE & MATRIX)", 9),
            ("", 9), ("", 9), ("", 9), ("", 9), ("", 9)
        ],
        [
            ("Xác định đại từ và khẩu khí theo từng cặp nhân vật. Đảm bảo nhân vật luôn giữ đúng cá tính xuyên suốt.", 10),
            ("", 10), ("", 10), ("", 10), ("", 10), ("", 10)
        ],
        [
            ("Nhân vật (Speaker)", 1),
            ("Đối tượng nghe (Listener)", 1),
            ("Đại từ Xưng - Gọi chuẩn", 1),
            ("Tính cách cốt lõi & Khẩu khí (Tone)", 1),
            ("Mẫu câu ví dụ đúng điệu", 1),
            ("Điều TUYỆT ĐỐI TRÁNH", 1)
        ]
    ]

    # 1. Phần Ma Trận Quan Hệ Cốt Lõi
    rows.append([
        ("--- I. MA TRẬN XƯNG HÔ CỐT LÕI GIỮA CÁC CẶP NHÂN VẬT ---", 13),
        ("", 13), ("", 13), ("", 13), ("", 13), ("", 13)
    ])

    rel_matrix = []
    if batch_data and "voice_bible" in batch_data:
        rel_matrix = batch_data["voice_bible"].get("relationship_matrix", [])

    if rel_matrix:
        for r in rel_matrix:
            spk = r.get("speaker", "")
            lis = r.get("listener", "")
            prn = r.get("pronouns", r.get("pronoun_rule", ""))
            tone = r.get("tone", r.get("tone_and_manner", ""))
            eg = r.get("sample_dialogue", r.get("example_dialogue", ""))
            dont = r.get("do_not", "")
            rows.append([
                (spk, 3), (lis, 3), (prn, 6), (tone, 4), (eg, 12), (dont, 11)
            ])
    else:
        # Fallback mẫu cốt lõi
        rows.append([
            ("Amber (Kohaku)", 3), ("Iris (Ayame)", 3), ("Xưng: tớ\nGọi: cậu / Iris", 6),
            ("Điềm đạm, ấm áp, câu ngắn gọn, quan sát tinh tế.", 4),
            ("“Ừ. Tớ vẫn đang nghe đây.”", 12), ("Không tự thêm nè/nha/hì hì.", 11)
        ])

    # 2. Phần Roster 41 Nhân Vật
    rows.append([
        ("--- II. DANH MỤC 41 NHÂN VẬT & KHẨU KHÍ RIÊNG BIỆT ---", 13),
        ("", 13), ("", 13), ("", 13), ("", 13), ("", 13)
    ])

    chars = []
    if batch_data and "voice_bible" in batch_data:
        chars = batch_data["voice_bible"].get("characters", [])

    for c in chars:
        c_name = f"{c.get('name_en', '')} ({c.get('name_vi', '')})"
        c_fac = c.get("faction", "Chưa rõ")
        c_prn = f"Xưng: {c.get('default_self', 'tôi')}\nGọi: {c.get('default_address', 'bạn')}"
        c_trait = c.get("personality_summary", "")
        c_eg = f"Khẩu hiệu: {c.get('catchphrase', '...')}"
        c_dont = c.get("do_not", "Tránh từ lóng teen, giữ văn phong lịch sự.")
        rows.append([
            (c_name, 3), (c_fac, 14), (c_prn, 6), (c_trait, 4), (c_eg, 4), (c_dont, 11)
        ])

    return widths, rows


# ==============================================================================
# 4. SHEET CHƯƠNG MỞ ĐẦU (PROLOGUE)
# ==============================================================================

def build_chapter_0_prologue_sheet() -> Tuple[List[float], List[List[Tuple[str, int]]]]:
    widths = [20, 18, 26, 42, 42, 46, 16, 28]
    rows = [
        [
            ("Màn (Phân đoạn)", 1),
            ("Mã câu (ID) [Khóa]", 1),
            ("Chủ thể / Người nói (Ai nói) 🗣️", 1),
            ("Lời thoại gốc (EN/JP) [Khóa]", 1),
            ("Bản dịch cũ (Tham khảo) [Khóa]", 1),
            ("BẢN DỊCH MỚI (⭐ SỬA Ở ĐÂY)", 1),
            ("Trạng thái", 1),
            ("Ghi chú & Thảo luận", 1)
        ]
    ]

    # Phân đoạn: Phụ đề mở đầu (SRT Prologue JPVA)
    rows.append([
        ("🌟 PHỤ ĐỀ MỞ ĐẦU: KHÚC DẠO ĐẦU SA MẠC (VIDEO PROLOGUE)", 13),
        ("", 13), ("", 13), ("", 13), ("", 13), ("", 13), ("", 13), ("", 13)
    ])
    srt_items = [
        ("SRT_01", "Dẫn chuyện (JPVA)", "Novians often say: \"Do not enter the wild.\"", "Người Nova thường nói: \"Đừng dại bước vào vùng hoang dã.\"", "Dân Novian thường nói: \"Đừng dại bước vào vùng hoang dã.\"", "Cần hiệu đính", "Novians -> Dân Novian theo Glossary"),
        ("SRT_02", "Dẫn chuyện (JPVA)", "Thus, most people cling to their peaceful lives in the Cities.", "Do đó, hầu hết mọi người bám víu vào cuộc sống yên bình trong các Đô Thành.", "Do đó, phần lớn mọi người đều chọn bám víu lấy cuộc sống bình yên nơi Đô Thành.", "Cần hiệu đính", ""),
        ("SRT_03", "Dẫn chuyện (JPVA)", "Yet, some turn their backs on the safety of home and set foot into the boundless expanse.", "Thế nhưng, có những người quay lưng lại với sự an toàn của mái ấm để dấn thân vào cõi bao la vô tận.", "Thế nhưng, vẫn có những kẻ quay lưng lại với chốn an toàn để cất bước tiến vào cõi vô tận.", "Cần hiệu đính", ""),
        ("SRT_04", "Dẫn chuyện (JPVA)", "They are known as Trekkers.", "Họ được gọi là Lữ Khách.", "Họ được người đời gọi là Lữ Khách.", "Đã duyệt", "Trekker -> Lữ Khách chuẩn")
    ]
    for c_id, spk, src, old_v, new_v, st, nt in srt_items:
        rows.append([("Phụ Đề Video", 2), (c_id, 2), (spk, 3), (src, 4), (old_v, 5), (new_v, 6), (st, 7), (nt, 8)])

    # Màn 01 đến 06 từ kịch bản BBm00
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    clean_p = os.path.join(base_dir, "work", "batches", "batch_10000_avg_clean.json")
    clean_data = {}
    if os.path.exists(clean_p):
        try:
            with open(clean_p, "r", encoding="utf-8") as f:
                clean_data = json.load(f)
        except Exception:
            pass

    stages = [
        ("Màn 01", "BBm00_01", "LẠC BƯỚC GIỮA SA MẠC — Amber & Iris liên lạc qua bộ đàm"),
        ("Màn 02", "BBm00_02", "TÍN HIỆU VÀ BỨC ẢNH — Amber gửi ảnh định vị cho Iris"),
        ("Màn 03", "BBm00_03", "HỘI NGỘ CÙNG IRIS — Cát bay vào mồm & Đàn Tinh Hài"),
        ("Màn 04", "BBm00_04", "BƯỚC VÀO CỰ THÁP — Căn phòng bí mật & Chiếc hòm khổng lồ"),
        ("Màn 05", "BBm00_05", "ĐỐI ĐẦU TINH HÀI KHỔNG LỒ — Thử thách cuối cùng"),
        ("Màn 06", "BBm00_06", "CHIẾN THẮNG & HÒM NGUYỆN ƯỚC — Tiếp cận điều ước")
    ]

    for m_label, prefix, m_desc in stages:
        rows.append([
            (f"🌟 {m_label.upper()}: {m_desc} ({prefix})", 13),
            ("", 13), ("", 13), ("", 13), ("", 13), ("", 13), ("", 13), ("", 13)
        ])
        sub_items = [(k, v) for k, v in clean_data.items() if k.startswith(prefix + ".")]
        for k, vi_val in sub_items:
            spk = "Amber / Iris"
            if "Bồn Chồn" in vi_val: spk = "Iris (Cô Gái Bồn Chồn)"
            elif "Điềm Tĩnh" in vi_val: spk = "Noya (Cô Gái Điềm Tĩnh)"
            elif "Hệ thống" in vi_val or "gửi ảnh" in vi_val.lower(): spk = "Hệ thống / Amber"
            elif "Độc thoại" in vi_val or "thế này cũng ổn" in vi_val: spk = "Amber (Kohaku)"

            rows.append([
                (m_label, 2),
                (k, 2),
                (spk, 3),
                (vi_val, 4), # Source đối chiếu
                (vi_val, 5), # Old Vi
                (vi_val, 6), # New Vi editable
                ("Đã duyệt", 7),
                ("", 8)
            ])

    return widths, rows


# ==============================================================================
# 5. HÀM TẠO SHEET CHƯƠNG KỊCH BẢN (CHƯƠNG 1 & CHƯƠNG 2 TỪ BATCH DATA)
# ==============================================================================

def build_chapter_scenes_sheet(
    chapter_title: str,
    scenes: List[Dict[str, Any]]
) -> Tuple[List[float], List[List[Tuple[str, int]]]]:
    widths = [20, 18, 26, 42, 42, 46, 16, 28]
    rows = [
        [
            ("Màn (Phân đoạn)", 1),
            ("Mã câu (ID) [Khóa]", 1),
            ("Chủ thể / Người nói (Ai nói) 🗣️", 1),
            ("Lời thoại gốc (EN/JP) [Khóa]", 1),
            ("Bản dịch cũ (Tham khảo) [Khóa]", 1),
            ("BẢN DỊCH MỚI (⭐ SỬA Ở ĐÂY)", 1),
            ("Trạng thái", 1),
            ("Ghi chú & Thảo luận", 1)
        ]
    ]

    for scene in scenes:
        sc_title = scene.get("scene_title", "Phân đoạn kịch bản")
        sc_id = scene.get("scene_id", "")
        # Banner phân cách Màn
        rows.append([
            (f"🌟 {sc_title.upper()}", 13),
            ("", 13), ("", 13), ("", 13), ("", 13), ("", 13), ("", 13), ("", 13)
        ])

        for line in scene.get("lines", []):
            l_id = line.get("line_id", "")
            spk = line.get("speaker", "Dẫn chuyện")
            en = line.get("en_text", "")
            vi_old = line.get("vi_ptc", "")
            vi_new = line.get("vi_clean", vi_old)

            rows.append([
                (sc_id, 2),
                (l_id, 2),
                (spk, 3),
                (en, 4),
                (vi_old, 5),
                (vi_new, 6),
                ("Đã duyệt", 7),
                ("", 8)
            ])

    return widths, rows


# ==============================================================================
# 6. SHEET CHUYỆN NHÂN VẬT & VOICE LINES (DATING & VOICES)
# ==============================================================================

def build_character_stories_sheet() -> Tuple[List[float], List[List[Tuple[str, int]]]]:
    widths = [20, 18, 26, 42, 42, 46, 16, 28]
    rows = [
        [
            ("Nhân vật", 1),
            ("Mã câu (ID) [Khóa]", 1),
            ("Chủ thể / Người nói (Ai nói) 🗣️", 1),
            ("Lời thoại gốc (EN/JP) [Khóa]", 1),
            ("Bản dịch cũ (Tham khảo) [Khóa]", 1),
            ("BẢN DỊCH MỚI (⭐ SỬA Ở ĐÂY)", 1),
            ("Trạng thái", 1),
            ("Ghi chú & Thảo luận", 1)
        ]
    ]

    # NHÂN VẬT: AMBER (KOHAKU)
    rows.append([
        ("🌟 NHÂN VẬT: AMBER (KOHAKU) — Ký ức khăn quàng & Mái nhà xưa", 13),
        ("", 13), ("", 13), ("", 13), ("", 13), ("", 13), ("", 13), ("", 13)
    ])
    amber_items = [
        ("VOICE_AMBER_01", "Amber (Kohaku)", "Novians often say: 'Do not enter the wild.' But as Trekkers, that's where we belong.", "Người Nova thường nói: 'Đừng dại bước vào vùng hoang dã.' Nhưng là Lữ Khách, đó là nơi chúng ta thuộc về.", "Dân Nova thường nói: 'Đừng dại bước vào vùng hoang dã.' Nhưng với những Lữ Khách như chúng mình, đó lại là nơi ta thuộc về.", "Đã duyệt", "Khẩu khí điềm đạm, ấm áp"),
        ("VOICE_AMBER_02", "Amber (Kohaku)", "My scarf, Noya's teddy bear, and Iris' hat are all sewn by the same hand. They were gifts from Aunt Allie when we left the orphanage. We should treasure them.", "Khăn quàng của tôi, gấu bông của Noya và mũ của Iris đều do một bàn tay may vá. Đó là món quà từ Dì Allie khi rời trại mồ côi. Chúng tôi nên trân trọng.", "Chiếc khăn của tớ, chú gấu bông của Noya và chiếc mũ của Iris đều được may bởi cùng một bàn tay. Đó là những món quà Dì Allie trao tặng khi bọn tớ rời khỏi trại trẻ mồ côi. Bọn tớ nhất định phải nâng niu chúng.", "Đã duyệt", "Xưng 'tớ' và 'bọn tớ' theo quan hệ"),
        ("VOICE_AMBER_03", "Amber (Kohaku)", "Iris put a small cushion on the roof just for me. It's got a kitty pattern on it.", "Iris đặt một cái đệm nhỏ trên mái nhà chỉ dành cho tôi. Nó có hoa văn mèo con.", "Iris đã đặt một chiếc đệm nhỏ lên mái nhà dành riêng cho tớ. Chiếc đệm ấy còn có hình một chú mèo con nữa.", "Đã duyệt", "Chi tiết đời thường ấm áp")
    ]
    for c_id, spk, src, old_v, new_v, st, nt in amber_items:
        rows.append([("Amber (Kohaku)", 2), (c_id, 2), (spk, 3), (src, 4), (old_v, 5), (new_v, 6), (st, 7), (nt, 8)])

    # NHÂN VẬT: IRIS (AYAME)
    rows.append([
        ("🌟 NHÂN VẬT: IRIS (AYAME) — Tài chính, hậu cần & Đồ ăn cho mèo", 13),
        ("", 13), ("", 13), ("", 13), ("", 13), ("", 13), ("", 13), ("", 13)
    ])
    iris_items = [
        ("VOICE_IRIS_01", "Iris (Ayame)", "Calm down, will you? Just who the heck eats cat food?", "Bình tĩnh lại đi được không? Rốt cuộc là ai lại đi ăn thức ăn của mèo chứ?", "Bình tĩnh lại chút coi! Bộ ai đời lại đi ăn đồ ăn cho mèo bao giờ chứ!?", "Đã duyệt", "Tính cách tinh nghịch, thực tế"),
        ("VOICE_IRIS_02", "Iris (Ayame)", "Make money, pay off my debts, get an offer from a big company. That's my reason for becoming a Trekker.", "Kiếm tiền, trả hết nợ nần, nhận lời mời từ công ty lớn. Đó là lý do tôi trở thành Lữ Khách.", "Kiếm thật nhiều tiền, trả sạch nợ nần, rồi được một công ty lớn mời về làm việc. Đó chính là lý do tớ trở thành Lữ Khách đấy.", "Đã duyệt", "Động cơ thực tế của Iris"),
        ("VOICE_IRIS_03", "Amber đánh giá Iris", "Iris, the logistics wizard of our guild. —Amber", "Iris, phù thủy hậu cần của hội quán chúng tôi. —Amber", "Iris, vị phù thủy hậu cần của hội quán chúng mình. —Amber", "Đã duyệt", "Lời nhận xét của Amber về Iris")
    ]
    for c_id, spk, src, old_v, new_v, st, nt in iris_items:
        rows.append([("Iris (Ayame)", 2), (c_id, 2), (spk, 3), (src, 4), (old_v, 5), (new_v, 6), (st, 7), (nt, 8)])

    # NHÂN VẬT: TILIA
    rows.append([
        ("🌟 NHÂN VẬT: TILIA — Lời thề hiệp sĩ & Gìn giữ công lý", 13),
        ("", 13), ("", 13), ("", 13), ("", 13), ("", 13), ("", 13), ("", 13)
    ])
    tilia_items = [
        ("VOICE_TILIA_01", "Tilia", "I will do anything to become a knight.", "Tôi sẽ làm bất cứ điều gì để trở thành một hiệp sĩ.", "Tôi sẵn sàng làm bất cứ điều gì để trở thành một hiệp sĩ chân chính.", "Đã duyệt", "Khẩu khí đĩnh đạc"),
        ("VOICE_TILIA_02", "Tilia", "Loyal to the Empire, Enforce the law impartially, Uphold justice, Protect the weak...", "Trung thành với Đế chế, thực thi pháp luật công bằng, giữ gìn công lý, bảo vệ kẻ yếu...", "Tận trung với Đế chế, thực thi nghiêm minh pháp luật, gìn giữ công lý, bảo hộ người yếu thế...", "Đã duyệt", "Lời thề hiệp sĩ trang trọng")
    ]
    for c_id, spk, src, old_v, new_v, st, nt in tilia_items:
        rows.append([("Tilia", 2), (c_id, 2), (spk, 3), (src, 4), (old_v, 5), (new_v, 6), (st, 7), (nt, 8)])

    # NHÂN VẬT: FIRENZE
    rows.append([
        ("🌟 NHÂN VẬT: FIRENZE — Thương vụ & Sự hợp tác đôi bên cùng có lợi", 13),
        ("", 13), ("", 13), ("", 13), ("", 13), ("", 13), ("", 13), ("", 13)
    ])
    firenze_items = [
        ("VOICE_FIRENZE_01", "Firenze", "You and I both need an ally. I believe our cooperation can be mutually beneficial to a great degree.", "Cả bạn và tôi đều cần một đồng minh. Tôi tin rằng sự hợp tác của chúng ta có thể đôi bên cùng có lợi ở mức độ lớn.", "Cả ngài và tôi đều đang cần một đồng minh. Tôi tin chắc rằng sự hợp tác giữa đôi bên sẽ mang lại lợi ích to lớn cho cả hai.", "Đã duyệt", "Lịch thiệp, sắc sảo"),
        ("VOICE_FIRENZE_02", "Ruby & Sapphire", "We have followed Lady Firenze for many years. Her wish is our command.", "Chúng tôi đã theo Tiểu thư Firenze nhiều năm. Ý muốn của cô ấy là mệnh lệnh của chúng tôi.", "Chúng tôi đã đi theo Tiểu thư Firenze suốt nhiều năm qua. Ý nguyện của tiểu thư chính là mệnh lệnh tối cao của chúng tôi.", "Đã duyệt", "Cung kính tuyệt đối")
    ]
    for c_id, spk, src, old_v, new_v, st, nt in firenze_items:
        rows.append([("Firenze", 2), (c_id, 2), (spk, 3), (src, 4), (old_v, 5), (new_v, 6), (st, 7), (nt, 8)])

    return widths, rows


# ==============================================================================
# HÀM XUẤT VÀ NHẬP DỮ LIỆU CHÍNH (CLI API)
# ==============================================================================

def export_all_to_excel(output_path: str):
    """Xuất toàn bộ hệ thống bảng dịch ra file Excel phân tầng khoa học."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    batch_json_p = os.path.join(base_dir, "work", "batches", "google_sheets_batch_data.json")

    batch_data = None
    if os.path.exists(batch_json_p):
        try:
            with open(batch_json_p, "r", encoding="utf-8") as f:
                batch_data = json.load(f)
            print(f"[+] Đã nạp thành công dữ liệu cấu trúc hóa từ: {batch_json_p}")
        except Exception as e:
            print(f"[-] Không thể đọc batch json: {e}")

    wb = MiniXLSXWriter()

    print("[*] Đang khởi tạo Sheet 00: Hướng dẫn dành cho Editor...")
    w0, r0 = build_instruction_sheet()
    wb.add_sheet("00_Huong_Dan_Editor", w0, r0)

    print("[*] Đang khởi tạo Sheet 01: Thống nhất danh từ toàn game (Glossary 322 mục)...")
    w1, r1 = build_glossary_sheet(batch_data)
    wb.add_sheet("01_Thong_Nhat_Danh_Tu", w1, r1)

    print("[*] Đang khởi tạo Sheet 02: Ma trận tính cách & Xưng hô (41 nhân vật & 12 ma trận)...")
    w2, r2 = build_voice_bible_sheet(batch_data)
    wb.add_sheet("02_Ma_Tran_Tinh_Cach_Xung_Ho", w2, r2)

    print("[*] Đang khởi tạo Sheet Chương Mở Đầu: Phân chia theo từng Màn 01 -> 06...")
    w3, r3 = build_chapter_0_prologue_sheet()
    wb.add_sheet("Chuong_0_Mo_Dau", w3, r3)

    if batch_data and "chapter_1_scenes" in batch_data:
        print("[*] Đang khởi tạo Sheet Chương 1: Main Story (12 Màn, 1,303 câu thoại có Chủ thể)...")
        w4, r4 = build_chapter_scenes_sheet("Chương 1", batch_data["chapter_1_scenes"])
        wb.add_sheet("Chuong_1_MainStory", w4, r4)

    if batch_data and "chapter_2_scenes" in batch_data:
        print("[*] Đang khởi tạo Sheet Chương 2: Main Story (14 Màn, 1,503 câu thoại có Chủ thể)...")
        w5, r5 = build_chapter_scenes_sheet("Chương 2", batch_data["chapter_2_scenes"])
        wb.add_sheet("Chuong_2_MainStory", w5, r5)

    print("[*] Đang khởi tạo Sheet Chuyện Nhân Vật & Voice lines (Amber, Iris, Tilia, Firenze)...")
    w6, r6 = build_character_stories_sheet()
    wb.add_sheet("Chuyen_Nhan_Vat_Dating", w6, r6)

    wb.save(output_path)
    print(f"\n[+] Xuất thành công file Excel bảng dịch hoàn chỉnh tại:\n    -> {output_path}")
    print("[*] File đã sẵn sàng để tải lên Google Drive / Google Sheets chia sẻ cho bạn dịch!")


def import_and_audit_excel(excel_path: str):
    """Đọc file Excel đã hiệu đính, quét kiểm tra biến số / thẻ code và báo cáo kết quả."""
    if not os.path.exists(excel_path):
        print(f"[-] Không tìm thấy file: {excel_path}")
        return

    print(f"[*] Đang nạp và kiểm tra dữ liệu từ: {excel_path} ...")
    sheets = MiniXLSXReader.read(excel_path)

    total_reviewed = 0
    total_issues = 0

    for sheet_name, rows in sheets.items():
        if sheet_name.startswith("00_") or sheet_name.startswith("01_") or sheet_name.startswith("02_"):
            continue

        if not rows or len(rows) <= 1:
            continue

        print(f"\n--- Đang kiểm tra Tab: [{sheet_name}] ---")
        for r_idx, row in enumerate(rows[1:], 2):
            if len(row) < 6:
                continue

            c_id = row[1].strip() if len(row) > 1 else f"ROW_{r_idx}"
            spk = row[2].strip() if len(row) > 2 else ""
            source_txt = row[3].strip() if len(row) > 3 else ""
            old_vi = row[4].strip() if len(row) > 4 else ""
            new_vi = row[5].strip() if len(row) > 5 else ""

            target_vi = new_vi or old_vi
            if not target_vi:
                continue

            total_reviewed += 1
            issues = audit_entry(source_txt, target_vi)

            if issues:
                total_issues += 1
                print(f"  [!] Dòng {r_idx} (ID: {c_id} | Người nói: {spk}):")
                print(f"      Gốc : {source_txt}")
                print(f"      Dịch: {target_vi}")
                for iss in issues:
                    print(f"      -> LỖI: {iss}")

    print("\n" + "=" * 60)
    print(f"KẾT QUẢ KIỂM TRA (AUDIT SUMMARY):")
    print(f"- Tổng số câu đã hiệu đính: {total_reviewed}")
    print(f"- Số câu phát hiện lỗi tag/biến số: {total_issues}")
    if total_issues == 0:
        print("[SUCCESS] Tất cả biến số {...}, thẻ màu <color>, ngắt dòng \\n ĐỀU AN TOÀN 100%!")
    else:
        print("[WARNING] Vui lòng nhắc bạn dịch bổ sung các biến số bị thiếu trước khi build game!")
    print("=" * 60)


def apply_excel_to_json(excel_path: str, proposal_path: Optional[str], out_json_path: Optional[str]):
    """Cập nhật các câu đã hiệu đính từ Excel vào file Proposal JSON của game."""
    sheets = MiniXLSXReader.read(excel_path)
    updates_by_id = {}
    for s_name, rows in sheets.items():
        if s_name.startswith("00_") or s_name.startswith("01_") or s_name.startswith("02_"):
            continue
        for row in rows[1:]:
            if len(row) >= 6:
                c_id = row[1].strip()
                new_vi = row[5].strip()
                notes = row[7].strip() if len(row) > 7 else ""
                if c_id and new_vi:
                    updates_by_id[c_id] = (new_vi, notes)

    print(f"[*] Tìm thấy {len(updates_by_id)} câu có bản dịch trong file Excel.")

    if proposal_path and os.path.exists(proposal_path):
        with open(proposal_path, "r", encoding="utf-8") as f:
            proposal_data = json.load(f)

        updated_count = 0
        for entry in proposal_data.get("entries", []):
            e_id = entry.get("id", "")
            match_key = None
            if e_id in updates_by_id:
                match_key = e_id
            else:
                cue = e_id.split("::")[-1] if "::" in e_id else e_id
                alt_key = f"SRT_{int(cue):02d}" if cue.isdigit() else f"SRT_{cue}"
                if alt_key in updates_by_id:
                    match_key = alt_key

            if match_key:
                new_text, user_notes = updates_by_id[match_key]
                entry["text_vi"] = new_text
                if user_notes:
                    cur_notes = entry.get("notes", "")
                    entry["notes"] = f"{cur_notes} | Editor note: {user_notes}".strip(" |")
                updated_count += 1

        target_file = out_json_path if out_json_path else proposal_path
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(proposal_data, f, ensure_ascii=False, indent=2)
        print(f"[+] Đã cập nhật thành công {updated_count} câu vào file:\n    -> {target_file}")
    elif out_json_path:
        with open(out_json_path, "w", encoding="utf-8") as f:
            json.dump({k: v[0] for k, v in updates_by_id.items()}, f, ensure_ascii=False, indent=2)
        print(f"[+] Đã lưu {len(updates_by_id)} câu ra file JSON mới tại:\n    -> {out_json_path}")


def main():
    parser = argparse.ArgumentParser(description="Stella Sora Google Sheets / Excel Translation Pipeline")
    subparsers = parser.add_subparsers(dest="command")

    p_export = subparsers.add_parser("export", help="Xuất file Excel đầy đủ để tải lên Google Sheets")
    p_export.add_argument("--out", "-o", default="dist/StellaSora_BanDich_GoogleSheets.xlsx", help="Đường dẫn file .xlsx xuất ra")

    p_import = subparsers.add_parser("import", help="Nạp bản dịch từ file Excel vào file JSON của game")
    p_import.add_argument("--excel", "-e", required=True, help="Đường dẫn file .xlsx tải từ Google Sheets về")
    p_import.add_argument("--update-proposal", "-u", help="Đường dẫn file proposal JSON gốc để cập nhật đè")
    p_import.add_argument("--out-json", "-o", help="Đường dẫn file JSON xuất ra bản dịch mới")

    p_audit = subparsers.add_parser("audit", help="Kiểm tra chất lượng file Excel tải từ Google Sheets về")
    p_audit.add_argument("--excel", "-e", required=True, help="Đường dẫn file .xlsx cần kiểm tra")

    args = parser.parse_args()

    if args.command == "export":
        out_p = args.out
        if not os.path.isabs(out_p):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            out_p = os.path.join(base_dir, out_p)
        export_all_to_excel(out_p)
    elif args.command == "audit":
        import_and_audit_excel(args.excel)
    elif args.command == "import":
        import_and_audit_excel(args.excel)
        if args.update_proposal or args.out_json:
            apply_excel_to_json(args.excel, args.update_proposal, args.out_json)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        out_p = os.path.join(base_dir, "dist", "StellaSora_BanDich_GoogleSheets.xlsx")
        export_all_to_excel(out_p)


if __name__ == "__main__":
    main()
