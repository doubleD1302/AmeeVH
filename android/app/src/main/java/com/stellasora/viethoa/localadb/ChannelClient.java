package com.stellasora.viethoa.localadb;
import android.content.*;
import android.content.pm.*;
import android.os.*;
import org.json.*;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.security.*;
import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import javax.net.ssl.SSLException;
import javax.net.ssl.SSLHandshakeException;

/** HTTPS-only metadata, explicit Android contracts, and size/hash-bound resumable downloads. */
final class ChannelClient {
 interface Progress { void update(String text, int percent); }
 static final String USER_AGENT = "StellaSora-Android-LocalADB/1.3.1";
 private static final long RELEASE_CACHE_TTL_MS = 15L * 60L * 1000L;
 private static final int DOWNLOAD_MAX_ATTEMPTS = 4;
 private final Context context;
 private final JSONObject config;
 final String repo, branch;
 private JSONObject release;

 ChannelClient(Context c) throws Exception {
  context = c;
  config = Store.config(c);
  Store.validateConfig(config);
  repo = config.getString("repo");
  branch = config.getString("branch");
 }

 private static HttpURLConnection open(String address) throws Exception {
  return openRequest(address, -1L);
 }

 private static HttpURLConnection openRequest(String address, long rangeOffset) throws Exception {
  URL url = new URL(address);
  for (int redirects = 0; redirects <= 5; redirects++) {
   if (!"https".equals(url.getProtocol()) || url.getUserInfo() != null) {
    throw new IOException("Nguồn tải cần là HTTPS hợp lệ.");
   }
   HttpURLConnection connection = (HttpURLConnection) url.openConnection();
   connection.setConnectTimeout(12000);
   connection.setReadTimeout(rangeOffset >= 0 ? 25000 : 15000);
   connection.setInstanceFollowRedirects(false);
   connection.setUseCaches(false);
   connection.setRequestProperty("User-Agent", USER_AGENT);
   connection.setRequestProperty("Accept", "application/json, application/octet-stream");
   if (rangeOffset >= 0) connection.setRequestProperty("Accept-Encoding", "identity");
   connection.setRequestProperty("Cache-Control", "no-cache");
   connection.setRequestProperty("Pragma", "no-cache");
   if (rangeOffset > 0) connection.setRequestProperty("Range", "bytes=" + rangeOffset + "-");
   int code = connection.getResponseCode();
   if (code >= 300 && code < 400) {
    String next = connection.getHeaderField("Location");
    connection.disconnect();
    if (next == null) throw new IOException("Máy chủ không có đích chuyển hướng.");
    url = new URL(url, next);
    continue;
   }
   if ((code == 403 || code == 429) && "api.github.com".equalsIgnoreCase(url.getHost())) {
    connection.disconnect();
    throw new StellaException("E-HTTP-" + code,
      "GitHub đang giới hạn lượt truy cập tạm thời từ mạng này (HTTP " + code + "). Hãy chờ vài phút hoặc đổi Wi-Fi/4G rồi thử lại.",
      null, "url", ErrorReport.safeUrl(address), "httpStatus", code);
   }
   if (rangeOffset >= 0) {
    if (code == 200 || (rangeOffset > 0 && (code == 206 || code == 416))) return connection;
    connection.disconnect();
    throw new IOException("Máy chủ trả HTTP " + code + " (" + url.getHost() + ").");
   }
   if (code != 200) {
    connection.disconnect();
    throw new IOException("Máy chủ trả HTTP " + code + " (" + url.getHost() + ").");
   }
   return connection;
  }
  throw new IOException("Nguồn tải chuyển hướng quá nhiều.");
 }

 private static byte[] bytes(String url, long size, String digest) throws Exception {
  HttpURLConnection con = open(url);
  try (InputStream in = con.getInputStream(); ByteArrayOutputStream out = new ByteArrayOutputStream()) {
   long deadline = SystemClock.elapsedRealtime() + 60000;
   byte[] b = new byte[32768];
   int n;
   while ((n = in.read(b)) != -1) {
    out.write(b, 0, n);
    if (out.size() > 4194304 || SystemClock.elapsedRealtime() > deadline) {
     throw new IOException("Metadata quá lớn hoặc quá thời hạn.");
    }
   }
   byte[] data = out.toByteArray();
   if (size >= 0 && data.length != size) throw new IOException("Kích thước metadata không khớp.");
   if (digest != null && !Store.hex(MessageDigest.getInstance("SHA-256").digest(data)).equals(digest)) {
    throw new IOException("SHA256 metadata không khớp bản công bố.");
   }
   return data;
  } finally {
   con.disconnect();
  }
 }

