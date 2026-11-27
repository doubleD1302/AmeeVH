package com.stellasora.viethoa.localadb;

import android.content.Context;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import javax.crypto.Cipher;
import javax.crypto.spec.IvParameterSpec;
import javax.crypto.spec.SecretKeySpec;

/**
 * Pure-Java client for official Stella Sora EN Android resource CDN (nova-static.stellasora.global).
 * Works on Wi-Fi and 4G/5G without Local ADB:
 *  - Fetches 432-byte /meta/serverlist.html to check server_data_version (~0.2s)
 *  - Only fetches /meta/and.html + final manifest when server_data_version changes
 *  - Compares official GAME_VER / RES_VER against locally stored Vietnamese receipt & journal
 */
final class OfficialAndroidClient {
 static final String ROOT_URL = "https://nova-static.stellasora.global";
 static final byte[] AES_KEY = "ma5Dn2FhC*Xhxy%c".getBytes(StandardCharsets.US_ASCII);
 static final String CACHE_FILE = "official_android_check.json";
 static final String GUARD_STATE_FILE = "official_guard_state.json";
 private static final int MAX_META_BYTES = 16 * 1024 * 1024;
 private static final Pattern HEADER_LINE = Pattern.compile("^\\$?(GAME_VER|CLIENT_VER|RES_VER|RESOURCE_VER|BIN_DIFF_PATCH_VER)[:=\\s]+([0-9A-Za-z_.-]+)");

 private OfficialAndroidClient() {}

 static final class ManifestRef {
  final String name;
  final String checksum;
  final long version;
  final String folder;
  final String url;

  ManifestRef(String name, String checksum, long version, String folder, String url) {
   this.name = name;
   this.checksum = checksum;
   this.version = version;
   this.folder = folder;
   this.url = url;
  }
 }

 static final class ProtoValue {
  final int wire;
  final long varint;
  final byte[] bytes;

  ProtoValue(int wire, long varint, byte[] bytes) {
   this.wire = wire;
   this.varint = varint;
   this.bytes = bytes;
  }
 }

 // ------------------------------------------------------------------ pure-JVM crypto & parsers

 static byte[] decryptMetadata(byte[] data) throws IOException {
  if (data == null || data.length < 32 || (data.length % 16) != 0) {
   throw new IOException("Dữ liệu máy chủ chính thức có độ dài mã hoá không hợp lệ.");
  }
  byte[] iv = new byte[16];
  System.arraycopy(data, 0, iv, 0, 16);
  byte[] cipherBytes = new byte[data.length - 16];
  System.arraycopy(data, 16, cipherBytes, 0, cipherBytes.length);
  byte[] plain;
  try {
   Cipher cipher = Cipher.getInstance("AES/CBC/NoPadding");
   cipher.init(Cipher.DECRYPT_MODE, new SecretKeySpec(AES_KEY, "AES"), new IvParameterSpec(iv));
   plain = cipher.doFinal(cipherBytes);
  } catch (Exception e) {
   throw new IOException("Dữ liệu máy chủ chính thức không giải mã được.", e);
  }
  if (plain.length == 0) {
   throw new IOException("Dữ liệu máy chủ chính thức rỗng sau giải mã.");
  }
  int pad = plain[plain.length - 1] & 0xFF;
  if (pad < 1 || pad > 16 || pad > plain.length) {
   throw new IOException("Dữ liệu máy chủ chính thức sai đệm giải mã.");
  }
  for (int i = plain.length - pad; i < plain.length; i++) {
   if ((plain[i] & 0xFF) != pad) {
    throw new IOException("Dữ liệu máy chủ chính thức sai đệm giải mã.");
   }
  }
  byte[] out = new byte[plain.length - pad];
  System.arraycopy(plain, 0, out, 0, out.length);
  return out;
 }

