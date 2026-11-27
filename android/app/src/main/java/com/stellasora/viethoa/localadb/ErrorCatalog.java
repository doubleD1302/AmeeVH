package com.stellasora.viethoa.localadb;
import java.io.EOFException;
import java.net.ConnectException;
import java.net.NoRouteToHostException;
import java.net.SocketException;
import java.net.SocketTimeoutException;
import java.net.UnknownHostException;
import java.security.cert.CertPathValidatorException;
import java.security.cert.CertificateException;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.zip.ZipException;
import javax.net.ssl.SSLException;

/**
 * Plain-language error catalog for the Android launcher. Same {@code E-...} namespace as the PC launcher
 * (docs/ERROR_CODES.md) so a copied code always means the same thing across platforms.
 * Pure Java (no Android or org.json types) so it can be unit-tested on a JVM.
 */
final class ErrorCatalog {
 private ErrorCatalog(){}

 /** Implemented by exceptions that carry an explicit catalog code (see StellaException). */
 interface Coded { String code(); }

 static final class Entry {
  final String code, title, summary, level;
  final boolean network;
  final String[] steps;
  final String[] quickActions;

  Entry(String code, String title, String summary, String level, boolean network, String[] steps) {
   this(code, title, summary, level, network, steps, new String[0]);
  }

  Entry(String code, String title, String summary, String level, boolean network, String[] steps, String[] quickActions) {
   this.code = code;
   this.title = title;
   this.summary = summary;
   this.level = level;
   this.network = network;
   this.steps = steps;
   this.quickActions = quickActions == null ? new String[0] : quickActions;
  }

  boolean isError() { return "error".equals(level); }
 }

 private static final LinkedHashMap<String, Entry> MAP = new LinkedHashMap<>();
 private static final String SEND = "Nếu vẫn lỗi sau các bước trên, bấm \"Sao chép báo lỗi chi tiết\" bên dưới và gửi cho nhóm phát triển.";
 private static final String REPORT = "Bấm \"Sao chép báo lỗi chi tiết\" và gửi cho nhóm phát triển.";

 private static String[] qa(String... ids) { return ids; }

 private static void add(String code, String title, String summary, String level, boolean network, String[] quickActions, String... steps) {
  MAP.put(code, new Entry(code, title, summary, level, network, steps, quickActions));
 }

