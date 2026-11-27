package com.stellasora.viethoa.localadb;
import android.content.*;
import android.os.*;
import org.json.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.util.*;
import java.util.regex.*;
import java.util.zip.*;

/** Android-only transaction client. Commands are generated here, never supplied by JS. */
final class GamePatcher {
 private static final Set<String> TERMINAL_STATES = Collections.unmodifiableSet(
   new HashSet<>(Arrays.asList("DONE", "RESTORED", "ROLLED_BACK", "ABORTED", "SUPERSEDED"))
 );
 private static final int STATE_BATCH_SIZE = 25;
 private static final int BACKUP_BATCH_SIZE = 10;

 private final Context context;
 private final AdbClient adb;
 private final ChannelClient.Progress progress;
 private JSONObject target;
 private long deadline;
 private String verifiedExternalBase;

 boolean hasTarget() { return target != null; }

 GamePatcher(Context c, AdbClient a, ChannelClient.Progress p) {
  context = c;
  adb = a;
  progress = p;
 }

 static String relative(String path) throws IOException {
  if (path.isEmpty() || !path.equals(path.trim()) || path.startsWith("/") || path.contains("\\") || path.contains(":")) {
   throw new IOException("Đường dẫn tệp Android không hợp lệ.");
  }
  for (String piece : path.split("/", -1)) {
   if (piece.isEmpty() || piece.equals(".") || piece.equals("..")) throw new IOException("Đường dẫn vượt phạm vi.");
  }
  for (char ch : path.toCharArray()) {
   if (ch < 32) throw new IOException("Đường dẫn chứa ký tự điều khiển.");
  }
  boolean allowed = path.equals("Persistent_Store/Tables/data.arcx")
    || path.equals("Persistent_Store/Scripts/lua.arcx")
    || path.matches("Persistent_Store/Videos/[^/<>:\"|?*]+\\.srt")
    || path.matches("Persistent_Store/AssetBundles/[A-Za-z0-9_.-]+\\.unity3d");
  if (!allowed) throw new IOException("Tệp không thuộc phạm vi Android được phép: " + path);
  return path;
 }

 static String relativeOfficial(String path) throws IOException {
  if (path == null || path.isEmpty() || !path.equals(path.trim()) || path.startsWith("/") || path.contains("\\") || path.contains(":")) {
   throw new IOException("Đường dẫn tệp khôi phục gốc không hợp lệ.");
  }
  for (String piece : path.split("/", -1)) {
   if (piece.isEmpty() || piece.equals(".") || piece.equals("..")) throw new IOException("Đường dẫn vượt phạm vi.");
  }
  for (char ch : path.toCharArray()) {
   if (ch < 32) throw new IOException("Đường dẫn chứa ký tự điều khiển.");
  }
  boolean allowed = path.equals("Persistent_Store/Tables/data.arcx")
    || path.equals("Persistent_Store/Scripts/lua.arcx")
    || path.equals("Persistent_Store/Scripts/hotfix.arch")
    || path.equals("Persistent_Store/Scripts/Hotfix.dll")
    || path.matches("Persistent_Store/Videos/[^/<>:\"|?*]+\\.(srt|mp4|config)")
    || path.matches("Persistent_Store/AssetBundles/[A-Za-z0-9_. -]+\\.unity3d")
    || path.matches("Persistent_Store/SoundBanks/[A-Za-z0-9_. -]+\\.(bnk|wem)")
    || path.matches("Persistent_Store/SoundBanks/(Media|Chinese|English|Japanese)/[A-Za-z0-9_. -]+\\.(bnk|wem)");
  if (!allowed) throw new IOException("Tệp không thuộc phạm vi khôi phục gốc được phép: " + path);
  return path;
 }

 private static boolean isSafeFuseAlias(String resolved, String expected, String requiredSuffix) {
  if (resolved == null || resolved.isEmpty()) return false;
  if (resolved.equals(expected)) return true;
  if (!resolved.endsWith(requiredSuffix)) return false;
  return resolved.startsWith("/data/media/")
    || resolved.startsWith("/mnt/pass_through/")
    || resolved.startsWith("/mnt/user/")
    || resolved.startsWith("/storage/emulated/");
 }

 private static String parseUserNumber(String raw) {
  if (raw == null) return "";
  String[] lines = raw.split("\\r?\\n");
  for (int i = lines.length - 1; i >= 0; i--) {
   String t = lines[i].trim();
   if (t.matches("[0-9]+")) return t;
  }
  return "";
 }

 JSONObject detect() throws Exception {
  if (!adb.verified) throw new StellaException("E-ADB-NOT-CONNECTED", "Chưa kết nối Local ADB.", null);
  String user = parseUserNumber(adb.exec("am get-current-user", 10000));
  if (user.isEmpty()) throw new IOException("Chưa xác định được người dùng Android.");
  String installed = adb.exec("pm path --user " + user + " " + Store.GAME + " || true", 12000);
  if (!installed.contains("package:")) {
   String other = "";
   try {
    String allPkgs = adb.exec("pm list packages --user " + user + " 2>/dev/null | grep -i -E 'stellasora|stella_sora' || true", 10000);
    for (String ln : allPkgs.split("\\r?\\n")) {
     String t = ln.trim().replaceFirst("^package:", "");
     if (!t.isEmpty() && !Store.GAME.equals(t)) { other = t; break; }
    }
   } catch (Exception ignored) {}
   if (!other.isEmpty()) {
    target = Store.obj("installed", false, "package", Store.GAME, "wrongEdition", other, "versionsKnown", false,
      "reason", "Phát hiện Stella Sora bản khu vực khác (" + other + "), không phải bản Global EN (com.YoStarEN.StellaSora).");
    return target;
   }
   target = Store.obj("installed", false, "package", Store.GAME, "versionsKnown", false, "reason", "Chưa tìm thấy gói Stella Sora Android.");
   return target;
  }
  String suffix = "/Android/data/" + Store.GAME + "/files";
  String expected = "/storage/emulated/" + user + suffix;
  String qExp = Store.q(expected);
  String qPkgDir = Store.q("/storage/emulated/" + user + "/Android/data/" + Store.GAME);
  String qDataDir = Store.q("/storage/emulated/" + user + "/Android/data");
  String qAndDir = Store.q("/storage/emulated/" + user + "/Android");
  String rootCheck = adb.exec(
    "if [ -L " + qAndDir + " ] || [ -L " + qDataDir + " ] || [ -L " + qPkgDir + " ] || [ -L " + qExp + " ]; then printf 'ERR:SYMLINK'; exit 0; fi; "
    + "if [ ! -e " + qExp + " ]; then printf 'ERR:NODATA'; exit 0; fi; "
    + "if [ ! -d " + qExp + " ]; then printf 'ERR:NOTDIR'; exit 0; fi; "
    + "readlink -f " + qExp, 10000).trim();
  if ("ERR:NODATA".equals(rootCheck)) {
   target = Store.obj("installed", true, "package", Store.GAME, "root", expected, "user", user, "noData", true, "versionsKnown", false,
     "gameVersion", "", "resourceVersion", "",
     "reason", "Chưa thấy thư mục dữ liệu game. Hãy mở Stella Sora 1 lần để game tải dữ liệu, thoát hẳn game rồi kiểm tra lại.");
   return target;
  }
  if ("ERR:SYMLINK".equals(rootCheck) || "ERR:NOTDIR".equals(rootCheck) || !isSafeFuseAlias(rootCheck, expected, suffix)) {
   throw new StellaException("E-GAME-ROOT-CHANGED", "Thư mục dữ liệu game không khớp vùng Android đã chọn.", null);
  }
  String root = expected;
  String androidId = adb.exec("settings --user " + user + " get secure android_id", 10000).trim();
  String device = adb.exec("getprop ro.product.device", 10000).trim();
  if (!androidId.matches("[0-9a-fA-F]{16}")) {
   String lowAid = androidId.toLowerCase(Locale.ROOT);
   if (lowAid.contains("securityexception") || lowAid.contains("permission") || lowAid.contains("denied")) {
    throw new StellaException("E-ADB-PERM", "Hệ điều hành đang chặn quyền đọc thông số Local ADB (SecurityException).", null);
   }
   String fp = adb.exec("getprop ro.build.fingerprint", 10000).trim();
   if (fp.isEmpty() || device.trim().isEmpty()) {
    throw new IOException("Chưa xác định được danh tính thiết bị.");
   }
   androidId = Store.digest("fallback|" + fp + "|" + device + "|" + user).substring(0, 16);
  }
  if (device.trim().isEmpty()) {
   throw new IOException("Chưa xác định được danh tính thiết bị.");
  }
  String deviceId = Store.digest(androidId + "|" + device + "|" + user);
  target = Store.obj("installed", true, "package", Store.GAME, "root", root, "user", user, "deviceId", deviceId, "versionsKnown", false, "gameVersion", "", "resourceVersion", "");
  String psCheck = adb.exec("if [ -L " + Store.q(root + "/Persistent_Store") + " ]; then printf 'ERR:LINK'; elif [ ! -d " + Store.q(root + "/Persistent_Store") + " ]; then printf 'ERR:NODATA'; else printf 'OK'; fi", 10000).trim();
  if ("ERR:NODATA".equals(psCheck)) {
   target.put("noData", true);
   target.put("reason", "Chưa thấy thư mục dữ liệu game (Persistent_Store). Hãy mở Stella Sora tải đủ tài nguyên trước khi cài.");
   return target;
  }
  if (!"OK".equals(psCheck)) {
   throw new StellaException("E-GAME-ROOT-CHANGED", "Thư mục dữ liệu game không khớp vùng Android đã chọn.", null);
  }
  String listing = adb.exec("find " + Store.q(root + "/Persistent_Store") + " -maxdepth 1 -type f -name '*.mani' -print", 10000);
  String chosen = null, game = null, resource = null;
  Map<String, String> maniByName = new LinkedHashMap<>();
  for (String file : listing.split("\\r?\\n")) {
   file = file.trim();
   if (!file.startsWith(root + "/Persistent_Store/")) continue;
   String baseName = file.substring(file.lastIndexOf('/') + 1);
   if (!baseName.matches("[A-Za-z0-9_.-]+\\.mani")) continue;
   String relMani = file.substring(root.length());
   String resolvedMani = adb.exec("if [ -L " + Store.q(file) + " ]; then printf 'ERR'; else readlink -f " + Store.q(file) + "; fi", 10000).trim();
   if (!isSafeFuseAlias(resolvedMani, file, suffix + relMani)) continue;
   maniByName.put(baseName, file);
  }
  // Authoritative resolution matching Yostar's Android engine:
  // 1) Read ss_and.mani first; if BIN_DIFF_PATCH_VER=N and p_N_m.ss_and.mani exists, prefer its final GAME_VER/RES_VER.
  // 2) Never fail when stale patch manifests (p_*_m.ss_and.mani) or ss_win.mani coexist in Persistent_Store.
  String primaryBase = maniByName.get("ss_and.mani");
  if (primaryBase != null) {
   String baseData = adb.exec("head -n 48 " + Store.q(primaryBase), 10000);
   String baseG = header(baseData, "GAME_VER");
   String baseC = header(baseData, "CLIENT_VER");
   String baseR = header(baseData, "RES_VER");
   if (baseR == null) baseR = header(baseData, "RESOURCE_VER");
   String patchNumRaw = header(baseData, "BIN_DIFF_PATCH_VER");
   String finalFile = primaryBase;
   String finalG = baseG;
   String finalR = baseR;
   if (patchNumRaw != null && patchNumRaw.matches("[0-9]+")) {
    try {
     int patchNum = Integer.parseInt(patchNumRaw);
     if (patchNum > 0) {
      String patchedMani = maniByName.get("p_" + patchNum + "_m.ss_and.mani");
      if (patchedMani != null) {
       String pData = adb.exec("head -n 48 " + Store.q(patchedMani), 10000);
       String pG = header(pData, "GAME_VER");
       String pR = header(pData, "RES_VER");
       if (pR == null) pR = header(pData, "RESOURCE_VER");
       if (pG != null) finalG = pG;
       if (pR != null) {
        finalR = pR;
        finalFile = patchedMani;
       }
      }
     }
    } catch (NumberFormatException ignored) {}
   }
   if (finalG == null) finalG = baseC;
   if (finalG != null && finalR != null) {
    game = finalG;
    resource = finalR;
    chosen = finalFile;
   }
  }
  if (chosen == null) {
   List<String> fallbackFiles = new ArrayList<>(maniByName.values());
   Collections.sort(fallbackFiles, (a, b) -> {
    String al = a.toLowerCase(Locale.ROOT), bl = b.toLowerCase(Locale.ROOT);
    boolean aAnd = al.contains("ss_and"), bAnd = bl.contains("ss_and");
    if (aAnd != bAnd) return aAnd ? -1 : 1;
    boolean aWin = al.contains("ss_win"), bWin = bl.contains("ss_win");
    if (aWin != bWin) return aWin ? 1 : -1;
    return a.compareTo(b);
   });
   String bestFallbackFile = null, bestFallbackG = null, bestFallbackR = null;
   for (String file : fallbackFiles) {
    String data = adb.exec("head -n 48 " + Store.q(file), 10000);
    String g = header(data, "GAME_VER");
    String c = header(data, "CLIENT_VER");
    String r = header(data, "RES_VER");
    if (r == null) r = header(data, "RESOURCE_VER");
    if (r == null) continue;
    if (g != null) {
     game = g;
     resource = r;
     chosen = file;
     break;
    }
    if (c != null && bestFallbackFile == null) {
     bestFallbackFile = file;
     bestFallbackG = c;
     bestFallbackR = r;
    }
   }
   if (chosen == null && bestFallbackFile != null) {
    game = bestFallbackG;
    resource = bestFallbackR;
    chosen = bestFallbackFile;
   }
  }
  if (chosen != null) {
   target.put("gameVersion", game);
   target.put("resourceVersion", resource);
   target.put("versionFile", chosen);
   target.put("versionsKnown", true);
   target.put("binding", Store.digest(deviceId + "|" + Store.GAME + "|" + root));
  } else {
   target.put("reason", "Chưa đọc được GAME_VER/RES_VER thực tế từ tài nguyên Android. Hãy mở game tải đủ dữ liệu trước khi cài.");
  }
  return target;
 }

 private static String header(String data, String key) {
  Matcher m = Pattern.compile("(?m)(?:^|[\\r\\n\\s$|])" + key + "[:=\\s]+([0-9A-Za-z_.-]+)").matcher(data);
  return m.find() ? m.group(1) : null;
 }

 private JSONObject requireTarget() throws Exception {
  JSONObject t = detect();
  if (!t.optBoolean("installed") || !t.optBoolean("versionsKnown")) {
   throw new IOException(t.optString("reason", "Chưa đọc được bản game."));
  }
  return t;
 }