 static Map<Integer, List<ProtoValue>> parseProtobuf(byte[] data) throws IOException {
  Map<Integer, List<ProtoValue>> map = new LinkedHashMap<>();
  int pos = 0;
  while (pos < data.length) {
   long[] tagRes = readVarint(data, pos);
   long tag = tagRes[0];
   pos = (int) tagRes[1];
   int fieldNo = (int) (tag >>> 3);
   int wire = (int) (tag & 7L);
   if (fieldNo <= 0) {
    throw new IOException("Dữ liệu máy chủ chính thức có trường không hợp lệ.");
   }
   ProtoValue pv;
   if (wire == 0) {
    long[] vRes = readVarint(data, pos);
    pos = (int) vRes[1];
    pv = new ProtoValue(0, vRes[0], null);
   } else if (wire == 1 || wire == 2 || wire == 5) {
    int size;
    if (wire == 2) {
     long[] sRes = readVarint(data, pos);
     if (sRes[0] < 0 || sRes[0] > MAX_META_BYTES) {
      throw new IOException("Dữ liệu máy chủ chính thức vượt kích thước hợp lệ.");
     }
     size = (int) sRes[0];
     pos = (int) sRes[1];
    } else {
     size = (wire == 1) ? 8 : 4;
    }
    if (pos + size > data.length) {
     throw new IOException("Dữ liệu máy chủ chính thức bị cắt cụt.");
    }
    byte[] slice = new byte[size];
    System.arraycopy(data, pos, slice, 0, size);
    pos += size;
    pv = new ProtoValue(wire, 0L, slice);
   } else {
    throw new IOException("Dữ liệu máy chủ chính thức có định dạng không hỗ trợ.");
   }
   map.computeIfAbsent(fieldNo, k -> new ArrayList<>()).add(pv);
  }
  return map;
 }

 private static long[] readVarint(byte[] data, int offset) throws IOException {
  long number = 0L;
  int pos = offset;
  for (int shift = 0; shift < 70; shift += 7) {
   if (pos >= data.length) {
    throw new IOException("Dữ liệu máy chủ chính thức bị cắt cụt.");
   }
   int b = data[pos++] & 0xFF;
   number |= (long) (b & 0x7F) << shift;
   if ((b & 0x80) == 0) {
    return new long[]{number, pos};
   }
  }
  throw new IOException("Dữ liệu máy chủ chính thức vượt phạm vi số.");
 }

 static long parseServerDataVersion(byte[] plain) throws IOException {
  Map<Integer, List<ProtoValue>> fields = parseProtobuf(plain);
  List<ProtoValue> f1 = fields.get(1);
  if (f1 == null || f1.isEmpty() || f1.get(0).wire != 0) {
   throw new IOException("Phản hồi máy chủ chính thức thiếu mã phiên bản.");
  }
  return f1.get(0).varint;
 }

 static Map<String, ManifestRef> parseAndHtmlDiff(byte[] plain, String rootUrl) throws IOException {
  Map<Integer, List<ProtoValue>> root = parseProtobuf(plain);
  List<ProtoValue> entries = root.get(1);
  if (entries == null || entries.isEmpty()) {
   throw new IOException("Phản hồi máy chủ chính thức không có danh sách tệp Android.");
  }
  Map<String, ManifestRef> diff = new HashMap<>();
  for (ProtoValue entry : entries) {
   if (entry.wire != 2 || entry.bytes == null) continue;
   Map<Integer, List<ProtoValue>> f = parseProtobuf(entry.bytes);
   String name = protoString(f, 1);
   String checksum = protoString(f, 2);
   Long version = protoVarint(f, 3);
   String folder = protoString(f, 4);
   if (name == null || checksum == null || version == null || folder == null) continue;
   String paddedMd5 = padMd5(checksum);
   String encoded = urlEncodePathSegment(name);
   String url = rootUrl + "/res/and/" + version + "/" + folder + "/" + encoded;
   diff.put(name, new ManifestRef(name, paddedMd5, version, folder, url));
  }
  return diff;
 }

 private static String protoString(Map<Integer, List<ProtoValue>> f, int key) {
  List<ProtoValue> arr = f.get(key);
  if (arr == null || arr.size() != 1 || arr.get(0).wire != 2 || arr.get(0).bytes == null) return null;
  return new String(arr.get(0).bytes, StandardCharsets.UTF_8);
 }

 private static Long protoVarint(Map<Integer, List<ProtoValue>> f, int key) {
  List<ProtoValue> arr = f.get(key);
  if (arr == null || arr.size() != 1 || arr.get(0).wire != 0) return null;
  return arr.get(0).varint;
 }

 private static String padMd5(String raw) {
  String s = raw == null ? "" : raw.trim().toLowerCase(Locale.ROOT);
  StringBuilder sb = new StringBuilder(32);
  while (sb.length() + s.length() < 32) sb.append('0');
  sb.append(s);
  return sb.toString();
 }