 static {
  // ------------------------------------------------------------------ network & GitHub
  add("E-NET", "Không kết nối được máy chủ",
    "Điện thoại không kết nối được tới máy chủ GitHub. Nguyên nhân thường do mạng đang yếu, VPN/DNS riêng đang chặn hoặc máy chủ đang bận.",
    "error", true, qa("probe_network", "sync_github", "open_wifi"),
    "Bấm \"Kiểm tra kết nối & DNS\" bên dưới để xác định lỗi nằm ở mạng hay ở máy chủ.",
    "Thử mở https://github.com trên trình duyệt. Nếu cũng không vào được thì mạng hiện tại đang bị chặn.",
    "Đổi mạng (Wi-Fi ↔ 4G/5G) hoặc tạm tắt VPN / DNS chặn quảng cáo rồi bấm Đồng bộ lại.", SEND);

  add("E-NET-OFFLINE", "Điện thoại chưa có đường ra Internet",
    "Hệ thống báo điện thoại không có kết nối mạng dùng được (đang bật chế độ máy bay, tắt Wi-Fi/4G hoặc Wi-Fi mất Internet).",
    "error", true, qa("open_wifi", "probe_network", "sync_github"),
    "Tắt chế độ máy bay, bật Wi-Fi hoặc dữ liệu di động (4G/5G).",
    "Nếu đang dùng Wi-Fi công cộng (quán cà phê, trường học, khách sạn), mở trình duyệt để đăng nhập Wi-Fi trước.",
    "Khi điện thoại đã vào được web bình thường, quay lại bấm Đồng bộ GitHub.");

  add("E-NET-CAPTIVE", "Mạng Wi-Fi đang yêu cầu đăng nhập (Captive Portal)",
    "Mạng Wi-Fi hiện tại đang chặn và chuyển hướng sang trang đăng nhập hoặc trang cảnh báo của nhà mạng thay vì trả dữ liệu từ GitHub.",
    "error", true, qa("open_wifi", "probe_network", "sync_github"),
    "Mở trình duyệt web trên điện thoại để hoàn tất trang đăng nhập Wi-Fi (hoặc chạm thông báo \"Đăng nhập vào mạng Wi-Fi\").",
    "Nếu không cần Wi-Fi công cộng, chuyển sang 4G/5G hoặc Wi-Fi khác rồi bấm Đồng bộ lại.", SEND);

  add("E-NET-DNS", "Không tìm ra địa chỉ GitHub (lỗi DNS)",
    "Điện thoại không tra được địa chỉ máy chủ GitHub. Thường do DNS của nhà mạng đang lỗi, DNS riêng tư (Private DNS) bị hỏng hoặc mạng đang chặn GitHub.",
    "error", true, qa("probe_network", "open_wifi", "sync_github"),
    "Bấm \"Kiểm tra kết nối & DNS\" để xem lỗi nằm ở DNS hay mất Internet hoàn toàn.",
    "Vào Cài đặt Android → Mạng & Internet → DNS riêng tư: chọn \"Tự động\" hoặc nhập dns.google / one.one.one.one.",
    "Hoặc đổi mạng (Wi-Fi ↔ 4G/5G), hoặc bật Cloudflare WARP (1.1.1.1) rồi thử lại.", SEND);

  add("E-NET-VPN-DNS", "VPN hoặc DNS riêng tư đang chặn GitHub",
    "Điện thoại vẫn ra được Internet nhưng chỉ tên miền GitHub bị chặn ở tầng DNS. Rất hay gặp khi dùng DNS chặn quảng cáo (AdGuard/NextDNS) cấu hình gắt hoặc VPN bị lỗi tuyến.",
    "error", true, qa("probe_network", "open_wifi", "sync_github"),
    "Vào Cài đặt Android → Mạng & Internet → DNS riêng tư và tạm đổi về \"Tự động\" hoặc dns.google.",
    "Tạm tắt VPN hoặc ứng dụng chặn quảng cáo (AdGuard, Blokada, DNS66...) rồi bấm Đồng bộ lại.",
    "Hoặc thử đổi giữa Wi-Fi và 4G/5G.", SEND);

  add("E-NET-TIMEOUT", "GitHub phản hồi quá chậm",
    "Ứng dụng đã gửi yêu cầu tới GitHub nhưng chờ quá thời hạn mà máy chủ không phản hồi. Thường do sóng yếu, mạng nghẽn giờ cao điểm hoặc định tuyến quốc tế chậm.",
    "error", true, qa("probe_network", "sync_github", "open_wifi"),
    "Chờ 1–2 phút rồi bấm Đồng bộ / thử lại.",
    "Đổi sang mạng khác ổn định hơn (Wi-Fi ↔ 4G/5G) hoặc đến gần bộ phát Wi-Fi.",
    "Tạm tắt VPN hoặc ứng dụng tăng tốc mạng nếu đang bật.", SEND);

  add("E-NET-REFUSED", "Máy chủ từ chối kết nối",
    "Kết nối tới máy chủ bị từ chối ngay lập tức. Thường do tường lửa, VPN, proxy hoặc ứng dụng chặn quảng cáo trên máy đang chặn cổng 443 (HTTPS).",
    "error", true, qa("probe_network", "open_wifi", "sync_github"),
    "Tạm tắt VPN, proxy, tường lửa (NetGuard/AdGuard) rồi thử lại.",
    "Đổi sang mạng khác (Wi-Fi ↔ 4G/5G) rồi bấm Đồng bộ lại.", SEND);

  add("E-NET-RESET", "Kết nối bị ngắt giữa chừng",
    "Đang tải dở dữ liệu thì đường truyền bị cắt đột ngột. Phần tệp đã tải hợp lệ vẫn được ứng dụng giữ lại để tải tiếp.",
    "error", true, qa("probe_network", "sync_github"),
    "Bấm thử lại — ứng dụng tự nối tiếp từ đoạn đã tải (HTTP Range), không cần tải lại từ đầu.",
    "Giữ màn hình sáng khi tải gói lớn, đứng gần Wi-Fi hoặc đổi sang mạng ổn định hơn.", SEND);

  add("E-NET-TLS-CERT", "Chứng chỉ bảo mật không được tin cậy",
    "Kết nối HTTPS bị từ chối vì chứng chỉ bảo mật không khớp trên điện thoại. Thường do ngày giờ hệ thống bị sai hoặc mạng/VPN đang chèn chứng chỉ lạ.",
    "error", true, qa("probe_network", "open_wifi", "sync_github"),
    "Vào Cài đặt Android → Hệ thống → Ngày & giờ, bật \"Đặt thời gian tự động\" và \"Đặt múi giờ tự động\".",
    "Tắt VPN/proxy hoặc đăng nhập nếu đang dùng Wi-Fi công cộng.",
    "Đổi sang mạng khác rồi thử lại.", SEND);

  add("E-NET-TLS", "Không thiết lập được kết nối an toàn (HTTPS)",
    "Quá trình bắt tay mã hóa HTTPS tới máy chủ thất bại. Thường do mạng/VPN can thiệp đường truyền hoặc kết nối quá chập chờn.",
    "error", true, qa("probe_network", "open_wifi", "sync_github"),
    "Tắt VPN/proxy rồi thử lại, hoặc đổi giữa Wi-Fi và 4G/5G.",
    "Kiểm tra ngày giờ điện thoại có đúng thực tế không và cập nhật dịch vụ Google Play nếu có.", SEND);

  add("E-HTTP-RATE", "GitHub đang giới hạn lượt truy cập",
    "GitHub tạm khóa yêu cầu vì địa chỉ IP mạng hiện tại gọi API quá nhiều lần trong 1 giờ (rất hay gặp trên 4G/5G dùng chung IP hoặc Wi-Fi công cộng).",
    "error", true, qa("open_wifi", "sync_github"),
    "Đổi sang mạng khác ngay (ví dụ chuyển từ 4G sang Wi-Fi hoặc bật/tắt Chế độ máy bay 10 giây để đổi IP 4G).",
    "Hoặc chờ 10–15 phút rồi bấm Đồng bộ GitHub lại.");

  add("E-HTTP-404", "Không tìm thấy tệp trên GitHub",
    "Bản phát hành hoặc tệp bảng kê không còn ở địa chỉ đang cấu hình (tên kho/nhánh bị sửa sai hoặc tệp vừa bị gỡ trên GitHub).",
    "error", true, qa("reset_channel", "sync_github"),
    "Bấm \"Khôi phục kênh GitHub mặc định\" (doubleD1302/AmeeVH · nhánh main) rồi bấm Đồng bộ lại.",
    "Nếu kênh đã là mặc định mà vẫn báo 404, đây là lỗi phía bản phát hành. " + REPORT);

  add("E-HTTP-5XX", "GitHub đang gặp sự cố máy chủ",
    "Máy chủ GitHub trả về lỗi nội bộ (HTTP 5xx). Đây là sự cố tạm thời phía GitHub, không phải lỗi của điện thoại hay ứng dụng.",
    "error", true, qa("probe_network", "sync_github"),
    "Chờ 2–5 phút rồi bấm thử lại.",
    "Có thể kiểm tra tình trạng máy chủ tại https://www.githubstatus.com.");

  add("E-HTTP-4XX", "GitHub từ chối yêu cầu",
    "Máy chủ GitHub trả về mã từ chối (HTTP 4xx) cho yêu cầu hiện tại.",
    "error", true, qa("probe_network", "sync_github"),
    "Kiểm tra lại Kho/Nhánh trong Cài đặt rồi thử lại sau ít phút hoặc đổi mạng.", SEND);

  // ------------------------------------------------------------------ data / package
  add("E-SYNC-PENDING", "Ứng dụng chưa đọc xong thông tin từ GitHub",
    "Ứng dụng chưa hoàn tất việc đọc bản phát hành và gói bản dịch Android từ GitHub nên chưa mở nút cài.",
    "info", false, qa("sync_github"),
    "Bấm \"Đồng bộ lại GitHub\" và chờ vài giây.",
    "Nếu vẫn không đồng bộ được, bấm lại vào thông báo lỗi để xem nguyên nhân cụ thể.");

  add("E-DATA-JSON", "Dữ liệu tải về không đọc được",
    "Nội dung máy chủ trả về không phải định dạng JSON hợp lệ. Thường xảy ra khi Wi-Fi công cộng chèn trang đăng nhập, hoặc nhà mạng/VPN trả trang cảnh báo.",
    "error", true, qa("probe_network", "open_wifi", "sync_github"),
    "Bấm \"Kiểm tra kết nối & DNS\" để xem mạng có bị chuyển hướng không.",
    "Mở trình duyệt vào https://github.com để kiểm tra có hiện trang đăng nhập Wi-Fi/cảnh báo không.",
    "Tắt VPN/DNS riêng hoặc đổi mạng rồi bấm Đồng bộ lại.", SEND);

  add("E-DATA-SCHEMA", "Dữ liệu GitHub trả về sai định dạng",
    "Ứng dụng đọc được phản hồi từ GitHub nhưng nội dung thiếu trường dữ liệu hoặc sai cấu trúc (có thể bản phát hành đang được upload dở).",
    "error", false, qa("sync_github"),
    "Chờ 2–3 phút rồi bấm \"Đồng bộ lại GitHub\".", SEND);

  add("E-DATA-UNVERIFIED", "Tệp phát hành chưa có mã xác minh SHA256",
    "Tệp trên GitHub không kèm mã băm xác minh toàn vẹn SHA256 nên ứng dụng từ chối tải để bảo vệ dữ liệu game.",
    "error", false, qa("sync_github"),
    "Đây là lỗi phía bản phát hành trên GitHub. " + REPORT);

  add("E-NO-PACKAGE", "Bản phát hành chưa có gói Android",
    "Bản phát hành mới nhất trên GitHub chưa đính kèm gói bản dịch dành cho Android (gói Windows không tương thích nên ứng dụng không tự cài).",
    "error", false, qa("sync_github"),
    "Chờ nhóm dịch đăng gói Android cho bản phát hành này rồi bấm Đồng bộ lại.",
    "Nếu bản phát hành đã công bố lâu mà vẫn báo thiếu: " + REPORT);

  add("E-MANIFEST-INVALID", "Bảng kê gói Android bị lỗi",
    "Tệp bảng kê gói bản dịch Android thiếu thông tin bắt buộc hoặc có đường dẫn không hợp lệ nên ứng dụng dừng để bảo vệ game. Game chưa bị thay đổi.",
    "error", false, qa("sync_github"),
    "Chờ bản phát hành được cập nhật lại rồi bấm Đồng bộ GitHub.", SEND);

  add("E-PKG-MISMATCH", "Phiên bản game chưa khớp gói Việt hoá",
    "Phiên bản Stella Sora trên điện thoại khác với phiên bản mà gói Việt hoá hiện tại hỗ trợ nên launcher tạm dừng cài để tránh lỗi xác minh tệp (BinDiff / Data check fail) khi mở game.",
    "warning", false, qa("launch_game", "open_play_store", "detect_game", "sync_github"),
    "Nếu game trên máy CŨ hơn gói Việt hoá: bấm \"Mở Stella Sora\" để game tự tải cập nhật mới nhất (hoặc cập nhật trên Google Play), vào tới màn hình chính rồi vuốt thoát hẳn game và quay lại cài.",
    "Nếu game trên máy MỚI hơn gói Việt hoá: bạn vẫn chơi bản gốc bình thường và bấm \"Đồng bộ GitHub\" sau khi nhóm dịch phát hành bản tương thích.",
    "Xem rõ phiên bản \"Game trên máy\" và \"Gói Việt hoá hỗ trợ\" ở bảng Thông tin kiểm tra bên dưới.");

  // ------------------------------------------------------------------ download
  add("E-DL-VERIFY", "Tệp tải về bị sai kích thước hoặc hỏng (SHA256)",
    "Tệp tải xong nhưng kích thước hoặc mã kiểm tra toàn vẹn (SHA256) không khớp bảng kê. Thường do đường truyền bị lỗi gói tin hoặc bản phát hành trỏ nhầm tệp.",
    "error", true, qa("probe_network", "install_patch"),
    "Bấm Cài / Thử lại — ứng dụng sẽ tải lại tệp lỗi và giữ nguyên các tệp đã tải đúng.",
    "Nếu lặp lại nhiều lần trên cùng một mạng, hãy đổi mạng (Wi-Fi ↔ 4G/5G) hoặc tắt VPN.", SEND);

  add("E-DL-RANGE", "Máy chủ trả dữ liệu tải tiếp không khớp",
    "Ứng dụng thử tải nối tiếp phần đang dở (HTTP 206 Range) nhưng máy chủ trả dải byte không đúng.",
    "error", true, qa("install_patch"),
    "Bấm thử lại — ứng dụng đã xoá tệp dở và sẽ tải sạch từ đầu.", SEND);

  add("E-DL-OVERSIZE", "Tệp trên máy chủ lớn hơn kích thước công bố",
    "Kích thước tệp thực tế vượt quá giới hạn kê khai trong bảng kê nên ứng dụng tự dừng tải để đảm bảo an toàn.",
    "error", true, qa("sync_github"),
    "Thử bấm Đồng bộ GitHub lại. Nếu vẫn gặp, đây thường là lỗi bảng kê phía phát hành. " + REPORT);

  add("E-DL-TIMEOUT", "Tải tệp quá lâu so với thời hạn",
    "Tốc độ mạng quá chậm khiến lượt tải vượt thời gian cho phép. Phần tệp đã tải hợp lệ vẫn được lưu tạm để tải tiếp.",
    "error", true, qa("probe_network", "install_patch"),
    "Bấm cài lại để tiếp tục tải phần còn lại.",
    "Đổi sang mạng nhanh/ổn định hơn và giữ màn hình sáng trong lúc tải.");

  add("E-DL-PARAM", "Thông tin tải không hợp lệ",
    "Bảng kê chứa địa chỉ tải hoặc kích thước tệp không hợp lệ.",
    "error", false, qa("sync_github"),
    "Đây là lỗi phía bản phát hành. " + REPORT);

  add("E-DL-RESPONSE", "Máy chủ trả phản hồi tải không hợp lệ",
    "Máy chủ chuyển hướng bất thường hoặc không trả về liên kết HTTPS hợp lệ khi tải gói.",
    "error", true, qa("probe_network", "sync_github"),
    "Kiểm tra mạng không có proxy/Captive Portal, chờ 1 phút rồi thử lại.", SEND);

  add("E-ZIP-CORRUPT", "Gói nén AssetBundles bị lỗi khi giải nén",
    "Tệp gói đồ họa (.zip) bị hỏng cấu trúc nén hoặc bộ nhớ máy đầy đột ngột trong quá trình giải nén.",
    "error", false, qa("install_patch"),
    "Kiểm tra bộ nhớ trống trên điện thoại (cần dư ít nhất 2–3 GB).",
    "Bấm cài lại để ứng dụng tải mới và giải nén lại gói sạch.", SEND);

  add("E-TIMEOUT", "Thao tác vượt quá thời hạn cho phép",
    "Quá trình xử lý chạy quá lâu nên ứng dụng tự dừng an toàn. Nếu đang ở bước cài đặt, nhật ký vẫn được giữ để phục hồi.",
    "error", false, qa("auto_connect", "recover"),
    "Giữ màn hình sáng, đảm bảo kết nối Local ADB ổn định rồi thử lại.",
    "Nếu thấy cảnh báo thao tác bị ngắt, bấm Phục hồi thao tác trước khi cài tiếp.", SEND);

  // ------------------------------------------------------------------ ADB & OEM compatibility
  add("E-DEVOPT", "Chưa bật Tuỳ chọn nhà phát triển",
    "Local ADB cần bật Tuỳ chọn nhà phát triển và Gỡ lỗi không dây để đọc/ghi thư mục dữ liệu game mà không cần máy tính hay root.",
    "warning", false, qa("open_device_info", "open_dev_settings"),
    "Bấm \"Mở Thông tin điện thoại\" (Samsung: vào tiếp Thông tin phần mềm).",
    "Chạm liên tiếp 7 lần vào \"Số bản dựng\" (Xiaomi/Redmi/POCO: chạm 7 lần vào \"Phiên bản OS / HyperOS / MIUI\") đến khi báo \"Bạn đã là nhà phát triển\".",
    "Quay lại ứng dụng và bật \"Gỡ lỗi không dây\" trong Tuỳ chọn nhà phát triển.");

  add("E-ADB-NO-WIFI", "Cần bật Wi-Fi để dùng Gỡ lỗi không dây",
    "Tính năng Gỡ lỗi không dây (Wireless Debugging) của Android bắt buộc điện thoại phải đang kết nối Wi-Fi (không hoạt động khi chỉ bật 4G/5G).",
    "warning", false, qa("open_wifi", "open_wireless"),
    "Bấm \"Mở cài đặt Wi-Fi\" và kết nối vào một mạng Wi-Fi bất kỳ (hoặc phát Wi-Fi từ thiết bị khác).",
    "Sau khi Wi-Fi đã kết nối, bật lại Gỡ lỗi không dây rồi bấm Kết nối nhanh Local ADB.");

  add("E-ADB-NOT-CONNECTED", "Chưa kết nối Local ADB",
    "Ứng dụng chưa kết nối được Local ADB tới chính điện thoại này nên chưa thể đọc phiên bản game hay cài bản dịch.",
    "warning", false, qa("auto_connect", "open_wireless", "start_pair"),
    "Nếu máy đã ghép đôi 1 lần trước đó: bật Gỡ lỗi không dây rồi bấm \"Kết nối nhanh Local ADB\" (không cần nhập lại mã 6 số).",
    "Nếu đây là lần đầu dùng trên máy này: bấm \"Ghép đôi qua thông báo\" để nhập mã 6 số một lần duy nhất.");

  add("E-ADB-CONN-REFUSED", "Gỡ lỗi không dây đang tắt hoặc cổng đã đổi",
    "Điện thoại từ chối kết nối Local ADB trên cổng đã lưu. Điều này xảy ra mỗi khi bạn tắt/bật lại Gỡ lỗi không dây, khởi động lại máy hoặc đổi Wi-Fi (Android tự đổi số cổng mới).",
    "error", false, qa("open_wireless", "auto_connect"),
    "Bấm \"Mở Gỡ lỗi không dây\" và gạt BẬT công tắc Gỡ lỗi không dây (nếu đang bật sẵn, hãy tắt đi rồi bật lại).",
    "Quay lại launcher và bấm \"Kết nối nhanh Local ADB\" để ứng dụng tự dò cổng mới.",
    "Nếu máy chặn dò tự động (mDNS), xem số cổng 5 chữ số ngay trên trang Gỡ lỗi không dây rồi nhập vào mục \"Kết nối thủ công\".");

  add("E-ADB-AUTH", "Điện thoại chưa chấp nhận khoá Local ADB",
    "Android không tin cậy khoá của launcher (thường do bạn vừa bấm Thu hồi uỷ quyền gỡ lỗi USB, xoá thiết bị ghép đôi hoặc cài mới lại ứng dụng).",
    "error", false, qa("start_pair", "open_wireless"),
    "Bấm \"Ghép đôi qua thông báo\" rồi mở Gỡ lỗi không dây → \"Ghép nối thiết bị bằng mã ghép nối\".",
    "Giữ cửa sổ mã 6 số đang mở, kéo thanh thông báo xuống để nhập mã 6 số (chỉ cần làm lại 1 lần).");

  add("E-ADB-PAIR", "Ghép đôi Local ADB chưa thành công",
    "Mã ghép đôi 6 số bị sai, đã hết hiệu lực (vì cửa sổ mã bị đóng) hoặc nhập nhầm cổng kết nối thay cho cổng ghép đôi.",
    "error", false, qa("start_pair", "open_wireless"),
    "Đảm bảo điện thoại đang kết nối Wi-Fi và đã cấp quyền Thông báo cho launcher.",
    "Vào Gỡ lỗi không dây → bấm \"Ghép nối thiết bị bằng mã ghép nối\" để lấy mã 6 số MỚI và GIỮ NGUYÊN cửa sổ đó trên màn hình.",
    "Kéo thanh thông báo xuống nhập đúng 6 chữ số. Nếu dùng Kết nối thủ công: nhập CỔNG ngay dưới mã 6 số (khác với cổng ở màn hình ngoài).");

  add("E-ADB-PERM", "Hệ điều hành đang chặn quyền Local ADB",
    "Local ADB đã kết nối được nhưng ROM điện thoại chặn quyền truy cập hệ thống hoặc thư mục Android/data (rất phổ biến trên OPPO/Realme/OnePlus và Xiaomi/Redmi/POCO).",
    "error", false, qa("open_dev_settings", "auto_connect"),
    "OPPO / Realme / OnePlus (ColorOS / OxygenOS): vào Tuỳ chọn nhà phát triển, cuộn xuống cuối cùng và BẬT \"Tắt giám sát quyền\" (Disable permission monitoring).",
    "Xiaomi / Redmi / POCO (HyperOS / MIUI): vào Tuỳ chọn nhà phát triển và BẬT \"Gỡ lỗi USB (Cài đặt bảo mật)\" (USB debugging - Security settings).",
    "Sau khi bật tuỳ chọn trên, tắt rồi bật lại Gỡ lỗi không dây và bấm \"Kết nối nhanh Local ADB\".", SEND);

  add("E-ADB-DISCONNECTED", "Kết nối Local ADB bị ngắt giữa chừng",
    "Kênh Local ADB bị Android đóng đột ngột khi đang xử lý (thường do tắt màn hình, chuyển mạng Wi-Fi hoặc trình tiết kiệm pin dừng tiến trình nền).",
    "error", false, qa("open_wireless", "auto_connect", "open_app_battery"),
    "Kiểm tra Wi-Fi vẫn đang kết nối và Gỡ lỗi không dây vẫn đang BẬT.",
    "Bấm \"Kết nối nhanh Local ADB\" để nối lại và giữ màn hình sáng trong suốt lúc cài.",
    "Khuyến nghị bấm \"Bỏ hạn chế pin cho app\" để máy không tự ngắt Local ADB giữa chừng.", SEND);

  add("E-ADB-TIMEOUT", "Local ADB không phản hồi kịp thời hạn",
    "Lệnh gửi qua Local ADB không nhận được phản hồi trong thời gian quy định. Thường do Gỡ lỗi không dây bị treo hoặc điện thoại vừa khóa màn hình.",
    "error", false, qa("open_wireless", "auto_connect"),
    "Tắt rồi bật lại công tắc \"Gỡ lỗi không dây\" trong Cài đặt Android.",
    "Quay lại ứng dụng, bấm \"Kết nối nhanh Local ADB\" và giữ màn hình sáng khi thao tác.", SEND);

  add("E-ADB-START", "Không khởi động được tiến trình Local ADB",
    "Tiến trình Local ADB cục bộ của ứng dụng không khởi động được hoặc bị hệ thống dừng sớm.",
    "error", false, qa("open_app_battery", "auto_connect"),
    "Đóng hẳn launcher khỏi danh sách ứng dụng gần đây rồi mở lại.",
    "Vào Cài đặt ứng dụng → Pin → chọn \"Không hạn chế\" (Unrestricted), rồi thử lại.",
    "Nếu vẫn gặp, khởi động lại điện thoại một lần.", SEND);

  add("E-ADB-KEY", "Khoá định danh Local ADB gặp vấn đề",
    "Khoá RSA riêng của launcher không đọc/tạo được hoặc chứng thư không khớp. Ứng dụng không tự tạo khoá đè lên khoá đã ghép đôi cũ.",
    "error", false, qa("start_pair"),
    "Đóng hẳn ứng dụng rồi mở lại thử một lần.",
    "Nếu vẫn lỗi, vào Thông tin ứng dụng → Xoá dữ liệu ứng dụng (hoặc gỡ cài lại launcher) rồi ghép đôi lại bằng mã 6 số.", SEND);

  add("E-ADB-INPUT", "Thông tin địa chỉ hoặc cổng Local ADB chưa hợp lệ",
    "Số cổng phải nằm trong khoảng 1024–65535, mã ghép đôi đúng 6 chữ số và địa chỉ phải thuộc chính điện thoại này.",
    "warning", false, qa("open_wireless"),
    "Mở trang Gỡ lỗi không dây và kiểm tra lại đúng số cổng 5 chữ số đang hiển thị.",
    "Giữ nguyên địa chỉ 127.0.0.1 (hoặc địa chỉ IP Wi-Fi của chính máy hiện trên trang Gỡ lỗi không dây).");

  add("E-ADB", "Lỗi thực thi lệnh Local ADB",
    "Một lệnh hệ thống gửi qua Local ADB không hoàn tất thành công.",
    "error", false, qa("open_wireless", "auto_connect", "open_dev_settings"),
    "Đảm bảo Wi-Fi đang bật, Gỡ lỗi không dây đang bật và trạng thái hiển thị \"Đã kết nối\".",
    "Nếu dùng OPPO/Realme/OnePlus/Xiaomi, kiểm tra đã bật \"Tắt giám sát quyền\" hoặc \"Gỡ lỗi USB (Cài đặt bảo mật)\" trong Tuỳ chọn nhà phát triển.",
    "Bấm \"Kết nối nhanh Local ADB\" rồi thử lại.", SEND);

  // ------------------------------------------------------------------ game detection & state
  add("E-NO-GAME", "Chưa tìm thấy game Stella Sora (bản Global EN)",
    "Không tìm thấy gói ứng dụng Stella Sora bản Global EN (com.YoStarEN.StellaSora) trên người dùng hiện tại của điện thoại.",
    "warning", false, qa("detect_game"),
    "Kiểm tra đã cài Stella Sora bản Global (Yostar EN, mã gói com.YoStarEN.StellaSora) trên chính điện thoại này chưa.",
    "Lưu ý: bản Việt hoá chỉ hỗ trợ bản Global EN, chưa hỗ trợ bản JP/CN/KR/TW hoặc game cài trong Không gian thứ 2 / Dual App khác người dùng.",
    "Sau khi cài xong, mở game 1 lần để tải dữ liệu rồi quay lại bấm \"Tìm và kiểm tra game\".");

  add("E-GAME-WRONG-EDITION", "Đang cài bản Stella Sora khu vực khác (không phải Global EN)",
    "Phát hiện máy có cài Stella Sora nhưng thuộc máy chủ/khu vực khác (JP/CN/KR/TW) chứ không phải bản Global EN (com.YoStarEN.StellaSora).",
    "warning", false, qa("detect_game"),
    "Bản Việt hoá hiện chỉ tương thích với Stella Sora bản Global EN (com.YoStarEN.StellaSora).",
    "Hãy tải và cài bản Global EN, mở game tải đủ dữ liệu rồi bấm \"Tìm và kiểm tra game\".");

  add("E-GAME-NO-DATA", "Game chưa có thư mục dữ liệu (chưa tải tài nguyên)",
    "Ứng dụng tìm thấy game Stella Sora nhưng chưa thấy thư mục dữ liệu tài nguyên bên trong Android/data. Thường xảy ra khi bạn vừa tải game xong nhưng chưa mở vào game lần nào.",
    "warning", false, qa("launch_game", "detect_game"),
    "Bấm \"Mở Stella Sora\", đăng nhập/chờ game tải xong gói dữ liệu vào màn hình chính.",
    "Thoát hẳn game (vuốt tắt khỏi đa nhiệm), sau đó quay lại bấm \"Tìm và kiểm tra game\".");

  add("E-GAME-VERSION", "Chưa đọc được phiên bản game và tài nguyên",
    "Ứng dụng chưa đọc được thông tin phiên bản (GAME_VER / RES_VER) trong tệp .mani của game hoặc các tệp phiên bản không thống nhất.",
    "error", false, qa("launch_game", "detect_game", "auto_connect"),
    "Mở Stella Sora cho game tải đủ tài nguyên mới nhất, rồi thoát hẳn game.",
    "Kiểm tra Local ADB vẫn đang kết nối và bấm \"Tìm và kiểm tra game\".", SEND);

  add("E-GAME-STATE", "Không kiểm tra được trạng thái game",
    "Ứng dụng chưa xác định chắc chắn Stella Sora đã thoát hẳn hay chưa nên tạm dừng để không làm hỏng dữ liệu game.",
    "error", false, qa("auto_connect", "detect_game"),
    "Vuốt đóng hẳn Stella Sora khỏi danh sách ứng dụng gần đây (hoặc Buộc dừng game trong Cài đặt Android).",
    "Kiểm tra Local ADB vẫn đang kết nối rồi thử lại.", SEND);

  add("E-GAME-RUNNING", "Stella Sora đang chạy",
    "Không thể cài hoặc khôi phục bản dịch khi game đang mở vì tệp game sẽ bị xung đột hoặc ghi đè sai.",
    "warning", false, qa("detect_game"),
    "Thoát hẳn Stella Sora và vuốt tắt game khỏi màn hình đa nhiệm (Ứng dụng gần đây).",
    "Quay lại launcher và bấm thao tác lại.");

  add("E-VER-CHANGED", "Game đã cập nhật kể từ lần cài trước",
    "Phiên bản game/tài nguyên trên máy hiện đã mới hơn lúc cài trước đó nên bản sao lưu cũ không thể dùng để khôi phục (sẽ làm lệch dữ liệu bản game mới).",
    "warning", false, qa("sync_github", "install_patch"),
    "Bấm \"Đồng bộ lại GitHub\" rồi chọn \"Cập nhật Việt hoá\" để cài bản dịch mới khớp phiên bản game hiện tại.");

  add("E-GAME-ROOT-CHANGED", "Thư mục dữ liệu game không khớp hoặc đã đổi",
    "Đường dẫn thư mục dữ liệu game không khớp vị trí chuẩn hoặc đã thay đổi giữa lúc launcher kiểm tra.",
    "error", false, qa("detect_game"),
    "Bấm \"Tìm và kiểm tra game\" để đọc lại vị trí dữ liệu game.",
    "Đảm bảo game được cài ở bộ nhớ trong chính (không dùng không gian ảo/clone app).", SEND);

  add("E-BIND-MISMATCH", "Nhật ký hoặc bản sao lưu thuộc thiết bị/thư mục khác",
    "Dữ liệu phục hồi hiện có không khớp với thiết bị hoặc thư mục game này nên ứng dụng từ chối ghi đè để giữ an toàn.",
    "error", false, qa("detect_game"),
    "Không sao chép thư mục backup/nhật ký từ máy khác sang.", SEND);

  // ------------------------------------------------------------------ storage / install / recovery
  add("E-STORAGE", "Điện thoại không đủ dung lượng trống",
    "Bộ nhớ trong còn quá ít chỗ trống để vừa tải gói, vừa tạo bản sao lưu gốc an toàn. Dữ liệu game hiện chưa bị thay đổi.",
    "error", false, qa("install_patch"),
    "Dọn dẹp và giải phóng thêm ít nhất 2–3 GB dung lượng trống trong bộ nhớ máy (xoá video, ảnh cũ, bộ nhớ đệm ứng dụng).",
    "Sau đó quay lại bấm cài đặt lại.");

  add("E-STORAGE-ACCESS", "Ứng dụng chưa truy cập được thư mục lưu tạm của nó",
    "Android không cho phép tạo hoặc ghi vào vùng lưu trữ tải xuống/sao lưu riêng của launcher.",
    "error", false, qa("install_patch"),
    "Đóng hẳn launcher rồi mở lại và kiểm tra bộ nhớ trong còn dung lượng trống.",
    "Nếu đang dùng thẻ nhớ gắn ngoài làm bộ nhớ chung hoặc không gian ảo, hãy cài launcher ở bộ nhớ chính.", SEND);

  add("E-FILE-CHANGED", "Tệp game bị thay đổi trong lúc launcher đang cài",
    "Có tiến trình khác (game vừa mở lại, Google Play đang cập nhật game hoặc ứng dụng dọn rác) vừa sửa tệp game nên launcher đã dừng ngay để tránh hỏng game.",
    "error", false, qa("detect_game", "install_patch"),
    "Đợi Google Play cập nhật xong (nếu có), thoát hẳn Stella Sora khỏi đa nhiệm.",
    "Bấm \"Tìm và kiểm tra game\" rồi thử cài lại.", SEND);

  add("E-VERIFY-WRITE", "Ghi xong nhưng đọc lại tệp không khớp",
    "Sau khi ghi tệp vào thư mục game, launcher đọc lại mã SHA256 để kiểm chứng nhưng kết quả không khớp dự kiến.",
    "error", false, qa("recover", "install_patch"),
    "Kiểm tra bộ nhớ máy còn dư ít nhất 2 GB và đảm bảo game đã thoát hẳn.",
    "Nếu ứng dụng báo cần phục hồi thao tác bị ngắt, bấm \"Phục hồi thao tác ngay\" trước rồi cài lại.", SEND);

  add("E-VERIFY", "Không đối chiếu được mã kiểm tra tệp trên máy",
    "Local ADB không đọc được kích thước hoặc mã SHA256 của tệp game trên máy để xác minh.",
    "error", false, qa("auto_connect", "open_dev_settings"),
    "Đảm bảo Local ADB đang kết nối ổn định và máy không chặn quyền đọc Android/data.",
    "Bấm \"Kết nối nhanh Local ADB\" rồi thử lại.", SEND);

  add("E-FILE-MISMATCH", "Tệp game không còn khớp bản Việt hoá đã cài",
    "Một số tệp đã thay đổi so với biên bản cài trước đó (do game tự tải hotfix mới hoặc bị công cụ khác ghi đè).",
    "warning", false, qa("install_patch"),
    "Bấm \"Cài / Cập nhật Việt hoá\" để áp dụng lại bản dịch đồng bộ mới nhất.");

  add("E-BACKUP", "Bản sao lưu gốc bị thiếu hoặc bị hỏng",
    "Launcher không tìm thấy bản sao lưu tệp gốc hoặc mã kiểm tra bản sao lưu không khớp (có thể bị ứng dụng dọn rác xoá mất thư mục Android/data của launcher).",
    "error", false, qa("install_patch"),
    "Không dùng ứng dụng dọn rác xoá dữ liệu của Stella Sora Launcher.",
    "Nếu muốn quay về bản tiếng Anh gốc hoàn toàn, bạn có thể vào trong game chọn sửa tệp hoặc gỡ cài lại Stella Sora từ cửa hàng.", SEND);

  add("E-JOURNAL", "Nhật ký thao tác bị hỏng",
    "Tệp nhật ký theo dõi thao tác dở dang bị lỗi cấu trúc nên ứng dụng giữ nguyên để tránh khôi phục sai.",
    "error", false, qa("detect_game"),
    "Bấm \"Sao chép báo lỗi chi tiết\" và gửi cho nhóm phát triển.",
    "Chưa xoá dữ liệu ứng dụng trước khi gửi báo lỗi.");

  add("E-RECOVERY-REQUIRED", "Có thao tác cài đặt trước đó bị ngắt giữa chừng",
    "Lần cài/khôi phục trước bị dừng đột ngột (tắt máy, mất kết nối ADB, hết pin…). Cần phục hồi về trạng thái sạch trước khi cài tiếp để game không bị lỗi.",
    "warning", false, qa("recover", "auto_connect"),
    "Đảm bảo Local ADB đang kết nối và Stella Sora đã thoát hẳn.",
    "Bấm \"Phục hồi thao tác ngay\" và chờ hoàn tất, sau đó có thể cài lại bình thường.");

  add("E-NO-RECOVERY", "Không có thao tác nào cần phục hồi",
    "Không có nhật ký thao tác dở dang nào cần xử lý. Trạng thái game đang sạch sẽ.",
    "info", false, qa(),
    "Bạn có thể tiếp tục sử dụng launcher bình thường.");

  add("E-NO-RECEIPT", "Chưa cài Việt hoá bằng ứng dụng này",
    "Chức năng Kiểm tra tệp và Khôi phục cần biên bản/sao lưu do chính launcher này tạo ra khi cài. Đây không phải lỗi hỏng game.",
    "info", false, qa("install_patch"),
    "Bấm \"Cài / Cập nhật Việt hoá\" để cài bản dịch.",
    "Nếu trước đây bạn cài thủ công bằng công cụ khác, hãy cài lại 1 lần qua launcher này.");

  add("E-SECURITY", "Bị chặn vì lý do an toàn",
    "Đường dẫn, liên kết hoặc tệp nén vượt ra ngoài phạm vi thư mục game cho phép nên launcher tự chặn để bảo vệ thiết bị và game.",
    "error", false, qa("sync_github"),
    "Không cài gói không rõ nguồn gốc. " + REPORT);

  add("E-BUSY", "Ứng dụng đang xử lý thao tác khác",
    "Một tác vụ khác vẫn đang chạy nên launcher tạm không nhận yêu cầu mới để tránh xung đột dữ liệu.",
    "warning", false, qa(),
    "Chờ thanh tiến trình hiện tại hoàn tất rồi thử lại.");

  // ------------------------------------------------------------------ app update (APK) & permissions
  add("E-APK-NONE", "Ứng dụng đã là phiên bản mới nhất",
    "Trên GitHub hiện chưa có phiên bản Launcher Android Local ADB nào mới hơn bản bạn đang cài.",
    "info", false, qa(),
    "Không cần cập nhật thêm.");

  add("E-APK-INSTALL-PERMISSION", "Chưa cấp quyền cài đặt APK từ ứng dụng",
    "Android yêu cầu bạn bật quyền \"Cho phép từ nguồn này\" cho Stella Sora Launcher trước khi mở trình cài đặt bản cập nhật APK.",
    "warning", false, qa("open_unknown_sources"),
    "Bấm \"Cấp quyền cài APK\" bên dưới và gạt BẬT công tắc cho phép.",
    "Quay lại ứng dụng và bấm \"Mở trình cài đặt Android\" thêm một lần nữa.");

  add("E-NOTIF-PERMISSION", "Chưa cấp quyền hiện Thông báo",
    "Android 13+ yêu cầu cấp quyền Thông báo thì launcher mới hiển thị được khung \"Nhập mã ghép đôi 6 số\" ngay trên thanh thông báo.",
    "warning", false, qa("open_app_notif", "open_wireless"),
    "Bấm \"Mở cài đặt thông báo\" và bật Cho phép thông báo (bao gồm nhóm \"Ghép đôi Local ADB\").",
    "Hoặc nếu không muốn dùng thông báo, bạn vẫn có thể chia đôi màn hình và nhập cổng + mã 6 số ở mục \"Kết nối thủ công\".");

  add("E-OEM-BG-RESTRICT", "Hệ thống tiết kiệm pin đang hạn chế ứng dụng nền",
    "Trình quản lý pin của hãng (Xiaomi, OPPO, Vivo, Samsung...) đã chặn hoặc dừng tác vụ nền của launcher.",
    "error", false, qa("open_app_battery", "auto_connect"),
    "Bấm \"Bỏ hạn chế pin cho app\" và chọn \"Không hạn chế\" (Unrestricted).",
    "Giữ màn hình launcher mở trong suốt quá trình đồng bộ và cài đặt bản dịch.", SEND);

  add("E-APK-SIGNATURE", "Chữ ký APK cập nhật không khớp",
    "Tệp APK tải về có chữ ký số khác với ứng dụng đang cài nên Android sẽ từ chối cài đè. Ứng dụng đã chủ động chặn để an toàn.",
    "error", false, qa("sync_github"),
    "Không cài tệp APK này. " + REPORT);

  add("E-APK-VERIFY", "Tệp APK tải về bị sai hoặc hỏng",
    "Kích thước hoặc mã kiểm tra SHA256 của tệp APK tải về không khớp thông tin phát hành.",
    "error", true, qa("probe_network", "sync_github"),
    "Bấm tải lại bản cập nhật ứng dụng.",
    "Nếu lặp lại nhiều lần, đổi mạng (Wi-Fi ↔ 4G/5G) rồi thử lại.", SEND);

  add("E-APK-INVALID", "Thông tin bản cập nhật APK không hợp lệ",
    "Kênh cập nhật APK thiếu dữ liệu xác minh hoặc tệp APK không đúng ứng dụng Local ADB này.",
    "error", false, qa("sync_github"),
    "Đây thường là lỗi phía bản phát hành. " + REPORT);

  // ------------------------------------------------------------------ misc
  add("E-CONFIG-CHANNEL", "Cài đặt kho GitHub chưa hợp lệ",
    "Tên kho hoặc tên nhánh GitHub bị nhập sai định dạng nên ứng dụng không biết địa chỉ tải bản dịch.",
    "error", false, qa("reset_channel", "sync_github"),
    "Bấm \"Khôi phục kênh GitHub mặc định\" (doubleD1302/AmeeVH · nhánh main).",
    "Lưu ý: tên kho có dạng tài-khoản/tên-kho, không chứa https:// hay khoảng trắng.");

  add("E-UI-BLOCKED", "Yêu cầu giao diện bị chặn",
    "Ứng dụng chặn một thao tác hoặc đường dẫn không thuộc giao diện tin cậy nội bộ.",
    "error", false, qa(),
    "Đóng hẳn ứng dụng rồi mở lại.", SEND);

  add("E-CANCELLED", "Thao tác đã được huỷ",
    "Thao tác đã dừng theo yêu cầu. Dữ liệu game được giữ nguyên ở trạng thái an toàn.",
    "info", false, qa(),
    "Bấm lại nút tương ứng khi bạn muốn thực hiện tiếp.");

  add("E-MEMORY", "Thiết bị không đủ bộ nhớ RAM",
    "Điện thoại hết RAM trống trong lúc giải nén hoặc xử lý gói dữ liệu nên hệ thống buộc dừng thao tác. Game chưa bị thay đổi.",
    "error", false, qa("install_patch"),
    "Đóng bớt các ứng dụng đang chạy ngầm (đặc biệt là game, trình duyệt nhiều tab, Facebook/TikTok).",
    "Quay lại launcher và bấm thử lại.", SEND);

  add("E-INTERNAL", "Ứng dụng gặp lỗi nội bộ",
    "Đã xảy ra lỗi ngoài dự kiến bên trong ứng dụng. Nếu thao tác chưa báo hoàn tất, dữ liệu game được bảo vệ bởi nhật ký.",
    "error", false, qa(),
    "Đóng hẳn ứng dụng khỏi đa nhiệm rồi mở lại.", SEND);

  add("E-UNKNOWN", "Lỗi chưa xác định",
    "Ứng dụng chưa phân loại được tình huống lỗi này. Toàn bộ thông tin kỹ thuật đã được ghi vào báo cáo để nhóm phát triển kiểm tra nhanh.",
    "error", false, qa("probe_network"),
    "Thử thực hiện lại thao tác một lần.", SEND);
 }

