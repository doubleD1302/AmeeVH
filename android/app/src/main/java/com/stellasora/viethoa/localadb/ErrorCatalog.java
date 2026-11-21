package com.stellasora.viethoa.localadb;
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
import javax.net.ssl.SSLException;

/**
 * Plain-language error catalog for the Android launcher. Same {@code E-...} namespace as the PC launcher
 * (docs/ERROR_CODES.md) so a copied code always means the same thing.
 * Pure Java (no Android or org.json types) so it can be unit-tested on a JVM.
 */
final class ErrorCatalog {
 private ErrorCatalog(){}

 /** Implemented by exceptions that carry an explicit catalog code (see StellaException). */
 interface Coded { String code(); }

 static final class Entry {
  final String code, title, summary, level; final boolean network; final String[] steps;
  Entry(String code,String title,String summary,String level,boolean network,String[] steps){this.code=code;this.title=title;this.summary=summary;this.level=level;this.network=network;this.steps=steps;}
  boolean isError(){return "error".equals(level);}
 }

 private static final LinkedHashMap<String,Entry> MAP = new LinkedHashMap<>();
 private static final String SEND = "Nếu vẫn lỗi, bấm \"Sao chép mã lỗi\" và gửi cho người làm bản dịch.";
 private static final String REPORT = "Bấm \"Sao chép mã lỗi\" và gửi cho người làm bản dịch.";
 private static void add(String code,String title,String summary,String level,boolean network,String... steps){MAP.put(code,new Entry(code,title,summary,level,network,steps));}