 private void closedAndVersion() throws Exception {
  String root = target.getString("root");
  String versionFile = target.getString("versionFile");
  String suffix = "/Android/data/" + Store.GAME + "/files";
  String verRel = versionFile.startsWith(root) ? versionFile.substring(root.length()) : "";
  String qRoot = Store.q(root), qVer = Store.q(versionFile);
  String cmd = "if [ -L " + qRoot + " ] || [ ! -d " + qRoot + " ]; then printf 'ERR:ROOT'; exit 0; fi; "
    + "r=$(readlink -f " + qRoot + ") || exit $?; "
    + "if command -v pidof >/dev/null 2>&1; then pidof " + Store.GAME + " >/dev/null 2>&1; s=$?; "
    + "if [ \"$s\" -eq 0 ]; then printf 'ERR:RUNNING'; exit 0; "
    + "elif [ \"$s\" -ne 1 ]; then ps -A 2>/dev/null | grep -F " + Store.q(Store.GAME) + " >/dev/null 2>&1 && { printf 'ERR:RUNNING'; exit 0; }; fi; "
    + "else ps -A 2>/dev/null | grep -F " + Store.q(Store.GAME) + " >/dev/null 2>&1 && { printf 'ERR:RUNNING'; exit 0; }; fi; "
    + "if [ -L " + qVer + " ] || [ ! -f " + qVer + " ]; then printf 'ERR:VERFILE'; exit 0; fi; "
    + "rv=$(readlink -f " + qVer + ") || exit $?; "
    + "printf 'OK\\n%s\\n%s\\n' \"$r\" \"$rv\"; head -n 48 " + qVer;
  String out = adb.exec(cmd, 12000);
  if ("ERR:ROOT".equals(out)) throw new IOException("Thư mục game đã đổi.");
  if ("ERR:RUNNING".equals(out)) throw new IOException("Hãy thoát Stella Sora trước khi thay đổi tài nguyên.");
  if ("ERR:VERFILE".equals(out)) throw new IOException("Tệp phiên bản đã thành liên kết hoặc đổi đường dẫn.");
  if (!out.startsWith("OK\n")) throw new IOException("Không kiểm tra được trạng thái game.");
  String[] parts = out.split("\\r?\\n", 4);
  if (parts.length < 4) throw new IOException("Không kiểm tra được trạng thái game.");
  if (!isSafeFuseAlias(parts[1].trim(), root, suffix)) throw new IOException("Thư mục game đã đổi.");
  if (!isSafeFuseAlias(parts[2].trim(), versionFile, suffix + verRel)) throw new IOException("Tệp phiên bản đã thành liên kết hoặc đổi đường dẫn.");
  String data = parts[3].trim();
  String g = header(data, "GAME_VER");
  if (g == null) g = header(data, "CLIENT_VER");
  String r = header(data, "RES_VER");
  if (r == null) r = header(data, "RESOURCE_VER");
  if (!target.getString("gameVersion").equals(g) || !target.getString("resourceVersion").equals(r)) {
   throw new IOException("Game đã cập nhật hoặc chưa đọc được phiên bản. Không ghi đè tài nguyên.");
  }
 }

 private String fullPath(String rel) throws Exception {
  return target.getString("root") + "/" + relative(rel);
 }

 private void verifySafeDirectories(Collection<String> relativePaths) throws Exception {
  String root = target.getString("root");
  String suffix = "/Android/data/" + Store.GAME + "/files";
  LinkedHashSet<String> dirs = new LinkedHashSet<>();
  dirs.add(root);
  for (String rel : relativePaths) {
   String clean = relative(rel);
   String[] pieces = clean.split("/");
   String current = root;
   for (int i = 0; i < pieces.length - 1; i++) {
    current += "/" + pieces[i];
    dirs.add(current);
   }
  }
  StringBuilder cmd = new StringBuilder("for d in");
  for (String d : dirs) cmd.append(' ').append(Store.q(d));
  cmd.append("; do if [ -L \"$d\" ] || [ ! -d \"$d\" ]; then printf 'ERR\\n'; exit 0; fi; readlink -f \"$d\" || exit $?; done");
  String res = adb.exec(cmd.toString(), 15000);
  if (res.startsWith("ERR")) {
   throw new IOException("Đường dẫn dữ liệu có liên kết hoặc thư mục chưa sẵn sàng.");
  }
  String[] resolvedLines = res.isEmpty() ? new String[0] : res.split("\\r?\\n");
  if (resolvedLines.length != dirs.size()) {
   throw new IOException("Đường dẫn dữ liệu có liên kết hoặc thư mục chưa sẵn sàng.");
  }
  int idx = 0;
  for (String d : dirs) {
   String relSuffix = suffix + d.substring(root.length());
   if (!isSafeFuseAlias(resolvedLines[idx++].trim(), d, relSuffix)) {
    throw new IOException("Đường dẫn dữ liệu có liên kết hoặc thư mục chưa sẵn sàng.");
   }
  }
 }

 private List<JSONObject> batchStates(List<String> fullPaths) throws Exception {
  List<JSONObject> all = new ArrayList<>(fullPaths.size());
  for (int start = 0; start < fullPaths.size(); start += STATE_BATCH_SIZE) {
   int end = Math.min(fullPaths.size(), start + STATE_BATCH_SIZE);
   List<String> chunk = fullPaths.subList(start, end);
   StringBuilder cmd = new StringBuilder("i=0; for p in");
   for (String p : chunk) cmd.append(' ').append(Store.q(p));
   cmd.append("; do if [ -L \"$p\" ]; then exit 73; ")
      .append("elif [ -f \"$p\" ]; then s=$(stat -c %s \"$p\") || exit $?; h=$(sha256sum \"$p\") || exit $?; printf '%s F %s %s\\n' \"$i\" \"$s\" \"${h%% *}\"; ")
      .append("elif [ -e \"$p\" ]; then exit 74; ")
      .append("else printf '%s A\\n' \"$i\"; fi; i=$((i+1)); done");
   String raw = adb.exec(cmd.toString(), 120000);
   String[] lines = raw.isEmpty() ? new String[0] : raw.split("\\r?\\n");
   if (lines.length != chunk.size()) throw new IOException("Chưa đối chiếu được kích thước/SHA256.");
   for (int k = 0; k < chunk.size(); k++) {
    String[] tok = lines[k].trim().split("\\s+");
    if (tok.length < 2 || !tok[0].equals(String.valueOf(k))) {
     throw new IOException("Chưa đối chiếu được kích thước/SHA256.");
    }
    if ("A".equals(tok[1]) && tok.length == 2) {
     all.add(Store.obj("exists", false));
    } else if ("F".equals(tok[1]) && tok.length >= 4 && tok[2].matches("[0-9]+") && tok[3].matches("[0-9a-fA-F]{64}")) {
     all.add(Store.obj("exists", true, "size", Long.parseLong(tok[2]), "sha256", tok[3].toLowerCase(Locale.ROOT)));
    } else {
     throw new IOException("Chưa đối chiếu được kích thước/SHA256.");
    }
   }
  }
  return all;
 }

 private static boolean same(JSONObject a, JSONObject b) {
  return a.optBoolean("exists") == b.optBoolean("exists")
    && (!a.optBoolean("exists") || (a.optLong("size", -1) == b.optLong("size", -2) && a.optString("sha256").equals(b.optString("sha256"))));
 }

 private String guard(String path, JSONObject expected) throws Exception {
  String q = Store.q(path);
  if (!expected.getBoolean("exists")) return "[ ! -e " + q + " ] && [ ! -L " + q + " ]";
  return "[ ! -L " + q + " ] && [ -f " + q + " ] && [ \"$(stat -c %s " + q + ")\" = " + Store.q(String.valueOf(expected.getLong("size"))) + " ] && h=$(sha256sum " + q + ") && [ \"${h%% *}\" = " + Store.q(expected.getString("sha256")) + " ]";
 }

 private void applyFileAtomic(JSONObject journal, String id, JSONObject f) throws Exception {
  String relPath = f.getString("path");
  String destination = fullPath(relPath);
  String source = f.getString("source");
  JSONObject before = f.getJSONObject("before");
  JSONObject after = f.getJSONObject("after");
  String temp = destination + ".stella-" + id + ".tmp";
  JSONObject tracked = journal.optJSONObject("temporaries");
  if (tracked == null) {
   tracked = new JSONObject();
   journal.put("temporaries", tracked);
  }
  boolean wasTracked = tracked.optBoolean(temp, false);
  tracked.put(temp, true);
  journal.put("pending", relPath);
  saveJournal(journal);

  String qTemp = Store.q(temp), qSrc = Store.q(source), qDest = Store.q(destination);
  String gBefore = guard(destination, before);
  String gTempAfter = guard(temp, after);
  String gDestAfter = guard(destination, after);
  StringBuilder cmd = new StringBuilder();
  cmd.append("if ! (").append(gBefore).append("); then printf 'ERR:BEFORE'; exit 0; fi; ");
  cmd.append("if [ -L ").append(qTemp).append(" ]; then printf 'ERR:TEMPLINK'; exit 0; fi; ");
  if (!wasTracked) {
   cmd.append("if [ -e ").append(qTemp).append(" ]; then printf 'ERR:UNTRACKED'; exit 0; fi; ");
  } else {
   cmd.append("if [ -e ").append(qTemp).append(" ] && ! (").append(gTempAfter).append("); then rm -f ").append(qTemp).append(" || exit $?; fi; ");
  }
  cmd.append("if [ ! -e ").append(qTemp).append(" ]; then cp ").append(qSrc).append(" ").append(qTemp).append(" || exit $?; ");
  cmd.append("if ! (").append(gTempAfter).append("); then rm -f ").append(qTemp).append("; printf 'ERR:TEMPVERIFY'; exit 0; fi; fi; ");
  cmd.append("if ! (").append(gBefore).append("); then printf 'ERR:BEFORE'; exit 0; fi; ");
  cmd.append("mv -f ").append(qTemp).append(" ").append(qDest).append(" || exit $?; ");
  cmd.append("if ! (").append(gDestAfter).append("); then printf 'ERR:AFTER'; exit 0; fi; ");
  cmd.append("printf 'OK'");

  String res = adb.exec(cmd.toString(), 120000);
  if ("OK".equals(res)) return;
  if ("ERR:BEFORE".equals(res)) throw new IOException("Tệp đã thay đổi trước khi ghi: " + relPath);
  if ("ERR:TEMPLINK".equals(res) || "ERR:UNTRACKED".equals(res)) throw new IOException("Tệp tạm đã tồn tại ngoài nhật ký; giữ nguyên: " + relPath);
  if ("ERR:TEMPVERIFY".equals(res)) throw new IOException("Tệp tạm không khớp nội dung cần cài/phục hồi: " + relPath);
  if ("ERR:AFTER".equals(res)) throw new IOException("Đọc lại sau cài không khớp: " + relPath);
  throw new IOException("Không thể ghi tệp an toàn (" + relPath + "): " + res);
 }

 private void restoreFileAtomic(JSONObject journal, String id, JSONObject f, JSONObject expectedCurrent) throws Exception {
  String relPath = f.getString("path");
  String path = fullPath(relPath);
  JSONObject before = f.getJSONObject("before");
  JSONObject expected = expectedCurrent != null ? expectedCurrent : f.getJSONObject("after");
  String qPath = Store.q(path);
  String gBefore = guard(path, before);
  String gExpected = guard(path, expected);

  if (before.getBoolean("exists")) {
   String backupPath = f.getString("backup");
   String temp = path + ".stella-restore-" + id + ".tmp";
   JSONObject tracked = journal.optJSONObject("temporaries");
   if (tracked == null) {
    tracked = new JSONObject();
    journal.put("temporaries", tracked);
   }
   boolean wasTracked = tracked.optBoolean(temp, false);
   tracked.put(temp, true);
   journal.put("pending", relPath);
   saveJournal(journal);

   String qTemp = Store.q(temp), qBackup = Store.q(backupPath);
   String gTempBefore = guard(temp, before);
   StringBuilder cmd = new StringBuilder();
   cmd.append("if (").append(gBefore).append("); then printf 'OK'; exit 0; fi; ");
   cmd.append("if ! (").append(gExpected).append("); then printf 'ERR:CHANGED'; exit 0; fi; ");
   cmd.append("if [ -L ").append(qTemp).append(" ]; then printf 'ERR:TEMPLINK'; exit 0; fi; ");
   if (!wasTracked) {
    cmd.append("if [ -e ").append(qTemp).append(" ]; then printf 'ERR:UNTRACKED'; exit 0; fi; ");
   } else {
    cmd.append("if [ -e ").append(qTemp).append(" ] && ! (").append(gTempBefore).append("); then rm -f ").append(qTemp).append(" || exit $?; fi; ");
   }
   cmd.append("if [ ! -e ").append(qTemp).append(" ]; then cp ").append(qBackup).append(" ").append(qTemp).append(" || exit $?; ");
   cmd.append("if ! (").append(gTempBefore).append("); then rm -f ").append(qTemp).append("; printf 'ERR:TEMPVERIFY'; exit 0; fi; fi; ");
   cmd.append("if ! (").append(gExpected).append("); then printf 'ERR:CHANGED'; exit 0; fi; ");
   cmd.append("mv -f ").append(qTemp).append(" ").append(qPath).append(" || exit $?; ");
   cmd.append("if ! (").append(gBefore).append("); then printf 'ERR:READBACK'; exit 0; fi; ");
   cmd.append("printf 'OK'");

   String res = adb.exec(cmd.toString(), 120000);
   if ("OK".equals(res)) return;
   if ("ERR:CHANGED".equals(res)) throw new IOException("Tệp đổi trong lúc phục hồi: " + relPath);
   if ("ERR:TEMPLINK".equals(res) || "ERR:UNTRACKED".equals(res)) throw new IOException("Tệp tạm đã tồn tại ngoài nhật ký; giữ nguyên: " + relPath);
   if ("ERR:TEMPVERIFY".equals(res)) throw new IOException("Tệp tạm không khớp nội dung cần cài/phục hồi: " + relPath);
   if ("ERR:READBACK".equals(res)) throw new IOException("Đọc lại phục hồi không khớp: " + relPath);
   throw new IOException("Không thể phục hồi tệp (" + relPath + "): " + res);
  } else {
   journal.put("pending", relPath);
   saveJournal(journal);
   String cmd = "if (" + gBefore + "); then printf 'OK'; exit 0; fi; "
     + "if ! (" + gExpected + "); then printf 'ERR:CHANGED'; exit 0; fi; "
     + "rm -f " + qPath + " || exit $?; "
     + "if ! (" + gBefore + "); then printf 'ERR:READBACK'; exit 0; fi; "
     + "printf 'OK'";
   String res = adb.exec(cmd, 120000);
   if ("OK".equals(res)) return;
   if ("ERR:CHANGED".equals(res)) throw new IOException("Tệp đổi trong lúc phục hồi: " + relPath);
   if ("ERR:READBACK".equals(res)) throw new IOException("Đọc lại phục hồi không khớp: " + relPath);
   throw new IOException("Không thể xoá tệp mới khi phục hồi (" + relPath + "): " + res);
  }
 }