 /** Ordered rules: first rule whose needle appears in text wins. rule[0] is the code. */
 private static final String[][] RULES = {
  {"E-DEVOPT", "Hãy bật Tuỳ chọn nhà phát triển", "Chưa bật Tuỳ chọn nhà phát triển"},
  {"E-ADB-NO-WIFI", "chưa kết nối Wi-Fi", "cần bật Wi-Fi", "Gỡ lỗi không dây cần Wi-Fi"},
  {"E-ADB-AUTH", "chưa chấp nhận khóa", "chưa chấp nhận khoá", "xác minh được danh tính shell", "unauthor", "AdbPairingRequired"},
  {"E-ADB-PAIR", "Ghép đôi chưa thành công", "Ghép nối chưa thành công", "Ghép nối thất bại", "Mã cần 6 số", "bad pairing"},
  {"E-ADB-PERM", "Permission denied", "Operation not permitted", "SecurityException", "EACCES", "chặn quyền", "giám sát quyền", "cài đặt bảo mật"},
  {"E-ADB-CONN-REFUSED", "Gỡ lỗi không dây đang tắt", "cổng kết nối đã đổi", "Chưa kết nối được ADB"},
  {"E-ADB-DISCONNECTED", "Tiến trình ADB đã dừng", "Tiến trình ADB đã đóng", "Kết nối ADB đã đóng", "ADB đã được dừng", "ADB đóng trước phản hồi"},
  {"E-ADB-TIMEOUT", "ADB quá thời hạn", "Lệnh ADB quá thời hạn", "Kênh ADB đã đóng"},
  {"E-ADB-START", "Chưa khởi động được Local ADB"},
  {"E-ADB-KEY", "Khóa ADB", "Khoá ADB", "vùng khóa ADB", "chứng thư ADB"},
  {"E-ADB-INPUT", "Cổng cần nằm trong", "Chỉ dùng địa chỉ của chính điện thoại", "Không kết nối ADB tới thiết bị khác"},
  {"E-ADB-NOT-CONNECTED", "Chưa kết nối Local ADB", "Chưa kết nối ADB", "Hãy kết nối và xác minh Local ADB", "Kết nối chưa được xác nhận"},
  {"E-VER-CHANGED", "Phiên bản game đã khác", "Game đã cập nhật"},
  {"E-GAME-RUNNING", "Hãy thoát Stella Sora", "Game Stella Sora hiện đang chạy"},
  {"E-GAME-STATE", "Không kiểm tra được trạng thái game"},
  {"E-GAME-WRONG-EDITION", "bản khu vực khác", "không phải bản Global EN"},
  {"E-GAME-NO-DATA", "chưa có thư mục dữ liệu", "Chưa thấy thư mục dữ liệu game", "chưa tạo dữ liệu game"},
  {"E-GAME-ROOT-CHANGED", "Thư mục game đã đổi", "Thư mục dữ liệu game không khớp"},
  {"E-GAME-VERSION", "Chưa đọc được bản game", "Chưa đọc được GAME_VER", "tiêu đề tài nguyên không thống nhất", "Chưa xác định được người dùng Android", "Chưa xác định được danh tính thiết bị"},
  {"E-NO-GAME", "Chưa tìm thấy ứng dụng Stella Sora", "Chưa tìm thấy gói Stella Sora", "Chưa tìm thấy game"},
  {"E-BIND-MISMATCH", "không thuộc thiết bị và thư mục game"},
  {"E-RECOVERY-REQUIRED", "Có nhật ký chưa hoàn tất", "phục hồi nhật ký chưa hoàn tất", "cần phục hồi từ nhật ký", "cần Phục hồi từ nhật ký"},
  {"E-NO-RECOVERY", "Không có thao tác bị ngắt"},
  {"E-NO-RECEIPT", "Chưa có biên bản", "Chưa có biên bản/backup"},
  {"E-PKG-MISMATCH", "không khớp phiên bản game", "Gói Android không khớp"},
  {"E-NO-PACKAGE", "Chưa có gói bản dịch Android", "không có gói Android", "gói bản dịch Android", "Chưa có gói"},
  {"E-MANIFEST-INVALID", "Bảng kê không dành cho Stella Sora Android", "Gói Android thiếu", "Gói Android cần kê khai", "Gói có đường dẫn tệp trùng", "Tệp thiếu kích thước", "Tệp thiếu URL", "Bundle thiếu", "Bundle chưa xác nhận", "Gói ZIP AssetBundles", "Gói vượt giới hạn"},
  {"E-NET-CAPTIVE", "Captive Portal", "trang đăng nhập Wi-Fi", "trả về trang HTML"},
  {"E-DATA-UNVERIFIED", "Metadata Android chưa có SHA256"},
  {"E-DATA-SCHEMA", "Bản phát hành chưa hợp lệ", "Dữ liệu máy chủ chính thức", "Phản hồi máy chủ chính thức"},
  {"E-APK-NONE", "Chưa có APK Local ADB mới hơn"},
  {"E-APK-INSTALL-PERMISSION", "quyền cài đặt APK", "nguồn không xác định"},
  {"E-NOTIF-PERMISSION", "Chưa được phép hiện thông báo"},
  {"E-OEM-BG-RESTRICT", "tiết kiệm pin", "giới hạn Android", "tác vụ nền", "ForegroundService"},
  {"E-APK-SIGNATURE", "Chữ ký APK", "chữ ký khác ứng dụng"},
  {"E-APK-VERIFY", "APK không khớp kích thước"},
  {"E-APK-INVALID", "Kênh APK", "Mã phiên bản APK", "Phiên bản APK", "Biến thể APK", "Tệp APK không thuộc", "không mới hơn bản đang cài", "Không thể đọc thông tin tệp APK"},
  {"E-CONFIG-CHANNEL", "Kho GitHub cần có dạng", "Nhánh GitHub không hợp lệ", "Giao diện không hợp lệ"},
  {"E-BUSY", "Hãy chờ thao tác", "Đang có thao tác", "ADB đang có thao tác"},
  {"E-CANCELLED", "Đã dừng tải tệp"},
  {"E-ZIP-CORRUPT", "giải nén AssetBundles", "tệp ZIP bị lỗi", "ZipException", "invalid entry crc"},
  {"E-STORAGE", "Không đủ bộ nhớ", "Không đủ dung lượng", "Bộ nhớ vùng game", "No space left", "ENOSPC"},
  {"E-STORAGE-ACCESS", "Chưa truy cập được bộ nhớ ngoài", "Không tạo được vùng", "Không tạo được thư mục trạng thái", "Vùng lưu vượt phạm vi", "Không xoá được tệp cũ", "Chưa chuyển được tệp tải"},
  {"E-DL-TIMEOUT", "Tải quá thời hạn", "Metadata quá lớn hoặc quá thời hạn"},
  {"E-TIMEOUT", "Thao tác vượt thời hạn", "quá thời hạn", "vượt thời hạn"},
  {"E-DL-RESPONSE", "Nguồn tải cần là HTTPS", "Máy chủ không có đích chuyển hướng", "chuyển hướng quá nhiều"},
  {"E-DL-VERIFY", "Tệp tải về không khớp", "Tệp tải về không đúng", "Kích thước metadata không khớp", "SHA256 metadata không khớp", "Tệp tải từ máy chủ Yostar sai MD5", "Bản gốc dựng lại không khớp MD5", "BZip2", "BSDIFF40"},
  {"E-FILE-MISMATCH", "Tệp bản dịch không khớp"},
  {"E-VERIFY-WRITE", "Đọc lại sau cài không khớp", "Đọc lại phục hồi không khớp", "Tệp tạm không khớp", "Không thể ghi tệp an toàn", "Không thể phục hồi tệp", "Không thể xoá tệp mới", "Chưa cập nhật được biên bản"},
  {"E-FILE-CHANGED", "Tệp đã thay đổi", "Tệp đã đổi", "Tệp game đổi", "Tệp đổi", "đổi ngoài thao tác", "Tệp tạm đã tồn tại ngoài nhật ký"},
  {"E-VERIFY", "Chưa đối chiếu được kích thước", "SHA256", "kích thước"},
  {"E-BACKUP", "Backup", "Không sao lưu được", "Không đủ dung lượng để sao lưu"},
  {"E-JOURNAL", "nhật ký", "Nhật ký", "vòng lặp biên bản", "Mã nhật ký", "biên bản cũ"},
  {"E-SECURITY", "liên kết", "vượt phạm vi", "vượt vùng ứng dụng", "không thuộc phạm vi", "Đường dẫn", "ký tự điều khiển", "tệp zip vượt giới hạn"},
  {"E-UI-BLOCKED", "Yêu cầu bị chặn", "Tải bị chặn", "không thuộc giao diện", "Liên kết không hợp lệ"},
  {"E-MEMORY", "OutOfMemoryError", "không đủ bộ nhớ RAM"},
  {"E-ADB", "ADB"},
  {"E-INTERNAL", "nội bộ", "không được hỗ trợ", "Dữ liệu quá lớn"},
 };