 private static String urlEncodePathSegment(String name) {
  try {
   return URLEncoder.encode(name, "UTF-8").replace("+", "%20");
  } catch (Exception e) {
   return name;
  }
 }

 static Map<String, String> parseManifestHeaders(byte[] data) {
  Map<String, String> headers = new LinkedHashMap<>();
  if (data == null || data.length == 0) return headers;
  int sampleLen = Math.min(data.length, 4096);
  String head = new String(data, 0, sampleLen, StandardCharsets.UTF_8);
  String[] lines = head.split("\\r?\\n");
  int limit = Math.min(lines.length, 40);
  for (int i = 0; i < limit; i++) {
   String ln = lines[i].trim();
   if (ln.isEmpty()) continue;
   Matcher m = HEADER_LINE.matcher(ln);
   if (m.find()) {
    String k = m.group(1);
    String v = m.group(2);
    if ("RESOURCE_VER".equals(k)) k = "RES_VER";
    headers.putIfAbsent(k, v);
   }
  }
  return headers;
 }

 static String md5Hex(byte[] data) throws IOException {
  try {
   MessageDigest md = MessageDigest.getInstance("MD5");
   byte[] d = md.digest(data);
   StringBuilder sb = new StringBuilder(32);
   for (byte b : d) sb.append(String.format(Locale.ROOT, "%02x", b));
   return sb.toString();
  } catch (Exception e) {
   throw new IOException("Lỗi nội bộ tính mã kiểm tra MD5.", e);
  }
 }

 static int compareDottedVersions(String a, String b) {
  if (a == null || b == null) return 0;
  String ca = a.trim().replaceFirst("^[vV]", "");
  String cb = b.trim().replaceFirst("^[vV]", "");
  if (!ca.matches("[0-9]+(\\.[0-9]+)*") || !cb.matches("[0-9]+(\\.[0-9]+)*")) return 0;
  String[] pa = ca.split("\\.");
  String[] pb = cb.split("\\.");
  int len = Math.max(pa.length, pb.length);
  for (int i = 0; i < len; i++) {
   long va = i < pa.length ? Long.parseLong(pa[i]) : 0L;
   long vb = i < pb.length ? Long.parseLong(pb[i]) : 0L;
   if (va != vb) return Long.compare(va, vb);
  }
  return 0;
 }

 static boolean isUpdateAvailable(String latestRes, String latestGame, String localRes, String localGame) {
  String lr = latestRes == null ? "" : latestRes.trim();
  String or = localRes == null ? "" : localRes.trim();
  if (lr.matches("[0-9]+") && or.matches("[0-9]+")) {
   try {
    long newR = Long.parseLong(lr);
    long oldR = Long.parseLong(or);
    if (newR > oldR) return true;
    if (newR < oldR) return false;
   } catch (NumberFormatException ignored) {}
  }
  String lg = latestGame == null ? "" : latestGame.trim();
  String og = localGame == null ? "" : localGame.trim();
  if (!lg.isEmpty() && !og.isEmpty() && !"unknown".equalsIgnoreCase(og)) {
   return compareDottedVersions(lg, og) > 0;
  }
  return false;
 }

 // ------------------------------------------------------------------ HTTP + Android state integration

 private static byte[] httpGetBytes(String urlStr, int timeoutMs) throws IOException {
  HttpURLConnection conn = null;
  try {
   URL url = new URL(urlStr);
   conn = (HttpURLConnection) url.openConnection();
   conn.setRequestMethod("GET");
   conn.setConnectTimeout(timeoutMs);
   conn.setReadTimeout(timeoutMs);
   conn.setInstanceFollowRedirects(true);
   conn.setRequestProperty("User-Agent", "StellaSoraVietHoaAndroid/2.0 (official-guard)");
   int status = conn.getResponseCode();
   if (status != 200) {
    throw new IOException("Máy chủ trả HTTP " + status + " (nova-static.stellasora.global).");
   }
   try (InputStream in = conn.getInputStream()) {
    ByteArrayOutputStream out = new ByteArrayOutputStream();
    byte[] buf = new byte[16384];
    int n;
    while ((n = in.read(buf)) != -1) {
     out.write(buf, 0, n);
     if (out.size() > MAX_META_BYTES) {
      throw new IOException("Dữ liệu quá lớn.");
     }
    }
    return out.toByteArray();
   }
  } finally {
   if (conn != null) conn.disconnect();
  }
 }