 static {
  // ------------------------------------------------------------------ network
  add("E-NET","Không kết nối được máy chủ","Điện thoại không nói chuyện được với máy chủ. Mạng có thể đang yếu, bị chặn hoặc máy chủ đang bận.","error",true,
    "Kiểm tra điện thoại có Internet không (thử mở https://github.com trên trình duyệt).","Tắt VPN/DNS riêng nếu đang dùng, hoặc đổi mạng (Wi-Fi ↔ 4G) rồi thử lại.",SEND);
  add("E-NET-OFFLINE","Điện thoại chưa có đường ra Internet","Điện thoại không có kết nối mạng dùng được. Có thể đang bật chế độ máy bay, Wi-Fi chưa đăng nhập hoặc mất sóng.","error",true,
    "Tắt chế độ máy bay, bật Wi-Fi hoặc dữ liệu di động.","Nếu dùng Wi-Fi công cộng, mở trình duyệt để đăng nhập trang của mạng đó.","Sau khi có mạng, bấm Đồng bộ GitHub.");
  add("E-NET-DNS","Không tìm ra địa chỉ GitHub (lỗi DNS)","Điện thoại không tra được địa chỉ của GitHub. Thường do mạng vừa mất kết nối, DNS của nhà mạng bị lỗi hoặc GitHub bị chặn ở mạng của bạn.","error",true,
    "Mở https://github.com trên trình duyệt. Nếu cũng không vào được thì lỗi nằm ở mạng của bạn, không phải ở ứng dụng.",
    "Đổi mạng (Wi-Fi ↔ 4G) rồi thử lại.",
    "Cài đặt → Mạng → DNS riêng tư: chọn \"Tự động\" hoặc nhập dns.google; hoặc bật VPN/Cloudflare WARP.",SEND);
  add("E-NET-TIMEOUT","GitHub phản hồi quá chậm","Ứng dụng đã gọi tới máy chủ nhưng chờ mãi không thấy trả lời (quá thời gian chờ). Mạng đang chập chờn hoặc bị nghẽn.","error",true,
    "Chờ 1–2 phút rồi thử lại.","Thử mạng khác (đổi giữa Wi-Fi và 4G).","Tắt VPN hoặc ứng dụng tăng tốc mạng nếu có.",SEND);
  add("E-NET-REFUSED","Máy chủ từ chối kết nối","Kết nối tới máy chủ bị từ chối ngay. Thường do mạng, VPN hoặc ứng dụng chặn quảng cáo đang chặn cổng 443 (HTTPS).","error",true,
    "Tạm tắt VPN, DNS chặn quảng cáo hoặc ứng dụng tường lửa rồi thử lại.","Đổi sang mạng khác.",SEND);
  add("E-NET-RESET","Kết nối bị ngắt giữa chừng","Đang tải dở thì kết nối bị cắt. Mạng chập chờn hoặc có ứng dụng đã ngắt kết nối.","error",true,
    "Thử lại, ứng dụng sẽ tải tiếp phần còn lại.","Nếu hay bị ngắt, đổi mạng hoặc đứng gần router hơn.",SEND);
  add("E-NET-TLS-CERT","Chứng chỉ bảo mật không được tin cậy","Kết nối HTTPS bị từ chối vì chứng chỉ của máy chủ không hợp lệ với điện thoại. Hay gặp khi ngày giờ máy sai hoặc mạng/VPN đang chèn vào kết nối.","error",true,
    "Kiểm tra ngày, giờ và múi giờ (bật \"Tự động đặt ngày giờ\").","Tắt VPN/proxy hoặc đổi sang mạng khác.","Nếu Wi-Fi công cộng bắt đăng nhập, hãy đăng nhập trước.",SEND);
  add("E-NET-TLS","Không thiết lập được kết nối an toàn (HTTPS)","Quá trình bắt tay bảo mật với máy chủ thất bại, thường do mạng can thiệp vào kết nối.","error",true,
    "Tắt VPN/proxy rồi thử lại, hoặc đổi mạng.","Cập nhật Android và Google Play services nếu có bản mới.",SEND);
  add("E-HTTP-RATE","GitHub đang giới hạn lượt truy cập","GitHub tạm chặn vì mạng của bạn gọi quá nhiều lần trong thời gian ngắn (hay gặp trên 4G hoặc Wi-Fi dùng chung một địa chỉ mạng).","error",true,
    "Chờ 10–15 phút rồi thử lại.","Hoặc đổi sang mạng khác (Wi-Fi ↔ 4G).");
  add("E-HTTP-404","Không tìm thấy tệp trên GitHub","Bản phát hành hoặc tệp ứng dụng cần không còn ở địa chỉ đó (đã bị xoá hoặc tên kho/nhánh bị sai).","error",true,
    "Vào Local ADB → Cài đặt kênh, kiểm tra Kho và Nhánh (mặc định doubleD1302/AmeeVH và main).","Nếu bạn chưa sửa gì ở đó, đây là lỗi phía người phát hành. "+REPORT);
  add("E-HTTP-5XX","GitHub đang gặp sự cố","Máy chủ GitHub trả về lỗi nội bộ (không phải lỗi của điện thoại).","error",true,
    "Chờ vài phút rồi thử lại.","Xem tình trạng tại https://www.githubstatus.com.");
  add("E-HTTP-4XX","GitHub từ chối yêu cầu","Máy chủ trả về một mã từ chối (HTTP 4xx) cho yêu cầu của ứng dụng.","error",true,
    "Thử lại sau ít phút hoặc đổi mạng.",SEND);
  // ------------------------------------------------------------------ data / package
  add("E-SYNC-PENDING","Ứng dụng chưa đọc xong thông tin từ GitHub","Ứng dụng chưa đồng bộ bản phát hành và gói Android nên chưa cho cài.","info",false,
    "Bấm Đồng bộ GitHub và chờ vài giây.","Nếu vẫn không được, mở lại để xem lý do cụ thể.");
  add("E-DATA-JSON","Dữ liệu tải về không đọc được","Máy chủ trả về nội dung không phải dữ liệu mong đợi. Hay gặp khi Wi-Fi công cộng bắt đăng nhập, hoặc VPN/DNS chèn trang cảnh báo.","error",true,
    "Mở trình duyệt, vào https://github.com xem có hiện trang đăng nhập/cảnh báo không.","Tắt VPN/DNS riêng rồi thử lại.",SEND);
  add("E-DATA-SCHEMA","Dữ liệu GitHub trả về sai định dạng","Ứng dụng đọc được tệp nhưng nội dung thiếu hoặc sai cấu trúc nên không dùng. Có thể tệp đang được cập nhật dở trên GitHub.","error",false,
    "Chờ vài phút rồi bấm Đồng bộ GitHub lại.",SEND);
  add("E-DATA-UNVERIFIED","Tệp phát hành chưa có mã xác minh","Tệp trên GitHub không kèm mã SHA256 nên ứng dụng từ chối dùng để đảm bảo an toàn.","error",false,
    "Đây là lỗi phía người phát hành. "+REPORT);
  add("E-NO-PACKAGE","Bản phát hành chưa có gói Android","Bản phát hành mới nhất trên GitHub chưa đính kèm gói Android tương thích (gói Windows hoặc APK overlay cũ không dùng được cho ứng dụng này).","error",false,
    "Chờ người làm bản dịch đăng gói Android.","Nếu đã chờ lâu mà vẫn vậy: "+REPORT);
  add("E-MANIFEST-INVALID","Bảng kê gói Android bị lỗi","Bảng kê thiếu thông tin hoặc có dữ liệu không hợp lệ nên ứng dụng dừng để tránh cài sai. Game chưa bị thay đổi.","error",false,
    "Chờ bản phát hành được sửa rồi bấm Đồng bộ GitHub lại.",SEND);
  add("E-PKG-MISMATCH","Gói bản dịch không khớp phiên bản game trên máy","Gói Android trên GitHub dành cho phiên bản game/tài nguyên khác với game đang cài trên điện thoại nên không cài để tránh làm hỏng game.","error",false,
    "Mở Stella Sora để game tự cập nhật tài nguyên mới nhất, rồi quay lại bấm \"Tìm và kiểm tra game\".","Nếu game đã mới nhất, chờ người làm bản dịch phát hành gói khớp phiên bản của bạn.","Kiểm tra phiên bản game/tài nguyên ghi trong mã lỗi.");
  // ------------------------------------------------------------------ download
  add("E-DL-VERIFY","Tệp tải về bị sai hoặc hỏng","Tệp tải xong nhưng kích thước hoặc mã kiểm tra (SHA256) không khớp bảng kê. Có thể do đường truyền lỗi hoặc bảng kê trỏ nhầm tệp.","error",true,
    "Bấm cài lại, ứng dụng sẽ tải lại tệp (phần hợp lệ đã tải được giữ lại).","Nếu lặp lại nhiều lần, đổi mạng rồi thử lại.",SEND);
  add("E-DL-RANGE","Máy chủ trả dữ liệu tải tiếp không đúng","Ứng dụng cố tải tiếp phần dở dang nhưng máy chủ trả phần dữ liệu không khớp.","error",true,
    "Bấm cài lại, ứng dụng sẽ tải lại từ đầu.",SEND);
  add("E-DL-OVERSIZE","Tệp trên máy chủ lớn hơn kích thước công bố","Tệp thực tế lớn hơn kích thước ghi trong bảng kê nên bị từ chối.","error",true,
    "Đây thường là lỗi phía người phát hành (bảng kê trỏ nhầm tệp). "+REPORT);
  add("E-DL-TIMEOUT","Tải quá lâu so với thời hạn","Tệp tải chậm hơn thời hạn cho phép. Phần đã tải hợp lệ vẫn được giữ lại.","error",true,
    "Bấm cài lại để tải tiếp.","Nếu mạng yếu, đổi mạng rồi thử lại.");
  add("E-DL-PARAM","Thông tin tải không hợp lệ","Bảng kê có địa chỉ hoặc kích thước tải không hợp lệ.","error",false,
    "Đây là lỗi phía người phát hành. "+REPORT);
  add("E-DL-RESPONSE","Máy chủ trả về dữ liệu tải không hợp lệ","Phản hồi của máy chủ khi tải tệp không đúng định dạng mong đợi (ví dụ nguồn không phải HTTPS hoặc chuyển hướng bất thường).","error",true,
    "Thử lại sau ít phút.",SEND);
  add("E-TIMEOUT","Thao tác quá thời hạn","Thao tác chạy lâu hơn thời hạn cho phép nên bị dừng để an toàn.","error",false,
    "Thử lại. Nếu mạng yếu, đổi mạng rồi thử lại.",SEND);
  // ------------------------------------------------------------------ ADB
  add("E-DEVOPT","Chưa bật Tuỳ chọn nhà phát triển","Local ADB cần Tuỳ chọn nhà phát triển và Gỡ lỗi không dây để ứng dụng đọc/ghi dữ liệu game một cách an toàn.","warning",false,
    "Cài đặt → Thông tin điện thoại → bấm 7 lần vào Số bản dựng để bật Tuỳ chọn nhà phát triển.","Sau đó vào Tuỳ chọn nhà phát triển → bật Gỡ lỗi không dây và quay lại ứng dụng.");
  add("E-ADB-NOT-CONNECTED","Chưa kết nối Local ADB","Ứng dụng cần kết nối Local ADB (kết nối tới chính điện thoại này) để cài bản dịch.","warning",false,
    "Bấm \"Kết nối nhanh Local ADB\" nếu máy đã ghép đôi trước đó.","Nếu chưa ghép đôi, vào Local ADB và làm theo hướng dẫn nhập mã 6 số một lần duy nhất.");
  add("E-ADB-AUTH","Điện thoại chưa chấp nhận khoá Local ADB","Android không tin khoá của ứng dụng (hoặc đã bị xoá khỏi danh sách thiết bị ghép đôi).","error",false,
    "Vào Tuỳ chọn nhà phát triển → Gỡ lỗi không dây → Ghép nối thiết bị bằng mã ghép nối.","Nhập mã 6 số vào ứng dụng để ghép đôi lại một lần.");
  add("E-ADB-PAIR","Ghép đôi chưa thành công","Mã ghép đôi sai, đã hết hạn hoặc cổng ghép đôi đã đổi. Mã ghép đôi khác cổng kết nối.","error",false,
    "Trong Gỡ lỗi không dây, bấm \"Ghép nối thiết bị bằng mã ghép nối\" để lấy mã MỚI và giữ cửa sổ đó mở.","Nhập đúng cổng ghép đôi và mã 6 số hiện trên cửa sổ đó.","Bật Wi-Fi (cần cùng một mạng Wi-Fi với chính điện thoại).");
  add("E-ADB-TIMEOUT","Local ADB không phản hồi","Kết nối Local ADB bị đóng hoặc không trả lời kịp.","error",false,
    "Tắt rồi bật lại Gỡ lỗi không dây, sau đó bấm Kết nối nhanh.","Giữ màn hình sáng khi kết nối.",SEND);
  add("E-ADB-START","Không khởi động được Local ADB","Dịch vụ Local ADB của ứng dụng không khởi động được.","error",false,
    "Đóng hẳn ứng dụng rồi mở lại.","Khởi động lại điện thoại nếu vẫn lỗi.",SEND);
  add("E-ADB-KEY","Khoá Local ADB gặp vấn đề","Khoá ADB riêng của ứng dụng không tạo được hoặc không khớp chứng thư. Ứng dụng không tự thay khoá đã ghép nối.","error",false,
    "Đóng hẳn ứng dụng rồi mở lại.","Nếu vẫn lỗi, xoá dữ liệu ứng dụng rồi ghép đôi lại.",SEND);
  add("E-ADB-INPUT","Thông tin kết nối Local ADB không hợp lệ","Cổng phải trong khoảng 1024–65535 và chỉ dùng địa chỉ của chính điện thoại này.","warning",false,
    "Nhập đúng cổng đang hiện trong Gỡ lỗi không dây.");
  add("E-ADB","Lỗi Local ADB","Lệnh gửi qua Local ADB không thực hiện được.","error",false,
    "Bảo đảm Gỡ lỗi không dây đang bật và ứng dụng hiển thị \"Đã kết nối\".","Bấm Kết nối nhanh rồi thử lại.",SEND);
  // ------------------------------------------------------------------ game
  add("E-NO-GAME","Chưa tìm thấy game Stella Sora","Không thấy ứng dụng Stella Sora (bản Global/EN của YoStar) trên điện thoại này.","warning",false,
    "Cài Stella Sora từ Google Play (com.YoStarEN.StellaSora).","Mở game một lần cho nó tải đủ dữ liệu, rồi bấm \"Tìm và kiểm tra game\".");
  add("E-GAME-VERSION","Chưa đọc được phiên bản game","Ứng dụng cần đọc phiên bản game và tài nguyên để chọn đúng gói, nhưng chưa đọc được hoặc các tệp báo phiên bản khác nhau.","error",false,
    "Mở Stella Sora để tải đủ dữ liệu, thoát game rồi bấm \"Tìm và kiểm tra game\".","Bảo đảm Local ADB đang kết nối.",SEND);
  add("E-GAME-STATE","Không kiểm tra được trạng thái game","Ứng dụng chưa xác định được game có đang chạy hay không nên dừng lại để không làm hỏng dữ liệu.","error",false,
    "Thoát hẳn Stella Sora (vuốt đóng khỏi danh sách ứng dụng gần đây) rồi thử lại.","Bảo đảm Local ADB đang kết nối.");
  add("E-GAME-RUNNING","Game đang chạy","Không thể thay đổi tệp khi game đang mở. Ứng dụng dừng lại để không làm hỏng dữ liệu.","warning",false,
    "Thoát hẳn Stella Sora (vuốt đóng khỏi danh sách ứng dụng gần đây).","Sau đó thử lại.");
  add("E-VER-CHANGED","Game đã cập nhật sau lần cài trước","Phiên bản game/tài nguyên đã khác lúc cài nên bản sao lưu cũ không dùng để khôi phục (sẽ ghi đè sai).","warning",false,
    "Bấm Cập nhật Việt hoá để cài lại bản dịch cho phiên bản game hiện tại.");
  add("E-GAME-ROOT-CHANGED","Thư mục dữ liệu game đã thay đổi","Thư mục game không còn khớp với nơi ứng dụng đã ghi nhận.","error",false,
    "Bấm \"Tìm và kiểm tra game\" để đọc lại thư mục.",SEND);
  add("E-BIND-MISMATCH","Nhật ký/bản sao lưu thuộc thiết bị hoặc thư mục khác","Dữ liệu phục hồi không thuộc điện thoại hoặc thư mục game này nên không dùng để tránh ghi đè sai.","error",false,
    "Không dùng bản sao lưu từ máy khác.",SEND);
  // ------------------------------------------------------------------ storage / install
  add("E-STORAGE","Không đủ dung lượng","Không còn đủ chỗ trống để tải gói, sao lưu và thay tệp một cách an toàn. Game chưa bị thay đổi.","error",false,
    "Giải phóng thêm vài GB bộ nhớ (xoá ảnh/video/ứng dụng không dùng).","Rồi bấm cài lại.");
  add("E-STORAGE-ACCESS","Ứng dụng chưa truy cập được vùng lưu trữ của nó","Ứng dụng không tạo hoặc không ghi được thư mục tải/sao lưu riêng.","error",false,
    "Đóng hẳn ứng dụng rồi mở lại.","Kiểm tra bộ nhớ trong còn trống.",SEND);
  add("E-FILE-CHANGED","Tệp game bị thay đổi trong lúc ứng dụng làm việc","Có thứ khác (Google Play đang cập nhật game, ứng dụng khác) vừa sửa tệp game nên ứng dụng dừng để không ghi đè sai. Game được giữ nguyên.","error",false,
    "Đợi Google Play cập nhật xong game (nếu có), thoát game rồi thử lại.",SEND);
  add("E-VERIFY-WRITE","Ghi xong nhưng đọc lại không khớp","Sau khi ghi tệp, ứng dụng đọc lại để kiểm tra nhưng nội dung khác dự kiến.","error",false,
    "Bảo đảm bộ nhớ còn trống, thoát game rồi thử lại.","Ứng dụng đã hoàn tác nếu cần; nếu thấy cảnh báo cần phục hồi, bấm Phục hồi thao tác.",SEND);
  add("E-VERIFY","Không đối chiếu được tệp trên máy","Ứng dụng không đọc được kích thước hoặc SHA256 của tệp game để đối chiếu.","error",false,
    "Bảo đảm Local ADB đang kết nối rồi thử lại.",SEND);
  add("E-FILE-MISMATCH","Tệp game không còn khớp bản Việt hoá đã cài","Một số tệp đã bị thay đổi sau khi cài (game tự cập nhật hoặc công cụ khác ghi đè).","warning",false,
    "Bấm Cập nhật/Cài lại Việt hoá để áp dụng lại.");
  add("E-BACKUP","Bản sao lưu bị thiếu hoặc hỏng","Ứng dụng cần bản sao lưu để khôi phục nhưng nó không còn hoặc sai nội dung (hoặc không sao lưu được tệp gốc).","error",false,
    "Giải phóng dung lượng rồi thử lại.","Nếu cần về bản gốc, gỡ và cài lại game từ Google Play.",SEND);
  add("E-JOURNAL","Nhật ký thao tác có vấn đề","Nhật ký ghi lại thao tác dở dang bị hỏng hoặc không hợp lệ. Ứng dụng giữ nguyên để bạn gửi cho người hỗ trợ.","error",false,
    "Bấm \"Sao chép mã lỗi\" và gửi cho người làm bản dịch.","Đừng xoá dữ liệu ứng dụng trước khi gửi.");
  add("E-RECOVERY-REQUIRED","Có thao tác trước đó bị ngắt giữa chừng","Lần cài/khôi phục trước chưa kết thúc (hết pin, tắt ngang…). Phải phục hồi trước khi làm tiếp để game không bị hỏng.","warning",false,
    "Bấm \"Phục hồi thao tác\" và chờ hoàn tất.","Sau đó cài lại như bình thường.");
  add("E-NO-RECOVERY","Không có thao tác nào cần phục hồi","Không có nhật ký dở dang nên không có gì để phục hồi.","info",false,
    "Không cần làm gì thêm.");
  add("E-NO-RECEIPT","Chưa cài Việt hoá bằng ứng dụng này","Kiểm tra tệp và Khôi phục cần biên bản/bản sao lưu do ứng dụng tạo lúc cài. Máy này chưa có nên chưa có gì để kiểm tra. Đây không phải lỗi hỏng game.","info",false,
    "Bấm \"Cài Việt hoá\" để cài bản dịch.","Nếu trước đây bạn cài bằng cách khác, hãy cài lại một lần bằng ứng dụng này.");
  add("E-SECURITY","Bị chặn vì không an toàn","Đường dẫn hoặc tệp nằm ngoài phạm vi cho phép (liên kết, đường dẫn lạ, tệp nén quá giới hạn) nên ứng dụng dừng để bảo vệ game. Game chưa bị thay đổi.","error",false,
    "Đừng dùng gói này. "+REPORT);
  add("E-BUSY","Ứng dụng đang bận","Một thao tác khác đang chạy nên ứng dụng chưa nhận thêm yêu cầu.","warning",false,
    "Chờ thao tác hiện tại hoàn tất rồi thử lại.");
  // ------------------------------------------------------------------ app update (APK)
  add("E-APK-NONE","Chưa có bản ứng dụng mới hơn","Trên GitHub chưa có APK Local ADB mới hơn bản đang dùng.","info",false,
    "Không cần làm gì, bạn đang dùng bản mới nhất.");
  add("E-APK-SIGNATURE","Chữ ký APK không khớp","APK tải về được ký bằng khoá khác với ứng dụng đang cài nên Android sẽ từ chối. Ứng dụng đã chặn để an toàn.","error",false,
    "Đừng cài APK này. "+REPORT);
  add("E-APK-VERIFY","APK tải về bị sai hoặc hỏng","Kích thước hoặc SHA256 của APK không khớp thông tin công bố.","error",true,
    "Bấm tải lại bản cập nhật.","Nếu lặp lại, đổi mạng rồi thử lại.",SEND);
  add("E-APK-INVALID","Thông tin bản cập nhật ứng dụng không hợp lệ","Kênh cập nhật APK thiếu dữ liệu hoặc APK không phải bản mới hợp lệ của ứng dụng này.","error",false,
    "Đây thường là lỗi phía người phát hành. "+REPORT);
  // ------------------------------------------------------------------ misc
  add("E-CONFIG-CHANNEL","Cài đặt kênh GitHub chưa hợp lệ","Tên kho hoặc nhánh GitHub có dạng không đúng nên ứng dụng không biết tải bản dịch ở đâu.","error",false,
    "Đặt lại Kho = doubleD1302/AmeeVH và Nhánh = main rồi lưu.","Kho phải có dạng tên-tài-khoản/tên-kho.");
  add("E-UI-BLOCKED","Yêu cầu bị chặn","Ứng dụng chặn một yêu cầu không thuộc giao diện tin cậy.","error",false,
    "Đóng và mở lại ứng dụng.",SEND);
  add("E-CANCELLED","Thao tác đã được huỷ","Thao tác đã bị dừng. Game được giữ ở trạng thái an toàn.","info",false,
    "Bấm lại nút tương ứng nếu muốn làm tiếp.");
  add("E-INTERNAL","Ứng dụng gặp lỗi nội bộ","Có lỗi ngoài dự kiến trong ứng dụng. Game chưa bị thay đổi nếu thao tác chưa báo hoàn tất.","error",false,
    "Đóng hẳn ứng dụng rồi mở lại.",SEND);
  add("E-UNKNOWN","Lỗi chưa xác định","Ứng dụng chưa nhận ra loại lỗi này. Thông tin chi tiết được lưu trong mã lỗi để người hỗ trợ xem.","error",false,
    "Thử lại một lần.",SEND);
 }