 private static final Pattern HTTP = Pattern.compile("HTTP ([0-9]{3})");

 static Entry lookup(String code) {
  if (code == null) return MAP.get("E-UNKNOWN");
  Entry e = MAP.get(code);
  if (e != null) return e;
  Matcher m = Pattern.compile("E-HTTP-([0-9]{3})").matcher(code);
  if (m.matches()) {
   int status = Integer.parseInt(m.group(1));
   Entry base = MAP.get(status == 511 ? "E-NET-CAPTIVE"
     : status == 403 || status == 429 ? "E-HTTP-RATE"
     : status == 404 ? "E-HTTP-404"
     : status >= 500 && status <= 599 ? "E-HTTP-5XX" : "E-HTTP-4XX");
   return new Entry(code, base.title + " (HTTP " + status + ")", base.summary, base.level, base.network, base.steps, base.quickActions);
  }
  return MAP.get("E-UNKNOWN");
 }

 static boolean known(String code) { return MAP.containsKey(code); }
 static java.util.Set<String> codes() { return MAP.keySet(); }

 static boolean isAdbAction(String action) {
  if (action == null) return false;
  return "pair".equals(action) || "connect".equals(action) || "autoConnect".equals(action)
    || "detect".equals(action) || "verify".equals(action) || "restore".equals(action)
    || "guardRestore".equals(action) || "recover".equals(action);
 }

