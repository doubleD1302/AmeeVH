package com.stellasora.viethoa.localadb;

import java.io.IOException;
import java.net.ConnectException;
import java.net.SocketException;
import java.net.SocketTimeoutException;
import java.net.UnknownHostException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.security.cert.CertPathValidatorException;
import java.util.ArrayList;
import java.util.List;
import java.util.TreeMap;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Stream;
import javax.net.ssl.SSLHandshakeException;

/**
 * JVM check for ErrorCatalog (pure Java, no Android needed).
 * Run: javac -encoding UTF-8 -d out ErrorCatalog.java ErrorCatalogCheck.java && java -cp out com.stellasora.viethoa.localadb.ErrorCatalogCheck <java-sources-dir>
 */
public final class ErrorCatalogCheck {
 private static int failures = 0, checks = 0;

 private static void eq(Object expected, Object actual, String what) {
  checks++;
  if (!expected.equals(actual)) { failures++; System.out.println("FAIL " + what + ": expected " + expected + " but was " + actual); }
 }
 private static void ok(boolean cond, String what) {
  checks++;
  if (!cond) { failures++; System.out.println("FAIL " + what); }
 }

 private static final class Coded extends IOException implements ErrorCatalog.Coded {
  final String c; Coded(String c) { super("x"); this.c = c; }
  @Override public String code() { return c; }
 }