 /**
  * Reads locally installed Vietnamese patch receipt & journal versions WITHOUT Local ADB.
  * Returns JSONObject with keys: vhModified, localGameVersion, localResourceVersion, translationVersion.
  */
 static JSONObject readInstalledLocalState(Context c) {
  JSONObject out = Store.obj(
    "vhModified", false,
    "localGameVersion", "",
    "localResourceVersion", "",
    "translationVersion", ""
  );
  try {
   File receiptsDir = Store.internal(c, "receipts");
   File[] files = receiptsDir.listFiles((d, name) -> name.matches("[0-9a-f]{64}\\.json"));
   if (files == null || files.length == 0) return out;

   File chosen = files[0];
   for (File f : files) {
    if (f.lastModified() > chosen.lastModified()) chosen = f;
   }
   JSONObject receipt = Store.read(chosen);
   JSONArray rf = receipt.optJSONArray("files");
   if (!Store.GAME.equals(receipt.optString("package")) || rf == null || rf.length() == 0) {
    return out;
   }
   out.put("vhModified", true);
   out.put("translationVersion", receipt.optString("version", ""));

   String jid = receipt.optString("journal_id", "");
   if (jid.matches("[a-f0-9-]{36}")) {
    File jf = Store.internal(c, "journals/" + jid + ".json");
    if (jf.isFile()) {
     JSONObject j = Store.read(jf);
     out.put("localGameVersion", j.optString("gameVersion", ""));
     out.put("localResourceVersion", j.optString("resourceVersion", ""));
    }
   }
  } catch (Exception ignored) {}
  return out;
 }

 /** Reads last persisted official guard evaluation in <1ms (safe for AccessibilityService / LaunchGuard). */
 static JSONObject readCachedGuardState(Context c) {
  JSONObject local = readInstalledLocalState(c);
  boolean vhModified = local.optBoolean("vhModified", false);
  String localGame = local.optString("localGameVersion", "");
  String localRes = local.optString("localResourceVersion", "");

  JSONObject fallback = Store.obj(
    "checked", false,
    "updateAvailable", false,
    "vhModified", vhModified,
    "needsRestore", false,
    "localGameVersion", localGame,
    "localResourceVersion", localRes,
    "latestGameVersion", "",
    "latestResourceVersion", "",
    "serverDataVersion", 0L,
    "checkedAt", 0L,
    "error", ""
  );

  File f = Store.internal(c, GUARD_STATE_FILE);
  if (!f.isFile()) return fallback;
  try {
   JSONObject saved = Store.read(f);
   String latestGame = saved.optString("latestGameVersion", "");
   String latestRes = saved.optString("latestResourceVersion", "");
   // Re-evaluate against live local receipt state (e.g. if user already restored!)
   boolean upd = isUpdateAvailable(latestRes, latestGame, localRes, localGame);
   saved.put("vhModified", vhModified);
   saved.put("localGameVersion", localGame);
   saved.put("localResourceVersion", localRes);
   saved.put("updateAvailable", upd);
   saved.put("needsRestore", vhModified && upd);
   return saved;
  } catch (Exception ignored) {
   return fallback;
  }
 }

 /**
  * Queries official Stella Sora Android CDN (432-byte serverlist fast path) and persists guard state.
  * Can optionally supply detected live local game/res versions (e.g. after ADB detect).
  */
 static JSONObject checkAndSave(Context c, int timeoutMs) throws IOException {
  return checkAndSave(c, timeoutMs, null, null);
 }