 private void cleanupTemps(JSONObject journal, boolean strictDirs) throws Exception {
  JSONObject tracked = journal.optJSONObject("temporaries");
  if (tracked == null || tracked.length() == 0) return;
  JSONArray files = journal.optJSONArray("files");
  if (files == null || files.length() == 0) return;
  String id = journal.getString("id");
  Set<String> relPaths = new LinkedHashSet<>();
  List<String> candidates = new ArrayList<>();
  for (int i = 0; i < files.length(); i++) {
   String rel = relative(files.getJSONObject(i).getString("path"));
   relPaths.add(rel);
   String full = target.getString("root") + "/" + rel;
   for (String temp : new String[]{full + ".stella-" + id + ".tmp", full + ".stella-restore-" + id + ".tmp"}) {
    if (tracked.optBoolean(temp)) candidates.add(temp);
   }
  }
  if (candidates.isEmpty()) return;
  if (strictDirs) {
   verifySafeDirectories(relPaths);
  } else {
   String root = target.getString("root");
   if (!adb.exec("readlink -f " + Store.q(root), 10000).trim().equals(root)) return;
  }
  for (int start = 0; start < candidates.size(); start += STATE_BATCH_SIZE) {
   List<String> sub = candidates.subList(start, Math.min(candidates.size(), start + STATE_BATCH_SIZE));
   StringBuilder cmd = new StringBuilder("for t in");
   for (String t : sub) cmd.append(' ').append(Store.q(t));
   cmd.append("; do p=$(dirname \"$t\"); if [ ! -L \"$p\" ] && [ -d \"$p\" ] && [ ! -L \"$t\" ] && [ -e \"$t\" ]; then rm -f \"$t\"; fi; done; printf 'OK'");
   adb.exec(cmd.toString(), 60000);
  }
 }

 static void deleteTree(File f) {
  if (f == null) return;
  try {
   Path p = f.toPath();
   if (!Files.exists(p, LinkOption.NOFOLLOW_LINKS)) return;
   if (Files.isSymbolicLink(p)) {
    Files.deleteIfExists(p);
    return;
   }
   if (f.isDirectory()) {
    File[] children = f.listFiles();
    if (children != null) {
     for (File child : children) deleteTree(child);
    }
   }
   Files.deleteIfExists(p);
  } catch (Exception ignored) {}
 }

 private void cleanStaleStaging() {
  try {
   File ext = context.getExternalFilesDir(null);
   if (ext == null || Files.isSymbolicLink(ext.toPath())) return;
   File stagingRoot = new File(ext, "staging");
   if (!stagingRoot.exists() || Files.isSymbolicLink(stagingRoot.toPath())) return;
   File[] children = stagingRoot.listFiles();
   if (children != null) {
    for (File child : children) deleteTree(child);
   }
  } catch (Exception ignored) {}
 }

 private void pruneHistory(String binding, String keepId) {
  try {
   Set<String> keep = new HashSet<>();
   if (keepId != null && !keepId.isEmpty()) keep.add(keepId);
   File act = active();
   if (act.isFile()) {
    try {
     JSONObject actObj = Store.read(act);
     String aid = actObj.optString("id", "");
     if (!aid.isEmpty() && !TERMINAL_STATES.contains(actObj.optString("state", ""))) {
      keep.add(aid);
     }
    } catch (Exception e) {
     return;
    }
   }
   File receiptsDir = Store.internal(context, "receipts");
   if (receiptsDir.isDirectory()) {
    File[] rFiles = receiptsDir.listFiles();
    if (rFiles != null) {
     for (File rf : rFiles) {
      if (!rf.isFile() || !rf.getName().endsWith(".json")) continue;
      try {
       String jid = Store.read(rf).optString("journal_id", "");
       if (!jid.isEmpty()) keep.add(jid);
      } catch (Exception e) {
       return;
      }
     }
    }
   }
   ArrayDeque<String> chainQueue = new ArrayDeque<>(keep);
   while (!chainQueue.isEmpty()) {
    String curJid = chainQueue.pollFirst();
    try {
     File jf = journalFile(curJid);
     if (!jf.isFile()) continue;
     JSONObject jo = Store.read(jf);
     JSONObject prevReceipt = jo.optJSONObject("previous_receipt");
     if (prevReceipt != null) {
      String prevJid = prevReceipt.optString("journal_id", "");
      if (!prevJid.isEmpty() && keep.add(prevJid)) {
       chainQueue.addLast(prevJid);
      }
     }
    } catch (Exception e) {
     return;
    }
   }
   File ext = context.getExternalFilesDir(null);
   if (ext != null && !Files.isSymbolicLink(ext.toPath()) && binding != null && !binding.isEmpty()) {
    File backupsForBinding = new File(ext, "backups/" + binding);
    if (backupsForBinding.isDirectory() && !Files.isSymbolicLink(backupsForBinding.toPath())) {
     File[] bDirs = backupsForBinding.listFiles();
     if (bDirs != null) {
      for (File bd : bDirs) {
       if (!keep.contains(bd.getName())) deleteTree(bd);
      }
     }
    }
   }
   File journalsDir = Store.internal(context, "journals");
   if (journalsDir.isDirectory() && !Files.isSymbolicLink(journalsDir.toPath())) {
    File[] jFiles = journalsDir.listFiles();
    if (jFiles != null) {
     for (File jf : jFiles) {
      if (!jf.isFile() || !jf.getName().endsWith(".json")) continue;
      String name = jf.getName();
      String jid = name.substring(0, name.length() - 5);
      if (keep.contains(jid)) continue;
      try {
       JSONObject jo = Store.read(jf);
       if (TERMINAL_STATES.contains(jo.optString("state", ""))) {
        jf.delete();
       }
      } catch (Exception ignored) {}
     }
    }
   }
  } catch (Exception ignored) {}
 }

 private File active() { return Store.internal(context, "state/active_journal.json"); }
 private File receipt(String binding) { return Store.internal(context, "receipts/" + binding + ".json"); }
 private File journalFile(String id) throws IOException {
  if (!id.matches("[a-f0-9-]{36}")) throw new IOException("Mã nhật ký không hợp lệ.");
  return Store.internal(context, "journals/" + id + ".json");
 }
 private void saveJournal(JSONObject j) throws Exception {
  Store.write(journalFile(j.getString("id")), j);
  Store.write(active(), j);
 }
 boolean pending() { return hasPending(context); }
 static boolean hasPending(Context context) {
  try {
   File active = Store.internal(context, "state/active_journal.json");
   return active.isFile() && !TERMINAL_STATES.contains(Store.read(active).getString("state"));
  } catch (Exception e) {
   return true;
  }
 }

 JSONObject receiptState() {
  try {
   if (target == null || !target.has("binding")) return Store.obj("present", false);
   File f = receipt(target.getString("binding"));
   if (!f.isFile()) return Store.obj("present", false);
   JSONObject r = Store.read(f);
   JSONObject out = Store.obj(
     "present", true,
     "version", r.getString("version"),
     "manifestSha256", r.optString("manifest_sha256", ""),
     "files", r.getJSONArray("files").length()
   );
   try {
    JSONObject j = Store.read(journalFile(r.getString("journal_id")));
    String g = j.optString("gameVersion"), res = j.optString("resourceVersion");
    out.put("installedGameVersion", g);
    out.put("installedResourceVersion", res);
    out.put("stale", !g.equals(target.optString("gameVersion")) || !res.equals(target.optString("resourceVersion")));
   } catch (Exception ignored) {}
   return out;
  } catch (Exception e) {
   return Store.obj("present", false, "message", "Chưa đọc được biên bản cài đặt.");
  }
 }

 private void step(String text, int percent) throws Exception {
  if (deadline > 0 && SystemClock.elapsedRealtime() > deadline) {
   throw new IOException("Thao tác vượt thời hạn; giữ nhật ký để phục hồi.");
  }
  if (progress != null) progress.update(text, percent);
 }

 private void checkIdentity(JSONObject journal) throws Exception {
  if (!journal.getString("binding").equals(target.getString("binding"))
    || !journal.getString("deviceId").equals(target.getString("deviceId"))
    || !journal.getString("package").equals(Store.GAME)
    || !journal.getString("root").equals(target.getString("root"))) {
   throw new StellaException("E-BIND-MISMATCH", "Nhật ký/backup không thuộc thiết bị và thư mục game này.", null);
  }
 }

 private void bound(JSONObject journal) throws Exception {
  checkIdentity(journal);
  if (!journal.getString("gameVersion").equals(target.getString("gameVersion"))
    || !journal.getString("resourceVersion").equals(target.getString("resourceVersion"))) {
   throw new StellaException("E-VER-CHANGED",
     "Game đã cập nhật kể từ lần cài trước (lần cài: game " + journal.getString("gameVersion") + " · tài nguyên " + journal.getString("resourceVersion")
       + "; hiện tại: game " + target.getString("gameVersion") + " · tài nguyên " + target.getString("resourceVersion")
       + "). Bản sao lưu cũ thuộc phiên bản trước nên không được dùng để khôi phục, tránh ghi đè tệp của bản game mới. Hãy bấm Cập nhật Việt hoá để cài lại cho phiên bản hiện tại.",
     null,
     "installedGameVersion", journal.getString("gameVersion"),
     "installedResourceVersion", journal.getString("resourceVersion"),
     "currentGameVersion", target.getString("gameVersion"),
     "currentResourceVersion", target.getString("resourceVersion"));
  }
 }

 private String ensureExternalBase() throws Exception {
  File ext = context.getExternalFilesDir(null);
  if (ext == null) throw new IOException("Chưa truy cập được bộ nhớ ngoài của ứng dụng.");
  if (Files.isSymbolicLink(ext.toPath())) throw new IOException("Vùng lưu tạm hoặc backup có liên kết.");
  String base = ext.getCanonicalPath();
  String extSuffix = "/Android/data/" + Store.APP + "/files";
  if (verifiedExternalBase == null || !verifiedExternalBase.equals(base)) {
   String actual = adb.exec("[ ! -L " + Store.q(base) + " ] && [ -d " + Store.q(base) + " ] && readlink -f " + Store.q(base), 10000).trim();
   if (!isSafeFuseAlias(actual, base, extSuffix)) throw new IOException("Vùng lưu tạm hoặc backup có liên kết.");
   verifiedExternalBase = base;
  }
  return verifiedExternalBase;
 }

 private String ownExternalPath(File file) throws Exception {
  String base = ensureExternalBase();
  Path basePath = new File(base).toPath();
  for (Path cur = file.toPath(); cur != null && !cur.equals(basePath); cur = cur.getParent()) {
   if (Files.exists(cur, LinkOption.NOFOLLOW_LINKS) && Files.isSymbolicLink(cur)) {
    throw new IOException("Vùng lưu tạm hoặc backup có liên kết.");
   }
  }
  String path = file.getCanonicalPath();
  if (!path.startsWith(base + "/") && !path.startsWith(base + File.separator)) {
   throw new IOException("Tệp tạm/backup vượt vùng ứng dụng.");
  }
  return path;
 }

 JSONObject install(ChannelClient channel) throws Exception {
  return install(channel, null);
 }