 /** Ordered rules: the first rule whose needle appears in the text wins. {rule[0]} is the code. */
 private static final String[][] RULES = {
  {"E-DEVOPT","Hãy bật Tuỳ chọn nhà phát triển"},
  {"E-ADB-AUTH","chưa chấp nhận khóa","xác minh được danh tính shell","unauthor"},
  {"E-ADB-PAIR","Ghép đôi chưa thành công","Ghép nối chưa thành công","Mã cần 6 số"},
  {"E-ADB-TIMEOUT","ADB quá thời hạn","Kênh ADB đã đóng"},
  {"E-ADB-START","Chưa khởi động được Local ADB"},
  {"E-ADB-KEY","Khóa ADB","vùng khóa ADB"},
  {"E-ADB-INPUT","Cổng cần nằm trong","Chỉ dùng địa chỉ của chính điện thoại","Không kết nối ADB tới thiết bị khác"},
  {"E-ADB-NOT-CONNECTED","Chưa kết nối Local ADB","Hãy kết nối và xác minh Local ADB","Kết nối chưa được xác nhận"},
  {"E-VER-CHANGED","Phiên bản game đã khác","Game đã cập nhật"},
  {"E-GAME-RUNNING","Hãy thoát Stella Sora","Game Stella Sora hiện đang chạy"},
  {"E-GAME-STATE","Không kiểm tra được trạng thái game"},
  {"E-GAME-ROOT-CHANGED","Thư mục game đã đổi","Thư mục dữ liệu game không khớp"},
  {"E-GAME-VERSION","Chưa đọc được bản game","tiêu đề tài nguyên không thống nhất","Chưa xác định được người dùng Android","Chưa xác định được danh tính thiết bị"},
  {"E-NO-GAME","Chưa tìm thấy ứng dụng Stella Sora","Chưa tìm thấy game"},
  {"E-BIND-MISMATCH","không thuộc thiết bị và thư mục game"},
  {"E-RECOVERY-REQUIRED","Có nhật ký chưa hoàn tất","phục hồi nhật ký chưa hoàn tất","cần phục hồi từ nhật ký"},
  {"E-NO-RECOVERY","Không có thao tác bị ngắt"},
  {"E-NO-RECEIPT","Chưa có biên bản","Chưa có biên bản/backup"},
  {"E-PKG-MISMATCH","không khớp phiên bản game","Gói Android không khớp"},
  {"E-NO-PACKAGE","Chưa có gói bản dịch Android","không có gói Android","gói bản dịch Android","Chưa có gói"},
  {"E-MANIFEST-INVALID","Bảng kê không dành cho Stella Sora Android","Gói Android thiếu","Gói Android cần kê khai","Gói có đường dẫn tệp trùng","Tệp thiếu kích thước","Tệp thiếu URL","Bundle thiếu","Bundle chưa xác nhận","Gói ZIP AssetBundles","Gói vượt giới hạn"},
  {"E-DATA-UNVERIFIED","Metadata Android chưa có SHA256"},
  {"E-DATA-SCHEMA","Bản phát hành chưa hợp lệ"},
  {"E-APK-NONE","Chưa có APK Local ADB mới hơn"},
  {"E-APK-SIGNATURE","Chữ ký APK","chữ ký khác ứng dụng"},
  {"E-APK-VERIFY","APK không khớp kích thước"},
  {"E-APK-INVALID","Kênh APK","Mã phiên bản APK","Phiên bản APK","Biến thể APK","Tệp APK không thuộc","không mới hơn bản đang cài","Không thể đọc thông tin tệp APK"},
  {"E-CONFIG-CHANNEL","Kho GitHub cần có dạng","Nhánh GitHub không hợp lệ"},
  {"E-BUSY","Hãy chờ thao tác","Đang có thao tác"},
  {"E-CANCELLED","Đã dừng tải tệp"},
  {"E-STORAGE","Không đủ bộ nhớ","Không đủ dung lượng","Bộ nhớ vùng game","No space left","ENOSPC"},
  {"E-STORAGE-ACCESS","Chưa truy cập được bộ nhớ ngoài","Không tạo được vùng","Không tạo được thư mục trạng thái","Vùng lưu vượt phạm vi","Không xoá được tệp cũ","Chưa chuyển được tệp tải"},
  {"E-DL-TIMEOUT","Tải quá thời hạn","Metadata quá lớn hoặc quá thời hạn"},
  {"E-TIMEOUT","Thao tác vượt thời hạn","quá thời hạn","vượt thời hạn"},
  {"E-DL-RESPONSE","Nguồn tải cần là HTTPS","Máy chủ không có đích chuyển hướng","chuyển hướng quá nhiều"},
  {"E-DL-VERIFY","Tệp tải về không khớp","Tệp tải về không đúng","Kích thước metadata không khớp","SHA256 metadata không khớp"},
  {"E-FILE-MISMATCH","Tệp bản dịch không khớp"},
  {"E-VERIFY-WRITE","Đọc lại sau cài không khớp","Đọc lại phục hồi không khớp","Tệp tạm không khớp","Không thể ghi tệp an toàn","Không thể phục hồi tệp","Không thể xoá tệp mới","Chưa cập nhật được biên bản"},
  {"E-FILE-CHANGED","Tệp đã thay đổi","Tệp đã đổi","Tệp game đổi","Tệp đổi","đổi ngoài thao tác","Tệp tạm đã tồn tại ngoài nhật ký"},
  {"E-VERIFY","Chưa đối chiếu được kích thước","SHA256","kích thước"},
  {"E-BACKUP","Backup","Không sao lưu được","Không đủ dung lượng để sao lưu"},
  {"E-JOURNAL","nhật ký","Nhật ký","vòng lặp biên bản","Mã nhật ký","biên bản cũ"},
  {"E-SECURITY","liên kết","vượt phạm vi","vượt vùng ứng dụng","không thuộc phạm vi","Đường dẫn","ký tự điều khiển","tệp zip vượt giới hạn"},
  {"E-UI-BLOCKED","Yêu cầu bị chặn","Tải bị chặn","không thuộc giao diện","Liên kết không hợp lệ"},
  {"E-ADB","ADB"},
  {"E-INTERNAL","nội bộ","không được hỗ trợ","Dữ liệu quá lớn"},
 };