 public static void main(String[] args) throws Exception {
  // ---- catalog completeness
  for (String code : ErrorCatalog.codes()) {
   ErrorCatalog.Entry e = ErrorCatalog.lookup(code);
   ok(code.startsWith("E-"), code + " must start with E-");
   ok(!e.title.trim().isEmpty() && !e.summary.trim().isEmpty(), code + " needs a title and a summary");
   if (e.isError()) ok(e.steps.length >= 1, code + " (error) needs at least one step");
   for (String s : e.steps) ok(!s.trim().isEmpty(), code + " has an empty step");
  }
  eq("E-UNKNOWN", ErrorCatalog.lookup("E-NOPE").code, "unknown code falls back");
  eq("E-HTTP-429", ErrorCatalog.lookup("E-HTTP-429").code, "http code kept");
  ok(ErrorCatalog.lookup("E-HTTP-429").title.contains("giới hạn"), "429 explains rate limiting");
  ok(ErrorCatalog.lookup("E-HTTP-503").title.contains("sự cố"), "5xx explains GitHub outage");
  ok(ErrorCatalog.lookup("E-HTTP-418").title.contains("từ chối"), "other 4xx");

  // ---- exceptions
  eq("E-NET-DNS", ErrorCatalog.classify(new UnknownHostException("Unable to resolve host \"api.github.com\": No address associated with hostname")), "dns");
  eq("E-NET-TIMEOUT", ErrorCatalog.classify(new SocketTimeoutException("failed to connect to api.github.com after 12000ms")), "timeout");
  eq("E-NET-REFUSED", ErrorCatalog.classify(new ConnectException("Failed to connect to /1.2.3.4:443: ECONNREFUSED (Connection refused)")), "refused");
  eq("E-NET-OFFLINE", ErrorCatalog.classify(new ConnectException("connect failed: ENETUNREACH (Network is unreachable)")), "unreachable");
  eq("E-NET-RESET", ErrorCatalog.classify(new SocketException("Connection reset")), "reset");
  eq("E-NET-RESET", ErrorCatalog.classify(new SocketException("Software caused connection abort")), "abort");
  eq("E-NET-TLS-CERT", ErrorCatalog.classify(new SSLHandshakeException("Trust anchor for certification path not found.")), "cert");
  eq("E-NET-TLS-CERT", ErrorCatalog.classify(new IOException("wrapped", new CertPathValidatorException("path"))), "cert chain");
  eq("E-NET-TLS", ErrorCatalog.classify(new SSLHandshakeException("Handshake failed")), "tls");
  eq("E-STORAGE", ErrorCatalog.classify(new IOException("write failed: ENOSPC (No space left on device)")), "enospc");
  eq("E-DATA-JSON", ErrorCatalog.classify(new RuntimeException("x", new org.json.JSONException("Value <html> of type java.lang.String cannot be converted to JSONObject"))), "json");
  eq("E-DL-VERIFY", ErrorCatalog.classify(new Coded("E-DL-VERIFY")), "explicit code wins");
  eq("E-NET-DNS", ErrorCatalog.classify(new IOException("outer", new UnknownHostException("h"))), "cause chain");
  eq("E-HTTP-404", ErrorCatalog.classify(new IOException("Máy chủ trả HTTP 404 (raw.githubusercontent.com).")), "http status in text");
  eq("E-INTERNAL", ErrorCatalog.classify(new IllegalStateException("boom")), "non-IO bug is internal");
  eq("E-UNKNOWN", ErrorCatalog.classify(new IOException("???")), "unmatched IO");

  // ---- the exact messages users have been seeing
  TreeMap<String, String> samples = new TreeMap<>();
  samples.put("Hãy bật Tuỳ chọn nhà phát triển trước khi kết nối Local ADB.", "E-DEVOPT");
  samples.put("Chưa kết nối Local ADB.", "E-ADB-NOT-CONNECTED");
  samples.put("Hãy kết nối và xác minh Local ADB trước.", "E-ADB-NOT-CONNECTED");
  samples.put("ADB quá thời hạn, kết nối đã đóng.", "E-ADB-TIMEOUT");
  samples.put("Chưa tìm thấy ứng dụng Stella Sora Android.", "E-NO-GAME");
  samples.put("Hãy thoát Stella Sora trước khi thay đổi tài nguyên.", "E-GAME-RUNNING");
  samples.put("Game đã cập nhật hoặc chưa đọc được phiên bản. Không ghi đè tài nguyên.", "E-VER-CHANGED");
  samples.put("Gói Android không khớp phiên bản game hoặc tài nguyên đã đọc. Không cài đặt.", "E-PKG-MISMATCH");
  samples.put("Chưa có gói bản dịch Android tương thích trên GitHub. Gói Windows và APK overlay cũ không được dùng cho ứng dụng này.", "E-NO-PACKAGE");
  samples.put("Không đủ bộ nhớ để tải và kiểm tra gói Android.", "E-STORAGE");
  samples.put("Không đủ dung lượng để sao lưu và thay tệp an toàn.", "E-STORAGE");
  samples.put("Bộ nhớ vùng game không đủ hoặc chưa xác định được.", "E-STORAGE");
  samples.put("Tệp đã thay đổi trước khi ghi: Persistent_Store/Tables/data.arcx", "E-FILE-CHANGED");
  samples.put("Tệp game đổi trước khi sao lưu: x", "E-FILE-CHANGED");
  samples.put("Đọc lại sau cài không khớp: x", "E-VERIFY-WRITE");
  samples.put("Backup không khớp tệp gốc: x", "E-BACKUP");
  samples.put("Có nhật ký chưa hoàn tất. Hãy chọn Phục hồi thao tác trước.", "E-RECOVERY-REQUIRED");
  samples.put("Chưa có biên bản của lần cài bằng ứng dụng này.", "E-NO-RECEIPT");
  samples.put("Tệp bản dịch không khớp: x", "E-FILE-MISMATCH");
  samples.put("Tệp tải về không khớp kích thước hoặc SHA256: x", "E-DL-VERIFY");
  samples.put("Thao tác vượt thời hạn", "E-TIMEOUT");
  samples.put("Tải quá thời hạn.", "E-DL-TIMEOUT");
  samples.put("Máy chủ trả HTTP 503 (github.com).", "E-HTTP-503");
  samples.put("Chữ ký APK khác ứng dụng đang dùng.", "E-APK-SIGNATURE");
  samples.put("Chưa có APK Local ADB mới hơn ứng dụng đang dùng.", "E-APK-NONE");
  samples.put("Kho GitHub cần có dạng tài-khoản/tên-kho.", "E-CONFIG-CHANNEL");
  samples.put("Yêu cầu bị chặn", "E-UI-BLOCKED");
  for (var e : samples.entrySet()) eq(e.getValue(), ErrorCatalog.classifyText(e.getKey()), "message: " + e.getKey());
  for (var e : samples.entrySet()) ok(ErrorCatalog.known(e.getValue()) || e.getValue().startsWith("E-HTTP-"), "sample code exists: " + e.getValue());

  // ---- every user-visible message in the sources must map to a specific code
  if (args.length > 0) {
   Pattern p = Pattern.compile("new (?:IOException|IllegalStateException|SecurityException|IllegalArgumentException)\\(\\s*\"((?:[^\"\\\\]|\\\\.)*)\"");
   List<String> unknown = new ArrayList<>();
   int total = 0;
   try (Stream<Path> files = Files.list(Paths.get(args[0]))) {
    for (Path f : (Iterable<Path>) files.filter(x -> x.toString().endsWith(".java"))::iterator) {
     Matcher m = p.matcher(new String(Files.readAllBytes(f), StandardCharsets.UTF_8));
     while (m.find()) {
      String msg = m.group(1).replace("\\\"", "\"");
      if (msg.isEmpty() || msg.indexOf(' ') < 0) continue;   // "x" placeholders / non-user text
      if (msg.endsWith("HTTP ")) msg += "404";                 // literal is followed by a concatenated status code
      total++;
      if (ErrorCatalog.classifyText(msg).equals("E-UNKNOWN")) unknown.add(f.getFileName() + ": " + msg);
     }
    }
   }
   System.out.println("scanned " + total + " message literals; unmapped: " + unknown.size());
   for (String u : unknown) System.out.println("  UNMAPPED " + u);
   ok(unknown.isEmpty(), "all source messages map to a specific code");
  }

  System.out.println(checks + " checks, " + failures + " failures");
  System.exit(failures == 0 ? 0 : 1);
 }
}