 JSONObject install(ChannelClient channel, JSONObject prefetchedManifest) throws Exception {
  verifiedExternalBase = null;
  deadline = SystemClock.elapsedRealtime() + 5400000;
  requireTarget();
  closedAndVersion();
  if (pending()) throw new IOException("Có nhật ký chưa hoàn tất. Hãy chọn Phục hồi thao tác trước.");
  cleanStaleStaging();
  JSONObject manifest = prefetchedManifest != null ? prefetchedManifest : channel.androidManifest(channel.freshRelease());
  VersionCompatibility.Diagnosis diag = VersionCompatibility.diagnose(
    manifest.optString("client_game_version"), manifest.optString("resource_version"),
    target.optString("gameVersion"), target.optString("resourceVersion"));
  if (!diag.isMatch()) {
   String msg;
   if ("game_older".equals(diag.kind)) {
    msg = "Game trên máy (v" + diag.observedGame + ") đang cũ hơn gói Việt hoá mới nhất (v" + diag.declaredGameSummary + "). Hãy mở Stella Sora cho game cập nhật lên v" + diag.declaredGameSummary + ", thoát hẳn game rồi cài lại.";
   } else if ("game_newer".equals(diag.kind)) {
    msg = "Game trên máy (v" + diag.observedGame + ") mới hơn gói Việt hoá hiện tại (v" + diag.declaredGameSummary + "). Vui lòng chờ nhóm dịch phát hành bản tương thích.";
   } else {
    msg = "Gói Android (v" + diag.declaredGameSummary + " · " + diag.declaredResourceSummary + ") chưa khớp game trên máy (v" + diag.observedGame + " · RES " + diag.observedResource + ").";
   }
   throw new StellaException("E-PKG-MISMATCH", msg, null,
     "mismatchKind", diag.kind,
     "gameVersion", diag.observedGame,
     "resourceVersion", diag.observedResource,
     "supportedGameVersion", diag.declaredGameSummary);
  }
  step("Đang chuẩn bị cài đặt cho Stella Sora Android...", 5);
  ensureExternalBase();
  String id = UUID.randomUUID().toString(), binding = target.getString("binding");
  File stage = Store.external(context, "staging/" + id);
  File backup = Store.external(context, "backups/" + binding + "/" + id);
  ownExternalPath(stage);
  ownExternalPath(backup);
  JSONArray files = manifest.getJSONArray("files"), plan = new JSONArray();
  long total = manifest.getLong("total_size"), beforeTotal = 0, maxFile = 0;
  File rp = receipt(binding);
  Object previous = JSONObject.NULL;
  if (rp.isFile()) {
   JSONObject existingReceipt = Store.read(rp);
   String prevJid = existingReceipt.optString("journal_id", "");
   if (!prevJid.isEmpty()) {
    File prevJf = journalFile(prevJid);
    if (prevJf.isFile()) {
     JSONObject prevJournal = Store.read(prevJf);
     if (prevJournal.optString("gameVersion").equals(target.optString("gameVersion"))
       && prevJournal.optString("resourceVersion").equals(target.optString("resourceVersion"))) {
      previous = existingReceipt;
     }
    }
   }
  }
  JSONObject j = Store.obj(
    "schema", 1,
    "id", id,
    "state", "PREPARING",
    "binding", binding,
    "deviceId", target.getString("deviceId"),
    "package", Store.GAME,
    "root", target.getString("root"),
    "gameVersion", target.getString("gameVersion"),
    "resourceVersion", target.getString("resourceVersion"),
    "version", manifest.getString("version"),
    "manifest_sha256", manifest.optString("manifest_sha256", ""),
    "files", plan,
    "previous_receipt", previous
  );
  saveJournal(j);
  try {
   if (new StatFs(stage.getAbsolutePath()).getAvailableBytes() < total + 16777216) {
    throw new IOException("Không đủ bộ nhớ để tải và kiểm tra gói Android.");
   }
   JSONObject packageZip = manifest.optJSONObject("package_zip");
   Map<String, File> extractedBundles = new HashMap<>();
   if (packageZip != null) {
    File zipFile = new File(stage, "bundles.zip");
    step("Tải gói AssetBundles nén (" + (packageZip.getLong("size") / 1048576) + " MB)...", 5);
    ChannelClient.download(packageZip.getString("url"), zipFile, packageZip.getLong("size"), packageZip.getString("sha256"), (label, pct) -> {
     if (SystemClock.elapsedRealtime() > deadline) throw new IllegalStateException("Tải quá thời hạn.");
     if (progress != null) progress.update("Đang tải AssetBundles (" + pct + "%)", 5 + pct * 9 / 100);
    });
    step("Đang giải nén AssetBundles...", 15);
    extractZip(zipFile, stage, extractedBundles);
    zipFile.delete();
   }

   List<String> relPaths = new ArrayList<>(files.length());
   List<String> destPaths = new ArrayList<>(files.length());
   List<String> sourcePaths = new ArrayList<>(files.length());
   List<JSONObject> afterStates = new ArrayList<>(files.length());

   for (int i = 0; i < files.length(); i++) {
    final int index = i;
    JSONObject f = files.getJSONObject(i);
    String fPath = relative(f.getString("path"));
    long expectedSize = f.getLong("size");
    String expectedSha = f.getString("sha256").toLowerCase(Locale.ROOT);
    File source;
    String bundleName = new File(fPath).getName();
    if (fPath.startsWith("Persistent_Store/AssetBundles/") && extractedBundles.containsKey(bundleName)) {
     source = extractedBundles.get(bundleName);
    } else {
     source = new File(stage, i + ".payload");
     step("Tải tệp " + (i + 1) + " / " + files.length(), 15 + index * 10 / files.length());
     ChannelClient.download(f.getString("url"), source, expectedSize, expectedSha, (label, pct) -> {
      if (SystemClock.elapsedRealtime() > deadline) throw new IllegalStateException("Tải quá thời hạn.");
      if (progress != null) progress.update(label, 15 + index * 10 / files.length());
     });
    }
    String canonicalSource = ownExternalPath(source);
    if (!source.isFile() || source.length() != expectedSize || !Store.hash(source).equalsIgnoreCase(expectedSha)) {
     throw new IOException("Tệp tải về không khớp kích thước hoặc SHA256: " + fPath);
    }
    relPaths.add(fPath);
    destPaths.add(fullPath(fPath));
    sourcePaths.add(canonicalSource);
    afterStates.add(Store.obj("exists", true, "size", expectedSize, "sha256", expectedSha));
    maxFile = Math.max(maxFile, expectedSize);
   }

   step("Đang kiểm tra thư mục và tệp hiện tại...", 26);
   verifySafeDirectories(relPaths);
   List<JSONObject> beforeStates = batchStates(destPaths);
   for (int i = 0; i < files.length(); i++) {
    JSONObject before = beforeStates.get(i);
    beforeTotal += before.optLong("size", 0);
    File backupFile = new File(backup, i + ".original");
    String canonicalBackup = ownExternalPath(backupFile);
    plan.put(Store.obj(
      "path", relPaths.get(i),
      "before", before,
      "after", afterStates.get(i),
      "source", sourcePaths.get(i),
      "backup", canonicalBackup
    ));
   }
   saveJournal(j);

   closedAndVersion();
   long required = beforeTotal + maxFile + 16777216;
   long localAvail = new StatFs(backup.getAbsolutePath()).getAvailableBytes();
   if (localAvail < required) {
    throw new IOException("Không đủ dung lượng để sao lưu và thay tệp an toàn.");
   }
   long gameAvail = localAvail;
   try {
    String df = adb.exec("(df -Pk " + Store.q(target.getString("root")) + " 2>/dev/null || df -k " + Store.q(target.getString("root")) + ") | tail -n 1", 10000);
    String[] columns = df.trim().split("\\s+");
    long parsedKb = -1;
    if (columns.length >= 4 && columns[3].matches("[0-9]+")) {
     parsedKb = Long.parseLong(columns[3]);
    } else if (columns.length >= 3 && columns[2].matches("[0-9]+")) {
     parsedKb = Long.parseLong(columns[2]);
    }
    if (parsedKb >= 0) gameAvail = parsedKb * 1024L;
   } catch (Exception ignored) {
    // Fallback to StatFs on shared emulated storage when OEM df format differs.
   }
   if (gameAvail < required) {
    throw new IOException("Bộ nhớ vùng game không đủ hoặc chưa xác định được.");
   }

   verifySafeDirectories(relPaths);
   for (int start = 0; start < plan.length(); start += BACKUP_BATCH_SIZE) {
    int end = Math.min(plan.length(), start + BACKUP_BATCH_SIZE);
    StringBuilder cmd = new StringBuilder();
    for (int i = start; i < end; i++) {
     JSONObject item = plan.getJSONObject(i);
     String rel = item.getString("path");
     String dest = destPaths.get(i);
     JSONObject before = item.getJSONObject("before");
     if (!before.getBoolean("exists")) {
      cmd.append("if ! (").append(guard(dest, before)).append("); then printf 'ERR:81:%s' ").append(Store.q(rel)).append("; exit 0; fi; ");
     } else {
      String saved = item.getString("backup");
      String qSaved = Store.q(saved), qDest = Store.q(dest);
      cmd.append("if [ -e ").append(qSaved).append(" ] || [ -L ").append(qSaved).append(" ]; then printf 'ERR:82:%s' ").append(Store.q(rel)).append("; exit 0; fi; ");
      cmd.append("if ! (").append(guard(dest, before)).append("); then printf 'ERR:81:%s' ").append(Store.q(rel)).append("; exit 0; fi; ");
      cmd.append("cp ").append(qDest).append(" ").append(qSaved).append(" || exit $?; ");
      cmd.append("if ! (").append(guard(saved, before)).append("); then printf 'ERR:83:%s' ").append(Store.q(rel)).append("; exit 0; fi; ");
     }
    }
    cmd.append("printf 'OK'");
    String bRes = adb.exec(cmd.toString(), 120000);
    if (!"OK".equals(bRes)) {
     if (bRes.startsWith("ERR:81:")) throw new IOException("Tệp game đổi trước khi sao lưu: " + bRes.substring(7));
     if (bRes.startsWith("ERR:82:") || bRes.startsWith("ERR:83:")) throw new IOException("Backup không khớp tệp gốc: " + bRes.substring(7));
     throw new IOException("Không sao lưu được tệp gốc: " + bRes);
    }
    for (int i = start; i < end; i++) {
     JSONObject item = plan.getJSONObject(i);
     if (item.getJSONObject("before").getBoolean("exists")) {
      ownExternalPath(new File(item.getString("backup")));
     }
    }
    step("Đã sao lưu " + end + " / " + plan.length(), 30 + end * 18 / plan.length());
   }

   j.put("state", "APPLYING");
   saveJournal(j);
   verifySafeDirectories(relPaths);
   closedAndVersion();
   long lastVerCheck = SystemClock.elapsedRealtime();

   for (int i = 0; i < plan.length(); i++) {
    if (i > 0 && (i % 15 == 0 || SystemClock.elapsedRealtime() - lastVerCheck >= 2500L)) {
     closedAndVersion();
     lastVerCheck = SystemClock.elapsedRealtime();
    }
    JSONObject f = plan.getJSONObject(i);
    applyFileAtomic(j, id, f);
    step("Đã cài và đọc lại " + (i + 1) + " / " + plan.length(), 48 + (i + 1) * 47 / plan.length());
   }

   closedAndVersion();
   step("Đang đối chiếu toàn bộ tệp sau cài...", 96);
   verifySafeDirectories(relPaths);
   List<JSONObject> finalStates = batchStates(destPaths);
   for (int i = 0; i < plan.length(); i++) {
    JSONObject f = plan.getJSONObject(i);
    if (!same(finalStates.get(i), f.getJSONObject("after"))) {
     throw new IOException("Tệp đã đổi trước khi ghi biên bản: " + f.getString("path"));
    }
   }

   JSONObject r = Store.obj(
     "schema", 1,
     "journal_id", id,
     "binding", binding,
     "version", manifest.getString("version"),
     "manifest_sha256", manifest.optString("manifest_sha256", ""),
     "files", plan,
     "package", Store.GAME,
     "root", target.getString("root"),
     "deviceId", target.getString("deviceId")
   );
   Store.write(rp, r);
   j.remove("pending");
   j.put("state", "DONE");
   saveJournal(j);
   pruneHistory(binding, id);
   step("Đã hoàn tất gói Android và đối chiếu tệp.", 100);
   return r;
  } catch (Exception failure) {
   if ("PREPARING".equals(j.optString("state"))) {
    j.remove("pending");
    j.put("state", "ABORTED");
    saveJournal(j);
    deleteTree(backup);
   } else {
    try {
     restoreJournal(j, false);
     deleteTree(backup);
    } catch (Exception recovery) {
     j.put("state", "RECOVERY_REQUIRED");
     saveJournal(j);
     throw new StellaException("E-RECOVERY-REQUIRED",
       "Thao tác chưa hoàn tất; cần Phục hồi từ nhật ký. " + Store.cleanError(recovery),
       recovery,
       "originalError", Store.cleanError(failure),
       "journalState", "RECOVERY_REQUIRED");
    }
   }
   throw new StellaException(ErrorReport.classify(failure),
     "Chưa cài hoàn tất. Các thay đổi đã được đưa về trạng thái trước cài: " + Store.cleanError(failure),
     failure,
     "journalState", j.optString("state"),
     "rolledBack", true);
  } finally {
   deleteTree(stage);
   cleanStaleStaging();
  }
 }

 JSONObject verify() throws Exception {
  verifiedExternalBase = null;
  deadline = SystemClock.elapsedRealtime() + 5400000;
  requireTarget();
  File f = receipt(target.getString("binding"));
  if (!f.isFile()) throw new IOException("Chưa có biên bản của lần cài bằng ứng dụng này.");
  JSONObject r = Store.read(f), j = Store.read(journalFile(r.getString("journal_id")));
  bound(j);
  JSONArray list = j.getJSONArray("files");
  List<String> relPaths = new ArrayList<>(list.length());
  List<String> destPaths = new ArrayList<>(list.length());
  for (int i = 0; i < list.length(); i++) {
   String rel = relative(list.getJSONObject(i).getString("path"));
   relPaths.add(rel);
   destPaths.add(fullPath(rel));
  }
  verifySafeDirectories(relPaths);
  for (int start = 0; start < destPaths.size(); start += STATE_BATCH_SIZE) {
   int end = Math.min(destPaths.size(), start + STATE_BATCH_SIZE);
   List<JSONObject> states = batchStates(destPaths.subList(start, end));
   for (int k = 0; k < states.size(); k++) {
    int idx = start + k;
    JSONObject item = list.getJSONObject(idx);
    if (!same(states.get(k), item.getJSONObject("after"))) {
     throw new IOException("Tệp bản dịch không khớp: " + item.getString("path"));
    }
   }
   step("Đối chiếu " + end + " / " + list.length(), 100 * end / list.length());
  }
  return Store.obj("files", list.length(), "version", r.getString("version"));
 }

 boolean forceStopGame() throws Exception {
  if (!adb.verified) throw new StellaException("E-ADB-NOT-CONNECTED", "Chưa kết nối Local ADB.", null);
  adb.exec("am force-stop " + Store.GAME + " || true", 10000);
  try { Thread.sleep(350); } catch (InterruptedException ignored) {}
  String check = adb.exec(
    "if command -v pidof >/dev/null 2>&1; then pidof " + Store.GAME + " >/dev/null 2>&1 && printf 'RUNNING' || printf 'STOPPED'; "
      + "else ps -A 2>/dev/null | grep -F " + Store.q(Store.GAME) + " >/dev/null 2>&1 && printf 'RUNNING' || printf 'STOPPED'; fi",
    10000
  ).trim();
  return !"RUNNING".equals(check);
 }

 private static final class DeviceMd5State {
  final boolean exists;
  final long size;
  final String md5; // empty when absent or size mismatched

  DeviceMd5State(boolean exists, long size, String md5) {
   this.exists = exists;
   this.size = size;
   this.md5 = md5;
  }
 }

 private static final class OfficialTarget {
  final String rel;
  final String name;
  final String destPath;
  final String action; // keep | replace | delete
  final long expectedSize;
  final String expectedMd5;
  final boolean existedBefore;
  File sourceFile;
  String sourceKind = ""; // backup | cdn

  OfficialTarget(String rel, String name, String destPath, String action, long expectedSize, String expectedMd5, boolean existedBefore) {
   this.rel = rel;
   this.name = name;
   this.destPath = destPath;
   this.action = action;
   this.expectedSize = expectedSize;
   this.expectedMd5 = expectedMd5;
   this.existedBefore = existedBefore;
  }
 }

 private String fullOfficialPath(String rel) throws Exception {
  return target.getString("root") + "/" + relativeOfficial(rel);
 }

 private void ensureAndVerifyOfficialDirs(Collection<String> relativePaths) throws Exception {
  String root = target.getString("root");
  String suffix = "/Android/data/" + Store.GAME + "/files";
  LinkedHashSet<String> dirs = new LinkedHashSet<>();
  dirs.add(root);
  dirs.add(root + "/Persistent_Store");
  for (String rel : relativePaths) {
   String clean = relativeOfficial(rel);
   String[] pieces = clean.split("/");
   String current = root;
   for (int i = 0; i < pieces.length - 1; i++) {
    current += "/" + pieces[i];
    dirs.add(current);
   }
  }
  StringBuilder cmd = new StringBuilder("for d in");
  for (String d : dirs) cmd.append(' ').append(Store.q(d));
  cmd.append("; do if [ -L \"$d\" ]; then printf 'ERR\\n'; exit 0; fi; ");
  cmd.append("if [ ! -e \"$d\" ]; then mkdir -p \"$d\" || exit $?; fi; ");
  cmd.append("if [ -L \"$d\" ] || [ ! -d \"$d\" ]; then printf 'ERR\\n'; exit 0; fi; ");
  cmd.append("readlink -f \"$d\" || exit $?; done");
  String res = adb.exec(cmd.toString(), 15000);
  if (res.startsWith("ERR")) {
   throw new IOException("Đường dẫn dữ liệu có liên kết hoặc thư mục chưa sẵn sàng.");
  }
  String[] resolvedLines = res.isEmpty() ? new String[0] : res.split("\\r?\\n");
  if (resolvedLines.length != dirs.size()) {
   throw new IOException("Đường dẫn dữ liệu có liên kết hoặc thư mục chưa sẵn sàng.");
  }
  int idx = 0;
  for (String d : dirs) {
   String relSuffix = suffix + d.substring(root.length());
   if (!isSafeFuseAlias(resolvedLines[idx++].trim(), d, relSuffix)) {
    throw new IOException("Đường dẫn dữ liệu có liên kết hoặc thư mục chưa sẵn sàng.");
   }
  }
 }