 static JSONObject json(String url) throws Exception {
  return new JSONObject(new String(bytes(url, -1, null), StandardCharsets.UTF_8));
 }

 private static boolean validReleaseObject(JSONObject r) {
  return r != null && !r.optBoolean("draft") && !r.optBoolean("prerelease") && r.has("assets") && !r.optString("tag_name").isEmpty();
 }

 JSONObject freshRelease() throws Exception {
  File relCache = Store.internal(context, "cache/rel_" + Store.digest(repo + "/" + branch) + ".json");
  try {
   JSONObject r = json("https://api.github.com/repos/" + repo + "/releases/latest");
   if (!validReleaseObject(r)) throw new IOException("Bản phát hành chưa hợp lệ.");
   try {
    Store.write(relCache, Store.obj("cachedAt", System.currentTimeMillis(), "release", r));
   } catch (Exception ignored) {}
   release = r;
   return r;
  } catch (StellaException rateLimited) {
   if (("E-HTTP-403".equals(rateLimited.code) || "E-HTTP-429".equals(rateLimited.code)) && relCache.isFile()) {
    try {
     JSONObject cachedWrap = Store.read(relCache);
     long age = System.currentTimeMillis() - cachedWrap.optLong("cachedAt", 0L);
     JSONObject cachedRel = cachedWrap.optJSONObject("release");
     if (age >= -60000L && age < RELEASE_CACHE_TTL_MS && validReleaseObject(cachedRel)) {
      release = cachedRel;
      return cachedRel;
     }
    } catch (Exception ignored) {}
   }
   throw rateLimited;
  }
 }

 private JSONObject findAsset(JSONObject r, String... names) throws Exception {
  JSONArray a = r.getJSONArray("assets");
  for (int i = 0; i < a.length(); i++) {
   JSONObject item = a.getJSONObject(i);
   for (String name : names) {
    if (item.optString("name").equals(name)) return item;
   }
  }
  return null;
 }

 private JSONObject assetJson(JSONObject a) throws Exception {
  String digest = a.optString("digest");
  if (!digest.matches("sha256:[0-9a-fA-F]{64}")) throw new IOException("Metadata Android chưa có SHA256 được công bố.");
  return new JSONObject(new String(bytes(a.getString("browser_download_url"), a.getLong("size"), digest.substring(7).toLowerCase(Locale.ROOT)), StandardCharsets.UTF_8));
 }

 boolean hasAndroidManifest(JSONObject r) throws Exception {
  return findAsset(r, "android_patch_manifest.json", "stella_android_manifest.json") != null;
 }

 JSONObject androidManifest(JSONObject r) throws Exception {
  JSONObject a = findAsset(r, "android_patch_manifest.json", "stella_android_manifest.json");
  if (a == null) throw new IOException("Chưa có gói bản dịch Android tương thích trên GitHub. Gói Windows và APK overlay cũ không được dùng cho ứng dụng này.");
  return alignAssetUrls(r, validateManifest(assetJson(a)));
 }

 /** The manifest may name a URL from an older release for a file whose size and SHA256 match an asset published in THIS release. Prefer the asset of this release. */
 private static String sameReleaseUrl(JSONObject r, String url, long size, String sha) {
  try {
   if (url == null || url.isEmpty()) return url;
   String name = nameOf(url);
   JSONArray assets = r.getJSONArray("assets");
   for (int i = 0; i < assets.length(); i++) {
    JSONObject asset = assets.getJSONObject(i);
    if (!name.equals(asset.optString("name"))) continue;
    String digest = asset.optString("digest");
    String candidate = asset.optString("browser_download_url");
    if (asset.optLong("size", -1) == size && digest.equalsIgnoreCase("sha256:" + sha) && candidate.startsWith("https://")) {
     return candidate;
    }
   }
  } catch (Exception ignored) {}
  return url;
 }

