package com.stellasora.viethoa.localadb;

import android.content.Context;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.BufferedInputStream;
import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
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

 static final class FileEntry {
  final String name;
  final String checksum;
  final long size;
  final String packageTag;

  FileEntry(String name, String checksum, long size) {
   this(name, checksum, size, "");
  }

  FileEntry(String name, String checksum, long size, String packageTag) {
   this.name = name;
   this.checksum = checksum;
   this.size = size;
   this.packageTag = packageTag == null ? "" : packageTag;
  }
 }

 static final class PatchEntry {
  final String name;
  final String checksum;
  final long size;
  final String oldChecksum;
  final String kind;

  PatchEntry(String name, String checksum, long size, String oldChecksum, String kind) {
   this.name = name;
   this.checksum = checksum;
   this.size = size;
   this.oldChecksum = oldChecksum;
   this.kind = kind;
  }
 }

 static final class ParsedManifest {
  final Map<String, String> headers;
  final Map<String, FileEntry> files;
  final Map<String, PatchEntry> patches;

  ParsedManifest(Map<String, String> headers, Map<String, FileEntry> files, Map<String, PatchEntry> patches) {
   this.headers = headers;
   this.files = files;
   this.patches = patches;
  }
 }

 static final class PatchStep {
  final int step;
  final String resVer;
  final Set<String> targets;

  PatchStep(int step, String resVer, Set<String> targets) {
   this.step = step;
   this.resVer = resVer;
   this.targets = targets;
  }
 }

 interface RestoreProgress {
  void onStatus(String message);
 }

 static final class AndroidCatalog {
  final long serverDataVersion;
  final String baseResVersion;
  final String latestGameVersion;
  final String latestResourceVersion;
  final Map<String, ManifestRef> diff;
  final Map<String, FileEntry> baseFiles;
  final Map<String, FileEntry> finalFiles;
  final Map<String, FileEntry> versions; // key = name + "\0" + checksum
  final Map<String, PatchEntry> patchIndex; // key = name + "\0" + newChecksum
  final List<PatchStep> patchSteps;

  AndroidCatalog(
    long serverDataVersion,
    String baseResVersion,
    String latestGameVersion,
    String latestResourceVersion,
    Map<String, ManifestRef> diff,
    Map<String, FileEntry> baseFiles,
    Map<String, FileEntry> finalFiles,
    Map<String, FileEntry> versions,
    Map<String, PatchEntry> patchIndex,
    List<PatchStep> patchSteps
  ) {
   this.serverDataVersion = serverDataVersion;
   this.baseResVersion = baseResVersion;
   this.latestGameVersion = latestGameVersion;
   this.latestResourceVersion = latestResourceVersion;
   this.diff = diff;
   this.baseFiles = baseFiles;
   this.finalFiles = finalFiles;
   this.versions = versions;
   this.patchIndex = patchIndex;
   this.patchSteps = patchSteps;
  }

  static String vKey(String name, String checksum) {
   return name + "\0" + checksum.toLowerCase(Locale.ROOT);
  }

  boolean knows(String name, String checksum) {
   return versions.containsKey(vKey(name, checksum));
  }

  Integer stepForResourceVersion(String localResVer) {
   String lr = localResVer == null ? "" : localResVer.trim();
   if (lr.isEmpty()) return null;
   if (lr.equals(baseResVersion)) return 0;
   for (PatchStep st : patchSteps) {
    if (lr.equals(st.resVer)) return st.step;
   }
   return null;
  }

  Set<String> pendingPatchNames(String localResVer) {
   Set<String> out = new LinkedHashSet<>();
   if (patchSteps.isEmpty()) return out;
   String lr = localResVer == null ? "" : localResVer.trim();
   if (!lr.isEmpty() && lr.equals(latestResourceVersion)) return out;
   if (lr.matches("[0-9]+") && latestResourceVersion != null && latestResourceVersion.matches("[0-9]+")) {
    try {
     if (Long.parseLong(lr) >= Long.parseLong(latestResourceVersion)) return out;
    } catch (NumberFormatException ignored) {}
   }
   Integer exact = stepForResourceVersion(lr);
   int localStep = 0;
   if (exact != null) {
    localStep = exact;
   } else if (lr.matches("[0-9]+")) {
    try {
     long lrVal = Long.parseLong(lr);
     for (PatchStep st : patchSteps) {
      if (st.resVer != null && st.resVer.matches("[0-9]+")) {
       long sv = Long.parseLong(st.resVer);
       if (sv <= lrVal && st.step > localStep) localStep = st.step;
      }
     }
    } catch (NumberFormatException ignored) {}
   }
   for (PatchStep st : patchSteps) {
    if (st.step > localStep) out.addAll(st.targets);
   }
   return out;
  }

  File materialize(String name, String checksum, File cacheDir, int timeoutMs, RestoreProgress progress) throws IOException {
   return materializeInternal(name, checksum.toLowerCase(Locale.ROOT), cacheDir, timeoutMs, progress, new HashSet<>());
  }

  private File materializeInternal(String name, String checksum, File cacheDir, int timeoutMs, RestoreProgress progress, Set<String> trail) throws IOException {
   String key = vKey(name, checksum);
   if (!trail.add(key)) {
    throw new IOException("Chuỗi bản vá máy chủ chính thức bị tuần hoàn: " + name);
   }
   if (trail.size() > 64) {
    throw new IOException("Chuỗi bản vá máy chủ chính thức quá sâu: " + name);
   }
   try {
    FileEntry rec = versions.get(key);
    if (rec == null) {
     throw new IOException("Máy chủ Yostar không còn lưu phiên bản " + name + " (" + checksum.substring(0, Math.min(8, checksum.length())) + "…).");
    }
    File finalDir = new File(cacheDir, "final");
    File inputDir = new File(cacheDir, "inputs");
    if (!finalDir.isDirectory() && !finalDir.mkdirs()) throw new IOException("Không tạo được thư mục đệm tải gốc.");
    if (!inputDir.isDirectory() && !inputDir.mkdirs()) throw new IOException("Không tạo được thư mục đệm bản vá.");

    File outFile = new File(finalDir, checksum + ".bin");
    if (matchesMd5(outFile, rec.size, checksum)) {
     return outFile;
    }

    ManifestRef direct = diff.get(name);
    if (direct != null && checksum.equalsIgnoreCase(direct.checksum)) {
     if (progress != null) progress.onStatus("Đang tải bản gốc: " + name);
     downloadVerifiedFile(direct.url, outFile, rec.size, checksum, timeoutMs);
     return outFile;
    }

    PatchEntry patch = patchIndex.get(key);
    if (patch == null) {
     throw new IOException("Không dựng được bản gốc " + name + " (" + checksum.substring(0, Math.min(8, checksum.length())) + "…) từ máy chủ Yostar.");
    }
    ManifestRef remote = diff.get(patch.name);
    if (remote == null || !patch.checksum.equalsIgnoreCase(remote.checksum)) {
     throw new IOException("Dữ liệu bản vá máy chủ Yostar không khớp: " + patch.name);
    }
    if ("N".equals(patch.kind)) {
     if (!checksum.equalsIgnoreCase(remote.checksum)) {
      throw new IOException("Tệp mới máy chủ Yostar không khớp MD5: " + name);
     }
     if (progress != null) progress.onStatus("Đang tải bản gốc: " + name);
     downloadVerifiedFile(remote.url, outFile, rec.size, checksum, timeoutMs);
     return outFile;
    }
    if (!"U".equals(patch.kind)) {
     throw new IOException("Kiểu bản vá chưa hỗ trợ: " + patch.kind);
    }

    File baseFile = materializeInternal(name, patch.oldChecksum, cacheDir, timeoutMs, progress, trail);
    File deltaFile = new File(inputDir, patch.checksum + ".delta");
    if (!matchesMd5(deltaFile, patch.size, patch.checksum)) {
     if (progress != null) progress.onStatus("Đang tải bản vá gốc: " + name);
     downloadVerifiedFile(remote.url, deltaFile, patch.size, patch.checksum, timeoutMs);
    }
    File tmpOut = new File(finalDir, ".rebuild_" + UUID.randomUUID().toString().replace("-", "") + ".tmp");
    try {
     if (progress != null) progress.onStatus("Đang dựng lại bản gốc: " + name);
     Bsdiff40.apply(baseFile, deltaFile, tmpOut, rec.size);
     if (!matchesMd5(tmpOut, rec.size, checksum)) {
      throw new IOException("Bản gốc dựng lại không khớp MD5: " + name);
     }
     if (outFile.exists()) outFile.delete();
     if (!tmpOut.renameTo(outFile)) {
      throw new IOException("Không thể lưu tệp bản gốc sau khi dựng: " + name);
     }
    } finally {
     if (tmpOut.exists()) tmpOut.delete();
     if (deltaFile.exists()) deltaFile.delete();
    }
    return outFile;
   } finally {
    trail.remove(key);
   }
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

 /** Reads last persisted official guard evaluation in <1ms (safe for LaunchGuard). */
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

 private static final Pattern PATCH_NAME_RE = Pattern.compile("^p_\\d+_[un]\\.(.+)$");
 private static final Pattern SAFE_SIMPLE_NAME_RE = Pattern.compile("^[A-Za-z0-9_. -]+$");
 private static final Pattern SAFE_VIDEO_NAME_RE = Pattern.compile("^[^/<>:\"|?*]+$");

 /** Maps ANY Stella Sora manifest filename 1:1 to its Persistent_Store relative path (null if invalid). */
 static String officialRelativePath(String name) {
  if (name == null || name.isEmpty() || !name.equals(name.trim()) || name.contains("/") || name.contains("\\") || name.contains("..") || name.contains(":")) return null;
  for (int i = 0; i < name.length(); i++) {
   if (name.charAt(i) < 32) return null;
  }
  if ("data.arcx".equals(name)) return "Persistent_Store/Tables/data.arcx";
  if ("lua.arcx".equals(name) || "hotfix.arch".equals(name)) return "Persistent_Store/Scripts/" + name;
  if (name.endsWith(".srt") || name.endsWith(".mp4") || name.endsWith(".config")) {
   return SAFE_VIDEO_NAME_RE.matcher(name).matches() ? "Persistent_Store/Videos/" + name : null;
  }
  if (!SAFE_SIMPLE_NAME_RE.matcher(name).matches()) return null;
  if (name.endsWith(".media.wem")) {
   String stem = name.substring(0, name.length() - 10);
   return stem.isEmpty() ? null : "Persistent_Store/SoundBanks/Media/" + stem + ".wem";
  }
  if (name.endsWith(".cn.bnk")) {
   String stem = name.substring(0, name.length() - 7);
   return stem.isEmpty() ? null : "Persistent_Store/SoundBanks/Chinese/" + stem + ".bnk";
  }
  if (name.endsWith(".en.bnk")) {
   String stem = name.substring(0, name.length() - 7);
   return stem.isEmpty() ? null : "Persistent_Store/SoundBanks/English/" + stem + ".bnk";
  }
  if (name.endsWith(".jp.bnk")) {
   String stem = name.substring(0, name.length() - 7);
   return stem.isEmpty() ? null : "Persistent_Store/SoundBanks/Japanese/" + stem + ".bnk";
  }
  if (name.endsWith(".bnk") || name.endsWith(".wem")) {
   return "Persistent_Store/SoundBanks/" + name;
  }
  if (name.endsWith(".unity3d")) return "Persistent_Store/AssetBundles/" + name;
  return null;
 }

 /** Exact inverse of officialRelativePath(): maps Persistent_Store/<subpath> back to its manifest key. */
 static String manifestNameFromRelativePath(String rel) {
  if (rel == null || rel.isEmpty()) return null;
  String norm = rel.replace('\\', '/');
  while (norm.startsWith("/")) norm = norm.substring(1);
  String sub = norm.startsWith("Persistent_Store/") ? norm.substring("Persistent_Store/".length()) : norm;
  if (sub.isEmpty() || sub.contains("..") || sub.indexOf('/') < 0) return null;
  if ("Tables/data.arcx".equals(sub)) return "data.arcx";
  if ("Scripts/lua.arcx".equals(sub)) return "lua.arcx";
  if ("Scripts/hotfix.arch".equals(sub)) return "hotfix.arch";
  if (sub.startsWith("Videos/")) {
   String f = sub.substring("Videos/".length());
   if (!f.contains("/") && (f.endsWith(".srt") || f.endsWith(".mp4") || f.endsWith(".config"))) return f;
   return null;
  }
  if (sub.startsWith("AssetBundles/")) {
   String f = sub.substring("AssetBundles/".length());
   if (!f.contains("/") && f.endsWith(".unity3d")) return f;
   return null;
  }
  if (sub.startsWith("SoundBanks/")) {
   String rest = sub.substring("SoundBanks/".length());
   int slash = rest.indexOf('/');
   if (slash < 0) {
    return (rest.endsWith(".bnk") || rest.endsWith(".wem")) ? rest : null;
   }
   String folder = rest.substring(0, slash);
   String f = rest.substring(slash + 1);
   if (f.contains("/")) return null;
   if ("Media".equals(folder) && f.endsWith(".wem") && f.length() > 4) {
    return f.substring(0, f.length() - 4) + ".media.wem";
   }
   if ("Chinese".equals(folder) && f.endsWith(".bnk") && f.length() > 4) {
    return f.substring(0, f.length() - 4) + ".cn.bnk";
   }
   if ("English".equals(folder) && f.endsWith(".bnk") && f.length() > 4) {
    return f.substring(0, f.length() - 4) + ".en.bnk";
   }
   if ("Japanese".equals(folder) && f.endsWith(".bnk") && f.length() > 4) {
    return f.substring(0, f.length() - 4) + ".jp.bnk";
   }
   return null;
  }
  return null;
 }

 static Set<String> parsePrefsPackageTags(String prefsText) {
  Set<String> tags = new LinkedHashSet<>();
  if (prefsText == null || prefsText.isEmpty()) return tags;
  for (String line : prefsText.split("\\r?\\n")) {
   if (line.startsWith("PACKAGE_TAGS:")) {
    String raw = line.substring("PACKAGE_TAGS:".length()).trim();
    for (String t : raw.split("\\|")) {
     String clean = t.trim();
     if (!clean.isEmpty()) tags.add(clean);
    }
    break;
   }
  }
  return tags;
 }

 /** Returns updated prefs.dat text if LOCAL_BIN_DIFF_PATCH_RESOURCE_VERSION > expectedStep, else null. */
 static String syncPrefsPatchVersionText(String prefsText, int expectedStep) {
  if (prefsText == null || prefsText.isEmpty() || expectedStep < 0) return null;
  String[] lines = prefsText.split("\\r?\\n");
  boolean changed = false;
  StringBuilder out = new StringBuilder();
  for (String line : lines) {
   if (line.startsWith("LOCAL_BIN_DIFF_PATCH_RESOURCE_VERSION:")) {
    String raw = line.substring("LOCAL_BIN_DIFF_PATCH_RESOURCE_VERSION:".length()).trim();
    if (raw.matches("[0-9]+")) {
     try {
      if (Integer.parseInt(raw) > expectedStep) {
       out.append("LOCAL_BIN_DIFF_PATCH_RESOURCE_VERSION:").append(expectedStep).append('\n');
       changed = true;
       continue;
      }
     } catch (NumberFormatException ignored) {}
    }
   }
   out.append(line).append('\n');
  }
  return changed ? out.toString() : null;
 }

 static final class FileVersionsAudit {
  final Set<String> allRels;
  final Set<String> mismatchedRels;
  final Set<String> strayNewRels;

  FileVersionsAudit(Set<String> allRels, Set<String> mismatchedRels, Set<String> strayNewRels) {
   this.allRels = allRels;
   this.mismatchedRels = mismatchedRels;
   this.strayNewRels = strayNewRels;
  }
 }

 static FileVersionsAudit auditFileVersionsText(String rawText, Map<String, FileEntry> localFiles, Set<String> pendingNames) {
  Set<String> allRels = new LinkedHashSet<>();
  Set<String> mismatched = new LinkedHashSet<>();
  Set<String> strayNew = new LinkedHashSet<>();
  if (rawText == null || rawText.isEmpty()) return new FileVersionsAudit(allRels, mismatched, strayNew);
  String text = rawText.charAt(0) == '\uFEFF' ? rawText.substring(1) : rawText;
  for (String line : text.split("\\r?\\n")) {
   String s = line.trim();
   int pipe = s.indexOf('|');
   if (pipe <= 0) continue;
   String rawPath = s.substring(0, pipe);
   String val = s.substring(pipe + 1).trim();
   String norm = rawPath.replace('\\', '/');
   while (norm.startsWith("/")) norm = norm.substring(1);
   if (norm.equals("Persistent_Store/ss_and.mani") || norm.equals("Persistent_Store/ss_win.mani")) continue;
   allRels.add(norm);
   String mname = manifestNameFromRelativePath(norm);
   if (mname == null) continue;
   FileEntry rec = localFiles.get(mname);
   if (rec == null) {
    if (pendingNames != null && pendingNames.contains(mname)) strayNew.add(norm);
   } else if (!rec.checksum.equalsIgnoreCase(val)) {
    mismatched.add(norm);
   }
  }
  return new FileVersionsAudit(allRels, mismatched, strayNew);
 }

 static final class SyncedFileVersions {
  final String text;
  final int changes;

  SyncedFileVersions(String text, int changes) {
   this.text = text;
   this.changes = changes;
  }
 }

 static SyncedFileVersions buildSyncedFileVersionsText(
   String rawText,
   String localResVer,
   Map<String, FileEntry> localFiles,
   Map<String, String> verifiedRelToMd5,
   Set<String> deletedRels,
   Set<String> existingRelsOrNull,
   String manifestRel
 ) {
  if (rawText == null) return new SyncedFileVersions(null, 0);
  String text = (!rawText.isEmpty() && rawText.charAt(0) == '\uFEFF') ? rawText.substring(1) : rawText;
  char sep = '/';
  boolean detectedSep = false;
  LinkedHashMap<String, String> ordered = new LinkedHashMap<>();
  for (String line : text.split("\\r?\\n")) {
   String s = line.trim();
   int pipe = s.indexOf('|');
   if (pipe <= 0) continue;
   String rawPath = s.substring(0, pipe);
   String val = s.substring(pipe + 1).trim();
   if (!detectedSep) {
    if (rawPath.startsWith("\\")) { sep = '\\'; detectedSep = true; }
    else if (rawPath.startsWith("/")) { sep = '/'; detectedSep = true; }
   }
   String norm = rawPath.replace('\\', '/');
   while (norm.startsWith("/")) norm = norm.substring(1);
   ordered.put(norm, val);
  }
  int changes = 0;
  List<String> keys = new ArrayList<>(ordered.keySet());
  for (String rel : keys) {
   if (rel.equals(manifestRel)) continue;
   String mname = manifestNameFromRelativePath(rel);
   if (mname == null) continue;
   FileEntry rec = localFiles.get(mname);
   boolean missingOnDisk = existingRelsOrNull != null
     && !existingRelsOrNull.contains(rel)
     && (verifiedRelToMd5 == null || !verifiedRelToMd5.containsKey(rel));
   if (rec == null || missingOnDisk || !rec.checksum.equalsIgnoreCase(ordered.get(rel))) {
    ordered.remove(rel);
    changes++;
   }
  }
  if (deletedRels != null) {
   for (String del : deletedRels) {
    if (ordered.remove(del) != null) changes++;
   }
  }
  if (verifiedRelToMd5 != null) {
   for (Map.Entry<String, String> e : verifiedRelToMd5.entrySet()) {
    String want = e.getValue().toLowerCase(Locale.ROOT);
    String cur = ordered.get(e.getKey());
    if (cur == null || !cur.equalsIgnoreCase(want)) {
     ordered.put(e.getKey(), want);
     changes++;
    }
   }
  }
  if (manifestRel != null && !manifestRel.isEmpty() && localResVer != null && !localResVer.isEmpty()) {
   if (!localResVer.equals(ordered.get(manifestRel))) {
    ordered.put(manifestRel, localResVer);
    changes++;
   }
  }
  if (changes == 0) return new SyncedFileVersions(null, 0);
  StringBuilder out = new StringBuilder(ordered.size() * 64);
  for (Map.Entry<String, String> e : ordered.entrySet()) {
   out.append(sep).append(e.getKey().replace('/', sep)).append('|').append(e.getValue()).append('\n');
  }
  return new SyncedFileVersions(out.toString(), changes);
 }

 static ParsedManifest parseManifestFull(byte[] data) throws IOException {
  if (data == null || data.length == 0) {
   throw new IOException("Tệp manifest trống.");
  }
  String text = new String(data, StandardCharsets.UTF_8);
  if (!text.isEmpty() && text.charAt(0) == '\uFEFF') {
   text = text.substring(1);
  }
  Map<String, String> headers = new LinkedHashMap<>();
  Map<String, FileEntry> files = new LinkedHashMap<>();
  Map<String, PatchEntry> patches = new LinkedHashMap<>();
  String[] lines = text.split("\\r?\\n");
  for (String line : lines) {
   if (line.isEmpty()) continue;
   if (line.charAt(0) == '$') {
    int sep = line.indexOf(':');
    if (sep <= 1) continue;
    String key = line.substring(1, sep);
    String val = line.substring(sep + 1);
    if ("BIN_DIFF_PATCH_FILE".equals(key)) {
     String[] p = val.split("\\|");
     if (p.length >= 5) {
      String oldRaw = p[3].startsWith("@") ? p[3].substring(1) : p[3];
      try {
       long pSize = Long.parseLong(p[2]);
       patches.put(p[0], new PatchEntry(p[0], padMd5(p[1]), pSize, padMd5(oldRaw), p[4]));
      } catch (NumberFormatException ignored) {}
     }
    } else if (!"BIN_DIFF_PATCH_INFO".equals(key)) {
     if ("RESOURCE_VER".equals(key)) key = "RES_VER";
     headers.put(key, val);
    }
   } else {
    String[] p = line.split("\\|");
    if (p.length >= 4) {
     try {
      long sz = Long.parseLong(p[2]);
      String pkgTag = p.length >= 5 ? p[4].trim() : "";
      files.put(p[0], new FileEntry(p[0], padMd5(p[1]), sz, pkgTag));
     } catch (NumberFormatException ignored) {}
    }
   }
  }
  return new ParsedManifest(headers, files, patches);
 }

 static String md5File(File file) throws IOException {
  try (InputStream in = new BufferedInputStream(new FileInputStream(file), 65536)) {
   MessageDigest md = MessageDigest.getInstance("MD5");
   byte[] buf = new byte[65536];
   int n;
   while ((n = in.read(buf)) != -1) {
    md.update(buf, 0, n);
   }
   byte[] d = md.digest();
   StringBuilder sb = new StringBuilder(32);
   for (byte b : d) sb.append(String.format(Locale.ROOT, "%02x", b));
   return sb.toString();
  } catch (IOException e) {
   throw e;
  } catch (Exception e) {
   throw new IOException("Lỗi nội bộ tính mã kiểm tra MD5.", e);
  }
 }

 static boolean matchesMd5(File file, long expectedSize, String expectedMd5) {
  if (file == null || !file.isFile() || file.length() != expectedSize) return false;
  try {
   return md5File(file).equalsIgnoreCase(expectedMd5);
  } catch (IOException e) {
   return false;
  }
 }

 private static boolean looksLikeHtml(byte[] buf, int len) {
  int i = 0;
  if (len >= 3 && (buf[0] & 0xFF) == 0xEF && (buf[1] & 0xFF) == 0xBB && (buf[2] & 0xFF) == 0xBF) i = 3;
  while (i < len && (buf[i] == ' ' || buf[i] == '\t' || buf[i] == '\r' || buf[i] == '\n')) i++;
  if (i >= len || buf[i] != '<') return false;
  String head = new String(buf, i, Math.min(len - i, 128), StandardCharsets.US_ASCII).toLowerCase(Locale.ROOT);
  return head.startsWith("<!doctype html") || head.startsWith("<html") || head.startsWith("<head") || head.startsWith("<body") || head.startsWith("<script");
 }

 static void downloadVerifiedFile(String urlStr, File dest, long expectedSize, String expectedMd5, int timeoutMs) throws IOException {
  if (urlStr == null || (!urlStr.startsWith(ROOT_URL + "/") && !urlStr.equals(ROOT_URL))) {
   throw new IOException("URL không thuộc máy chủ chính thức Yostar: " + urlStr);
  }
  if (matchesMd5(dest, expectedSize, expectedMd5)) return;
  File part = new File(dest.getParentFile(), dest.getName() + ".part");
  IOException lastErr = null;
  for (int attempt = 0; attempt < 3; attempt++) {
   HttpURLConnection conn = null;
   try {
    long offset = part.isFile() ? part.length() : 0L;
    if (offset > expectedSize) {
     part.delete();
     offset = 0L;
    }
    if (expectedSize == 0 || !part.isFile() || offset != expectedSize) {
     URL url = new URL(urlStr);
     conn = (HttpURLConnection) url.openConnection();
     conn.setRequestMethod("GET");
     conn.setConnectTimeout(timeoutMs);
     conn.setReadTimeout(Math.max(timeoutMs, 30000));
     conn.setInstanceFollowRedirects(true);
     conn.setRequestProperty("User-Agent", "StellaSoraVietHoaAndroid/2.1 (official-restore)");
     conn.setRequestProperty("Accept-Encoding", "identity");
     conn.setRequestProperty("Cache-Control", "no-cache");
     if (offset > 0) {
      conn.setRequestProperty("Range", "bytes=" + offset + "-");
     }
     int status = conn.getResponseCode();
     String ct = conn.getContentType();
     if (ct != null && ct.toLowerCase(Locale.ROOT).startsWith("text/html")) {
      throw new IOException("Mạng Wi-Fi đang chuyển hướng sang trang đăng nhập (Captive Portal).");
     }
     boolean append;
     if (offset > 0 && status == 206) {
      append = true;
     } else if (status == 200) {
      offset = 0L;
      append = false;
     } else if (status == 416) {
      part.delete();
      throw new IOException("Dải byte tải tiếp không khớp (HTTP 416).");
     } else {
      throw new IOException("Máy chủ Yostar trả HTTP " + status + ".");
     }
     try (InputStream in = conn.getInputStream();
          FileOutputStream fos = new FileOutputStream(part, append)) {
      byte[] buf = new byte[65536];
      long written = offset;
      boolean checkedHtml = false;
      int n;
      while ((n = in.read(buf)) != -1) {
       if (!checkedHtml) {
        checkedHtml = true;
        if (offset == 0 && looksLikeHtml(buf, n)) {
         throw new IOException("Mạng Wi-Fi đang trả trang đăng nhập (Captive Portal) thay vì tệp game.");
        }
       }
       written += n;
       if (written > expectedSize) {
        part.delete();
        throw new IOException("Tệp tải về vượt kích thước bảng kê Yostar.");
       }
       fos.write(buf, 0, n);
      }
      fos.flush();
     }
    }
    if (!matchesMd5(part, expectedSize, expectedMd5)) {
     part.delete();
     throw new IOException("Tệp tải từ máy chủ Yostar sai MD5 hoặc kích thước.");
    }
    if (dest.exists()) dest.delete();
    if (!part.renameTo(dest)) {
     throw new IOException("Không lưu được tệp tải về vào bộ nhớ đệm.");
    }
    return;
   } catch (IOException e) {
    lastErr = e;
    if (e.getMessage() != null && e.getMessage().contains("Captive Portal")) throw e;
    if (attempt < 2) {
     try { Thread.sleep(1000L * (attempt + 1)); } catch (InterruptedException ie) { Thread.currentThread().interrupt(); throw e; }
    }
   } finally {
    if (conn != null) conn.disconnect();
   }
  }
  throw lastErr != null ? lastErr : new IOException("Không tải được tệp từ máy chủ Yostar.");
 }

 /** Fetches the complete official Android CDN catalog (ss_and.mani + ss_and_add.mani + p_1..p_N) for MD5-verified restore. */
 static AndroidCatalog fetchCatalog(int timeoutMs) throws IOException {
  byte[] slEnc = httpGetBytes(ROOT_URL + "/meta/serverlist.html?nocache=" + System.nanoTime(), timeoutMs);
  long serverVer = parseServerDataVersion(decryptMetadata(slEnc));

  byte[] andEnc = httpGetBytes(ROOT_URL + "/meta/and.html?nocache=" + System.nanoTime(), timeoutMs);
  Map<String, ManifestRef> diff = parseAndHtmlDiff(decryptMetadata(andEnc), ROOT_URL);

  ManifestRef baseRef = diff.get("ss_and.mani");
  if (baseRef == null) {
   throw new IOException("Máy chủ Yostar thiếu tệp ss_and.mani.");
  }
  byte[] baseBytes = httpGetBytes(baseRef.url, timeoutMs);
  if (!md5Hex(baseBytes).equalsIgnoreCase(baseRef.checksum)) {
   throw new IOException("Manifest gốc ss_and.mani từ Yostar sai MD5.");
  }
  ParsedManifest base = parseManifestFull(baseBytes);
  int patchCount = 0;
  try {
   patchCount = Integer.parseInt(base.headers.getOrDefault("BIN_DIFF_PATCH_VER", "0"));
  } catch (NumberFormatException ignored) {}

  Map<String, FileEntry> baseFiles = new LinkedHashMap<>(base.files);
  Map<String, FileEntry> versions = new HashMap<>();
  Map<String, PatchEntry> patchIndex = new HashMap<>();
  List<PatchStep> patchSteps = new ArrayList<>();

  for (FileEntry fe : base.files.values()) {
   versions.put(AndroidCatalog.vKey(fe.name, fe.checksum), fe);
  }

  ManifestRef addRef = diff.get("ss_and_add.mani");
  if (addRef != null) {
   byte[] addBytes = httpGetBytes(addRef.url, timeoutMs);
   if (!md5Hex(addBytes).equalsIgnoreCase(addRef.checksum)) {
    throw new IOException("Manifest bổ sung ss_and_add.mani từ Yostar sai MD5.");
   }
   ParsedManifest addM = parseManifestFull(addBytes);
   baseFiles.putAll(addM.files);
   for (FileEntry fe : addM.files.values()) {
    versions.put(AndroidCatalog.vKey(fe.name, fe.checksum), fe);
   }
  }

  ParsedManifest finalMani = base;
  for (int i = 1; i <= patchCount; i++) {
   String mName = "p_" + i + "_m.ss_and.mani";
   ManifestRef mRef = diff.get(mName);
   if (mRef == null) {
    throw new IOException("Máy chủ Yostar thiếu manifest bản vá " + mName);
   }
   byte[] mBytes = httpGetBytes(mRef.url, timeoutMs);
   if (!md5Hex(mBytes).equalsIgnoreCase(mRef.checksum)) {
    throw new IOException("Manifest bản vá " + mName + " từ Yostar sai MD5.");
   }
   ParsedManifest pm = parseManifestFull(mBytes);
   for (FileEntry fe : pm.files.values()) {
    versions.put(AndroidCatalog.vKey(fe.name, fe.checksum), fe);
   }
   Set<String> stepTargets = new LinkedHashSet<>();
   for (Map.Entry<String, PatchEntry> pe : pm.patches.entrySet()) {
    Matcher mt = PATCH_NAME_RE.matcher(pe.getKey());
    if (mt.matches()) {
     String targetName = mt.group(1);
     FileEntry targetRec = pm.files.get(targetName);
     if (targetRec != null) {
      patchIndex.put(AndroidCatalog.vKey(targetName, targetRec.checksum), pe.getValue());
      stepTargets.add(targetName);
     }
    }
   }
   patchSteps.add(new PatchStep(i, pm.headers.getOrDefault("RES_VER", ""), stepTargets));
   if (i == patchCount) finalMani = pm;
  }

  // Verify snapshot did not rotate mid-read
  byte[] slEnc2 = httpGetBytes(ROOT_URL + "/meta/serverlist.html?nocache=" + System.nanoTime(), timeoutMs);
  long serverVer2 = parseServerDataVersion(decryptMetadata(slEnc2));
  if (serverVer2 != serverVer) {
   throw new IOException("Máy chủ Yostar vừa cập nhật trong lúc kiểm tra; hãy thử lại sau vài giây.");
  }

  Map<String, FileEntry> finalFiles = new LinkedHashMap<>(baseFiles);
  finalFiles.putAll(finalMani.files);

  String baseRes = base.headers.getOrDefault("RES_VER", "");
  String latestRes = finalMani.headers.getOrDefault("RES_VER", baseRes);
  String latestGame = finalMani.headers.getOrDefault("GAME_VER", base.headers.getOrDefault("GAME_VER", ""));
  if (latestGame.isEmpty()) latestGame = finalMani.headers.getOrDefault("CLIENT_VER", "");

  return new AndroidCatalog(
    serverVer, baseRes, latestGame, latestRes,
    diff, baseFiles, finalFiles, versions, patchIndex, patchSteps
  );
 }

 /**
  * Streams a device-side {@code find ... -exec stat -c '%s %n' {} +} output file written directly to
  * staging storage (avoiding the 128 KiB ADB Binder stdout limit), recording every valid official
  * relative path, any size mismatches against {@code localFiles}, and top-level language bundles/subtitles.
  */
 static int parseDeviceTreeScanFile(
   File file,
   String prefix,
   Map<String, FileEntry> localFiles,
   Set<String> existing,
   List<String> mismatches,
   List<String> languageRels
 ) throws IOException {
  if (file == null || !file.isFile()) return 0;
  int parsed = 0;
  try (BufferedReader br = new BufferedReader(new InputStreamReader(new FileInputStream(file), StandardCharsets.UTF_8), 32768)) {
   String line;
   while ((line = br.readLine()) != null) {
    int sp = line.indexOf(' ');
    if (sp <= 0 || sp + 1 >= line.length()) continue;
    String szStr = line.substring(0, sp).trim();
    if (!szStr.matches("[0-9]+")) continue;
    String full = line.substring(sp + 1);
    while (full.endsWith("\r")) full = full.substring(0, full.length() - 1);
    if (!full.startsWith(prefix)) continue;
    String rel = full.substring(prefix.length());
    String mname;
    if ("Persistent_Store/Scripts/Hotfix.dll".equals(rel)) {
     mname = null;
    } else {
     mname = manifestNameFromRelativePath(rel);
     if (mname == null) continue;
     String canonical = officialRelativePath(mname);
     if (canonical == null || !canonical.equals(rel)) continue;
    }
    parsed++;
    if (existing != null) existing.add(rel);
    if (languageRels != null) {
     if ((rel.startsWith("Persistent_Store/AssetBundles/") && rel.endsWith(".en.unity3d")
        && rel.indexOf('/', "Persistent_Store/AssetBundles/".length()) < 0)
       || (rel.startsWith("Persistent_Store/Videos/") && rel.endsWith(".srt")
        && rel.indexOf('/', "Persistent_Store/Videos/".length()) < 0)) {
      languageRels.add(rel);
     }
    }
    if (mname != null && localFiles != null && mismatches != null) {
     FileEntry rec = localFiles.get(mname);
     if (rec != null) {
      try {
       long actualSize = Long.parseLong(szStr);
       if (actualSize != rec.size) {
        mismatches.add(rel);
       }
      } catch (NumberFormatException ignored) {}
     }
    }
   }
  }
  return parsed;
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