 private static final Pattern HTTP = Pattern.compile("HTTP ([0-9]{3})");

 static Entry lookup(String code){
  if(code==null) return MAP.get("E-UNKNOWN");
  Entry e=MAP.get(code);
  if(e!=null) return e;
  Matcher m=Pattern.compile("E-HTTP-([0-9]{3})").matcher(code);
  if(m.matches()){
   int status=Integer.parseInt(m.group(1));
   Entry base=MAP.get(status==403||status==429?"E-HTTP-RATE":status==404?"E-HTTP-404":status>=500&&status<=599?"E-HTTP-5XX":"E-HTTP-4XX");
   return new Entry(code,base.title+" (HTTP "+status+")",base.summary,base.level,base.network,base.steps);
  }
  return MAP.get("E-UNKNOWN");
 }

 static boolean known(String code){return MAP.containsKey(code);}
 static java.util.Set<String> codes(){return MAP.keySet();}

 /** Code for a message string (Vietnamese app messages, HTTP statuses, OS errno text); {@code null} when nothing matches. */
 static String matchText(String text){
  if(text==null||text.isEmpty()) return null;
  Matcher http=HTTP.matcher(text);
  if(http.find()) return "E-HTTP-"+http.group(1);
  for(String[] rule:RULES) for(int i=1;i<rule.length;i++) if(text.contains(rule[i])) return rule[0];
  return null;
 }

