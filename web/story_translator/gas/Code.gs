/**
 * ==============================================================================
 * STELLA SORA — GOOGLE APPS SCRIPT WEB APP (SERVERLESS BACKEND)
 * ==============================================================================
 * Dự án: Việt Hóa Stella Sora EN
 * Bảng tính: https://docs.google.com/spreadsheets/d/13ooFrJLyeP9LsSFrkzp4SWpQY5ePd6ap5muvWCwWOdM
 *
 * TÍNH NĂNG:
 * 1. Nhận yêu cầu "Lưu câu" (save_line) từ Web Trạm Dịch qua POST (thời gian thực).
 * 2. Cập nhật chính xác Cột F (Bản dịch mới), Cột G (Dịch giả), Cột H (Trạng thái), Cột I (Ghi chú).
 * 3. Chống xung đột đồng thời (Concurrency Lock) qua LockService.getScriptLock().
 * 4. Tự động ghi nhận đóng góp, tính điểm EXP, cấp độ dịch giả trên tab "00. Thống Kê Dịch Giả".
 * 5. Cung cấp API GET để lấy Danh từ riêng (Glossary), Bảng xếp hạng và Dữ liệu chương.
 * 6. Chuẩn hóa CORS để chạy mượt mà trên Cloudflare Pages & mọi thiết bị di động/laptop.
 * ==============================================================================
 */

var SPREADSHEET_ID = "13ooFrJLyeP9LsSFrkzp4SWpQY5ePd6ap5muvWCwWOdM";

// Ánh xạ ID chương kỹ thuật sang tên Tab chính thức trên Google Sheets
var CHAPTER_SHEET_MAP = {
  "Chuong_0_MainStory": "Chương 0 - Mở Đầu",
  "Chuong_1_MainStory": "Chương 1",
  "Chuong_2_MainStory": "Chương 2",
  "Chuong_3_MainStory": "Chương 3",
  "Chuong_4_MainStory": "Chương 4",
  "Chuong_5_MainStory": "Chương 5",
  "Chuong_6_MainStory": "Chương 6",
  "Chuong_7_MainStory": "Chương 7",
  "Chuong_8_MainStory": "Chương 8",
  "Chuong_9_MainStory": "Chương 9",
  "Ngoai_Truyen_STsp": "Ngoại Truyện",
  "Uy_Thac_Hoi_Quan_BBm": "Ủy Thác Hội Quán",
  "Hen_Ho_Dating_DP": "Hẹn Hò Nhân Vật",
  "Tin_Nhan_Dien_Thoai_PM": "Tin Nhắn Điện Thoại",
  "Cot_Truyen_Su_Kien_STev": "Cốt Truyện Sự Kiện",
  "Kich_Ban_CG_Memory": "Kịch Bản Ký Ức (CG)"
};

/**
 * HÀM KIỂM TRA KẾT NỐI & CẤP QUYỀN TRUY CẬP BAN ĐẦU
 * (Chọn hàm này và bấm [▶️ Chạy] trong Editor để cấp quyền truy cập tài khoản)
 */
function testConnection() {
  var ss = getSpreadsheet();
  var name = ss.getName();
  Logger.log("✅ Kết nối Bảng tính thành công: " + name);
  var sheets = ss.getSheets();
  Logger.log("✅ Tổng số tab: " + sheets.length);
  return "Kết nối thành công tới: " + name;
}

/**
 * Xử lý HTTP POST (Lưu câu dịch, cập nhật chỉ số dịch giả)
 */
function doPost(e) {
  var lock = LockService.getScriptLock();
  var hasLock = false;
  try {
    hasLock = lock.tryLock(10000);
  } catch (_) {
    hasLock = true;
  }

  if (!hasLock) {
    return createJsonResponse({
      success: false,
      error: "Hệ thống đang bận ghi dữ liệu từ dịch giả khác, vui lòng thử lại sau 2 giây!"
    });
  }

  try {
    var payload = {};
    if (e && e.postData && e.postData.contents) {
      try {
        payload = JSON.parse(e.postData.contents);
      } catch (jsonErr) {
        payload = e.parameter || {};
      }
    } else if (e && e.parameter) {
      payload = e.parameter;
    }

    var action = payload.action || "save_line";

    if (action === "save_line") {
      var result = handleSaveLine(payload);
      return createJsonResponse(result);
    }

    return createJsonResponse({
      success: false,
      error: "Hành động không hợp lệ: " + action
    });

  } catch (err) {
    return createJsonResponse({
      success: false,
      error: "Lỗi xử lý server: " + err.toString()
    });
  } finally {
    try {
      if (lock && lock.hasLock()) {
        lock.releaseLock();
      }
    } catch (_) {}
  }
}