 static JSONObject checkAndSave(Context c, int timeoutMs, String overrideLocalGame, String overrideLocalRes) throws IOException {
  long now = System.currentTimeMillis();
  long token = System.nanoTime();
  byte[] slEnc = httpGetBytes(ROOT_URL + "/meta/serverlist.html?nocache=" + token, timeoutMs);
  byte[] slPlain = decryptMetadata(slEnc);
  long serverDataVer = parseServerDataVersion(slPlain);

  JSONObject cache = null;
  File cacheFile = Store.internal(c, CACHE_FILE);
  if (cacheFile.isFile()) {
   try { cache = Store.read(cacheFile); } catch (Exception ignored) {}
  }

  String latestRes = "";
  String latestGame = "";
  String latestClient = "";

  if (cache != null
    && cache.optLong("serverDataVersion", -1L) == serverDataVer
    && !cache.optString("resourceVersion", "").isEmpty()) {
   latestRes = cache.optString("resourceVersion", "");
   latestGame = cache.optString("gameVersion", "");
   latestClient = cache.optString("clientVersion", "");
  } else {
   byte[] andEnc = httpGetBytes(ROOT_URL + "/meta/and.html?nocache=" + System.nanoTime(), timeoutMs);
   byte[] andPlain = decryptMetadata(andEnc);
   Map<String, ManifestRef> diff = parseAndHtmlDiff(andPlain, ROOT_URL);
   ManifestRef baseRef = diff.get("ss_and.mani");
   if (baseRef == null) {
    throw new IOException("Phản hồi máy chủ chính thức thiếu tệp ss_and.mani.");
   }
   byte[] baseBytes = httpGetBytes(baseRef.url, timeoutMs);
   if (!md5Hex(baseBytes).equalsIgnoreCase(baseRef.checksum)) {
    throw new IOException("Tệp tải về không khớp kích thước hoặc SHA256: ss_and.mani");
   }
   Map<String, String> baseHeaders = parseManifestHeaders(baseBytes);
   int patchCount = 0;
   try {
    patchCount = Integer.parseInt(baseHeaders.getOrDefault("BIN_DIFF_PATCH_VER", "0"));
   } catch (NumberFormatException ignored) {}

   Map<String, String> finalHeaders = baseHeaders;
   if (patchCount > 0) {
    String finalName = "p_" + patchCount + "_m.ss_and.mani";
    ManifestRef finalRef = diff.get(finalName);
    if (finalRef != null) {
     byte[] finalBytes = httpGetBytes(finalRef.url, timeoutMs);
     if (!md5Hex(finalBytes).equalsIgnoreCase(finalRef.checksum)) {
      throw new IOException("Tệp tải về không khớp kích thước hoặc SHA256: " + finalName);
     }
     finalHeaders = parseManifestHeaders(finalBytes);
    }
   }

   latestRes = finalHeaders.getOrDefault("RES_VER", baseHeaders.getOrDefault("RES_VER", ""));
   latestGame = finalHeaders.getOrDefault("GAME_VER", baseHeaders.getOrDefault("GAME_VER", ""));
   latestClient = finalHeaders.getOrDefault("CLIENT_VER", baseHeaders.getOrDefault("CLIENT_VER", ""));
   if (latestGame.isEmpty()) latestGame = latestClient;

   try {
    Store.write(cacheFile, Store.obj(
      "serverDataVersion", serverDataVer,
      "resourceVersion", latestRes,
      "gameVersion", latestGame,
      "clientVersion", latestClient,
      "checkedAt", now
    ));
   } catch (Exception ignored) {}
  }

  JSONObject local = readInstalledLocalState(c);
  boolean vhModified = local.optBoolean("vhModified", false);
  String localGame = (overrideLocalGame != null && !overrideLocalGame.isEmpty())
    ? overrideLocalGame : local.optString("localGameVersion", "");
  String localRes = (overrideLocalRes != null && !overrideLocalRes.isEmpty())
    ? overrideLocalRes : local.optString("localResourceVersion", "");

  boolean updateAvailable = isUpdateAvailable(latestRes, latestGame, localRes, localGame);
  boolean needsRestore = vhModified && updateAvailable;

  JSONObject guardState = Store.obj(
    "checked", true,
    "updateAvailable", updateAvailable,
    "vhModified", vhModified,
    "needsRestore", needsRestore,
    "localGameVersion", localGame,
    "localResourceVersion", localRes,
    "latestGameVersion", latestGame,
    "latestResourceVersion", latestRes,
    "serverDataVersion", serverDataVer,
    "checkedAt", now,
    "error", ""
  );
  try {
   Store.write(Store.internal(c, GUARD_STATE_FILE), guardState);
  } catch (Exception ignored) {}
  return guardState;
 }

 /** Clears pending restore guard state & Heads-Up alert after successful restore to vanilla. */
 static void clearGuardAlertAfterRestore(Context c) {
  try {
   JSONObject current = readCachedGuardState(c);
   current.put("vhModified", false);
   current.put("needsRestore", false);
   Store.write(Store.internal(c, GUARD_STATE_FILE), current);
  } catch (Exception ignored) {}
  try { OfficialUpdateNotice.cancel(c); } catch (Exception ignored) {}
 }
}