 private List<DeviceMd5State> batchMd5States(List<String> fullPaths, List<Long> expectedSizes) throws Exception {
  List<DeviceMd5State> all = new ArrayList<>(fullPaths.size());
  for (int start = 0; start < fullPaths.size(); start += STATE_BATCH_SIZE) {
   int end = Math.min(fullPaths.size(), start + STATE_BATCH_SIZE);
   StringBuilder cmd = new StringBuilder();
   for (int k = 0; k < end - start; k++) {
    int idx = start + k;
    String qP = Store.q(fullPaths.get(idx));
    long expSz = expectedSizes.get(idx);
    cmd.append("p=").append(qP).append("; ")
      .append("if [ -L \"$p\" ]; then exit 73; ")
      .append("elif [ -f \"$p\" ]; then s=$(stat -c %s \"$p\") || exit $?; ");
    if (expSz >= 0) {
     cmd.append("if [ \"$s\" = ").append(Store.q(String.valueOf(expSz))).append(" ]; then ")
       .append("h=$(md5sum \"$p\") || exit $?; printf '").append(k).append(" F %s %s\\n' \"$s\" \"${h%% *}\"; ")
       .append("else printf '").append(k).append(" S %s\\n' \"$s\"; fi; ");
    } else {
     cmd.append("printf '").append(k).append(" S %s\\n' \"$s\"; ");
    }
    cmd.append("elif [ -e \"$p\" ]; then exit 74; ")
      .append("else printf '").append(k).append(" A\\n'; fi; ");
   }
   String raw = adb.exec(cmd.toString(), 120000);
   String[] lines = raw.isEmpty() ? new String[0] : raw.split("\\r?\\n");
   if (lines.length != (end - start)) {
    throw new IOException("Chưa đối chiếu được kích thước/MD5 tệp game.");
   }
   for (int k = 0; k < end - start; k++) {
    String[] tok = lines[k].trim().split("\\s+");
    if (tok.length < 2 || !tok[0].equals(String.valueOf(k))) {
     throw new IOException("Chưa đối chiếu được kích thước/MD5 tệp game.");
    }
    if ("A".equals(tok[1]) && tok.length == 2) {
     all.add(new DeviceMd5State(false, -1L, ""));
    } else if ("S".equals(tok[1]) && tok.length >= 3 && tok[2].matches("[0-9]+")) {
     all.add(new DeviceMd5State(true, Long.parseLong(tok[2]), ""));
    } else if ("F".equals(tok[1]) && tok.length >= 4 && tok[2].matches("[0-9]+") && tok[3].matches("[0-9a-fA-F]{32}")) {
     all.add(new DeviceMd5State(true, Long.parseLong(tok[2]), tok[3].toLowerCase(Locale.ROOT)));
    } else {
     throw new IOException("Chưa đối chiếu được kích thước/MD5 tệp game.");
    }
   }
  }
  return all;
 }

 private byte[] pullManifestBytes(String remotePath, File localTemp) throws Exception {
  String root = target.getString("root");
  String suffix = "/Android/data/" + Store.GAME + "/files";
  String rel = remotePath.startsWith(root) ? remotePath.substring(root.length()) : "";
  String qRemote = Store.q(remotePath);
  String qLocal = Store.q(ownExternalPath(localTemp));
  String check = adb.exec(
    "if [ ! -e " + qRemote + " ]; then printf 'MISSING'; exit 0; fi; "
      + "if [ -L " + qRemote + " ] || [ ! -f " + qRemote + " ]; then printf 'ERR:BAD'; exit 0; fi; "
      + "s=$(stat -c %s " + qRemote + ") || exit $?; "
      + "if [ \"$s\" -gt 33554432 ]; then printf 'ERR:SIZE'; exit 0; fi; "
      + "r=$(readlink -f " + qRemote + ") || exit $?; "
      + "cp " + qRemote + " " + qLocal + " || exit $?; "
      + "printf 'OK\\n%s' \"$r\"",
    30000
  ).trim();
  if ("MISSING".equals(check)) return null;
  if (!check.startsWith("OK\n")) {
   throw new IOException("Không đọc được tệp bảng kê game trên thiết bị: " + check);
  }
  String resolved = check.substring(3).trim();
  if (!isSafeFuseAlias(resolved, remotePath, suffix + rel)) {
   throw new IOException("Tệp bảng kê game có liên kết không an toàn.");
  }
  ownExternalPath(localTemp);
  return Files.readAllBytes(localTemp.toPath());
 }

 private OfficialAndroidClient.ParsedManifest pullLocalManifest(File stageDir) throws Exception {
  String psDir = target.getString("root") + "/Persistent_Store";
  byte[] baseBytes = pullManifestBytes(psDir + "/ss_and.mani", new File(stageDir, "local_ss_and.mani"));
  if (baseBytes == null) return null;
  OfficialAndroidClient.ParsedManifest base = OfficialAndroidClient.parseManifestFull(baseBytes);
  if (base.files.isEmpty()) return null;

  Map<String, String> mergedHeaders = new LinkedHashMap<>(base.headers);
  Map<String, OfficialAndroidClient.FileEntry> mergedFiles = new LinkedHashMap<>(base.files);
  Map<String, OfficialAndroidClient.PatchEntry> mergedPatches = new LinkedHashMap<>(base.patches);

  try {
   byte[] addBytes = pullManifestBytes(psDir + "/ss_and_add.mani", new File(stageDir, "local_ss_and_add.mani"));
   if (addBytes != null) {
    OfficialAndroidClient.ParsedManifest addM = OfficialAndroidClient.parseManifestFull(addBytes);
    mergedFiles.putAll(addM.files);
   }
  } catch (Exception ignored) {}

  String patchNumRaw = base.headers.getOrDefault("BIN_DIFF_PATCH_VER", "");
  if (patchNumRaw.matches("[0-9]+")) {
   try {
    int patchNum = Integer.parseInt(patchNumRaw);
    if (patchNum > 0) {
     byte[] pmBytes = pullManifestBytes(psDir + "/p_" + patchNum + "_m.ss_and.mani", new File(stageDir, "local_pm.mani"));
     if (pmBytes != null) {
      OfficialAndroidClient.ParsedManifest pm = OfficialAndroidClient.parseManifestFull(pmBytes);
      mergedFiles.putAll(pm.files);
      for (String k : new String[]{"RES_VER", "GAME_VER", "CLIENT_VER"}) {
       if (pm.headers.containsKey(k)) mergedHeaders.put(k, pm.headers.get(k));
      }
     }
    }
   } catch (Exception ignored) {}
  }
  return new OfficialAndroidClient.ParsedManifest(mergedHeaders, mergedFiles, mergedPatches);
 }

 private Map<Long, List<File>> indexLocalBackupsBySize(String binding) {
  Map<Long, List<File>> bySize = new HashMap<>();
  try {
   File ext = context.getExternalFilesDir(null);
   if (ext == null || Files.isSymbolicLink(ext.toPath())) return bySize;
   File bRoot = new File(ext, "backups/" + binding);
   if (!bRoot.isDirectory() || Files.isSymbolicLink(bRoot.toPath())) return bySize;
   File[] runs = bRoot.listFiles();
   if (runs == null) return bySize;
   Arrays.sort(runs, (a, b) -> Long.compare(b.lastModified(), a.lastModified()));
   for (File run : runs) {
    if (!run.isDirectory() || Files.isSymbolicLink(run.toPath())) continue;
    File[] items = run.listFiles();
    if (items == null) continue;
    for (File f : items) {
     if (f.isFile() && !Files.isSymbolicLink(f.toPath())) {
      bySize.computeIfAbsent(f.length(), k -> new ArrayList<>()).add(f);
     }
    }
   }
  } catch (Exception ignored) {}
  return bySize;
 }

 private static File findVerifiedBackup(Map<Long, List<File>> bySize, long expectedSize, String expectedMd5) {
  List<File> list = bySize.get(expectedSize);
  if (list == null) return null;
  for (File f : list) {
   if (OfficialAndroidClient.matchesMd5(f, expectedSize, expectedMd5)) {
    return f;
   }
  }
  return null;
 }

 private Set<String> collectReceiptRelativePaths(String binding) {
  Set<String> out = new LinkedHashSet<>();
  try {
   File f = receipt(binding);
   Set<String> visited = new HashSet<>();
   JSONObject cur = f.isFile() ? Store.read(f) : null;
   while (cur != null) {
    String jid = cur.optString("journal_id", "");
    if (!jid.isEmpty() && !visited.add(jid)) break;
    JSONArray files = cur.optJSONArray("files");
    if (files != null) {
     for (int i = 0; i < files.length(); i++) {
      String p = files.getJSONObject(i).optString("path", "");
      try { out.add(relativeOfficial(p)); } catch (Exception ignored) {}
     }
    }
    if (jid.matches("[a-f0-9-]{36}")) {
     File jf = journalFile(jid);
     if (jf.isFile()) {
      JSONObject jo = Store.read(jf);
      JSONArray jfiles = jo.optJSONArray("files");
      if (jfiles != null) {
       for (int i = 0; i < jfiles.length(); i++) {
        String p = jfiles.getJSONObject(i).optString("path", "");
        try { out.add(relativeOfficial(p)); } catch (Exception ignored) {}
       }
      }
      cur = jo.optJSONObject("previous_receipt");
      continue;
     }
    }
    cur = null;
   }
  } catch (Exception ignored) {}
  return out;
 }

 private List<String> scanDeviceLanguageFiles() {
  List<String> out = new ArrayList<>();
  try {
   String root = target.getString("root");
   String ps = root + "/Persistent_Store";
   String cmd = ""
     + "if [ -d " + Store.q(ps + "/AssetBundles") + " ] && [ ! -L " + Store.q(ps + "/AssetBundles") + " ]; then "
     + "find " + Store.q(ps + "/AssetBundles") + " -maxdepth 1 -type f -name '*.en.unity3d' -print 2>/dev/null || true; fi; "
     + "if [ -d " + Store.q(ps + "/Videos") + " ] && [ ! -L " + Store.q(ps + "/Videos") + " ]; then "
     + "find " + Store.q(ps + "/Videos") + " -maxdepth 1 -type f -name '*.srt' -print 2>/dev/null || true; fi";
   String listing = adb.exec(cmd, 20000);
   String prefix = root + "/";
   for (String line : listing.split("\\r?\\n")) {
    String trimmed = line.trim();
    if (!trimmed.startsWith(prefix)) continue;
    String rel = trimmed.substring(prefix.length());
    try {
     out.add(relativeOfficial(rel));
    } catch (Exception ignored) {}
   }
  } catch (Exception ignored) {}
  return out;
 }

 /**
  * Removes stale partial BinDiff patch files in Temporary_Store/ and Patch_Store/ (preserving directories)
  * and any leftover *.stella-*.tmp files in Persistent_Store/ so Stella Sora's updater starts completely clean.
  */
 private int cleanGamePatchCaches() {
  int removed = 0;
  try {
   String root = target.getString("root");
   String suffix = "/Android/data/" + Store.GAME + "/files";
   for (String sub : new String[]{"Temporary_Store", "Patch_Store"}) {
    String dir = root + "/" + sub;
    String qDir = Store.q(dir);
    String check = adb.exec(
      "if [ ! -e " + qDir + " ]; then printf 'NONE'; exit 0; fi; "
        + "if [ -L " + qDir + " ] || [ ! -d " + qDir + " ]; then printf 'SKIP'; exit 0; fi; "
        + "readlink -f " + qDir,
      10000
    ).trim();
    if ("NONE".equals(check) || "SKIP".equals(check)) continue;
    if (!isSafeFuseAlias(check, dir, suffix + "/" + sub)) continue;
    String countStr = adb.exec(
      "c=$(find " + qDir + " -type f 2>/dev/null | wc -l); "
        + "find " + qDir + " -type f -delete 2>/dev/null || find " + qDir + " -type f -exec rm -f {} + 2>/dev/null || true; "
        + "printf '%s' \"$c\"",
      30000
    ).trim();
    if (countStr.matches("[0-9]+")) {
     removed += Integer.parseInt(countStr);
    }
   }
   // Clean any stray launcher temp files in Persistent_Store subdirectories
   String ps = root + "/Persistent_Store";
   for (String sub : new String[]{"Tables", "Scripts", "AssetBundles", "Videos"}) {
    String dir = ps + "/" + sub;
    String qDir = Store.q(dir);
    adb.exec(
      "if [ -d " + qDir + " ] && [ ! -L " + qDir + " ]; then "
        + "find " + qDir + " -maxdepth 1 -type f -name '*.stella-*.tmp' -delete 2>/dev/null || true; fi",
      15000
    );
   }
   String sbDir = ps + "/SoundBanks";
   String qSb = Store.q(sbDir);
   adb.exec(
     "if [ -d " + qSb + " ] && [ ! -L " + qSb + " ]; then "
       + "find " + qSb + " -maxdepth 2 -type f -name '*.stella-*.tmp' -delete 2>/dev/null || true; fi",
     15000
   );
  } catch (Exception ignored) {}
  return removed;
 }

 private String pullOptionalRootFile(String fileName, File localTemp, long maxBytes) {
  if (!"file_versions.dat".equals(fileName) && !"prefs.dat".equals(fileName)) return null;
  try {
   String root = target.getString("root");
   String suffix = "/Android/data/" + Store.GAME + "/files";
   String remotePath = root + "/" + fileName;
   String qRemote = Store.q(remotePath);
   String qLocal = Store.q(ownExternalPath(localTemp));
   String check = adb.exec(
     "if [ ! -e " + qRemote + " ]; then printf 'MISSING'; exit 0; fi; "
       + "if [ -L " + qRemote + " ] || [ ! -f " + qRemote + " ]; then printf 'ERR:BAD'; exit 0; fi; "
       + "s=$(stat -c %s " + qRemote + ") || exit $?; "
       + "if [ \"$s\" -gt " + maxBytes + " ]; then printf 'ERR:SIZE'; exit 0; fi; "
       + "r=$(readlink -f " + qRemote + ") || exit $?; "
       + "cp " + qRemote + " " + qLocal + " || exit $?; "
       + "printf 'OK\\n%s' \"$r\"",
     30000
   ).trim();
   if (!check.startsWith("OK\n")) return null;
   String resolved = check.substring(3).trim();
   if (!isSafeFuseAlias(resolved, remotePath, suffix + "/" + fileName)) return null;
   ownExternalPath(localTemp);
   return new String(Files.readAllBytes(localTemp.toPath()), StandardCharsets.UTF_8);
  } catch (Exception ignored) {
   return null;
  }
 }

