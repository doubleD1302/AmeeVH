package com.stellasora.viethoa.localadb;
import android.Manifest;
import android.app.ActivityManager;
import android.content.Context;
import android.content.pm.PackageManager;
import android.net.ConnectivityManager;
import android.net.LinkProperties;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.os.Build;
import android.os.Looper;
import android.os.PowerManager;
import android.os.StatFs;
import android.os.SystemClock;
import android.provider.Settings;
import org.json.*;
import java.io.File;
import java.net.*;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Builds PC-parity, plain-language, PII-redacted error reports & live diagnostics for every error dialog.
 * Privacy: never includes ADB host/ports, pairing codes, device identifiers, bindings or URL query strings.
 */
final class ErrorReport {
 private static volatile String lastId = "", lastText = "";
 private static volatile JSONObject lastReport = null;

 private static final Pattern HTTP_STATUS_RE = Pattern.compile("HTTP\\s+(\\d{3})");
 private static final Pattern ADB_EXIT_RE = Pattern.compile("ADB dừng \\((\\d+)\\)");
 private static final Pattern ERRNO_RE = Pattern.compile("\\b(ENOSPC|EACCES|ECONNREFUSED|ECONNRESET|ETIMEDOUT|ENETUNREACH|EHOSTUNREACH|EPIPE|EROFS)\\b");
 private static final Pattern LOCAL_ENDPOINT_RE = Pattern.compile(
   "(?:127\\.0\\.0\\.1|localhost|10\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}|192\\.168\\.\\d{1,3}\\.\\d{1,3}|172\\.(?:1[6-9]|2\\d|3[01])\\.\\d{1,3}\\.\\d{1,3}|\\[::1\\]):\\d{2,5}"
 );
 private static final Pattern URL_AUTH_RE = Pattern.compile("(https?://)[^\\s/@]+@");
 private static final Pattern URL_QUERY_RE = Pattern.compile("(https?://[^\\s?#]+)[?#][^\\s\"'<>)]*");

 private ErrorReport() {}

 static String redact(String raw) {
  if (raw == null || raw.isEmpty()) return "";
  String s = URL_AUTH_RE.matcher(raw).replaceAll("$1");
  s = URL_QUERY_RE.matcher(s).replaceAll("$1");
  s = LOCAL_ENDPOINT_RE.matcher(s).replaceAll("<local-adb>");
  return s;
 }

 static String safeUrl(String address) {
  try {
   URL u = new URL(address);
   return u.getProtocol() + "://" + u.getHost() + u.getPath();
  } catch (Exception e) {
   return "(url không hợp lệ)";
  }
 }

 static String classify(Throwable e) { return ErrorCatalog.classify(e); }
 static String classify(Throwable e, String action) { return ErrorCatalog.classify(e, action); }
 static String classifyText(String text) { return ErrorCatalog.classifyText(text); }

 /** OEM family key for tailored Vietnamese guides & diagnostics (never PII). */
 static String oemFamily() {
  String m = (Build.MANUFACTURER + " " + Build.BRAND).toLowerCase(Locale.ROOT);
  if (m.contains("xiaomi") || m.contains("redmi") || m.contains("poco")) return "xiaomi";
  if (m.contains("samsung")) return "samsung";
  if (m.contains("oppo") || m.contains("realme") || m.contains("oneplus")) return "oppo";
  if (m.contains("vivo") || m.contains("iqoo")) return "vivo";
  if (m.contains("huawei") || m.contains("honor")) return "huawei";
  if (m.contains("google")) return "google";
  if (m.contains("sony")) return "sony";
  if (m.contains("asus") || m.contains("rog")) return "asus";
  if (m.contains("motorola") || m.contains("lenovo")) return "lenovo";
  if (m.contains("tecno") || m.contains("infinix") || m.contains("itel")) return "transsion";
  return "generic";
 }

 /** Developer-only notes appended to the report (the user-facing explanation comes from ErrorCatalog). */
 private static String hint(String code) {
  switch (code) {
   case "E-DL-VERIFY": return "Tệp tải về khác kích thước/SHA256 so với bảng kê (manifest). So sánh contentLength/receivedBytes với expectedSize.";
   case "E-DL-OVERSIZE": return "Tệp trên máy chủ lớn hơn kích thước công bố. Kiểm tra contentLength và URL trong manifest.";
   case "E-DL-RANGE": return "Máy chủ trả dải byte nối tiếp không khớp yêu cầu.";
   case "E-HTTP-403": case "E-HTTP-429": return "GitHub giới hạn lượt gọi API theo IP mạng (thường gặp trên 4G CGNAT hoặc Wi-Fi chung).";
   case "E-PKG-MISMATCH": return "Gói trên GitHub không khai báo phiên bản game/tài nguyên đang cài trên máy. So sánh payload.* với game.*.";
   case "E-FILE-CHANGED": return "Tệp game bị thay đổi ngoài thao tác của launcher (game vừa tự cập nhật?).";
   case "E-ADB-PERM": return "OEM ROM chặn quyền shell/Android/data (ColorOS Disable permission monitoring / MIUI USB debugging Security settings).";
   case "E-ADB-CONN-REFUSED": return "Wireless Debugging đang tắt hoặc cổng kết nối đã thay đổi sau khi tắt/mở lại.";
   case "E-NET-CAPTIVE": return "Wi-Fi công cộng hoặc router chèn trang HTML đăng nhập/cảnh báo.";
   default: return "";
  }
 }

 private static JSONObject pick(JSONObject from, String... keys) {
  JSONObject out = new JSONObject();
  if (from == null) return out;
  try {
   for (String k : keys) if (from.has(k)) out.put(k, from.get(k));
  } catch (JSONException ignored) {}
  return out;
 }

 private static JSONArray chain(Throwable e) {
  JSONArray list = new JSONArray();
  int depth = 0;
  for (Throwable t = e; t != null && depth < 6; t = t.getCause(), depth++) {
   try {
    JSONObject item = new JSONObject();
    item.put("class", t.getClass().getName());
    String m = t.getMessage();
    if (m != null) {
     String clean = redact(m);
     item.put("message", clean.length() > 600 ? clean.substring(0, 600) + "…" : clean);
    }
    if (t instanceof StellaException) {
     item.put("code", ((StellaException) t).code);
     item.put("details", ((StellaException) t).details);
    }
    JSONArray frames = new JSONArray();
    StackTraceElement[] st = t.getStackTrace();
    for (StackTraceElement f : st) {
     if (frames.length() >= 8) break;
     if (f.getClassName().startsWith("com.stellasora")) {
      frames.put(f.getClassName().replace("com.stellasora.viethoa.localadb.", "") + "." + f.getMethodName() + ":" + f.getLineNumber());
     }
    }
    if (frames.length() == 0) {
     for (StackTraceElement f : st) {
      if (frames.length() >= 5) break;
      frames.put(f.getClassName() + "." + f.getMethodName() + ":" + f.getLineNumber());
     }
    }
    item.put("stack", frames);
    list.put(item);
   } catch (JSONException ignored) {}
  }
  return list;
 }