 /** Code for a message string (Vietnamese app messages, HTTP statuses, OS errno text); {@code null} when nothing matches. */
 static String matchText(String text) {
  if (text == null || text.isEmpty()) return null;
  Matcher http = HTTP.matcher(text);
  if (http.find()) {
   String st = http.group(1);
   if ("511".equals(st)) return "E-NET-CAPTIVE";
   return "E-HTTP-" + st;
  }
  for (String[] rule : RULES) {
   for (int i = 1; i < rule.length; i++) {
    if (text.contains(rule[i])) return rule[0];
   }
  }
  String low = text.toLowerCase(Locale.ROOT);
  if (low.contains("enospc") || low.contains("no space left")) return "E-STORAGE";
  if (low.contains("eacces") || low.contains("permission denied") || low.contains("operation not permitted")) return "E-ADB-PERM";
  if (low.contains("econnrefused") || low.contains("connection refused")) return "E-NET-REFUSED";
  if (low.contains("enetunreach") || low.contains("network is unreachable") || low.contains("ehostunreach")) return "E-NET-OFFLINE";
  if (low.contains("econnreset") || low.contains("broken pipe") || low.contains("connection reset")) return "E-NET-RESET";
  if (low.contains("etimedout") || low.contains("timed out")) return "E-NET-TIMEOUT";
  if (low.contains("<!doctype html") || low.contains("<html")) return "E-NET-CAPTIVE";
  return null;
 }