 private void pushRootFileAtomic(String id, String fileName, File localFile) throws Exception {
  if (!"file_versions.dat".equals(fileName) && !"prefs.dat".equals(fileName)) {
   throw new IOException("Tệp cấu hình gốc không được phép: " + fileName);
  }
  String root = target.getString("root");
  String suffix = "/Android/data/" + Store.GAME + "/files";
  String destPath = root + "/" + fileName;
  String resolvedRoot = adb.exec("if [ -L " + Store.q(root) + " ] || [ ! -d " + Store.q(root) + " ]; then printf 'ERR'; else readlink -f " + Store.q(root) + "; fi", 10000).trim();
  if (!isSafeFuseAlias(resolvedRoot, root, suffix)) {
   throw new IOException("Thư mục dữ liệu game không an toàn khi cập nhật " + fileName);
  }
  String qSrc = Store.q(ownExternalPath(localFile));
  String qDest = Store.q(destPath);
  String tmp = destPath + ".stella-sync-" + id + ".tmp";
  String qTmp = Store.q(tmp);
  long sz = localFile.length();
  String md5 = OfficialAndroidClient.md5File(localFile);
  String qSz = Store.q(String.valueOf(sz));
  String qMd5 = Store.q(md5);
  String guardTmp = "[ ! -L " + qTmp + " ] && [ -f " + qTmp + " ] && [ \"$(stat -c %s " + qTmp + ")\" = " + qSz + " ] && h=$(md5sum " + qTmp + ") && [ \"${h%% *}\" = " + qMd5 + " ]";
  String guardDest = "[ ! -L " + qDest + " ] && [ -f " + qDest + " ] && [ \"$(stat -c %s " + qDest + ")\" = " + qSz + " ] && h=$(md5sum " + qDest + ") && [ \"${h%% *}\" = " + qMd5 + " ]";
  String cmd = "if [ -L " + qDest + " ] || [ -L " + qTmp + " ]; then printf 'ERR:LINK'; exit 0; fi; "
    + "rm -f " + qTmp + " || exit $?; "
    + "cp " + qSrc + " " + qTmp + " || exit $?; "
    + "if ! (" + guardTmp + "); then rm -f " + qTmp + "; printf 'ERR:TMP'; exit 0; fi; "
    + "mv -f " + qTmp + " " + qDest + " || exit $?; "
    + "if ! (" + guardDest + "); then printf 'ERR:DEST'; exit 0; fi; "
    + "printf 'OK'";
  String res = adb.exec(cmd, 60000).trim();
  if (!"OK".equals(res)) {
   throw new IOException("Không đồng bộ được " + fileName + ": " + res);
  }
 }

 private static final class DeviceTreeScan {
  final Set<String> existingRels; // null if scan was incomplete/unsupported
  final List<String> sizeMismatchRels;

  DeviceTreeScan(Set<String> existingRels, List<String> sizeMismatchRels) {
   this.existingRels = existingRels;
   this.sizeMismatchRels = sizeMismatchRels;
  }
 }

 private DeviceTreeScan scanDevicePersistentTree(Map<String, OfficialAndroidClient.FileEntry> localFiles) {
  Set<String> existing = new HashSet<>();
  List<String> mismatches = new ArrayList<>();
  try {
   String root = target.getString("root");
   String ps = root + "/Persistent_Store";
   StringBuilder cmd = new StringBuilder();
   for (String sub : new String[]{"Tables", "Scripts", "Videos", "AssetBundles", "SoundBanks"}) {
    String dir = ps + "/" + sub;
    String qDir = Store.q(dir);
    cmd.append("if [ -d ").append(qDir).append(" ] && [ ! -L ").append(qDir).append(" ]; then ")
      .append("find ").append(qDir).append(" -type f -exec stat -c '%s %n' {} + 2>/dev/null || true; fi; ");
   }
   String raw = adb.exec(cmd.toString(), 45000);
   String prefix = root + "/";
   for (String line : raw.split("\\r?\\n")) {
    int sp = line.indexOf(' ');
    if (sp <= 0 || sp + 1 >= line.length()) continue;
    String szStr = line.substring(0, sp).trim();
    if (!szStr.matches("[0-9]+")) continue;
    String full = line.substring(sp + 1).trim();
    if (!full.startsWith(prefix)) continue;
    String rel = full.substring(prefix.length());
    try {
     rel = relativeOfficial(rel);
    } catch (Exception ignored) {
     continue;
    }
    existing.add(rel);
    String mname = OfficialAndroidClient.manifestNameFromRelativePath(rel);
    if (mname == null) continue;
    OfficialAndroidClient.FileEntry rec = localFiles.get(mname);
    if (rec == null) continue;
    try {
     long actualSize = Long.parseLong(szStr);
     if (actualSize != rec.size) {
      mismatches.add(rel);
     }
    } catch (NumberFormatException ignored) {}
   }
  } catch (Exception ignored) {}
  boolean scanComplete = existing.contains("Persistent_Store/Tables/data.arcx")
    || existing.contains("Persistent_Store/Scripts/lua.arcx")
    || existing.size() >= 10;
  return new DeviceTreeScan(scanComplete ? existing : null, mismatches);
 }

 private boolean syncHotfixDllFromArchive(String id, File stageDir, File localVerifiedHotfixArch) {
  try {
   File archFile = localVerifiedHotfixArch;
   if (archFile == null || !archFile.isFile()) {
    String root = target.getString("root");
    String suffix = "/Android/data/" + Store.GAME + "/files";
    String remoteArch = root + "/Persistent_Store/Scripts/hotfix.arch";
    File pulled = new File(stageDir, "device_hotfix.arch");
    String qRemote = Store.q(remoteArch);
    String qLocal = Store.q(ownExternalPath(pulled));
    String check = adb.exec(
      "if [ ! -e " + qRemote + " ]; then printf 'MISSING'; exit 0; fi; "
        + "if [ -L " + qRemote + " ] || [ ! -f " + qRemote + " ]; then printf 'ERR:BAD'; exit 0; fi; "
        + "s=$(stat -c %s " + qRemote + ") || exit $?; "
        + "if [ \"$s\" -gt 134217728 ]; then printf 'ERR:SIZE'; exit 0; fi; "
        + "r=$(readlink -f " + qRemote + ") || exit $?; "
        + "cp " + qRemote + " " + qLocal + " || exit $?; "
        + "printf 'OK\\n%s' \"$r\"",
      45000
    ).trim();
    if (!check.startsWith("OK\n")) return false;
    String resolved = check.substring(3).trim();
    if (!isSafeFuseAlias(resolved, remoteArch, suffix + "/Persistent_Store/Scripts/hotfix.arch")) return false;
    ownExternalPath(pulled);
    archFile = pulled;
   }
   File extractedDll = new File(stageDir, "Hotfix.dll");
   long expectedSize = -1L;
   long expectedCrc = -1L;
   try (ZipFile zf = new ZipFile(archFile)) {
    ZipEntry ze = zf.getEntry("Hotfix.dll");
    if (ze == null || ze.isDirectory()) return false;
    expectedSize = ze.getSize();
    expectedCrc = ze.getCrc();
    byte[] buf = new byte[65536];
    CRC32 crc = new CRC32();
    long written = 0L;
    try (InputStream in = zf.getInputStream(ze);
         FileOutputStream fos = new FileOutputStream(extractedDll);
         BufferedOutputStream bos = new BufferedOutputStream(fos, buf.length)) {
     int n;
     while ((n = in.read(buf)) > 0) {
      bos.write(buf, 0, n);
      crc.update(buf, 0, n);
      written += n;
     }
     bos.flush();
    }
    if (expectedSize >= 0 && written != expectedSize) return false;
    if (expectedCrc >= 0 && crc.getValue() != expectedCrc) return false;
    expectedSize = written;
   } catch (ZipException notZip) {
    return false;
   }
   ownExternalPath(extractedDll);
   String dllMd5 = OfficialAndroidClient.md5File(extractedDll);
   String dllRel = "Persistent_Store/Scripts/Hotfix.dll";
   String dllDest = fullOfficialPath(dllRel);
   List<DeviceMd5State> curStates = batchMd5States(Collections.singletonList(dllDest), Collections.singletonList(expectedSize));
   DeviceMd5State cur = curStates.get(0);
   if (cur.exists && cur.size == expectedSize && dllMd5.equalsIgnoreCase(cur.md5)) {
    return false;
   }
   ensureAndVerifyOfficialDirs(Collections.singletonList(dllRel));
   OfficialTarget dllTarget = new OfficialTarget(dllRel, "Hotfix.dll", dllDest, "replace", expectedSize, dllMd5, cur.exists);
   dllTarget.sourceFile = extractedDll;
   dllTarget.sourceKind = "hotfix_arch";
   applyOfficialTargetAtomic(id, dllTarget, null);
   return true;
  } catch (Exception e) {
   DiagnosticLog.log(context, "restore", "Cảnh báo đồng bộ Hotfix.dll: " + Store.cleanError(e));
   return false;
  }
 }

 private int cleanOrphanedManifests(String expectedPatchMani) {
  int removed = 0;
  try {
   String root = target.getString("root");
   String ps = root + "/Persistent_Store";
   String listing = adb.exec("find " + Store.q(ps) + " -maxdepth 1 -type f -name 'p_*_m.ss_and.mani' -print 2>/dev/null || true", 15000);
   String prefix = ps + "/";
   for (String line : listing.split("\\r?\\n")) {
    String trimmed = line.trim();
    if (!trimmed.startsWith(prefix)) continue;
    String baseName = trimmed.substring(prefix.length());
    if (!baseName.matches("p_[0-9]+_m\\.ss_and\\.mani")) continue;
    if (expectedPatchMani != null && expectedPatchMani.equals(baseName)) continue;
    String res = adb.exec("if [ ! -L " + Store.q(trimmed) + " ] && [ -f " + Store.q(trimmed) + " ]; then rm -f " + Store.q(trimmed) + " && printf 'OK'; fi", 10000).trim();
    if ("OK".equals(res)) removed++;
   }
  } catch (Exception ignored) {}
  return removed;
 }

 private void applyOfficialTargetAtomic(String id, OfficialTarget t, File rollbackCopy) throws Exception {
  String qDest = Store.q(t.destPath);
  if ("delete".equals(t.action)) {
   if (t.existedBefore && rollbackCopy != null) {
    String qRb = Store.q(ownExternalPath(rollbackCopy));
    adb.exec("if [ -f " + qDest + " ] && [ ! -L " + qDest + " ]; then cp " + qDest + " " + qRb + " || exit $?; fi; printf 'OK'", 60000);
   }
   String res = adb.exec("rm -f " + qDest + " || exit $?; if [ -e " + qDest + " ]; then printf 'ERR:DEL'; else printf 'OK'; fi", 30000);
   if (!"OK".equals(res)) throw new IOException("Không xoá được tệp Việt hoá riêng: " + t.rel);
   return;
  }

  String qSrc = Store.q(ownExternalPath(t.sourceFile));
  String tmp = t.destPath + ".stella-official-" + id + ".tmp";
  String qTemp = Store.q(tmp);
  String qSize = Store.q(String.valueOf(t.expectedSize));
  String qMd5 = Store.q(t.expectedMd5);
  String md5GuardTemp = "[ ! -L " + qTemp + " ] && [ -f " + qTemp + " ] && [ \"$(stat -c %s " + qTemp + ")\" = " + qSize + " ] && h=$(md5sum " + qTemp + ") && [ \"${h%% *}\" = " + qMd5 + " ]";
  String md5GuardDest = "[ ! -L " + qDest + " ] && [ -f " + qDest + " ] && [ \"$(stat -c %s " + qDest + ")\" = " + qSize + " ] && h=$(md5sum " + qDest + ") && [ \"${h%% *}\" = " + qMd5 + " ]";

  StringBuilder cmd = new StringBuilder();
  if (t.existedBefore && rollbackCopy != null) {
   String qRb = Store.q(ownExternalPath(rollbackCopy));
   cmd.append("if [ -f ").append(qDest).append(" ] && [ ! -L ").append(qDest).append(" ]; then cp ").append(qDest).append(" ").append(qRb).append(" || exit $?; fi; ");
  }
  cmd.append("if [ -L ").append(qTemp).append(" ]; then printf 'ERR:TEMPLINK'; exit 0; fi; ");
  cmd.append("rm -f ").append(qTemp).append(" || exit $?; ");
  cmd.append("cp ").append(qSrc).append(" ").append(qTemp).append(" || exit $?; ");
  cmd.append("if ! (").append(md5GuardTemp).append("); then rm -f ").append(qTemp).append("; printf 'ERR:TEMPVERIFY'; exit 0; fi; ");
  cmd.append("mv -f ").append(qTemp).append(" ").append(qDest).append(" || exit $?; ");
  cmd.append("if ! (").append(md5GuardDest).append("); then printf 'ERR:READBACK'; exit 0; fi; ");
  cmd.append("printf 'OK'");

  String res = adb.exec(cmd.toString(), 120000);
  if ("OK".equals(res)) return;
  if ("ERR:TEMPLINK".equals(res)) throw new IOException("Tệp tạm có liên kết không an toàn: " + t.rel);
  if ("ERR:TEMPVERIFY".equals(res)) throw new IOException("Tệp tạm bản gốc sai MD5 khi chép vào máy: " + t.rel);
  if ("ERR:READBACK".equals(res)) throw new IOException("Đọc lại bản gốc sau khi ghi sai MD5: " + t.rel);
  throw new IOException("Không thể ghi bản gốc (" + t.rel + "): " + res);
 }

 private void markReceiptChainRestored(String binding) {
  try {
   File f = receipt(binding);
   Set<String> visited = new HashSet<>();
   JSONObject cur = f.isFile() ? Store.read(f) : null;
   while (cur != null) {
    String jid = cur.optString("journal_id", "");
    if (!jid.isEmpty() && !visited.add(jid)) break;
    if (jid.matches("[a-f0-9-]{36}")) {
     File jf = journalFile(jid);
     if (jf.isFile()) {
      JSONObject jo = Store.read(jf);
      jo.remove("pending");
      jo.put("state", "RESTORED");
      Store.write(jf, jo);
      cur = jo.optJSONObject("previous_receipt");
      continue;
     }
    }
    cur = null;
   }
   if (f.isFile()) f.delete();
   File act = active();
   if (act.isFile()) {
    JSONObject ao = Store.read(act);
    if (binding.equals(ao.optString("binding")) && "DONE".equals(ao.optString("state"))) {
     ao.put("state", "RESTORED");
     Store.write(act, ao);
    }
   }
  } catch (Exception ignored) {}
 }