 /** Never null: explicit code, then exception type, then message text, finally E-UNKNOWN. */
 static String classify(Throwable e){
  int depth=0;
  for(Throwable t=e;t!=null&&depth<8;t=t.getCause(),depth++) if(t instanceof Coded) return ((Coded)t).code();
  StringBuilder all=new StringBuilder();depth=0;
  for(Throwable t=e;t!=null&&depth<8;t=t.getCause(),depth++){
   String m=t.getMessage()==null?"":t.getMessage();
   String lower=m.toLowerCase(Locale.ROOT);
   all.append(m).append('\n');
   if(t instanceof UnknownHostException) return "E-NET-DNS";
   if(t instanceof SocketTimeoutException) return "E-NET-TIMEOUT";
   if(t instanceof CertificateException||t instanceof CertPathValidatorException) return "E-NET-TLS-CERT";
   if(t instanceof SSLException){
    boolean cert=lower.contains("certificate")||lower.contains("trust anchor")||lower.contains("certpath");
    Throwable c=t.getCause();
    return cert||c instanceof CertificateException||c instanceof CertPathValidatorException?"E-NET-TLS-CERT":"E-NET-TLS";
   }
   if(t instanceof NoRouteToHostException) return "E-NET-OFFLINE";
   if(t instanceof ConnectException) return lower.contains("enetunreach")||lower.contains("unreachable")||lower.contains("network is down")?"E-NET-OFFLINE":"E-NET-REFUSED";
   if(t instanceof SocketException){
    if(lower.contains("enetunreach")||lower.contains("unreachable")) return "E-NET-OFFLINE";
    return lower.contains("reset")||lower.contains("abort")||lower.contains("broken pipe")||lower.contains("econn")||lower.contains("eof")?"E-NET-RESET":"E-NET";
   }
   if("org.json.JSONException".equals(t.getClass().getName())) return "E-DATA-JSON";
  }
  String byText=matchText(all.toString());
  if(byText!=null) return byText;
  if(e==null) return "E-UNKNOWN";
  return e instanceof java.io.IOException?"E-UNKNOWN":"E-INTERNAL";
 }

 /** Overload for plain text with no exception (e.g. a message shown to the user). */
 static String classifyText(String text){
  String c=matchText(text);
  return c==null?"E-UNKNOWN":c;
 }
}