 private static long free(File f) {
  try { return f == null ? -1 : new StatFs(f.getAbsolutePath()).getAvailableBytes(); }
  catch (Exception e) { return -1; }
 }

 private static String fmtGb(long bytes) {
  if (bytes < 0) return "không đọc được";
  return String.format(Locale.ROOT, "%.1f GB", bytes / (1024.0 * 1024.0 * 1024.0));
 }

 // ------------------------------------------------------------------ network & device diagnosis
 static boolean isWifiConnected(Context c) {
  try {
   ConnectivityManager cm = (ConnectivityManager) c.getSystemService(Context.CONNECTIVITY_SERVICE);
   if (cm == null) return false;
   Network[] nets = cm.getAllNetworks();
   for (Network n : nets) {
    NetworkCapabilities nc = cm.getNetworkCapabilities(n);
    if (nc != null && nc.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)) return true;
   }
   Network active = cm.getActiveNetwork();
   if (active != null) {
    NetworkCapabilities nc = cm.getNetworkCapabilities(active);
    return nc != null && nc.hasTransport(NetworkCapabilities.TRANSPORT_WIFI);
   }
  } catch (Throwable ignored) {}
  return false;
 }

 /** How the phone is connected (type, validated, captive portal, private DNS). No addresses or identifiers. */
 static JSONObject networkInfo(Context c) {
  JSONObject o = new JSONObject();
  try {
   o.put("airplane", Settings.Global.getInt(c.getContentResolver(), Settings.Global.AIRPLANE_MODE_ON, 0) == 1);
   ConnectivityManager cm = (ConnectivityManager) c.getSystemService(Context.CONNECTIVITY_SERVICE);
   Network n = cm == null ? null : cm.getActiveNetwork();
   if (n == null) { o.put("active", false); return o; }
   o.put("active", true);
   NetworkCapabilities nc = cm.getNetworkCapabilities(n);
   if (nc != null) {
    JSONArray transports = new JSONArray();
    if (nc.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)) transports.put("wifi");
    if (nc.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR)) transports.put("cellular");
    if (nc.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET)) transports.put("ethernet");
    if (nc.hasTransport(NetworkCapabilities.TRANSPORT_VPN)) transports.put("vpn");
    o.put("transports", transports);
    o.put("internet", nc.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET));
    o.put("validated", nc.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED));
    o.put("captivePortal", nc.hasCapability(NetworkCapabilities.NET_CAPABILITY_CAPTIVE_PORTAL));
    o.put("metered", !nc.hasCapability(NetworkCapabilities.NET_CAPABILITY_NOT_METERED));
   }
   LinkProperties lp = cm.getLinkProperties(n);
   if (lp != null) {
    o.put("privateDns", lp.isPrivateDnsActive());
    String name = lp.getPrivateDnsServerName();
    if (name != null && !name.isEmpty()) o.put("privateDnsHost", name);
   }
   o.put("dataSaver", cm.getRestrictBackgroundStatus() == ConnectivityManager.RESTRICT_BACKGROUND_STATUS_ENABLED);
  } catch (Throwable t) {
   try { o.put("error", t.getClass().getSimpleName()); } catch (JSONException ignored) {}
  }
  return o;
 }

 static JSONObject deviceHealth(Context c) {
  JSONObject o = new JSONObject();
  try {
   o.put("release", Build.VERSION.RELEASE);
   o.put("sdk", Build.VERSION.SDK_INT);
   o.put("securityPatch", Build.VERSION.SECURITY_PATCH == null ? "" : Build.VERSION.SECURITY_PATCH);
   o.put("manufacturer", Build.MANUFACTURER);
   o.put("brand", Build.BRAND);
   o.put("model", Build.MODEL);
   o.put("oemFamily", oemFamily());
   o.put("abis", Build.SUPPORTED_ABIS != null && Build.SUPPORTED_ABIS.length > 0 ? Build.SUPPORTED_ABIS[0] : "?");
   o.put("locale", Locale.getDefault().toLanguageTag());
   o.put("timezone", TimeZone.getDefault().getID());
   o.put("devOptions", LauncherService.isDevOptions(c));
   boolean notifOk = Build.VERSION.SDK_INT < 33 || c.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED;
   o.put("notifPermission", notifOk);
   try { o.put("canInstallApk", c.getPackageManager().canRequestPackageInstalls()); } catch (Exception ignored) {}
   try {
    PowerManager pm = (PowerManager) c.getSystemService(Context.POWER_SERVICE);
    o.put("ignoringBatteryOpt", pm != null && pm.isIgnoringBatteryOptimizations(c.getPackageName()));
   } catch (Exception ignored) {}
   try {
    ActivityManager am = (ActivityManager) c.getSystemService(Context.ACTIVITY_SERVICE);
    if (am != null) {
     ActivityManager.MemoryInfo mi = new ActivityManager.MemoryInfo();
     am.getMemoryInfo(mi);
     o.put("ramAvailMb", mi.availMem / (1024L * 1024L));
     o.put("ramTotalMb", mi.totalMem / (1024L * 1024L));
     o.put("lowRam", mi.lowMemory);
    }
   } catch (Exception ignored) {}
  } catch (Throwable ignored) {}
  return o;
 }

 private static final class HostResult { volatile String dns = "pending", ip = "", tcp = "pending", detail = ""; volatile long ms = -1; }

 private static String reason(Throwable t) {
  String m = t.getMessage();
  String clean = m == null ? "" : redact(m);
  return t.getClass().getSimpleName() + (clean.isEmpty() ? "" : " (" + (clean.length() > 80 ? clean.substring(0, 80) : clean) + ")");
 }

 /** DNS + TCP:443 for GitHub's hosts + neutral control + Android Captive Portal status, bounded to ~8 s. Never call on main thread. */
 static JSONObject probe(Context c) {
  JSONObject net = c == null ? null : networkInfo(c);
  final String[] hosts = {"api.github.com", "raw.githubusercontent.com", "github.com"};
  final long start = SystemClock.elapsedRealtime(), end = start + 8000;
  final Map<String, HostResult> results = new LinkedHashMap<>();
  final List<Thread> threads = new ArrayList<>();
  for (final String host : hosts) {
   final HostResult r = new HostResult();
   results.put(host, r);
   Thread th = new Thread(() -> {
    try { r.ip = InetAddress.getByName(host).getHostAddress(); r.dns = "ok"; }
    catch (Throwable t) { r.dns = "fail"; r.tcp = "skip"; r.detail = reason(t); return; }
    long t1 = SystemClock.elapsedRealtime();
    try (Socket s = new Socket()) {
     s.connect(new InetSocketAddress(r.ip, 443), 3500);
     r.tcp = "ok";
     r.ms = SystemClock.elapsedRealtime() - t1;
    } catch (Throwable t) {
     r.tcp = "fail";
     r.detail = reason(t);
     r.ms = SystemClock.elapsedRealtime() - t1;
    }
   }, "probe-" + host);
   th.setDaemon(true);
   th.start();
   threads.add(th);
  }
  final String[] control = {"pending", "pending"}; // [dns, tcp]
  Thread cd = new Thread(() -> { try { InetAddress.getByName("www.microsoft.com"); control[0] = "ok"; } catch (Throwable t) { control[0] = "fail"; } }, "probe-ctl-dns");
  Thread ct = new Thread(() -> { try (Socket s = new Socket()) { s.connect(new InetSocketAddress("1.1.1.1", 443), 3500); control[1] = "ok"; } catch (Throwable t) { control[1] = "fail"; } }, "probe-ctl-tcp");
  cd.setDaemon(true); ct.setDaemon(true); cd.start(); ct.start();
  threads.add(cd); threads.add(ct);
  for (Thread th : threads) {
   long left = end - SystemClock.elapsedRealtime();
   if (left > 0) {
    try { th.join(left); } catch (InterruptedException ie) { Thread.currentThread().interrupt(); break; }
   }
  }
  JSONObject out = new JSONObject();
  try {
   JSONObject hostJson = new JSONObject();
   boolean allOk = true, dnsFail = false;
   StringBuilder failed = new StringBuilder();
   for (Map.Entry<String, HostResult> e : results.entrySet()) {
    HostResult r = e.getValue();
    if ("pending".equals(r.dns)) { r.dns = "fail"; r.tcp = "skip"; r.detail = "không trả lời kịp (quá thời gian chờ DNS)"; }
    else if ("pending".equals(r.tcp)) { r.tcp = "fail"; r.detail = "không kết nối kịp (quá thời gian chờ)"; }
    hostJson.put(e.getKey(), Store.obj("dns", r.dns, "ip", r.ip, "tcp", r.tcp, "ms", r.ms, "detail", r.detail));
    if (!"ok".equals(r.tcp)) {
     allOk = false;
     if (failed.length() > 0) failed.append(", ");
     failed.append(e.getKey());
    }
    if (!"ok".equals(r.dns)) dnsFail = true;
   }
   if ("pending".equals(control[0])) control[0] = "fail";
   if ("pending".equals(control[1])) control[1] = "fail";
   boolean cDns = "ok".equals(control[0]), cTcp = "ok".equals(control[1]);
   boolean captive = net != null && net.optBoolean("captivePortal");
   boolean airplane = net != null && net.optBoolean("airplane");
   boolean noActive = net != null && net.has("active") && !net.optBoolean("active");
   String verdict, text;
   if (airplane) {
    verdict = "offline";
    text = "Đang bật chế độ máy bay. Hãy tắt chế độ máy bay rồi thử lại.";
   } else if (noActive) {
    verdict = "offline";
    text = "Điện thoại chưa kết nối Wi-Fi hoặc dữ liệu di động.";
   } else if (captive) {
    verdict = "captive_portal";
    text = "Wi-Fi hiện tại đang yêu cầu đăng nhập (Captive Portal). Hãy mở trình duyệt đăng nhập Wi-Fi rồi thử lại.";
   } else if (allOk) {
    verdict = "ok";
    text = "Lúc kiểm tra, điện thoại kết nối tới GitHub bình thường. Lỗi có thể chỉ thoáng qua; hãy thử lại.";
   } else if (!cDns && !cTcp) {
    verdict = "offline";
    text = "Điện thoại đang mất Internet hoàn toàn (ngay cả điểm kiểm tra chung cũng không nối được). Hãy kiểm tra Wi-Fi/4G.";
   } else if (dnsFail && cDns) {
    verdict = "dns_blocked";
    text = "Internet vẫn hoạt động nhưng không tra được địa chỉ (" + failed + "). GitHub bị chặn ở DNS của mạng/VPN; thử đổi DNS riêng tư (dns.google) hoặc đổi mạng.";
   } else if (dnsFail) {
    verdict = "dns_broken";
    text = "Điện thoại ra được Internet qua IP trực tiếp nhưng DNS đang hỏng. Hãy đổi mạng hoặc đổi DNS riêng tư sang Tự động / dns.google.";
   } else {
    verdict = "blocked";
    text = "Internet vẫn hoạt động nhưng kết nối cổng 443 tới GitHub (" + failed + ") bị chặn hoặc quá chậm. Kiểm tra VPN/tường lửa hoặc đổi mạng.";
   }
   out.put("hosts", hostJson);
   out.put("control", Store.obj("dns", control[0], "tcp1111", control[1]));
   out.put("captivePortal", captive);
   if (net != null) {
    out.put("privateDns", net.optBoolean("privateDns"));
    if (!net.optString("privateDnsHost").isEmpty()) out.put("privateDnsHost", net.optString("privateDnsHost"));
   }
   out.put("verdict", verdict);
   out.put("verdictText", text);
   out.put("durationMs", SystemClock.elapsedRealtime() - start);
  } catch (JSONException ignored) {}
  return out;
 }

 static JSONObject probe() { return probe(null); }

 static List<String> formatProbe(JSONObject probe) {
  List<String> lines = new ArrayList<>();
  if (probe == null) return lines;
  JSONObject hosts = probe.optJSONObject("hosts");
  if (hosts != null) {
   Iterator<String> it = hosts.keys();
   while (it.hasNext()) {
    String h = it.next();
    JSONObject v = hosts.optJSONObject(h);
    if (v == null) continue;
    String dns = "ok".equals(v.optString("dns")) ? "DNS ok " + v.optString("ip") : "DNS LỖI";
    String tcpState = v.optString("tcp");
    String tcp;
    if ("ok".equals(tcpState)) {
     long ms = v.optLong("ms", -1);
     tcp = ms >= 0 ? "TCP:443 ok (" + ms + " ms)" : "TCP:443 ok";
    } else if ("skip".equals(tcpState)) {
     tcp = "TCP:443 bỏ qua";
    } else {
     tcp = "TCP:443 LỖI";
    }
    String detail = v.optString("detail");
    lines.add("  " + h + ": " + dns + "; " + tcp + (detail.isEmpty() ? "" : " — " + detail));
   }
  }
  JSONObject ctl = probe.optJSONObject("control");
  if (ctl != null) {
   lines.add("  Điểm đối chứng: DNS " + ctl.optString("dns", "?") + "; TCP 1.1.1.1:443 " + ctl.optString("tcp1111", "?"));
  }
  if (probe.has("captivePortal")) {
   lines.add("  Captive Portal: " + (probe.optBoolean("captivePortal") ? "PHÁT HIỆN (cần đăng nhập Wi-Fi)" : "Không phát hiện"));
  }
  if (probe.optBoolean("privateDns")) {
   String host = probe.optString("privateDnsHost");
   lines.add("  DNS riêng tư (Private DNS): Đang bật" + (host.isEmpty() ? "" : " (" + host + ")"));
  }
  lines.add("  Kết luận tự động (" + probe.optString("verdict", "?") + "): " + probe.optString("verdictText", ""));
  return lines;
 }

 private static String networkVerdict(JSONObject net, JSONObject probe) {
  if (net != null && net.optBoolean("airplane")) return "Đang bật chế độ máy bay. Hãy tắt chế độ máy bay rồi thử lại.";
  if (net != null && net.has("active") && !net.optBoolean("active")) return "Điện thoại chưa kết nối mạng nào (tắt Wi-Fi/dữ liệu di động hoặc mất sóng).";
  if (net != null && net.optBoolean("captivePortal")) return "Wi-Fi đang yêu cầu đăng nhập (Captive Portal). Hãy mở trình duyệt để đăng nhập Wi-Fi.";
  if (net != null && net.has("validated") && !net.optBoolean("validated")) return "Đã nối mạng nhưng Android báo mạng chưa ra được Internet. Hãy kiểm tra Wi-Fi/4G hoặc đổi mạng.";
  return probe == null ? "" : probe.optString("verdictText");
 }

 // ------------------------------------------------------------------ metadata extraction & context grid (PC-parity)
 private static JSONObject extractSignals(Throwable e, String message) {
  JSONObject sig = new JSONObject();
  try {
   StringBuilder combined = new StringBuilder();
   if (message != null) combined.append(message).append('\n');
   int depth = 0;
   for (Throwable t = e; t != null && depth < 6; t = t.getCause(), depth++) {
    if (t.getMessage() != null) combined.append(t.getMessage()).append('\n');
    if (t instanceof StellaException) {
     JSONObject d = ((StellaException) t).details;
     if (d.has("httpStatus") && !sig.has("httpStatus")) sig.put("httpStatus", d.optInt("httpStatus"));
     if (d.has("exitCode") && !sig.has("adbExit")) sig.put("adbExit", d.optInt("exitCode"));
     if (d.has("url") && !sig.has("targetUrl")) sig.put("targetUrl", safeUrl(d.optString("url")));
     if (d.has("file") && !sig.has("targetFile")) sig.put("targetFile", redact(d.optString("file")));
     if (d.has("brokerErrorClass") && !sig.has("sysClass")) sig.put("sysClass", d.optString("brokerErrorClass"));
    }
    if (!sig.has("sysClass")) sig.put("sysClass", t.getClass().getSimpleName());
   }
   String all = combined.toString();
   if (!sig.has("httpStatus")) {
    Matcher mh = HTTP_STATUS_RE.matcher(all);
    if (mh.find()) sig.put("httpStatus", Integer.parseInt(mh.group(1)));
   }
   if (!sig.has("adbExit")) {
    Matcher ma = ADB_EXIT_RE.matcher(all);
    if (ma.find()) sig.put("adbExit", Integer.parseInt(ma.group(1)));
   }
   Matcher me = ERRNO_RE.matcher(all);
   if (me.find()) sig.put("errno", me.group(1));
  } catch (Exception ignored) {}
  return sig;
 }

 private static JSONObject row(String label, String value, String tone) {
  return Store.obj("label", label, "value", value, "tone", tone);
 }

 static JSONArray buildContextRows(JSONObject r) {
  JSONArray rows = new JSONArray();
  try {
   String action = r.optString("action");
   rows.put(row("Thao tác", ErrorCatalog.actionLabel(action), "neutral"));

   JSONObject sig = r.optJSONObject("signals");
   List<String> sysParts = new ArrayList<>();
   if (sig != null) {
    if (sig.has("httpStatus")) sysParts.add("HTTP " + sig.optInt("httpStatus"));
    if (sig.has("adbExit")) sysParts.add("ADB exit " + sig.optInt("adbExit"));
    if (!sig.optString("errno").isEmpty()) sysParts.add(sig.optString("errno"));
    if (sysParts.isEmpty() && !sig.optString("sysClass").isEmpty()) sysParts.add(sig.optString("sysClass"));
   }
   if (!sysParts.isEmpty()) rows.put(row("Mã hệ thống", joinStrings(sysParts, " · "), "danger"));
   else rows.put(row("Mã hệ thống", "Không có mã hệ thống", "neutral"));

   // Network / DNS cell (matches PC SmartErrorDialog live updateable row)
   String netVal = "Chưa đo (bấm Kiểm tra kết nối)", netTone = "neutral";
   JSONObject probe = r.optJSONObject("probe");
   JSONObject net = r.optJSONObject("network");
   if (probe != null && !probe.optString("verdict").isEmpty()) {
    String v = probe.optString("verdict");
    if ("ok".equals(v)) { netVal = "GitHub: Kết nối tốt"; netTone = "ok"; }
    else if ("offline".equals(v)) { netVal = "Mất Internet hoàn toàn"; netTone = "danger"; }
    else if ("captive_portal".equals(v)) { netVal = "Captive Portal (cần đăng nhập Wi-Fi)"; netTone = "danger"; }
    else if ("dns_blocked".equals(v)) { netVal = "Lỗi DNS GitHub · 1.1.1.1 OK"; netTone = "warn"; }
    else if ("dns_broken".equals(v)) { netVal = "DNS hỏng · IP trực tiếp OK"; netTone = "warn"; }
    else if ("blocked".equals(v)) { netVal = "Kết nối tới GitHub bị chặn"; netTone = "danger"; }
    else { netVal = v; netTone = "warn"; }
   } else if (net != null) {
    if (net.optBoolean("airplane")) { netVal = "Đang bật Chế độ máy bay"; netTone = "danger"; }
    else if (net.has("active") && !net.optBoolean("active")) { netVal = "Không có kết nối mạng"; netTone = "danger"; }
    else if (net.optBoolean("captivePortal")) { netVal = "Wi-Fi cần đăng nhập (Captive Portal)"; netTone = "danger"; }
    else {
     JSONArray tr = net.optJSONArray("transports");
     String tLabel = formatTransports(tr);
     boolean privDns = net.optBoolean("privateDns");
     boolean val = !net.has("validated") || net.optBoolean("validated");
     netVal = tLabel + (val ? "" : " (chưa ra mạng)") + (privDns ? " · DNS riêng tư" : "");
     netTone = !val ? "danger" : (privDns ? "warn" : "ok");
    }
   }
   rows.put(row("Mạng / DNS", netVal, netTone));

   // Local ADB status
   JSONObject adb = r.optJSONObject("adb");
   boolean adbConn = adb != null && adb.optBoolean("connected");
   boolean adbId = adb != null && adb.optBoolean("hasIdentity");
   String adbVal = adbConn ? "Đã kết nối" : (adbId ? "Đã ghép đôi (chưa nối)" : "Chưa ghép đôi");
   rows.put(row("Local ADB", adbVal, adbConn ? "ok" : "warn"));

   // Storage & RAM
   JSONObject st = r.optJSONObject("storage");
   long intFree = st == null ? -1 : st.optLong("internalFreeBytes", -1);
   long extFree = st == null ? -1 : st.optLong("externalFreeBytes", -1);
   long bestFree = extFree >= 0 ? extFree : intFree;
   String diskVal = bestFree >= 0 ? ("Trống " + fmtGb(bestFree)) : "Không đọc được";
   JSONObject dev = r.optJSONObject("android");
   if (dev != null && dev.optLong("ramTotalMb", 0) > 0) {
    diskVal += String.format(Locale.ROOT, " · RAM %d/%d MB", dev.optLong("ramAvailMb"), dev.optLong("ramTotalMb"));
   }
   String diskTone = (bestFree >= 0 && bestFree < 1610612736L) ? "warn" : (bestFree >= 0 ? "ok" : "neutral");
   rows.put(row("Bộ nhớ / RAM", diskVal, diskTone));

   // Game status
   JSONObject game = r.optJSONObject("game");
   String gameVal = "Chưa tìm thấy", gameTone = "warn";
   if (game != null && game.optBoolean("installed")) {
    if (game.optBoolean("versionsKnown")) {
     gameVal = "v" + game.optString("gameVersion") + " · res " + game.optString("resourceVersion");
     gameTone = "ok";
    } else {
     gameVal = "Đã cài (chưa đọc phiên bản)";
     gameTone = "warn";
    }
   }
   rows.put(row("Game", gameVal, gameTone));

   // Device
   if (dev != null) {
    String devStr = dev.optString("manufacturer", "") + " " + dev.optString("model", "") + " · Android " + dev.optString("release", "?") + " (SDK " + dev.optInt("sdk", 0) + ")";
    rows.put(row("Thiết bị", devStr.trim(), "neutral"));
   }

   // Target file / URL if present
   if (sig != null && !sig.optString("targetFile").isEmpty()) {
    rows.put(row("Tệp mục tiêu", sig.optString("targetFile"), "mono"));
   } else if (sig != null && !sig.optString("targetUrl").isEmpty()) {
    rows.put(row("Địa chỉ truy cập", sig.optString("targetUrl"), "mono"));
   }
  } catch (Exception ignored) {}
  return rows;
 }

 // ------------------------------------------------------------------ report builder
 /** Never throws. {@code snapshot} is the launcher state at failure time (may be null). */
 static JSONObject build(Context c, String action, String title, String message, Throwable e, String forcedCode, JSONObject snapshot) {
  JSONObject r = new JSONObject();
  try {
   String cleanMsg = redact(message == null ? "" : message);
   String code = forcedCode != null && !forcedCode.isEmpty() ? forcedCode : (e != null ? classify(e, action) : classifyText(cleanMsg));
   JSONObject net = networkInfo(c);

   // Auto-upgrade generic network / ADB codes using live Android connectivity facts
   if ("E-NET".equals(code) || "E-NET-DNS".equals(code) || "E-NET-TIMEOUT".equals(code)) {
    if (net.optBoolean("airplane") || (net.has("active") && !net.optBoolean("active"))) {
     code = "E-NET-OFFLINE";
    } else if (net.optBoolean("captivePortal")) {
     code = "E-NET-CAPTIVE";
    }
   }
   if (("E-ADB-CONN-REFUSED".equals(code) || "E-ADB-TIMEOUT".equals(code) || "E-ADB-PAIR".equals(code)) && !isWifiConnected(c)) {
    code = "E-ADB-NO-WIFI";
   }

   ErrorCatalog.Entry entry = ErrorCatalog.lookup(code);
   JSONObject probe = null;
   if (entry.network && Looper.myLooper() != Looper.getMainLooper()) {
    probe = probe(c);
    String pv = probe.optString("verdict");
    if ("captive_portal".equals(pv) && !"E-NET-CAPTIVE".equals(code)) {
     code = "E-NET-CAPTIVE";
     entry = ErrorCatalog.lookup(code);
    } else if ("offline".equals(pv) && ("E-NET".equals(code) || "E-NET-DNS".equals(code) || "E-NET-TIMEOUT".equals(code))) {
     code = "E-NET-OFFLINE";
     entry = ErrorCatalog.lookup(code);
    } else if ("dns_blocked".equals(pv) && (net.optBoolean("privateDns") || hasTransport(net, "vpn"))) {
     code = "E-NET-VPN-DNS";
     entry = ErrorCatalog.lookup(code);
    }
   }

   long now = System.currentTimeMillis();
   SimpleDateFormat iso = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss (Z)", Locale.ROOT);
   String reportId = Long.toString(now, 36).toUpperCase(Locale.ROOT);
   r.put("code", code);
   r.put("reportId", reportId);
   r.put("time", iso.format(new Date(now)));
   r.put("title", title == null ? entry.title : title);
   r.put("message", cleanMsg);
   r.put("action", action == null ? "" : action);
   r.put("errorTitle", entry.title);
   r.put("level", entry.level);
   r.put("networkRelated", entry.network);

   JSONArray steps = new JSONArray();
   for (String s : entry.steps) steps.put(s);
   r.put("steps", steps);

   JSONArray quick = new JSONArray();
   for (String q : entry.quickActions) quick.put(q);
   r.put("quickActions", quick);

   String explain = entry.summary;
   r.put("network", net);
   if (probe != null) r.put("probe", probe);
   if (entry.network) {
    String verdict = networkVerdict(net, probe);
    if (!verdict.isEmpty()) explain += "\n\nKiểm tra tự động: " + verdict;
   }
   r.put("explain", explain);
   String hint = hint(code);
   if (!hint.isEmpty()) r.put("hint", hint);

   JSONObject s = snapshot == null ? new JSONObject() : snapshot;
   r.put("lastStep", s.optJSONObject("progress") == null ? "" : redact(s.getJSONObject("progress").optString("label")));
   r.put("phase", s.optString("phase"));
   r.put("app", pick(s.optJSONObject("app"), "versionName", "versionCode", "variant", "theme", "resolvedTheme"));
   r.put("android", deviceHealth(c));
   r.put("game", pick(s.optJSONObject("game"), "installed", "package", "versionsKnown", "gameVersion", "resourceVersion", "root", "reason"));
   r.put("github", pick(s.optJSONObject("github"), "repo", "branch", "releaseStatus", "releaseVersion", "manifestStatus", "translationVersion", "manifestSha256", "announcementStatus", "announcementError", "errorCode", "errorStage", "errorRaw", "message"));
   r.put("payload", pick(s.optJSONObject("payload"), "available", "compatible", "updateAvailable", "version", "fileCount", "reason", "reasonCode"));
   r.put("receipt", pick(s.optJSONObject("receipt"), "present", "version", "manifestSha256", "files", "stale", "installedGameVersion", "installedResourceVersion"));
   r.put("recovery", pick(s.optJSONObject("recovery"), "pending", "message"));
   JSONObject adb = s.optJSONObject("adb");
   r.put("adb", Store.obj(
     "connected", adb != null && adb.optBoolean("connected"),
     "hasIdentity", adb != null && adb.optBoolean("hasIdentity"),
     "status", adb == null ? "" : redact(adb.optString("status"))
   ));
   JSONObject storage = Store.obj("internalFreeBytes", free(c.getFilesDir()), "externalFreeBytes", free(c.getExternalFilesDir(null)));
   r.put("storage", storage);
   try {
    File active = Store.internal(c, "state/active_journal.json");
    if (active.isFile()) {
     JSONObject j = Store.read(active);
     r.put("journal", Store.obj(
       "state", j.optString("state"),
       "id", j.optString("id"),
       "version", j.optString("version"),
       "gameVersion", j.optString("gameVersion"),
       "resourceVersion", j.optString("resourceVersion"),
       "files", j.optJSONArray("files") == null ? 0 : j.getJSONArray("files").length(),
       "pendingFile", j.optString("pending")
     ));
    }
   } catch (Exception ignored) {}
   r.put("signals", extractSignals(e, cleanMsg));
   r.put("errorChain", e == null ? new JSONArray() : chain(e));

   JSONArray logArr = new JSONArray();
   for (String ln : DiagnosticLog.tail(c, 30)) logArr.put(ln);
   r.put("recentLogs", logArr);

   r.put("contextRows", buildContextRows(r));
   DiagnosticLog.log(c, "error", code + " (#" + reportId + ") [" + (action == null ? "app" : action) + "] " + cleanMsg);
  } catch (Exception ignored) {}
  return r;
 }

 /** Report for a known situation (no exception), e.g. "why is the install button blocked?". */
 static JSONObject explain(Context c, String code, String action, JSONObject snapshot) {
  ErrorCatalog.Entry e = ErrorCatalog.lookup(code);
  return build(c, action, e.title, e.summary, null, e.code, snapshot);
 }

 /** Updates a stored report in-place after user runs live network probe inside the Error Dialog. */
 static JSONObject attachProbe(Context c, String reportId, JSONObject probeResult) {
  JSONObject r = findReport(c, reportId);
  if (r == null || probeResult == null) return r;
  try {
   r.put("probe", probeResult);
   r.put("network", networkInfo(c));
   r.put("contextRows", buildContextRows(r));
   record(c, r);
  } catch (Exception ignored) {}
  return r;
 }

 /** Remembers the report (memory + disk) so the copy button can fetch it by id. Returns the same object. */
 static JSONObject record(Context c, JSONObject report) {
  try {
   lastId = report.optString("reportId");
   lastReport = report;
   lastText = text(report);
   Store.write(Store.internal(c, "state/last_error.json"), report);
  } catch (Exception ignored) {}
  return report;
 }

 private static boolean hasTransport(JSONObject net, String transport) {
  JSONArray tr = net == null ? null : net.optJSONArray("transports");
  if (tr == null) return false;
  for (int i = 0; i < tr.length(); i++) if (transport.equals(tr.optString(i))) return true;
  return false;
 }

 private static String formatTransports(JSONArray tr) {
  if (tr == null || tr.length() == 0) return "Không rõ";
  List<String> names = new ArrayList<>();
  for (int i = 0; i < tr.length(); i++) {
   String t = tr.optString(i);
   if ("wifi".equals(t)) names.add("Wi-Fi");
   else if ("cellular".equals(t)) names.add("4G/5G");
   else if ("vpn".equals(t)) names.add("VPN");
   else if ("ethernet".equals(t)) names.add("Ethernet");
   else names.add(t);
  }
  return joinStrings(names, " + ");
 }

 private static String joinStrings(List<String> list, String sep) {
  StringBuilder sb = new StringBuilder();
  for (int i = 0; i < list.size(); i++) {
   if (i > 0) sb.append(sep);
   sb.append(list.get(i));
  }
  return sb.toString();
 }

 private static String yn(boolean v) { return v ? "Có" : "Không"; }

 /** Clean PC-parity human-readable diagnostic text ready to paste to developers. */
 static String text(JSONObject r) {
  try {
   JSONObject dev = r.optJSONObject("android");
   JSONObject app = r.optJSONObject("app");
   JSONObject sig = r.optJSONObject("signals");
   StringBuilder sb = new StringBuilder();

   sb.append("STELLA SORA VIỆT HOÁ — MÃ LỖI ").append(r.optString("code", "E-UNKNOWN"))
     .append(" (#").append(r.optString("reportId", "?")).append(")\n");
   sb.append("Nền tảng: Android ").append(dev == null ? "?" : dev.optString("release", "?"))
     .append(" (SDK ").append(dev == null ? "?" : dev.optString("sdk", "?")).append(") · ")
     .append(dev == null ? "?" : (dev.optString("manufacturer", "") + " " + dev.optString("model", "")).trim())
     .append(" · Launcher v").append(app == null ? "?" : app.optString("versionName", "?"))
     .append(" (code ").append(app == null ? "?" : app.optString("versionCode", "?")).append(")\n");
   sb.append("Thời gian: ").append(r.optString("time", "?")).append('\n');
   String act = r.optString("action");
   sb.append("Đang làm: ").append(ErrorCatalog.actionLabel(act))
     .append(act.isEmpty() ? "" : " [" + act + "]").append('\n');
   sb.append("Bước cuối: ").append(r.optString("lastStep").isEmpty() ? "(không có)" : r.optString("lastStep")).append("\n\n");

   sb.append("Tiêu đề: ").append(r.optString("errorTitle")).append('\n');
   sb.append("Giải thích: ").append(r.optString("explain")).append('\n');
   JSONArray steps = r.optJSONArray("steps");
   if (steps != null && steps.length() > 0) {
    sb.append("Cách xử lý đã gợi ý:\n");
    for (int i = 0; i < steps.length(); i++) {
     sb.append("  ").append(i + 1).append(". ").append(steps.optString(i)).append('\n');
    }
   }
   sb.append("Thông báo gốc: ").append(r.optString("message").isEmpty() ? "(không có)" : r.optString("message")).append('\n');
   if (sig != null) {
    List<String> sp = new ArrayList<>();
    if (sig.has("httpStatus")) sp.add("HTTP=" + sig.optInt("httpStatus"));
    if (sig.has("adbExit")) sp.add("ADB_EXIT=" + sig.optInt("adbExit"));
    if (!sig.optString("errno").isEmpty()) sp.add("ERRNO=" + sig.optString("errno"));
    if (!sig.optString("sysClass").isEmpty()) sp.add("CLASS=" + sig.optString("sysClass"));
    if (!sp.isEmpty()) sb.append("Mã hệ thống: ").append(joinStrings(sp, " · ")).append('\n');
    if (!sig.optString("targetFile").isEmpty()) sb.append("Tệp mục tiêu: ").append(sig.optString("targetFile")).append('\n');
    if (!sig.optString("targetUrl").isEmpty()) sb.append("Địa chỉ truy cập: ").append(sig.optString("targetUrl")).append('\n');
   }
   if (!r.optString("hint").isEmpty()) {
    sb.append("Ghi chú Dev: ").append(r.optString("hint")).append('\n');
   }

   JSONObject probe = r.optJSONObject("probe");
   if (probe != null) {
    sb.append("\n--- Đo kết nối mạng lúc lỗi ---\n");
    for (String ln : formatProbe(probe)) sb.append(ln).append('\n');
   }

   sb.append("\n--- Thiết bị & Hệ thống ---\n");
   sb.append("Launcher: v").append(app == null ? "?" : app.optString("versionName", "?"))
     .append(" (code ").append(app == null ? "?" : app.optString("versionCode", "?"))
     .append(", ").append(app == null ? "localadb" : app.optString("variant", "localadb")).append(')');
   if (app != null && !app.optString("theme").isEmpty()) {
    sb.append(" · Giao diện: ").append(app.optString("theme")).append(" (đang hiển thị: ").append(app.optString("resolvedTheme", "?")).append(')');
   }
   sb.append('\n');
   if (dev != null) {
    sb.append("Android: ").append(dev.optString("release", "?"))
      .append(" (SDK ").append(dev.optString("sdk", "?"))
      .append(dev.optString("securityPatch").isEmpty() ? "" : " · vá bảo mật " + dev.optString("securityPatch"))
      .append(") · ABI: ").append(dev.optString("abis", "?")).append('\n');
    sb.append("Thiết bị: ").append(dev.optString("manufacturer", "?")).append(" / ")
      .append(dev.optString("brand", "?")).append(" / ").append(dev.optString("model", "?"))
      .append(" (nhóm OEM: ").append(dev.optString("oemFamily", "generic")).append(")\n");
    sb.append("Ngôn ngữ / Múi giờ: ").append(dev.optString("locale", "?")).append(" · ").append(dev.optString("timezone", "?")).append('\n');
    sb.append("Quyền & Cài đặt: Tuỳ chọn nhà phát triển=").append(yn(dev.optBoolean("devOptions")))
      .append(" · Thông báo=").append(yn(dev.optBoolean("notifPermission")))
      .append(" · Cài APK=").append(yn(dev.optBoolean("canInstallApk")))
      .append(" · Bỏ tối ưu pin=").append(yn(dev.optBoolean("ignoringBatteryOpt"))).append('\n');
    if (dev.optLong("ramTotalMb", 0) > 0) {
     sb.append("RAM: khả dụng ").append(dev.optLong("ramAvailMb")).append(" MB / tổng ").append(dev.optLong("ramTotalMb"))
       .append(" MB (cảnh báo thiếu RAM: ").append(yn(dev.optBoolean("lowRam"))).append(")\n");
    }
   }
   JSONObject st = r.optJSONObject("storage");
   if (st != null) {
    sb.append("Bộ nhớ trống: Bộ nhớ trong ").append(fmtGb(st.optLong("internalFreeBytes", -1)))
      .append(" · Bộ nhớ ngoài ứng dụng ").append(fmtGb(st.optLong("externalFreeBytes", -1))).append('\n');
   }
   JSONObject net = r.optJSONObject("network");
   if (net != null) {
    sb.append("Mạng: ").append(net.optBoolean("active") ? formatTransports(net.optJSONArray("transports")) : "Không có mạng")
      .append(" (Chế độ máy bay=").append(yn(net.optBoolean("airplane")))
      .append(", Internet=").append(yn(net.optBoolean("internet")))
      .append(", Xác thực=").append(yn(net.optBoolean("validated")))
      .append(", CaptivePortal=").append(yn(net.optBoolean("captivePortal")))
      .append(", PrivateDNS=").append(net.optBoolean("privateDns") ? ("Bật" + (net.optString("privateDnsHost").isEmpty() ? "" : " (" + net.optString("privateDnsHost") + ")")) : "Tắt")
      .append(", Tiết kiệm dữ liệu=").append(yn(net.optBoolean("dataSaver"))).append(")\n");
   }

   JSONObject adb = r.optJSONObject("adb");
   sb.append("\n--- Local ADB ---\n");
   sb.append("Đã kết nối: ").append(yn(adb != null && adb.optBoolean("connected")))
     .append(" · Đã có khoá ghép đôi: ").append(yn(adb != null && adb.optBoolean("hasIdentity"))).append('\n');
   sb.append("Trạng thái: ").append(adb == null || adb.optString("status").isEmpty() ? "(không có)" : adb.optString("status")).append('\n');

   JSONObject game = r.optJSONObject("game");
   JSONObject rc = r.optJSONObject("receipt");
   JSONObject rec = r.optJSONObject("recovery");
   sb.append("\n--- Game ---\n");
   sb.append("Đã cài đặt: ").append(yn(game != null && game.optBoolean("installed")))
     .append(" (").append(game == null ? Store.GAME : game.optString("package", Store.GAME)).append(")\n");
   sb.append("Phiên bản: game ").append(game == null || game.optString("gameVersion").isEmpty() ? "?" : game.optString("gameVersion"))
     .append(" / tài nguyên ").append(game == null || game.optString("resourceVersion").isEmpty() ? "?" : game.optString("resourceVersion"))
     .append(" (đọc đủ: ").append(yn(game != null && game.optBoolean("versionsKnown"))).append(")\n");
   sb.append("Đường dẫn: ").append(game == null || game.optString("root").isEmpty() ? "(chưa xác định)" : game.optString("root")).append('\n');
   if (rc != null && rc.optBoolean("present")) {
    sb.append("Biên bản cài: có · bản dịch ").append(rc.optString("version", "?"))
      .append(" · ").append(rc.optInt("files", 0)).append(" tệp · lỗi thời: ").append(yn(rc.optBoolean("stale"))).append('\n');
   } else {
    sb.append("Biên bản cài: KHÔNG CÓ\n");
   }
   sb.append("Phục hồi dở dang: ").append(yn(rec != null && rec.optBoolean("pending"))).append('\n');

   JSONObject gh = r.optJSONObject("github");
   JSONObject pl = r.optJSONObject("payload");
   sb.append("\n--- GitHub / Kênh cập nhật ---\n");
   if (gh != null) {
    sb.append("Kho/nhánh: ").append(gh.optString("repo", "?")).append(" @ ").append(gh.optString("branch", "?")).append('\n');
    sb.append("Bản phát hành: ").append(gh.optString("releaseStatus", "?")).append(" · ").append(gh.optString("releaseVersion", "chưa đọc được")).append('\n');
    sb.append("Bảng kê Android: ").append(gh.optString("manifestStatus", "?"))
      .append(" · bản dịch ").append(gh.optString("translationVersion", "chưa có"))
      .append(pl != null && pl.optInt("fileCount", 0) > 0 ? (" · " + pl.optInt("fileCount") + " tệp") : "").append('\n');
    sb.append("Thông báo: ").append(gh.optString("announcementStatus", "?")).append('\n');
    if (!gh.optString("errorCode").isEmpty()) {
     sb.append("Lỗi đồng bộ [").append(gh.optString("errorCode")).append(" / ").append(gh.optString("errorStage", "?")).append("]: ")
       .append(gh.optString("errorRaw", gh.optString("message"))).append('\n');
    }
   }
   if (pl != null && !pl.optString("reason").isEmpty()) {
    sb.append("Trạng thái gói: tương thích=").append(yn(pl.optBoolean("compatible")))
      .append(" · ").append(pl.optString("reason")).append('\n');
   }

   JSONObject journal = r.optJSONObject("journal");
   if (journal != null) {
    sb.append("\n--- Nhật ký giao dịch (Journal) ---\n");
    sb.append("Trạng thái: ").append(journal.optString("state"))
      .append(" · bản dịch ").append(journal.optString("version"))
      .append(" · game ").append(journal.optString("gameVersion")).append('/').append(journal.optString("resourceVersion"))
      .append(" · ").append(journal.optInt("files")).append(" tệp")
      .append(journal.optString("pendingFile").isEmpty() ? "" : " · đang ghi: " + journal.optString("pendingFile")).append('\n');
   }

   JSONArray chain = r.optJSONArray("errorChain");
   if (chain != null && chain.length() > 0) {
    sb.append("\n--- Chuỗi lỗi (ngoài → trong) ---\n");
    for (int i = 0; i < chain.length(); i++) {
     JSONObject it = chain.optJSONObject(i);
     if (it == null) continue;
     sb.append("  ").append(i + 1).append(". ").append(it.optString("class"));
     if (!it.optString("code").isEmpty()) sb.append(" [").append(it.optString("code")).append(']');
     if (!it.optString("message").isEmpty()) sb.append(": ").append(it.optString("message"));
     sb.append('\n');
     JSONObject det = it.optJSONObject("details");
     if (det != null && det.length() > 0) sb.append("     chi tiết: ").append(det.toString()).append('\n');
    }
    JSONObject first = chain.optJSONObject(0);
    JSONArray stack = first == null ? null : first.optJSONArray("stack");
    if (stack != null && stack.length() > 0) {
     sb.append("\n--- Vết lỗi (rút gọn) ---\n");
     for (int i = 0; i < stack.length(); i++) sb.append("  at ").append(stack.optString(i)).append('\n');
    }
   }

   JSONArray logs = r.optJSONArray("recentLogs");
   if (logs != null && logs.length() > 0) {
    sb.append("\n--- Nhật ký launcher (").append(logs.length()).append(" dòng gần nhất) ---\n");
    for (int i = 0; i < logs.length(); i++) sb.append("  ").append(logs.optString(i)).append('\n');
   }

   return redact(sb.toString());
  } catch (Exception e) {
   return redact(r.toString());
  }
 }

 /** Full PC-style system diagnostics report (used by Settings → Sao chép báo cáo chẩn đoán). */
 static String buildDiagnosticsText(Context c, JSONObject snapshot) {
  JSONObject r = build(c, "diagnostics", "Báo cáo chẩn đoán hệ thống", "Chẩn đoán trạng thái thiết bị, Local ADB, game và GitHub.", null, "E-NO-RECOVERY", snapshot);
  String body = text(r);
  JSONObject lastErr = lastSummary(c);
  if (lastErr.length() > 0) {
   body += "\n--- Lỗi gần nhất đã ghi nhận ---\n"
     + "  Mã: " + lastErr.optString("code") + " (#" + lastErr.optString("reportId") + ")\n"
     + "  Thời gian: " + lastErr.optString("time") + " · Thao tác: " + lastErr.optString("action") + "\n"
     + "  Nội dung: " + redact(lastErr.optString("message")) + "\n";
  }
  return body.replace("MÃ LỖI E-NO-RECOVERY", "BÁO CÁO CHẨN ĐOÁN");
 }

 /** Text of the report with the given id, or the latest one when id is empty or unknown. Null when none exists. */
 static String find(Context c, String id) {
  if (!lastText.isEmpty() && (id == null || id.isEmpty() || id.equals(lastId))) return lastText;
  try {
   File f = Store.internal(c, "state/last_error.json");
   if (f.isFile()) {
    JSONObject r = Store.read(f);
    if (id == null || id.isEmpty() || id.equals(r.optString("reportId"))) return text(r);
   }
  } catch (Exception ignored) {}
  return lastText.isEmpty() ? null : lastText;
 }

 /** The report object with the given id (memory first, then disk). Null when unknown. */
 static JSONObject findReport(Context c, String id) {
  JSONObject m = lastReport;
  if (m != null && (id == null || id.isEmpty() || id.equals(m.optString("reportId")))) return m;
  try {
   File f = Store.internal(c, "state/last_error.json");
   if (f.isFile()) {
    JSONObject r = Store.read(f);
    if (id == null || id.isEmpty() || id.equals(r.optString("reportId"))) return r;
   }
  } catch (Exception ignored) {}
  return null;
 }

 /** One-line summary of the last error for the diagnostics report & UI state. */
 static JSONObject lastSummary(Context c) {
  try {
   JSONObject m = lastReport;
   if (m != null) return pick(m, "code", "reportId", "time", "action", "errorTitle", "message");
   File f = Store.internal(c, "state/last_error.json");
   if (f.isFile()) return pick(Store.read(f), "code", "reportId", "time", "action", "errorTitle", "message");
  } catch (Exception ignored) {}
  return new JSONObject();
 }

 /** Adds the explanation, context grid, quick actions, and report preview to a message event payload. */
 static JSONObject attach(JSONObject data, JSONObject report) {
  try {
   if (report != null) {
    data.put("code", report.optString("code"));
    data.put("reportId", report.optString("reportId"));
    data.put("errorTitle", report.optString("errorTitle"));
    data.put("explain", report.optString("explain"));
    data.put("level", report.optString("level"));
    data.put("networkRelated", report.optBoolean("networkRelated"));
    if (report.optJSONArray("steps") != null) data.put("steps", report.getJSONArray("steps"));
    if (report.optJSONArray("quickActions") != null) data.put("quickActions", report.getJSONArray("quickActions"));
    if (report.optJSONArray("contextRows") != null) data.put("contextRows", report.getJSONArray("contextRows"));
    if (report.optJSONObject("probe") != null) {
     JSONObject p = report.getJSONObject("probe");
     JSONArray pLines = new JSONArray();
     for (String ln : formatProbe(p)) pLines.put(ln);
     data.put("probe", Store.obj("verdict", p.optString("verdict"), "verdictText", p.optString("verdictText"), "lines", pLines));
    }
    data.put("reportPreview", text(report));
   }
  } catch (JSONException ignored) {}
  return data;
 }
}