 JSONObject restore() throws Exception {
  verifiedExternalBase = null;
  deadline = SystemClock.elapsedRealtime() + 5400000;
  requireTarget();
  if (pending()) throw new IOException("Hãy phục hồi nhật ký chưa hoàn tất trước.");
  closedAndVersion();
  ensureExternalBase();

  String binding = target.getString("binding");
  String id = UUID.randomUUID().toString();
  File stage = Store.external(context, "staging/restore_" + id);
  // Keep official_cache reusable across retries so a dropped Wi-Fi connection resumes immediately;
  // it is wiped cleanly once restore succeeds.
  File cdnCache = Store.external(context, "official_cache");
  File rollbackDir = new File(stage, "rollback");
  ownExternalPath(stage);
  ownExternalPath(cdnCache);
  if (!rollbackDir.isDirectory() && !rollbackDir.mkdirs()) {
   throw new IOException("Không tạo được thư mục đệm khôi phục gốc.");
  }
  boolean restoreSucceeded = false;

  try {
   step("Đang đọc bảng kê gốc ss_and.mani trên thiết bị...", 6);
   OfficialAndroidClient.ParsedManifest localManifest = pullLocalManifest(stage);
   if (localManifest == null) {
    // Fallback to legacy local-backup journal restore only when ss_and.mani is absent
    File rf = receipt(binding);
    if (!rf.isFile()) {
     throw new IOException("Không đọc được ss_and.mani và chưa có biên bản cài đặt để khôi phục.");
    }
    restoreLegacyReceiptChain(binding);
    int cleaned = cleanGamePatchCaches();
    cleanStaleStaging();
    pruneHistory(binding, null);
    OfficialAndroidClient.clearGuardAlertAfterRestore(context);
    return Store.obj("replaced", 0, "alreadyOfficial", 0, "deleted", 0, "cleanedTempFiles", cleaned,
      "message", "Đã khôi phục tệp theo biên bản cũ và dọn " + cleaned + " tệp tạm.");
   }

   String localResVer = localManifest.headers.getOrDefault("RES_VER", target.optString("resourceVersion", ""));
   String expectedPatchMani = null;
   String basePatchVerRaw = localManifest.headers.getOrDefault("BIN_DIFF_PATCH_VER", "");
   if (basePatchVerRaw.matches("[0-9]+")) {
    try {
     int pv = Integer.parseInt(basePatchVerRaw);
     if (pv > 0) expectedPatchMani = "p_" + pv + "_m.ss_and.mani";
    } catch (NumberFormatException ignored) {}
   }
   step("Đang đọc file_versions.dat, prefs.dat và hỏi máy chủ Yostar...", 12);
   String prefsText = pullOptionalRootFile("prefs.dat", new File(stage, "local_prefs.dat"), 262144L);
   Set<String> activePackageTags = OfficialAndroidClient.parsePrefsPackageTags(prefsText);
   String fvText = pullOptionalRootFile("file_versions.dat", new File(stage, "local_file_versions.dat"), 67108864L);

   OfficialAndroidClient.AndroidCatalog catalog = null;
   IOException cdnFetchError = null;
   try {
    catalog = OfficialAndroidClient.fetchCatalog(25000);
   } catch (IOException netErr) {
    cdnFetchError = netErr;
    DiagnosticLog.log(context, "restore", "Chưa kết nối được máy chủ Yostar (" + Store.cleanError(netErr) + "); thử đối chiếu backup MD5 cục bộ.");
   }

   Set<String> pendingNames = catalog != null ? catalog.pendingPatchNames(localResVer) : Collections.emptySet();
   OfficialAndroidClient.FileVersionsAudit fvAudit = OfficialAndroidClient.auditFileVersionsText(fvText, localManifest.files, pendingNames);
   step("Đang quét nhanh kích thước toàn bộ tài nguyên trong Persistent_Store...", 17);
   DeviceTreeScan treeScan = scanDevicePersistentTree(localManifest.files);

   Map<String, Boolean> candidateMap = new LinkedHashMap<>();
   Set<String> strayNewRels = new HashSet<>();
   candidateMap.put("Persistent_Store/Tables/data.arcx", true);
   candidateMap.put("Persistent_Store/Scripts/lua.arcx", true);
   for (String rPath : collectReceiptRelativePaths(binding)) {
    candidateMap.put(rPath, true);
   }
   for (String dPath : scanDeviceLanguageFiles()) {
    candidateMap.putIfAbsent(dPath, false);
   }
   // Include updated/added .en.unity3d & .srt from local ss_and.mani (catches deleted bundles -> "no found patch target bundle")
   for (OfficialAndroidClient.FileEntry fe : localManifest.files.values()) {
    if (!fe.name.endsWith(".en.unity3d") && !fe.name.endsWith(".srt")) continue;
    String rel = OfficialAndroidClient.officialRelativePath(fe.name);
    if (rel == null) continue;
    boolean inBaseSame = catalog != null
      && catalog.baseFiles.containsKey(fe.name)
      && catalog.baseFiles.get(fe.name).checksum.equalsIgnoreCase(fe.checksum);
    if (!inBaseSame || fvAudit.allRels.contains(rel)) {
     candidateMap.putIfAbsent(rel, false);
    }
   }
   // Include EVERY file touched by pending CDN BinDiff patches (p_k > localResVer):
   // ALL SoundBanks (.bnk/.media.wem), non-.en bundles, hotfix.arch, AND stray 'N' new files!
   Set<String> pendingTrackedRels = new HashSet<>();
   for (String pName : pendingNames) {
    String rel = OfficialAndroidClient.officialRelativePath(pName);
    if (rel == null) continue;
    if (localManifest.files.containsKey(pName)) {
     candidateMap.putIfAbsent(rel, false);
     pendingTrackedRels.add(rel);
    } else {
     // Brand-new ('N') file from a newer patch step: delete if left partial/corrupt on device!
     candidateMap.putIfAbsent(rel, false);
     strayNewRels.add(rel);
    }
   }
   // Audit EVERY file whose file_versions.dat hash disagrees with ss_and.mani (catches same-size half-patched files!)
   for (String fvBadRel : fvAudit.mismatchedRels) {
    try {
     String clean = relativeOfficial(fvBadRel);
     candidateMap.putIfAbsent(clean, false);
    } catch (Exception ignored) {}
   }
   for (String fvNewRel : fvAudit.strayNewRels) {
    try {
     String clean = relativeOfficial(fvNewRel);
     candidateMap.putIfAbsent(clean, false);
     strayNewRels.add(clean);
    } catch (Exception ignored) {}
   }
   // Audit EVERY file in Persistent_Store whose actual disk size disagrees with ss_and.mani!
   for (String badSzRel : treeScan.sizeMismatchRels) {
    candidateMap.putIfAbsent(badSzRel, false);
   }

   List<String> candRels = new ArrayList<>(candidateMap.keySet());
   List<String> candNames = new ArrayList<>(candRels.size());
   List<String> candFullPaths = new ArrayList<>(candRels.size());
   List<Long> candExpectedSizes = new ArrayList<>(candRels.size());
   for (String rel : candRels) {
    String mapped = OfficialAndroidClient.manifestNameFromRelativePath(rel);
    String name = mapped != null ? mapped : rel.substring(rel.lastIndexOf('/') + 1);
    candNames.add(name);
    OfficialAndroidClient.FileEntry rec = localManifest.files.get(name);
    candFullPaths.add(fullOfficialPath(rel));
    candExpectedSizes.add(rec != null ? rec.size : -1L);
   }

   step("Đang đối chiếu MD5 " + candRels.size() + " tệp với ss_and.mani...", 22);
   List<DeviceMd5State> devStates = batchMd5States(candFullPaths, candExpectedSizes);

   List<OfficialTarget> targets = new ArrayList<>();
   List<OfficialTarget> todo = new ArrayList<>();
   int alreadyOfficial = 0;
   int repairedPending = 0;
   for (int i = 0; i < candRels.size(); i++) {
    String rel = candRels.get(i);
    boolean fromReceipt = Boolean.TRUE.equals(candidateMap.get(rel));
    String name = candNames.get(i);
    DeviceMd5State st = devStates.get(i);
    OfficialAndroidClient.FileEntry rec = localManifest.files.get(name);
    if (rec == null) {
     if ((fromReceipt || strayNewRels.contains(rel)) && st.exists && !"data.arcx".equals(name) && !"lua.arcx".equals(name)) {
      OfficialTarget t = new OfficialTarget(rel, name, candFullPaths.get(i), "delete", 0L, "", true);
      targets.add(t);
      todo.add(t);
     }
     continue;
    }
    if (st.exists && st.size == rec.size && rec.checksum.equalsIgnoreCase(st.md5)) {
     alreadyOfficial++;
     targets.add(new OfficialTarget(rel, name, candFullPaths.get(i), "keep", rec.size, rec.checksum, true));
     continue;
    }
    boolean mustReplace;
    if (st.exists) {
     // File exists in Persistent_Store with WRONG size or MD5 (Vietnamese, stale, corrupted, or half-patched!)
     mustReplace = true;
    } else {
     boolean inBaseSame = catalog != null
       && catalog.baseFiles.containsKey(name)
       && catalog.baseFiles.get(name).checksum.equalsIgnoreCase(rec.checksum);
     if ("data.arcx".equals(name) || "lua.arcx".equals(name)) {
      mustReplace = true;
     } else if (pendingNames.contains(name)) {
      // On Android, ALL game bundles & SoundBanks live in Persistent_Store/ (no desktop InstallResource!).
      // NEVER skip a missing core pending 'U' target even if inBaseSame == true!
      mustReplace = rec.packageTag.isEmpty() || activePackageTags.contains(rec.packageTag);
     } else if (name.endsWith(".en.unity3d") || name.endsWith(".srt")) {
      mustReplace = !inBaseSame || fvAudit.allRels.contains(rel);
     } else {
      mustReplace = false;
     }
    }
    if (mustReplace) {
     OfficialTarget t = new OfficialTarget(rel, name, candFullPaths.get(i), "replace", rec.size, rec.checksum, st.exists);
     targets.add(t);
     todo.add(t);
     if (pendingTrackedRels.contains(rel)) repairedPending++;
    }
   }

   // Resolve every REPLACE target: Tier 1 exact-MD5 local backup -> Tier 2 official Yostar Android CDN + BSDIFF40
   Map<Long, List<File>> backupsBySize = indexLocalBackupsBySize(binding);
   List<OfficialTarget> needCdn = new ArrayList<>();
   int fromBackup = 0;
   for (OfficialTarget t : todo) {
    if (!"replace".equals(t.action)) continue;
    File bak = findVerifiedBackup(backupsBySize, t.expectedSize, t.expectedMd5);
    if (bak != null) {
     t.sourceFile = bak;
     t.sourceKind = "backup";
     fromBackup++;
    } else {
     needCdn.add(t);
    }
   }

   int fromCdn = 0;
   if (!needCdn.isEmpty()) {
    if (catalog == null) {
     throw new IOException(
       "Cần kết nối mạng để tải " + needCdn.size() + " tệp gốc từ máy chủ Yostar (bản sao lưu cục bộ bị thiếu hoặc không khớp MD5 ss_and.mani): "
         + (cdnFetchError != null ? Store.cleanError(cdnFetchError) : "không có mạng."),
       cdnFetchError
     );
    }
    long needBytes = 0L;
    for (OfficialTarget t : needCdn) {
     if (!catalog.knows(t.name, t.expectedMd5)) {
      throw new IOException(
        "Máy chủ Yostar không còn lưu phiên bản cũ của " + t.name + " (" + t.expectedMd5.substring(0, 8)
          + "…). Hãy mở Stella Sora → bấm nút Sửa tài nguyên (Repair) trên màn hình chính hoặc cài lại game từ Google Play."
      );
     }
     needBytes += t.expectedSize;
    }
    if (new StatFs(cdnCache.getAbsolutePath()).getAvailableBytes() < needBytes + 33554432L) {
     throw new IOException("Không đủ bộ nhớ trống để tải và xác minh tài nguyên gốc từ Yostar.");
    }
    for (int i = 0; i < needCdn.size(); i++) {
     OfficialTarget t = needCdn.get(i);
     final int idx = i + 1;
     final int totalNeed = needCdn.size();
     int pct = 28 + (36 * i / Math.max(1, totalNeed));
     step("Đang tải bản gốc Yostar (" + idx + "/" + totalNeed + "): " + t.name, pct);
     File f = catalog.materialize(t.name, t.expectedMd5, cdnCache, 25000, msg -> {
      try { step(msg + " (" + idx + "/" + totalNeed + ")", pct); } catch (Exception ignored) {}
     });
     ownExternalPath(f);
     if (!OfficialAndroidClient.matchesMd5(f, t.expectedSize, t.expectedMd5)) {
      throw new IOException("Tệp tải từ Yostar sai MD5: " + t.name);
     }
     t.sourceFile = f;
     t.sourceKind = "cdn";
     fromCdn++;
    }
   }

   DiagnosticLog.log(context, "restore",
     "Kế hoạch khôi phục gốc Android (RES " + localResVer + "): thay " + (fromBackup + fromCdn)
       + " tệp (backup MD5 chuẩn=" + fromBackup + ", Yostar CDN=" + fromCdn
       + "), giữ nguyên " + alreadyOfficial + " tệp đã chuẩn, xoá " + (todo.size() - fromBackup - fromCdn) + " tệp Việt hoá riêng.");

   // Apply atomically with rollback safety
   if (!todo.isEmpty()) {
    List<String> todoRels = new ArrayList<>(todo.size());
    for (OfficialTarget t : todo) todoRels.add(t.rel);
    ensureAndVerifyOfficialDirs(todoRels);
    closedAndVersion();

    List<OfficialTarget> applied = new ArrayList<>();
    List<File> rollbackCopies = new ArrayList<>();
    long lastVerCheck = SystemClock.elapsedRealtime();
    try {
     for (int i = 0; i < todo.size(); i++) {
      if (i > 0 && (i % 15 == 0 || SystemClock.elapsedRealtime() - lastVerCheck >= 2500L)) {
       closedAndVersion();
       lastVerCheck = SystemClock.elapsedRealtime();
      }
      OfficialTarget t = todo.get(i);
      File rb = t.existedBefore ? new File(rollbackDir, i + ".prev") : null;
      applyOfficialTargetAtomic(id, t, rb);
      applied.add(t);
      rollbackCopies.add(rb);
      step("Đang khôi phục bản gốc (" + (i + 1) + "/" + todo.size() + "): " + t.name, 65 + (25 * (i + 1) / Math.max(1, todo.size())));
     }

     // Final batch MD5 readback verification across ALL replaced files
     List<String> checkPaths = new ArrayList<>();
     List<Long> checkSizes = new ArrayList<>();
     List<OfficialTarget> replacedList = new ArrayList<>();
     for (OfficialTarget t : todo) {
      if ("replace".equals(t.action)) {
       checkPaths.add(t.destPath);
       checkSizes.add(t.expectedSize);
       replacedList.add(t);
      }
     }
     if (!checkPaths.isEmpty()) {
      step("Đang xác minh MD5 toàn bộ tệp sau khôi phục...", 92);
      List<DeviceMd5State> finalStates = batchMd5States(checkPaths, checkSizes);
      for (int i = 0; i < replacedList.size(); i++) {
       OfficialTarget t = replacedList.get(i);
       DeviceMd5State fs = finalStates.get(i);
       if (!fs.exists || fs.size != t.expectedSize || !t.expectedMd5.equalsIgnoreCase(fs.md5)) {
        throw new IOException("Xác minh MD5 sau khôi phục thất bại: " + t.rel);
       }
      }
     }
    } catch (Exception applyErr) {
     // Best-effort rollback of already-swapped files
     for (int i = applied.size() - 1; i >= 0; i--) {
      OfficialTarget t = applied.get(i);
      File rb = rollbackCopies.get(i);
      try {
       if (t.existedBefore && rb != null && rb.isFile()) {
        adb.exec("cp " + Store.q(rb.getCanonicalPath()) + " " + Store.q(t.destPath) + " || true", 60000);
       } else if (!t.existedBefore) {
        adb.exec("rm -f " + Store.q(t.destPath) + " || true", 15000);
       }
      } catch (Exception ignored) {}
     }
     throw applyErr;
    }
   }

   step("Đang đồng bộ Hotfix.dll, file_versions.dat và dọn bộ nhớ tạm...", 95);
   File replacedHotfixArch = null;
   Map<String, String> verifiedRelToMd5 = new LinkedHashMap<>();
   Set<String> deletedRels = new HashSet<>();
   for (OfficialTarget t : targets) {
    if ("delete".equals(t.action)) {
     deletedRels.add(t.rel);
    } else if (("keep".equals(t.action) || "replace".equals(t.action)) && t.expectedMd5 != null && !t.expectedMd5.isEmpty()) {
     verifiedRelToMd5.put(t.rel, t.expectedMd5);
     if ("replace".equals(t.action) && "hotfix.arch".equals(t.name) && t.sourceFile != null) {
      replacedHotfixArch = t.sourceFile;
     }
    }
   }
   boolean hotfixDllSynced = syncHotfixDllFromArchive(id, stage, replacedHotfixArch);

   int fvSynced = 0;
   if (fvText != null) {
    Set<String> postExisting = null;
    if (treeScan.existingRels != null) {
     postExisting = new HashSet<>(treeScan.existingRels);
     postExisting.addAll(verifiedRelToMd5.keySet());
     postExisting.removeAll(deletedRels);
    }
    OfficialAndroidClient.SyncedFileVersions syncedFv = OfficialAndroidClient.buildSyncedFileVersionsText(
      fvText, localResVer, localManifest.files, verifiedRelToMd5, deletedRels, postExisting, "Persistent_Store/ss_and.mani"
    );
    if (syncedFv.text != null && syncedFv.changes > 0) {
     File fvOut = new File(stage, "synced_file_versions.dat");
     Files.write(fvOut.toPath(), syncedFv.text.getBytes(StandardCharsets.UTF_8));
     pushRootFileAtomic(id, "file_versions.dat", fvOut);
     fvSynced = syncedFv.changes;
    }
   }

   boolean prefsSynced = false;
   if (prefsText != null && catalog != null) {
    Integer exactStep = catalog.stepForResourceVersion(localResVer);
    if (exactStep != null) {
     String updatedPrefs = OfficialAndroidClient.syncPrefsPatchVersionText(prefsText, exactStep);
     if (updatedPrefs != null) {
      File prefsOut = new File(stage, "synced_prefs.dat");
      Files.write(prefsOut.toPath(), updatedPrefs.getBytes(StandardCharsets.UTF_8));
      pushRootFileAtomic(id, "prefs.dat", prefsOut);
      prefsSynced = true;
     }
    }
   }

   int cleanedTemp = cleanGamePatchCaches();
   int cleanedOrphans = cleanOrphanedManifests(expectedPatchMani);
   markReceiptChainRestored(binding);
   cleanStaleStaging();
   pruneHistory(binding, null);
   OfficialAndroidClient.clearGuardAlertAfterRestore(context);

   int replacedCount = fromBackup + fromCdn;
   int deletedCount = todo.size() - replacedCount;
   String summaryMsg = "Đã khôi phục dữ liệu gốc chuẩn MD5 (RES " + localResVer + "): thay " + replacedCount
     + " tệp (" + fromCdn + " tải từ Yostar, " + fromBackup + " từ backup chuẩn), giữ " + alreadyOfficial
     + " tệp đã gốc" + (deletedCount > 0 ? ", gỡ " + deletedCount + " tệp thừa/Việt hoá" : "")
     + (fvSynced > 0 ? ", đồng bộ " + fvSynced + " mục file_versions.dat" : "")
     + (hotfixDllSynced ? ", đồng bộ Hotfix.dll" : "")
     + (cleanedTemp > 0 ? ", dọn " + cleanedTemp + " tệp tạm cập nhật" : "")
     + (cleanedOrphans > 0 ? ", dọn " + cleanedOrphans + " bảng kê thừa" : "") + ".";
   DiagnosticLog.log(context, "restore", summaryMsg);
   step("Đã hoàn tất khôi phục dữ liệu gốc chuẩn MD5.", 100);
   restoreSucceeded = true;
   return Store.obj(
     "replaced", replacedCount,
     "alreadyOfficial", alreadyOfficial,
     "deleted", deletedCount,
     "fromBackup", fromBackup,
     "fromCdn", fromCdn,
     "repairedPending", repairedPending,
     "hotfixDllSynced", hotfixDllSynced,
     "fileVersionsSynced", fvSynced,
     "prefsSynced", prefsSynced,
     "cleanedTempFiles", cleanedTemp,
     "cleanedOrphanedManifests", cleanedOrphans,
     "resourceVersion", localResVer,
     "message", summaryMsg
   );
  } finally {
   deleteTree(stage);
   if (restoreSucceeded) deleteTree(cdnCache);
  }
 }