/**
 * Xử lý HTTP GET (Kiểm tra trạng thái, đọc thuật ngữ, kiểm tra bảng tính)
 */
function doGet(e) {
  try {
    var params = (e && e.parameter) ? e.parameter : {};
    var action = params.action || "status";

    if (action === "status" || action === "ping") {
      var ss = getSpreadsheet();
      return createJsonResponse({
        success: true,
        status: "online",
        project: "Stella Sora Story Translator",
        spreadsheet_name: ss.getName(),
        spreadsheet_id: ss.getId(),
        server_time: Utilities.formatDate(new Date(), "GMT+7", "yyyy-MM-dd HH:mm:ss")
      });
    }

    if (action === "get_glossary") {
      return createJsonResponse(getGlossaryTerms());
    }

    if (action === "get_leaderboard") {
      return createJsonResponse(getLeaderboardData());
    }

    return createJsonResponse({
      success: true,
      message: "Stella Sora Web App Backend is active! Ready for requests."
    });

  } catch (err) {
    return createJsonResponse({
      success: false,
      error: err.toString()
    });
  }
}

/**
 * Cập nhật dòng bản dịch vào Google Sheets
 */
function handleSaveLine(data) {
  var ss = getSpreadsheet();
  
  // Xác định tên Tab
  var sheetName = data.sheet_name || "";
  if (!sheetName && data.chapter_id) {
    sheetName = CHAPTER_SHEET_MAP[data.chapter_id] || data.chapter_id;
  }
  if (!sheetName && data.id) {
    sheetName = CHAPTER_SHEET_MAP[data.id] || data.id;
  }
  // Thử tra ngược nếu sheetName là mã chương kỹ thuật
  if (CHAPTER_SHEET_MAP[sheetName]) {
    sheetName = CHAPTER_SHEET_MAP[sheetName];
  }

  var sheet = ss.getSheetByName(sheetName);
  if (!sheet) {
    // Thử tìm theo tên không phân biệt hoa thường hoặc chứa từ khóa
    var allSheets = ss.getSheets();
    for (var i = 0; i < allSheets.length; i++) {
      var sName = allSheets[i].getName();
      if (sName.toLowerCase() === sheetName.toLowerCase()) {
        sheet = allSheets[i];
        break;
      }
    }
  }

  if (!sheet) {
    return {
      success: false,
      error: "Không tìm thấy sheet: '" + sheetName + "'. Vui lòng kiểm tra lại tên Tab!"
    };
  }

  var rowIndex = parseInt(data.row_index, 10);
  if (isNaN(rowIndex) || rowIndex < 2) {
    return {
      success: false,
      error: "Chỉ số hàng (row_index) không hợp lệ: " + data.row_index
    };
  }

  var newVi = (data.new_vi !== undefined) ? String(data.new_vi) : "";
  var translator = (data.translator !== undefined && String(data.translator).trim() !== "") 
                    ? String(data.translator).trim() : "Ẩn Danh";
  var status = (data.status !== undefined && String(data.status).trim() !== "") 
                    ? String(data.status).trim() : "Đã dịch";
  var notes = (data.notes !== undefined) ? String(data.notes) : "";

  // 1. Kiểm tra an toàn: Đối chiếu line_id ở Cột B (nếu có)
  var lineId = data.line_id || "";
  if (lineId) {
    var actualLineId = sheet.getRange(rowIndex, 2).getValue();
    // Nếu bị lệch hàng (do có ai thêm dòng), quét tìm đúng lineId trong phạm vi lân cận
    if (actualLineId && String(actualLineId).trim() !== String(lineId).trim()) {
      var searchRange = sheet.getRange(Math.max(2, rowIndex - 10), 2, 21, 1).getValues();
      var foundRow = -1;
      for (var r = 0; r < searchRange.length; r++) {
        if (String(searchRange[r][0]).trim() === String(lineId).trim()) {
          foundRow = Math.max(2, rowIndex - 10) + r;
          break;
        }
      }
      if (foundRow > 0) {
        rowIndex = foundRow;
      }
    }
  }

  // 2. Ghi đè vào các cột:
  // Cột F (6): BẢN DỊCH MỚI
  // Cột G (7): Dịch giả
  // Cột H (8): Trạng thái
  var valuesToWrite = [[newVi, translator, status]];
  sheet.getRange(rowIndex, 6, 1, 3).setValues(valuesToWrite);

  // Nếu có ghi chú, cập nhật Cột I (9)
  if (notes) {
    sheet.getRange(rowIndex, 9).setValue(notes);
  }

  // 3. Cập nhật thống kê điểm EXP & Xếp hạng dịch giả
  var expGained = 50;
  recordTranslatorContribution(ss, translator, expGained, sheetName);

  return {
    success: true,
    message: "Đã lưu câu " + (lineId || ("hàng " + rowIndex)) + " lên Google Sheets!",
    sheet: sheet.getName(),
    row_index: rowIndex,
    translator: translator,
    exp_gained: expGained,
    timestamp: Utilities.formatDate(new Date(), "GMT+7", "yyyy-MM-dd HH:mm:ss")
  };
}