 /** Never null: explicit code, then exception type, then message text, finally E-UNKNOWN. */
 static String classify(Throwable e) {
  return classify(e, null);
 }

 /** Context-aware classification: distinguishes Local ADB socket failures from GitHub network failures. */
 static String classify(Throwable e, String action) {
  int depth = 0;
  for (Throwable t = e; t != null && depth < 8; t = t.getCause(), depth++) {
   if (t instanceof Coded) return ((Coded) t).code();
  }
  boolean adbCtx = isAdbAction(action);
  StringBuilder all = new StringBuilder();
  depth = 0;
  for (Throwable t = e; t != null && depth < 8; t = t.getCause(), depth++) {
   String cls = t.getClass().getName();
   String m = t.getMessage() == null ? "" : t.getMessage();
   String lower = m.toLowerCase(Locale.ROOT);
   all.append(m).append('\n');

   if (t instanceof OutOfMemoryError) return "E-MEMORY";
   if (t instanceof ZipException) return "E-ZIP-CORRUPT";
   if (cls.contains("AdbPairingRequired") || cls.contains("AdbAuthentication")) return "E-ADB-AUTH";
   if (cls.contains("ForegroundServiceStartNotAllowed")) return "E-OEM-BG-RESTRICT";

   if (adbCtx) {
    if (t instanceof NoRouteToHostException) return "E-ADB-NO-WIFI";
    if (t instanceof ConnectException) {
     if (lower.contains("enetunreach") || lower.contains("unreachable") || lower.contains("network is down")) return "E-ADB-NO-WIFI";
     return "E-ADB-CONN-REFUSED";
    }
    if (t instanceof SocketTimeoutException) return "E-ADB-TIMEOUT";
    if (t instanceof EOFException) return "E-ADB-DISCONNECTED";
    if (t instanceof SocketException) {
     if (lower.contains("enetunreach") || lower.contains("unreachable")) return "E-ADB-NO-WIFI";
     return "E-ADB-DISCONNECTED";
    }
    if (t instanceof SSLException) return "pair".equals(action) ? "E-ADB-PAIR" : "E-ADB-AUTH";
   }

   if (t instanceof UnknownHostException) return "E-NET-DNS";
   if (t instanceof SocketTimeoutException) return "E-NET-TIMEOUT";
   if (t instanceof CertificateException || t instanceof CertPathValidatorException) return "E-NET-TLS-CERT";
   if (t instanceof SSLException) {
    boolean cert = lower.contains("certificate") || lower.contains("trust anchor") || lower.contains("certpath");
    Throwable c = t.getCause();
    return cert || c instanceof CertificateException || c instanceof CertPathValidatorException ? "E-NET-TLS-CERT" : "E-NET-TLS";
   }
   if (t instanceof NoRouteToHostException) return "E-NET-OFFLINE";
   if (t instanceof ConnectException) {
    return lower.contains("enetunreach") || lower.contains("unreachable") || lower.contains("network is down") ? "E-NET-OFFLINE" : "E-NET-REFUSED";
   }
   if (t instanceof EOFException) return "E-NET-RESET";
   if (t instanceof SocketException) {
    if (lower.contains("enetunreach") || lower.contains("unreachable")) return "E-NET-OFFLINE";
    return lower.contains("reset") || lower.contains("abort") || lower.contains("broken pipe") || lower.contains("econn") || lower.contains("eof") ? "E-NET-RESET" : "E-NET";
   }
   if ("org.json.JSONException".equals(cls)) {
    if (lower.contains("<html") || lower.contains("<!doctype")) return "E-NET-CAPTIVE";
    return "E-DATA-JSON";
   }
  }
  String byText = matchText(all.toString());
  if (byText != null) return byText;
  if (e == null) return "E-UNKNOWN";
  return e instanceof java.io.IOException ? "E-UNKNOWN" : "E-INTERNAL";
 }