 private void restoreLegacyReceiptChain(String binding) throws Exception {
  File f = receipt(binding);
  Set<String> visited = new HashSet<>();
  while (f.isFile()) {
   JSONObject r = Store.read(f);
   String jid = r.getString("journal_id");
   if (!visited.add(jid)) {
    throw new IOException("Phát hiện vòng lặp biên bản phục hồi: " + jid);
   }
   JSONObject j = Store.read(journalFile(jid));
   if (visited.size() > 1
     && (!j.optString("gameVersion").equals(target.optString("gameVersion"))
       || !j.optString("resourceVersion").equals(target.optString("resourceVersion")))) {
    if (!f.delete()) throw new IOException("Chưa xoá được biên bản cũ sau khôi phục.");
    break;
   }
   restoreJournal(j, true);
  }
 }

 JSONObject recover() throws Exception {
  verifiedExternalBase = null;
  deadline = SystemClock.elapsedRealtime() + 5400000;
  requireTarget();
  if (!pending()) throw new IOException("Không có thao tác bị ngắt cần phục hồi.");
  JSONObject j = Store.read(active());
  checkIdentity(j);
  String id = j.getString("id");
  String binding = j.getString("binding");
  if (!j.optString("gameVersion").equals(target.optString("gameVersion"))
    || !j.optString("resourceVersion").equals(target.optString("resourceVersion"))) {
   try { cleanupTemps(j, false); } catch (Exception ignored) {}
   j.remove("pending");
   j.put("state", "SUPERSEDED");
   saveJournal(j);
   cleanStaleStaging();
   pruneHistory(binding, null);
   return Store.obj(
     "state", "SUPERSEDED",
     "message", "Game đã cập nhật sang phiên bản mới; nhật ký cũ đã được đóng an toàn (không ghi đè tệp mới). Bạn có thể cài bản Việt hoá mới ngay."
   );
  }
  bound(j);
  if ("PREPARING".equals(j.optString("state"))) {
   try { cleanupTemps(j, false); } catch (Exception ignored) {}
   j.remove("pending");
   j.put("state", "ABORTED");
   saveJournal(j);
   cleanStaleStaging();
   pruneHistory(binding, null);
   return Store.obj("state", "ABORTED", "message", "Đã đóng nhật ký chuẩn bị chưa hoàn tất.");
  }
  restoreJournal(j, false);
  cleanStaleStaging();
  pruneHistory(binding, null);
  return Store.obj("state", j.optString("state", "ROLLED_BACK"), "message", "Đã phục hồi nhật ký chưa hoàn tất.");
 }

 private void restoreJournal(JSONObject j, boolean explicitRestore) throws Exception {
  bound(j);
  closedAndVersion();
  ensureExternalBase();
  JSONArray files = j.getJSONArray("files");
  String id = j.getString("id");
  List<String> relPaths = new ArrayList<>(files.length());
  List<String> destPaths = new ArrayList<>(files.length());
  for (int i = 0; i < files.length(); i++) {
   String rel = relative(files.getJSONObject(i).getString("path"));
   relPaths.add(rel);
   destPaths.add(fullPath(rel));
  }
  if (!relPaths.isEmpty()) verifySafeDirectories(relPaths);
  List<JSONObject> currentStates = batchStates(destPaths);
  List<String> driftedPaths = new ArrayList<>();
  int alreadyVanilla = 0;
  for (int i = 0; i < files.length(); i++) {
   JSONObject f = files.getJSONObject(i);
   JSONObject current = currentStates.get(i);
   JSONObject before = f.getJSONObject("before");
   JSONObject after = f.getJSONObject("after");
   boolean isBefore = same(current, before);
   boolean isAfter = same(current, after);
   if (isBefore) {
    alreadyVanilla++;
    continue;
   }
   if (!isAfter) {
    if (!explicitRestore) {
     throw new IOException("Tệp đã đổi ngoài thao tác; giữ nguyên: " + f.getString("path"));
    }
    driftedPaths.add(f.getString("path"));
   }
   if (before.getBoolean("exists")) {
    File bFile = new File(f.getString("backup"));
    ownExternalPath(bFile);
    if (!bFile.isFile() || bFile.length() != before.getLong("size") || !Store.hash(bFile).equalsIgnoreCase(before.getString("sha256"))) {
     throw new IOException("Backup bị thiếu hoặc sai SHA256: " + f.getString("path"));
    }
   }
  }
  if (!driftedPaths.isEmpty()) {
   DiagnosticLog.log(context, "restore",
     "Phát hiện " + driftedPaths.size() + " tệp khác biên bản sau cài (VD: " + driftedPaths.get(0)
       + "); tiếp tục khôi phục bản sao lưu gốc đã xác minh SHA256 cho game "
       + j.optString("gameVersion") + "/" + j.optString("resourceVersion") + ".");
  }
  if (alreadyVanilla > 0) {
   DiagnosticLog.log(context, "restore",
     "Bỏ qua " + alreadyVanilla + " tệp đã ở đúng trạng thái gốc trước cài.");
  }

  j.put("state", "RESTORING");
  saveJournal(j);
  long lastVerCheck = SystemClock.elapsedRealtime();
  int mutatedCount = 0;
  for (int i = 0; i < files.length(); i++) {
   JSONObject f = files.getJSONObject(i);
   JSONObject before = f.getJSONObject("before");
   JSONObject current = currentStates.get(i);
   if (same(current, before)) {
    continue;
   }
   if (mutatedCount > 0 && (mutatedCount % 15 == 0 || SystemClock.elapsedRealtime() - lastVerCheck >= 2500L)) {
    closedAndVersion();
    lastVerCheck = SystemClock.elapsedRealtime();
   }
   restoreFileAtomic(j, id, f, current);
   mutatedCount++;
   step("Đã phục hồi " + (i + 1) + " / " + files.length(), 92 * (i + 1) / Math.max(1, files.length()));
  }

  closedAndVersion();
  if (!relPaths.isEmpty()) {
   verifySafeDirectories(relPaths);
   List<JSONObject> restoredStates = batchStates(destPaths);
   for (int i = 0; i < files.length(); i++) {
    JSONObject f = files.getJSONObject(i);
    if (!same(restoredStates.get(i), f.getJSONObject("before"))) {
     throw new IOException("Đọc lại phục hồi không khớp: " + f.getString("path"));
    }
   }
  }
  cleanupTemps(j, true);
  File rp = receipt(target.getString("binding"));
  Object previous = j.opt("previous_receipt");
  if (previous instanceof JSONObject) {
   Store.write(rp, (JSONObject) previous);
  } else if (rp.exists() && !rp.delete()) {
   throw new IOException("Chưa cập nhật được biên bản phục hồi.");
  }
  j.remove("pending");
  j.put("state", explicitRestore ? "RESTORED" : "ROLLED_BACK");
  saveJournal(j);
  step("Đã hoàn tất khôi phục tệp gốc.", 100);
 }

 private static void extractZip(File zipFile, File targetDir, Map<String, File> outMap) throws Exception {
  byte[] buffer = new byte[65536];
  String base = targetDir.getCanonicalPath();
  try (ZipInputStream zis = new ZipInputStream(new BufferedInputStream(new FileInputStream(zipFile)))) {
   ZipEntry ze;
   while ((ze = zis.getNextEntry()) != null) {
    if (ze.isDirectory()) continue;
    String name = new File(ze.getName()).getName();
    File target = new File(targetDir, name);
    if (!target.getCanonicalPath().startsWith(base + File.separator) || Files.isSymbolicLink(target.toPath())) {
     throw new SecurityException("Phát hiện tệp zip vượt giới hạn: " + ze.getName());
    }
    try (FileOutputStream fos = new FileOutputStream(target); BufferedOutputStream bos = new BufferedOutputStream(fos, buffer.length)) {
     int len;
     while ((len = zis.read(buffer)) > 0) bos.write(buffer, 0, len);
    }
    zis.closeEntry();
    outMap.put(name, target);
   }
  } catch (ZipException ze) {
   throw new StellaException("E-ZIP-CORRUPT", "Lỗi khi giải nén AssetBundles: " + Store.cleanError(ze), ze, "file", zipFile.getName());
  } catch (OutOfMemoryError oom) {
   throw new StellaException("E-MEMORY", "Thiết bị không đủ bộ nhớ RAM khi giải nén AssetBundles.", oom, "file", zipFile.getName());
  }
 }
}