 private static JSONObject alignAssetUrls(JSONObject r, JSONObject manifest) throws Exception {
  JSONObject zip = manifest.optJSONObject("package_zip");
  if (zip != null) {
   String fixed = sameReleaseUrl(r, zip.getString("url"), zip.getLong("size"), zip.getString("sha256"));
   if (!fixed.equals(zip.getString("url"))) {
    JSONObject copy = new JSONObject(zip.toString());
    copy.put("url", fixed);
    manifest.put("package_zip", copy);
   }
  }
  JSONArray files = manifest.getJSONArray("files");
  for (int i = 0; i < files.length(); i++) {
   JSONObject f = files.getJSONObject(i);
   String url = f.optString("url", "");
   if (url.isEmpty()) continue;
   String fixed = sameReleaseUrl(r, url, f.getLong("size"), f.getString("sha256"));
   if (!fixed.equals(url)) f.put("url", fixed);
  }
  return manifest;
 }

 static JSONObject validateManifest(JSONObject raw) throws Exception {
  if (!raw.optString("platform").equalsIgnoreCase("android") || !raw.optString("game_package").equals(Store.GAME)) {
   throw new IOException("Bảng kê không dành cho Stella Sora Android.");
  }
  String game = raw.optString("client_game_version"), resource = raw.optString("resource_version"), version = raw.optString("version");
  if (game.trim().isEmpty() || resource.trim().isEmpty() || version.trim().isEmpty()) {
   throw new IOException("Gói Android thiếu phiên bản game, tài nguyên hoặc bản dịch.");
  }
  JSONObject pZip = raw.optJSONObject("package_zip");
  if (pZip != null) {
   String zUrl = pZip.optString("url");
   long zSize = pZip.optLong("size", -1);
   String zSha = pZip.optString("sha256").toLowerCase(Locale.ROOT);
   if (zSize <= 0 || !zSha.matches("[0-9a-f]{64}") || !zUrl.startsWith("https://")) {
    throw new IOException("Gói ZIP AssetBundles Android thiếu URL, kích thước hoặc SHA256 hợp lệ.");
   }
  }
  JSONArray list = new JSONArray();
  Object data = raw.opt("files");
  if (data instanceof JSONArray) {
   list = (JSONArray) data;
  } else if (data instanceof JSONObject) {
   JSONObject map = (JSONObject) data;
   Iterator<String> keys = map.keys();
   while (keys.hasNext()) {
    String key = keys.next();
    JSONObject file = new JSONObject(map.getJSONObject(key).toString());
    file.put("path", key);
    list.put(file);
   }
  }
  if (list.length() == 0 || list.length() > 5000) throw new IOException("Gói Android cần kê khai danh sách tệp rõ ràng.");
  JSONArray normalized = new JSONArray();
  Set<String> seen = new HashSet<>();
  List<String> canonicalLines = new ArrayList<>(list.length());
  long total = 0;
  for (int i = 0; i < list.length(); i++) {
   JSONObject f = list.getJSONObject(i);
   String path = GamePatcher.relative(f.getString("path"));
   if (!seen.add(path.toLowerCase(Locale.ROOT))) throw new IOException("Gói có đường dẫn tệp trùng nhau.");
   String digest = f.optString("sha256").toLowerCase(Locale.ROOT);
   long size = f.optLong("size", -1);
   String url = f.optString("url", f.optString("source_url", ""));
   boolean isBundle = path.startsWith("Persistent_Store/AssetBundles/");
   if (size < 0 || size > 1073741824L || !digest.matches("[0-9a-f]{64}")) {
    throw new IOException("Tệp thiếu kích thước hoặc SHA256 hợp lệ: " + path);
   }
   if (!isBundle && !url.startsWith("https://")) throw new IOException("Tệp thiếu URL hợp lệ: " + path);
   if (isBundle && pZip == null && !url.startsWith("https://")) throw new IOException("Bundle thiếu URL hoặc gói zip: " + path);
   if (isBundle && !f.optString("asset_platform").equalsIgnoreCase("android")) {
    throw new IOException("Bundle chưa xác nhận nền tảng Android: " + path);
   }
   total = Math.addExact(total, size);
   if (total > 2147483648L) throw new IOException("Gói vượt giới hạn dung lượng của candidate.");
   JSONObject item = Store.obj("path", path, "size", size, "sha256", digest, "asset_platform", f.optString("asset_platform"));
   if (!url.isEmpty()) item.put("url", url);
   normalized.put(item);
   canonicalLines.add(path + ":" + size + ":" + digest + "\n");
  }
  Collections.sort(canonicalLines);
  MessageDigest md = MessageDigest.getInstance("SHA-256");
  for (String line : canonicalLines) md.update(line.getBytes(StandardCharsets.UTF_8));
  String manifestDigest = Store.hex(md.digest());
  JSONObject res = Store.obj(
    "platform", "android",
    "game_package", Store.GAME,
    "client_game_version", game,
    "resource_version", resource,
    "version", version,
    "files", normalized,
    "total_size", total,
    "manifest_sha256", manifestDigest
  );
  if (pZip != null) res.put("package_zip", pZip);
  return res;
 }