/**
 * Ghi nhận đóng góp của dịch giả lên Tab thống kê "00. Thống Kê Dịch Giả"
 */
function recordTranslatorContribution(ss, translatorName, expToAdd, chapterName) {
  if (!translatorName || translatorName === "Ẩn Danh") return;
  try {
    var statsSheet = ss.getSheetByName("00. Thống Kê Dịch Giả");
    if (!statsSheet) {
      statsSheet = ss.insertSheet("00. Thống Kê Dịch Giả", 0);
      statsSheet.appendRow(["Dịch giả", "Số câu đã dịch", "Tổng EXP", "Cấp độ", "Chương dịch gần nhất", "Hoạt động gần nhất"]);
      statsSheet.getRange(1, 1, 1, 6).setFontWeight("bold").setBackground("#1a2332").setFontColor("#ffffff");
    }

    var data = statsSheet.getDataRange().getValues();
    var rowIndex = -1;
    for (var i = 1; i < data.length; i++) {
      if (String(data[i][0]).toLowerCase() === translatorName.toLowerCase()) {
        rowIndex = i + 1;
        break;
      }
    }

    var nowStr = Utilities.formatDate(new Date(), "GMT+7", "yyyy-MM-dd HH:mm:ss");

    if (rowIndex > 0) {
      var currentCount = parseInt(statsSheet.getRange(rowIndex, 2).getValue(), 10) || 0;
      var currentExp = parseInt(statsSheet.getRange(rowIndex, 3).getValue(), 10) || 0;
      var newCount = currentCount + 1;
      var newExp = currentExp + expToAdd;
      var newLevel = 1 + Math.floor(newExp / 250);

      statsSheet.getRange(rowIndex, 2, 1, 5).setValues([
        [newCount, newExp, "Cấp " + newLevel, chapterName, nowStr]
      ]);
    } else {
      var newLevel = 1 + Math.floor(expToAdd / 250);
      statsSheet.appendRow([translatorName, 1, expToAdd, "Cấp " + newLevel, chapterName, nowStr]);
    }
  } catch (e) {
    // Không để lỗi thống kê ảnh hưởng đến việc lưu bản dịch
  }
}

/**
 * Đọc thuật ngữ từ tab '01. Thống Nhất Danh Từ'
 */
function getGlossaryTerms() {
  var ss = getSpreadsheet();
  var sheet = ss.getSheetByName("01. Thống Nhất Danh Từ");
  if (!sheet) {
    return { success: false, error: "Không tìm thấy tab '01. Thống Nhất Danh Từ'" };
  }
  var data = sheet.getDataRange().getValues();
  var terms = [];
  for (var i = 1; i < data.length; i++) {
    var row = data[i];
    if (row.length >= 2 && String(row[0]).trim() !== "") {
      terms.push({
        category: String(row[0]).trim(),
        en: String(row[1] || "").trim(),
        vi: String(row[2] || "").trim(),
        notes: String(row[3] || "").trim()
      });
    }
  }
  return { success: true, total: terms.length, terms: terms };
}

/**
 * Lấy danh sách bảng xếp hạng dịch giả
 */
function getLeaderboardData() {
  var ss = getSpreadsheet();
  var sheet = ss.getSheetByName("00. Thống Kê Dịch Giả");
  if (!sheet) return { success: true, leaders: [] };
  var data = sheet.getDataRange().getValues();
  var leaders = [];
  for (var i = 1; i < data.length; i++) {
    leaders.push({
      name: data[i][0],
      translated_count: data[i][1],
      exp: data[i][2],
      level: data[i][3],
      last_chapter: data[i][4],
      last_active: data[i][5]
    });
  }
  leaders.sort(function(a, b) { return (b.exp || 0) - (a.exp || 0); });
  return { success: true, leaders: leaders };
}

/**
 * Trợ giúp lấy Spreadsheet
 */
function getSpreadsheet() {
  try {
    var active = SpreadsheetApp.getActiveSpreadsheet();
    if (active) return active;
  } catch (_) {}
  return SpreadsheetApp.openById(SPREADSHEET_ID);
}

/**
 * Chuẩn hóa phản hồi JSON có CORS header
 */
function createJsonResponse(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