 /** Overload for plain text with no exception (e.g. a message shown to the user). */
 static String classifyText(String text) {
  String c = matchText(text);
  return c == null ? "E-UNKNOWN" : c;
 }

 /** Human Vietnamese label for launcher action names. */
 static String actionLabel(String action) {
  if (action == null || action.isEmpty()) return "Thao tác ứng dụng";
  switch (action) {
   case "sync": return "Đồng bộ GitHub";
   case "pair": return "Ghép đôi Local ADB";
   case "connect": return "Kết nối Local ADB";
   case "autoConnect": return "Kết nối nhanh Local ADB";
   case "detect": return "Tìm và kiểm tra game";
   case "install": return "Cài / Cập nhật Việt hoá";
   case "verify": return "Kiểm tra tệp đã cài";
   case "restore": return "Khôi phục bản trước cài";
   case "guardRestore": return "Đóng game & Khôi phục dữ liệu gốc";
   case "checkOfficialUpdate": return "Kiểm tra máy chủ cập nhật Yostar";
   case "recover": return "Phục hồi thao tác bị ngắt";
   case "checkUpdate": return "Kiểm tra cập nhật ứng dụng";
   case "prepareUpdate": return "Tải bản cập nhật APK";
   case "installUpdate": return "Mở trình cài đặt APK";
   case "saveSettings": return "Lưu cài đặt";
   case "launchGame": return "Mở Stella Sora";
   case "probeNetwork": return "Kiểm tra kết nối & DNS";
   case "explain": return "Xem lý do chưa cài được";
   case "startPairingNotification": return "Ghép đôi qua thông báo";
   default: return action;
  }
 }
}