 JSONObject sync() throws Exception {
  JSONObject out = Store.obj("repo", repo, "branch", branch, "announcementStatus", "error", "manifestStatus", "unavailable");
  String key = Store.digest(repo + "/" + branch);
  File cached = Store.internal(context, "cache/ann_" + key + ".json");
  try {
   JSONObject news = json("https://raw.githubusercontent.com/" + repo + "/" + URLEncoder.encode(branch, "UTF-8") + "/launcher/notifications.json");
   JSONArray announcements = news.getJSONArray("announcements");
   out.put("notifications", announcements);
   out.put("announcementStatus", "online");
   out.put("announcementVersion", news.optString("version"));
   try { Store.write(cached, news); } catch (IOException ignored) {}
  } catch (Exception e) {
   out.put("announcementError", Store.cleanError(e));
   boolean loaded = false;
   if (cached.isFile()) {
    try {
     JSONObject c = Store.read(cached);
     out.put("notifications", c.getJSONArray("announcements"));
     out.put("announcementStatus", "cached");
     out.put("announcementVersion", c.optString("version"));
     loaded = true;
    } catch (Exception ignored) {}
   }
   if (!loaded) {
    try {
     JSONObject bundled = Store.asset(context, "notifications.json");
     out.put("notifications", bundled.getJSONArray("announcements"));
     out.put("announcementStatus", "bundled");
     out.put("announcementVersion", bundled.optString("version"));
    } catch (Exception ignored) {}
   }
  }
  try {
   JSONObject r = freshRelease();
   out.put("releaseVersion", r.getString("tag_name"));
   out.put("releaseNotes", r.optString("body"));
   out.put("releaseStatus", "online");
   try {
    JSONObject status = launcherAvailability(r);
    out.put("launcherStatus", status.getString("status"));
    if (status.has("metadata")) out.put("launcherUpdate", status.getJSONObject("metadata"));
   } catch (Exception ignored) {}
   try {
    if (!hasAndroidManifest(r)) {
     out.put("manifestStatus", "none");
     out.put("message", "Bản phát hành hiện tại không có gói Android.");
    } else {
     JSONObject manifest = androidManifest(r);
     out.put("manifest", manifest);
     out.put("manifestStatus", "available");
     out.put("translationVersion", manifest.getString("version"));
     out.put("manifestSha256", manifest.optString("manifest_sha256"));
     out.put("message", "Đã đọc gói Android được kê khai.");
    }
   } catch (Exception e) {
    out.put("manifestStatus", "unavailable");
    out.put("message", Store.cleanError(e));
   }
  } catch (Exception e) {
   out.put("releaseStatus", "error");
   out.put("message", "Chưa đọc được bản phát hành: " + Store.cleanError(e));
  }
  return out;
 }

 static String nameOf(String url) {
  String path = ErrorReport.safeUrl(url);
  int slash = path.lastIndexOf('/');
  return slash >= 0 ? path.substring(slash + 1) : path;
 }

 private static boolean validContentRange(String cr, long offset, long size) {
  if (cr == null || size <= 0 || offset < 0 || offset >= size) return false;
  Matcher m = Pattern.compile("(?i)^bytes\\s+(\\d+)-(\\d+)/(\\d+)$").matcher(cr.trim());
  if (!m.matches()) return false;
  try {
   long start = Long.parseLong(m.group(1));
   long end = Long.parseLong(m.group(2));
   long total = Long.parseLong(m.group(3));
   return start == offset && end == size - 1 && total == size;
  } catch (NumberFormatException e) {
   return false;
  }
 }

 private static boolean isTransientDownloadError(Throwable e) {
  for (Throwable t = e; t != null; t = t.getCause()) {
   if (t instanceof StellaException) return false;
   if (t instanceof SocketTimeoutException || t instanceof SocketException || t instanceof EOFException) return true;
   if (t instanceof SSLException && !(t instanceof SSLHandshakeException)) return true;
  }
  return false;
 }

 private static void sleepBackoff(int attempt) throws IOException {
  try {
   Thread.sleep(1200L * attempt);
  } catch (InterruptedException ie) {
   Thread.currentThread().interrupt();
   throw new IOException("Đã dừng tải tệp.", ie);
  }
 }

 private static void promotePartToDestination(File part, File destination, String name) throws IOException {
  if (destination.exists() && !destination.delete()) {
   throw new IOException("Không xoá được tệp cũ để cập nhật (" + name + ").");
  }
  if (!part.renameTo(destination)) {
   throw new IOException("Chưa chuyển được tệp tải đã xác minh (" + name + ").");
  }
  File legacyPart = new File(destination.getParentFile(), destination.getName() + ".part");
  if (legacyPart.isFile()) legacyPart.delete();
 }

 static void download(String url, File destination, long size, String digest, Progress progress) throws Exception {
  String shown = ErrorReport.safeUrl(url), name = nameOf(url);
  if (size < 0 || size > 1073741824L || digest == null || !digest.matches("[0-9a-fA-F]{64}")) {
   throw new StellaException("E-DL-PARAM", "Thông tin tải không hợp lệ (" + name + ").", null, "url", shown, "expectedSize", size);
  }
  String normDigest = digest.toLowerCase(Locale.ROOT);
  if (destination.isFile() && destination.length() == size && Store.hash(destination).equalsIgnoreCase(normDigest)) {
   if (progress != null) progress.update("Đã xác minh tệp có sẵn (" + size + " byte)", 100);
   return;
  }
  File parent = destination.getParentFile();
  if (parent != null && !parent.isDirectory() && !parent.mkdirs()) {
   throw new IOException("Không tạo được vùng tải.");
  }
  File part = new File(parent, destination.getName() + "." + normDigest.substring(0, 12) + ".part");
  if (part.isFile()) {
   long existingLen = part.length();
   if (existingLen > size) {
    part.delete();
   } else if (existingLen == size) {
    if (Store.hash(part).equalsIgnoreCase(normDigest)) {
     promotePartToDestination(part, destination, name);
     if (progress != null) progress.update("Đã tải " + size + " / " + size + " byte", 100);
     return;
    }
    part.delete();
   }
  }
  long deadline = SystemClock.elapsedRealtime() + 1200000L;
  Exception lastTransient = null;
  for (int attempt = 1; attempt <= DOWNLOAD_MAX_ATTEMPTS; attempt++) {
   long offset = (part.isFile() && part.length() > 0 && part.length() < size) ? part.length() : 0L;
   if (offset == 0L && part.exists()) part.delete();
   HttpURLConnection con = null;
   try {
    con = openRequest(url, offset);
    int code = con.getResponseCode();
    String servedHost = con.getURL().getHost();
    if (code == 416) {
     con.disconnect();
     con = null;
     part.delete();
     if (attempt < DOWNLOAD_MAX_ATTEMPTS) {
      sleepBackoff(attempt);
      continue;
     }
     throw new StellaException("E-DL-RANGE", "Máy chủ từ chối dải byte tải tiếp (HTTP 416, " + name + ").", null, "url", shown, "expectedSize", size);
    }
    boolean append = false;
    if (offset > 0 && code == 206) {
     String cr = con.getHeaderField("Content-Range");
     if (!validContentRange(cr, offset, size)) {
      con.disconnect();
      con = null;
      part.delete();
      if (attempt < DOWNLOAD_MAX_ATTEMPTS) {
       sleepBackoff(attempt);
       continue;
      }
      throw new StellaException("E-DL-RANGE", "Máy chủ trả dải byte không hợp lệ (" + name + ").", null, "url", shown, "contentRange", cr == null ? "" : cr, "expectedOffset", offset, "expectedSize", size);
     }
     append = true;
    } else {
     offset = 0L;
     append = false;
    }
    long contentLength = con.getContentLengthLong();
    if (contentLength >= 0 && offset + contentLength > size) {
     part.delete();
     throw new StellaException("E-DL-OVERSIZE", "Tệp trên máy chủ lớn hơn kích thước đã công bố (" + name + ").", null, "url", shown, "servedFrom", servedHost, "expectedSize", size, "receivedBytesWhenStopped", offset, "contentLength", contentLength);
    }
    long count = append ? offset : 0L;
    try (InputStream in = con.getInputStream(); FileOutputStream out = new FileOutputStream(part, append)) {
     byte[] b = new byte[131072];
     int n;
     try {
      while ((n = in.read(b)) != -1) {
       if (n == 0) continue;
       if (count + n > size) {
        out.close();
        part.delete();
        throw new StellaException("E-DL-OVERSIZE", "Tệp trên máy chủ lớn hơn kích thước đã công bố (" + name + ").", null, "url", shown, "servedFrom", servedHost, "expectedSize", size, "receivedBytesWhenStopped", count + n, "contentLength", contentLength);
       }
       out.write(b, 0, n);
       count += n;
       if (SystemClock.elapsedRealtime() > deadline) {
        out.flush();
        try { out.getFD().sync(); } catch (IOException ignored) {}
        throw new StellaException("E-DL-TIMEOUT", "Tải quá thời hạn (" + name + ").", null, "url", shown, "expectedSize", size, "receivedBytes", count);
       }
       if (progress != null) progress.update("Đang tải " + count + " / " + size + " byte", size > 0 ? (int) (100L * count / size) : 100);
      }
     } finally {
      try { out.flush(); out.getFD().sync(); } catch (IOException ignored) {}
     }
    }
    if (count < size) {
     if (contentLength >= 0 && offset + contentLength < size) {
      part.delete();
      throw new StellaException("E-DL-VERIFY", "Tệp tải về không đúng kích thước hoặc SHA256 (" + name + ": nhận " + count + " byte, cần " + size + " byte).", null, "url", shown, "servedFrom", servedHost, "contentLength", contentLength, "expectedSize", size, "receivedBytes", count, "sizeMatches", false, "expectedSha256", normDigest, "actualSha256", "", "hashMatches", false);
     }
     lastTransient = new EOFException("Luồng tải bị ngắt sớm (" + count + "/" + size + " byte).");
     if (attempt < DOWNLOAD_MAX_ATTEMPTS) {
      if (progress != null) progress.update("Mạng gián đoạn, đang nối lại (" + (attempt + 1) + "/" + DOWNLOAD_MAX_ATTEMPTS + ")…", size > 0 ? (int) (100L * count / size) : 0);
      sleepBackoff(attempt);
      continue;
     }
     throw new StellaException("E-DL-VERIFY", "Tải bị ngắt giữa chừng sau " + DOWNLOAD_MAX_ATTEMPTS + " lần thử (" + name + ": đã lưu " + count + " / " + size + " byte, bấm thử lại để tải tiếp).", lastTransient, "url", shown, "servedFrom", servedHost, "contentLength", contentLength, "expectedSize", size, "receivedBytes", count, "sizeMatches", false, "expectedSha256", normDigest);
    }
    String actual = Store.hash(part);
    boolean hashOk = actual.equalsIgnoreCase(normDigest);
    if (!hashOk) {
     part.delete();
     throw new StellaException("E-DL-VERIFY", "Tệp tải về không đúng kích thước hoặc SHA256 (" + name + ": nhận " + count + " byte, cần " + size + " byte).", null, "url", shown, "servedFrom", servedHost, "contentLength", contentLength, "expectedSize", size, "receivedBytes", count, "sizeMatches", true, "expectedSha256", normDigest, "actualSha256", actual, "hashMatches", false);
    }
    promotePartToDestination(part, destination, name);
    if (progress != null) progress.update("Đã tải " + size + " / " + size + " byte", 100);
    return;
   } catch (Exception e) {
    if (e instanceof StellaException || e instanceof IllegalStateException) {
     throw e;
    }
    if (isTransientDownloadError(e) && attempt < DOWNLOAD_MAX_ATTEMPTS) {
     lastTransient = e;
     long saved = part.isFile() ? part.length() : 0L;
     if (progress != null) progress.update("Mạng gián đoạn, đang nối lại (" + (attempt + 1) + "/" + DOWNLOAD_MAX_ATTEMPTS + ")…", size > 0 ? (int) (100L * saved / size) : 0);
     sleepBackoff(attempt);
     continue;
    }
    if (part.isFile() && part.length() >= size) part.delete();
    throw e;
   } finally {
    if (con != null) con.disconnect();
   }
  }
 }

 JSONObject updateChannel() throws Exception { return updateChannel(freshRelease()); }
 JSONObject updateChannel(JSONObject releaseData) throws Exception {
  JSONObject state = launcherAvailability(releaseData);
  if (!"available".equals(state.getString("status"))) throw new IOException("Chưa có APK Local ADB mới hơn ứng dụng đang dùng.");
  return state.getJSONObject("metadata");
 }

 JSONObject launcherAvailability(JSONObject releaseData) throws Exception {
  JSONObject a = findAsset(releaseData, "android_localadb_launcher.json", "stella_android_localadb_channel.json");
  if (a == null) return Store.obj("status", "none");
  JSONObject j = assetJson(a);
  if (!j.optString("platform").equals("android") || !j.optString("variant").equals("localadb") || !j.optString("application_id").equals(Store.APP)) {
   throw new IOException("Kênh APK khác nền tảng, ứng dụng hoặc biến thể.");
  }
  if (j.optLong("version_code", 0) <= 0 || j.optString("version_name").trim().isEmpty()
    || !j.optString("sha256").matches("[0-9a-fA-F]{64}") || !j.optString("signing_cert_sha256").matches("[0-9a-fA-F]{64}")
    || j.optLong("size", -1) <= 0 || j.getLong("size") > 125829120 || !j.optString("apk_url").startsWith("https://")) {
   throw new IOException("Kênh APK thiếu dữ liệu xác minh.");
  }
  PackageInfo own = context.getPackageManager().getPackageInfo(Store.APP, PackageManager.GET_SIGNING_CERTIFICATES);
  if (!signers(own).contains(j.getString("signing_cert_sha256").toLowerCase(Locale.ROOT))) {
   throw new IOException("Kênh APK có chữ ký khác ứng dụng hiện tại.");
  }
  return j.getLong("version_code") > own.getLongVersionCode() ? Store.obj("status", "available", "metadata", j) : Store.obj("status", "none");
 }

 static void verifyApk(Context c, File file, JSONObject metadata) throws Exception {
  if (file.length() != metadata.getLong("size") || !Store.hash(file).equalsIgnoreCase(metadata.getString("sha256"))) {
   throw new IOException("APK không khớp kích thước hoặc SHA256.");
  }
  PackageManager pm = c.getPackageManager();
  int flags = PackageManager.GET_SIGNING_CERTIFICATES | PackageManager.GET_META_DATA;
  PackageInfo target = pm.getPackageArchiveInfo(file.getAbsolutePath(), flags);
  if (target == null) target = pm.getPackageArchiveInfo(file.getAbsolutePath(), PackageManager.GET_META_DATA);
  if (target == null) target = pm.getPackageArchiveInfo(file.getAbsolutePath(), 0);
  if (target == null) throw new IOException("Không thể đọc thông tin tệp APK.");
  PackageInfo current = pm.getPackageInfo(Store.APP, flags);
  if (!Store.APP.equals(target.packageName)) throw new IOException("Tệp APK không thuộc ứng dụng này (" + target.packageName + ").");
  if (target.getLongVersionCode() != metadata.getLong("version_code")) {
   throw new IOException("Mã phiên bản APK (" + target.getLongVersionCode() + ") không khớp metadata (" + metadata.getLong("version_code") + ").");
  }
  if (target.getLongVersionCode() <= current.getLongVersionCode()) {
   throw new IOException("Phiên bản APK tải về (" + target.getLongVersionCode() + ") không mới hơn bản đang cài (" + current.getLongVersionCode() + ").");
  }
  if (target.applicationInfo != null && target.applicationInfo.metaData != null) {
   String variant = target.applicationInfo.metaData.getString("launcher_variant");
   if (variant != null && !"localadb".equals(variant)) {
    throw new IOException("Biến thể APK (" + variant + ") không khớp biến thể đang dùng (localadb).");
   }
  }
  Set<String> old = signers(current), fresh = signers(target);
  if (!fresh.isEmpty()) {
   if (!old.isEmpty() && !old.equals(fresh)) throw new IOException("Chữ ký APK khác ứng dụng đang dùng.");
   if (!fresh.contains(metadata.getString("signing_cert_sha256").toLowerCase(Locale.ROOT))) {
    throw new IOException("Chữ ký APK không khớp chứng chỉ công bố.");
   }
  }
 }

 private static Set<String> signers(PackageInfo p) throws Exception {
  Set<String> result = new HashSet<>();
  if (p.signingInfo == null) return result;
  for (android.content.pm.Signature s : p.signingInfo.getApkContentsSigners()) {
   result.add(Store.hex(MessageDigest.getInstance("SHA-256").digest(s.toByteArray())));
  }
  return result;
 }
}
