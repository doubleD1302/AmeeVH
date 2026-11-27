package com.stellasora.viethoa.localadb;
import android.Manifest;
import android.app.*;
import android.content.*;
import android.content.pm.*;
import android.content.res.Configuration;
import android.net.Uri;
import android.os.*;
import org.json.*;
import java.io.*;
import java.lang.ref.WeakReference;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;

/** Foreground owner of work and durable journals; Activity may leave for Settings. */
public final class LauncherService extends Service {
 interface Listener { void event(JSONObject e); }
 private static volatile LauncherService live;
 private static WeakReference<Listener> listener = new WeakReference<>(null);
 private static final ExecutorService probeExecutor = Executors.newSingleThreadExecutor();

 static void listen(Listener l) { listener = new WeakReference<>(l); }
 static void unlisten(Listener l) {
  if (listener.get() == l) listener.clear();
  LauncherService s = live;
  if (s != null) s.main.post(s::finishIdle);
 }

 private final Handler main = new Handler(Looper.getMainLooper());
 private final ExecutorService worker = Executors.newSingleThreadExecutor();
 private final AtomicBoolean busy = new AtomicBoolean();
 private volatile boolean mutating;
 private volatile boolean destroying;
 private AdbClient adb;
 private GamePatcher patcher;
 private JSONObject state, manifest, updateMetadata;
 private volatile long manifestSyncedAt;
 private PowerManager.WakeLock wake;
 private PairingDiscovery discovery;
 private volatile long generation;
 private String nonce = "", pairHost = "";
 private int pairPort;
 private volatile boolean quickActive;
 private volatile boolean awaitingCode;
 private volatile boolean pendingGuardRestore;
 private long quickDeadline, lastPublish;

 static boolean isPinShortcutSupported(Context c) {
  try {
   android.content.pm.ShortcutManager sm = c.getSystemService(android.content.pm.ShortcutManager.class);
   return sm != null && sm.isRequestPinShortcutSupported();
  } catch (Exception ignored) {
   return false;
  }
 }

 static final int NOTICE = 4101;
 static final String PAIR_CHANNEL = "stella_pairing_v1", WORK_CHANNEL = "stella_work_v1";

 static boolean isDevOptions(Context c) {
  try {
   return android.provider.Settings.Global.getInt(c.getContentResolver(), android.provider.Settings.Global.DEVELOPMENT_SETTINGS_ENABLED, 0) != 0;
  } catch (Exception e) {
   return false;
  }
 }

 static String resolveTheme(Context c, String pref) {
  String norm = Store.normalizeTheme(pref);
  if ("dark".equals(norm) || "light".equals(norm)) return norm;
  int night = c.getResources().getConfiguration().uiMode & Configuration.UI_MODE_NIGHT_MASK;
  return night == Configuration.UI_MODE_NIGHT_YES ? "dark" : "light";
 }

 static JSONObject deviceInfo() {
  return Store.obj(
    "manufacturer", Build.MANUFACTURER,
    "brand", Build.BRAND,
    "model", Build.MODEL,
    "release", Build.VERSION.RELEASE,
    "sdk", Build.VERSION.SDK_INT,
    "oemFamily", ErrorReport.oemFamily()
  );
 }

 static JSONObject base(Context c) {
  JSONObject cfg;
  String warning = "";
  try {
   cfg = Store.config(c);
  } catch (Exception e) {
   cfg = Store.obj("repo", "", "branch", "", "host", "127.0.0.1", "connection_port", 0, "theme", "system");
   warning = "Cấu hình chưa đọc được. Hãy sửa và lưu trong Cài đặt.";
  }
  String themePref = Store.normalizeTheme(cfg.optString("theme", "system"));
  String resolvedTheme = resolveTheme(c, themePref);
  JSONObject support;
  try {
   support = Store.asset(c, "support/payment_methods.json");
  } catch (Exception e) {
   support = Store.obj("methods", new JSONArray());
  }
  String appVer = "2.1.5";
  long appCode = 28;
  try {
   PackageInfo pi = c.getPackageManager().getPackageInfo(Store.APP, 0);
   appVer = pi.versionName;
   appCode = pi.getLongVersionCode();
  } catch (Exception ignored) {}
  boolean hasId = KeyMaterial.hasIdentity(c);
  return Store.obj(
    "busy", false,
    "mutating", false,
    "phase", "idle",
    "message", warning.isEmpty() ? (hasId ? "Máy đã ghép đôi trước đó. Bấm Kết nối nhanh Local ADB để dùng ngay." : "Chưa kết nối Local ADB.") : warning,
    "progress", Store.obj("percent", 0, "indeterminate", false, "label", ""),
    "devOptionsEnabled", isDevOptions(c),
    "device", deviceInfo(),
    "lastError", ErrorReport.lastSummary(c),
    "adb", Store.obj(
      "connected", false,
      "paired", hasId,
      "hasIdentity", hasId,
      "host", cfg.optString("host", "127.0.0.1"),
      "pairingPort", 0,
      "connectionPort", cfg.optInt("connection_port", 0),
      "status", hasId ? "Đã có khóa ghép đôi · Chưa kết nối" : "Chưa kết nối",
      "ownHosts", AdbClient.ownAddresses(),
      "notificationPairing", Store.obj("active", false, "stage", "", "message", "Có thể ghép đôi từ thông báo hoặc nhập cổng thủ công.")
    ),
    "game", Store.obj("installed", false, "package", Store.GAME, "versionsKnown", false),
    "github", Store.obj("repo", cfg.optString("repo"), "branch", cfg.optString("branch"), "announcementStatus", "unavailable", "manifestStatus", "unavailable", "message", "Chưa đồng bộ GitHub."),
    "notifications", new JSONArray(),
    "payload", Store.obj("available", false, "compatible", false, "updateAvailable", false, "reason", "Chưa có thông tin gói Android tương thích."),
    "config", Store.obj("repo", cfg.optString("repo"), "branch", cfg.optString("branch"), "host", cfg.optString("host", "127.0.0.1"), "connectionPort", cfg.optInt("connection_port", 0), "theme", themePref),
    "update", Store.obj("available", false, "downloaded", false, "message", "Chưa kiểm tra bản APK Local ADB mới."),
    "recovery", Store.obj("pending", GamePatcher.hasPending(c), "message", ""),
    "receipt", Store.obj("present", false),
    "officialUpdate", OfficialAndroidClient.readCachedGuardState(c),
    "guard", Store.obj(
      "accessibilityEnabled", GameLaunchGuardService.isEnabled(c),
      "overlayEnabled", GameLaunchGuardService.canDrawOverlay(c),
      "canPinShortcut", isPinShortcutSupported(c),
      "pendingRestore", false
    ),
    "support", support,
    "app", Store.obj("applicationId", Store.APP, "versionName", appVer, "versionCode", appCode, "variant", "localadb", "theme", themePref, "resolvedTheme", resolvedTheme)
  );
 }

 static JSONObject snapshot(Context c) {
  LauncherService s = live;
  if (s == null) return base(c);
  synchronized (s) {
   try {
    JSONObject j = new JSONObject(s.state.toString());
    j.put("busy", s.busy.get());
    j.put("mutating", s.mutating);
    j.put("devOptionsEnabled", isDevOptions(c));
    j.put("device", deviceInfo());
    j.put("lastError", ErrorReport.lastSummary(c));
    String themePref = Store.theme(c);
    j.getJSONObject("config").put("theme", themePref);
    JSONObject appObj = j.getJSONObject("app");
    appObj.put("theme", themePref);
    appObj.put("resolvedTheme", resolveTheme(c, themePref));
    JSONObject adbObj = j.getJSONObject("adb");
    adbObj.put("connected", s.adb != null && s.adb.verified);
    adbObj.put("hasIdentity", KeyMaterial.hasIdentity(c));
    j.put("officialUpdate", OfficialAndroidClient.readCachedGuardState(c));
    j.put("guard", Store.obj(
      "accessibilityEnabled", GameLaunchGuardService.isEnabled(c),
      "overlayEnabled", GameLaunchGuardService.canDrawOverlay(c),
      "canPinShortcut", isPinShortcutSupported(c),
      "pendingRestore", s.pendingGuardRestore
    ));
    return j;
   } catch (Exception e) {
    return base(c);
   }
  }
 }

 static void dispatch(Context c, String action, JSONObject args) {
  Intent i = new Intent(c, LauncherService.class).putExtra("action", action).putExtra("args", args.toString());
  try {
   c.startForegroundService(i);
  } catch (RuntimeException fgError) {
   try {
    c.startService(i);
   } catch (RuntimeException fallbackError) {
    DiagnosticLog.log(c, "service", "startService blocked: " + Store.cleanError(fallbackError));
    JSONObject report = ErrorReport.record(c, ErrorReport.build(c, action, "Tác vụ nền bị chặn",
      "Hệ thống tiết kiệm pin đang chặn khởi chạy dịch vụ nền (" + Store.cleanError(fallbackError) + ").",
      fallbackError, "E-OEM-BG-RESTRICT", snapshot(c)));
    Listener l = listener.get();
    if (l != null) {
     l.event(Store.obj("type", "message", "data", ErrorReport.attach(Store.obj("title", "Tác vụ nền bị chặn", "message", report.optString("message"), "error", true), report)));
    }
   }
  }
 }

 /** Runs non-blocking async network probe (DNS + TCP:443 + Captive Portal) and updates the Smart Error Dialog live. */
 static void probeNetwork(Context c, String reportId) {
  final Context appCtx = c.getApplicationContext();
  probeExecutor.execute(() -> {
   DiagnosticLog.log(appCtx, "probe", "Bắt đầu đo DNS/TCP:443/Captive Portal");
   JSONObject probe = ErrorReport.probe(appCtx);
   JSONObject updatedReport = (reportId != null && !reportId.isEmpty())
     ? ErrorReport.attachProbe(appCtx, reportId, probe) : null;
   JSONArray lines = new JSONArray();
   for (String ln : ErrorReport.formatProbe(probe)) lines.put(ln);
   JSONObject payload = Store.obj(
     "reportId", reportId == null ? "" : reportId,
     "verdict", probe.optString("verdict"),
     "verdictText", probe.optString("verdictText"),
     "durationMs", probe.optLong("durationMs", 0),
     "lines", lines
   );
   if (updatedReport != null) {
    try {
     payload.put("contextRows", updatedReport.optJSONArray("contextRows"));
     payload.put("reportPreview", ErrorReport.text(updatedReport));
    } catch (JSONException ignored) {}
   }
   DiagnosticLog.log(appCtx, "probe", "Kết quả đo mạng: " + probe.optString("verdict") + " (" + probe.optLong("durationMs") + "ms)");
   Listener l = listener.get();
   if (l != null) l.event(Store.obj("type", "probeResult", "data", payload));
  });
 }

 @Override public void onCreate() {
  super.onCreate();
  live = this;
  state = base(this);
  adb = new AdbClient(this);
  patcher = new GamePatcher(this, adb, (message, percent) -> progress(message, percent));
  adb.onLoss = () -> {
   if (!adb.verified) {
    DiagnosticLog.log(this, "adb", "Kết nối Local ADB đã đóng hoặc mất xác nhận.");
    setAdb("status", "Kết nối chưa được xác nhận hoặc đã đóng. Hãy kết nối lại.");
    try { refreshPayload(); } catch (Exception ignored) {}
    publish(true);
   }
  };
  NotificationManager manager = getSystemService(NotificationManager.class);
  manager.createNotificationChannel(new NotificationChannel(WORK_CHANNEL, "Tác vụ Stella Sora", NotificationManager.IMPORTANCE_LOW));
  NotificationChannel pairing = new NotificationChannel(PAIR_CHANNEL, "Ghép đôi Local ADB", NotificationManager.IMPORTANCE_HIGH);
  pairing.setDescription("Nhập mã ghép đôi khi đang ở Gỡ lỗi không dây");
  manager.createNotificationChannel(pairing);
  PowerManager power = (PowerManager) getSystemService(POWER_SERVICE);
  wake = power.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "StellaSora:Operation");
  wake.setReferenceCounted(false);
 }

 @Override public IBinder onBind(Intent i) { return null; }

 @Override public int onStartCommand(Intent i, int flags, int startId) {
  foreground("Đang xử lý yêu cầu…");
  if (i == null) {
   finishIdle();
   return START_NOT_STICKY;
  }
  String action = i.getStringExtra("action");
  try {
   JSONObject args = new JSONObject(i.getStringExtra("args") == null ? "{}" : i.getStringExtra("args"));
   if ("startPairingNotification".equals(action)) startQuickPair();
   else if ("cancelPairing".equals(action)) cancelQuick();
   else if ("disconnect".equals(action)) {
    if (busy.get()) {
     message("Đang có thao tác", "Hãy chờ thao tác hoàn tất trước khi ngắt kết nối.", true);
    } else {
     cancelQuick();
     adb.disconnect();
     DiagnosticLog.log(this, "adb", "Người dùng ngắt kết nối Local ADB.");
     setMessage("Đã ngắt Local ADB.");
     publish(true);
     finishIdle();
    }
   } else runTask(action, args);
  } catch (Exception e) {
   message("Không thể thực hiện", Store.cleanError(e), true);
   finishIdle();
  }
  return START_NOT_STICKY;
 }

 private void runTask(String action, JSONObject args) {
  if (!busy.compareAndSet(false, true)) {
   message("Đang có thao tác", "Hãy chờ thao tác đang chạy hoàn tất.", true);
   return;
  }
  DiagnosticLog.log(this, action, "Bắt đầu thao tác");
  mutating = Arrays.asList("install", "restore", "guardRestore", "recover").contains(action);
  long startedGeneration = generation;
  set("phase", action);
  set("progress", Store.obj("percent", 0, "indeterminate", true, "label", "Đang thực hiện…"));
  setMessage("Đang thực hiện…");
  if ("pair".equals(action) || "autoConnect".equals(action)) {
   awaitingCode = false;
   closeDiscovery();
  }
  if (!wake.isHeld()) wake.acquire(5700000);
  publish(true);

  worker.execute(() -> {
   boolean beginAutoConnect = false;
   boolean promptWirelessIfSlow = false;
   boolean emitUpdatePrepared = false;
   boolean continueGuardRestore = false;
   try {
    switch (action) {
     case "sync": {
      JSONObject result = new ChannelClient(this).sync();
      manifest = result.optJSONObject("manifest");
      manifestSyncedAt = manifest != null ? SystemClock.elapsedRealtime() : 0L;
      if (manifest != null) {
       JSONObject receipt = snapshot(this).optJSONObject("receipt");
       UpdateNotice.observe(this, result.optString("repo") + "/" + result.optString("branch"), manifest.optString("version"), result.optString("releaseNotes"), receipt != null && receipt.optBoolean("present") ? receipt.optString("version") : UpdateNotice.installed(this), false);
      }
      String syncCode = result.optString("errorCode");
      if (!syncCode.isEmpty()) {
       JSONObject snap = snapshot(this);
       snap.put("github", result);
       JSONObject rep = ErrorReport.record(this, ErrorReport.build(this, "sync", "Đồng bộ GitHub", result.optString("errorRaw"), null, syncCode, snap));
       result.put("errorReportId", rep.optString("reportId"));
       result.put("errorTitle", rep.optString("errorTitle"));
      }
      set("github", result);
      set("notifications", result.optJSONArray("notifications") == null ? new JSONArray() : result.getJSONArray("notifications"));
      try {
       JSONObject curGame = snapshot(this).optJSONObject("game");
       String lg = (curGame != null && curGame.optBoolean("versionsKnown")) ? curGame.optString("gameVersion", "") : null;
       String lr = (curGame != null && curGame.optBoolean("versionsKnown")) ? curGame.optString("resourceVersion", "") : null;
       JSONObject off = OfficialAndroidClient.checkAndSave(this, 6000, lg, lr);
       set("officialUpdate", off);
       OfficialUpdateNotice.notifyIfNeeded(this, off);
      } catch (Exception ignored) {}
      String msg = result.optString("message", "Đã đọc trạng thái GitHub.");
      DiagnosticLog.log(this, "sync", msg);
      setMessage(msg);
      break;
     }
     case "checkOfficialUpdate": {
      JSONObject curGame = snapshot(this).optJSONObject("game");
      String lg = (curGame != null && curGame.optBoolean("versionsKnown")) ? curGame.optString("gameVersion", "") : null;
      String lr = (curGame != null && curGame.optBoolean("versionsKnown")) ? curGame.optString("resourceVersion", "") : null;
      JSONObject off = OfficialAndroidClient.checkAndSave(this, 10000, lg, lr);
      set("officialUpdate", off);
      OfficialUpdateNotice.notifyIfNeeded(this, off);
      String msg = off.optBoolean("needsRestore")
        ? ("Yostar đã phát hành bản cập nhật mới (RES " + off.optString("latestResourceVersion") + "). Hãy khôi phục dữ liệu gốc trước khi vào game!")
        : ("Máy chủ Yostar hiện tại: v" + off.optString("latestGameVersion", "?") + " · RES " + off.optString("latestResourceVersion", "?") + ".");
      DiagnosticLog.log(this, "checkOfficialUpdate", msg);
      setMessage(msg);
      break;
     }
     case "saveSettings": {
      saveSettings(args);
      DiagnosticLog.log(this, "settings", "Đã lưu cài đặt cục bộ.");
      setMessage("Đã lưu cài đặt trên máy. Không tải cấu hình cá nhân lên mạng.");
      break;
     }
     case "resetChannel": {
      JSONObject cfg;
      try { cfg = Store.config(this); } catch (Exception ignored) { cfg = Store.defaults(); }
      cfg.put("repo", Store.REPO);
      cfg.put("branch", "main");
      Store.validateConfig(cfg);
      synchronized (UpdateNotice.class) {
       Store.write(Store.internal(this, "config.json"), cfg);
       UpdateNotice.channelChanged(this);
      }
      set("config", configState(cfg));
      manifest = null;
      manifestSyncedAt = 0L;
      JSONObject result = new ChannelClient(this).sync();
      manifest = result.optJSONObject("manifest");
      manifestSyncedAt = manifest != null ? SystemClock.elapsedRealtime() : 0L;
      set("github", result);
      set("notifications", result.optJSONArray("notifications") == null ? new JSONArray() : result.getJSONArray("notifications"));
      DiagnosticLog.log(this, "resetChannel", "Đã khôi phục kênh mặc định và đồng bộ lại.");
      setMessage("Đã khôi phục kênh GitHub mặc định (doubleD1302/AmeeVH · main) và đồng bộ lại.");
      break;
     }
     case "pair": {
      if (!ErrorReport.isWifiConnected(this)) {
       throw new StellaException("E-ADB-NO-WIFI", "Điện thoại chưa kết nối Wi-Fi. Hãy bật Wi-Fi để dùng Gỡ lỗi không dây.", null);
      }
      adb.pair(args.getString("host"), args.getInt("pairingPort"), args.getString("code"));
      if (startedGeneration != generation) break;
      setAdb("paired", true);
      setAdb("hasIdentity", KeyMaterial.hasIdentity(this));
      setAdb("host", AdbClient.ownHost(args.getString("host")));
      setAdb("pairingPort", args.getInt("pairingPort"));
      setAdb("status", "Đã ghép nối; chưa kết nối.");
      DiagnosticLog.log(this, "pair", "Ghép đôi Local ADB thành công; đang dò cổng kết nối.");
      setMessage("Đã ghép nối. Đang tìm cổng kết nối riêng…");
      beginAutoConnect = true;
      break;
     }
     case "connect": {
      if (!ErrorReport.isWifiConnected(this)) {
       throw new StellaException("E-ADB-NO-WIFI", "Điện thoại chưa kết nối Wi-Fi. Hãy bật Wi-Fi để dùng Gỡ lỗi không dây.", null);
      }
      adb.connect(args.getString("host"), args.getInt("connectionPort"));
      if (startedGeneration != generation) {
       adb.cancelBroker();
       break;
      }
      recordConnectedEndpoint(args.getString("host"), args.getInt("connectionPort"), startedGeneration);
      if (startedGeneration != generation) break;
      closeDiscovery();
      quickActive = false;
      nonce = "";
      setPairing("connected", "Đã kết nối và nhận được phản hồi id hợp lệ.");
      if (startedGeneration != generation) break;
      detectGame();
      DiagnosticLog.log(this, "connect", "Đã kết nối Local ADB và kiểm tra game.");
      if (startedGeneration == generation) {
       setMessage("Đã kết nối Local ADB. Thông tin gói Android được kiểm tra riêng.");
       if (pendingGuardRestore) continueGuardRestore = true;
      }
      break;
     }
     case "autoConnect": {
      if (!isDevOptions(this)) {
       throw new StellaException("E-DEVOPT", "Hãy bật Tuỳ chọn nhà phát triển trước khi kết nối Local ADB.", null);
      }
      if (!ErrorReport.isWifiConnected(this)) {
       throw new StellaException("E-ADB-NO-WIFI", "Điện thoại chưa kết nối Wi-Fi. Gỡ lỗi không dây bắt buộc dùng Wi-Fi.", null);
      }
      if (adb.verified) {
       detectGame();
       setMessage("Local ADB đang kết nối sẵn sàng.");
       if (pendingGuardRestore) continueGuardRestore = true;
       break;
      }
      JSONObject cfg = Store.config(this);
      int savedPort = cfg.optInt("connection_port", 0);
      String rawHost = cfg.optString("host", "127.0.0.1");
      LinkedHashSet<String> candidateHosts = new LinkedHashSet<>();
      try { candidateHosts.add(AdbClient.ownHost(rawHost)); } catch (Exception ignored) {}
      candidateHosts.add("127.0.0.1");
      JSONArray ownIps = AdbClient.ownAddresses();
      for (int idx = 0; idx < ownIps.length(); idx++) {
       String ip = ownIps.optString(idx);
       if (!ip.isEmpty()) candidateHosts.add(ip);
      }
      boolean quickConnected = false;
      if (savedPort >= 1024 && savedPort <= 65535) {
       progress("Đang kết nối nhanh qua cổng đã lưu…", -1);
       for (String hostCandidate : candidateHosts) {
        if (startedGeneration != generation) break;
        try {
         adb.connect(hostCandidate, savedPort, 5000);
         if (startedGeneration != generation) {
          adb.cancelBroker();
          break;
         }
         recordConnectedEndpoint(hostCandidate, savedPort, startedGeneration);
         closeDiscovery();
         quickActive = false;
         nonce = "";
         setPairing("connected", "Đã kết nối nhanh Local ADB.");
         detectGame();
         DiagnosticLog.log(this, "autoConnect", "Kết nối nhanh qua cổng đã lưu thành công.");
         if (startedGeneration == generation) {
          setMessage("Đã kết nối nhanh Local ADB thành công.");
          if (pendingGuardRestore) continueGuardRestore = true;
         }
         quickConnected = true;
         break;
        } catch (StellaException authErr) {
         if ("E-ADB-AUTH".equals(authErr.code)) throw authErr;
        } catch (Exception ignored) {}
       }
      }
      if (!quickConnected && startedGeneration == generation) {
       beginAutoConnect = true;
       promptWirelessIfSlow = true;
       setAdb("status", "Đang tự tìm cổng Gỡ lỗi không dây…");
       DiagnosticLog.log(this, "autoConnect", "Cổng cũ không phản hồi; chuyển sang dò mDNS tự động.");
       setMessage("Đang tự dò cổng Gỡ lỗi không dây (không cần nhập lại mã 6 số)…");
      }
      break;
     }
     case "detect":
      detectGame();
      DiagnosticLog.log(this, "detect", "Hoàn tất kiểm tra game trên thiết bị.");
      setMessage("Đã đọc thông tin game thực tế từ thiết bị.");
      break;
     case "install": {
      JSONObject prefetched = (manifest != null && manifestSyncedAt > 0 && SystemClock.elapsedRealtime() - manifestSyncedAt < 60000L) ? manifest : null;
      JSONObject receipt = patcher.install(new ChannelClient(this), prefetched);
      detectGame();
      String okMsg = "Đã hoàn tất " + receipt.getJSONArray("files").length() + " tệp Android và ghi biên bản.";
      DiagnosticLog.log(this, "install", okMsg);
      setMessage(okMsg);
      break;
     }
     case "verify": {
      JSONObject verified = patcher.verify();
      String okMsg = "Đã đối chiếu " + verified.getInt("files") + " tệp của bản dịch " + verified.getString("version") + ".";
      DiagnosticLog.log(this, "verify", okMsg);
      setMessage(okMsg);
      break;
     }
     case "restore": {
      JSONObject restoreRes = patcher.restore();
      detectGame();
      set("officialUpdate", OfficialAndroidClient.readCachedGuardState(this));
      String okRestore = restoreRes != null && !restoreRes.optString("message", "").isEmpty()
        ? restoreRes.optString("message")
        : "Đã khôi phục dữ liệu gốc chuẩn MD5 của nhà phát hành.";
      DiagnosticLog.log(this, "restore", okRestore);
      setMessage(okRestore);
      break;
     }
     case "guardRestore": {
      if (!adb.verified) {
       if (!isDevOptions(this)) {
        pendingGuardRestore = false;
        throw new StellaException("E-DEVOPT", "Hãy bật Tuỳ chọn nhà phát triển trước khi kết nối Local ADB.", null);
       }
       if (!ErrorReport.isWifiConnected(this)) {
        pendingGuardRestore = false;
        throw new StellaException("E-ADB-NO-WIFI", "Điện thoại chưa kết nối Wi-Fi. Gỡ lỗi không dây bắt buộc dùng Wi-Fi.", null);
       }
       pendingGuardRestore = true;
       beginAutoConnect = true;
       promptWirelessIfSlow = true;
       setAdb("status", "Đang kết nối Local ADB để khôi phục dữ liệu gốc…");
       setMessage("Đang tự kết nối Local ADB để đóng Stella Sora và khôi phục dữ liệu gốc…");
       break;
      }
      pendingGuardRestore = false;
      progress("Đang đóng Stella Sora an toàn trước khi khôi phục…", 10);
      patcher.forceStopGame();
      if (!patcher.hasTarget()) detectGame();
      progress("Đang khôi phục dữ liệu gốc chuẩn MD5 từ Yostar…", 25);
      JSONObject guardRes = patcher.restore();
      detectGame();
      JSONObject offAfter = OfficialAndroidClient.readCachedGuardState(this);
      set("officialUpdate", offAfter);
      String guardDetail = guardRes != null ? guardRes.optString("message", "") : "";
      DiagnosticLog.log(this, "guardRestore", "Đã đóng Stella Sora và khôi phục dữ liệu gốc hoàn tất. " + guardDetail);
      String curG = state.getJSONObject("game").optString("gameVersion", "");
      String latestG = offAfter.optString("latestGameVersion", "");
      if (latestG.isEmpty() && manifest != null) latestG = manifest.optString("client_game_version", "");
      String targetLabel = !latestG.isEmpty() ? ("v" + latestG) : "bản mới nhất";
      String curLabel = !curG.isEmpty() ? (" (v" + curG + ")") : "";
      setMessage("Đã khôi phục dữ liệu gốc! Hãy mở Stella Sora để cập nhật lên " + targetLabel + ", thoát hẳn game rồi cài lại Việt hoá.");
      JSONObject guideData = Store.obj(
        "title", "Đã khôi phục dữ liệu gốc thành công!",
        "errorTitle", "Đã khôi phục dữ liệu gốc thành công!",
        "message", "Stella Sora trên máy đã về bản gốc sạch sẽ" + curLabel + ". Hãy mở game để tự tải bản cập nhật " + targetLabel + " rồi mới cài lại Việt hoá.",
        "explain", "Stella Sora trên máy đã về bản gốc sạch sẽ" + curLabel + ". Đây là bước cần thiết để game tải bản cập nhật " + targetLabel + " mà không gặp lỗi xác minh tệp.",
        "error", false,
        "level", "info",
        "steps", new JSONArray(Arrays.asList(
          "Bấm \"Mở Stella Sora\" bên dưới để game tự tải dữ liệu cập nhật " + targetLabel + " (nếu game yêu cầu cập nhật app, bấm \"Mở Google Play\").",
          "Chờ game tải xong vào tới màn hình đăng nhập/chính, sau đó vuốt thoát hẳn Stella Sora khỏi đa nhiệm.",
          "Quay lại launcher — ứng dụng sẽ tự nhận phiên bản mới để bạn bấm \"Cài Việt hoá ngay\"."
        )),
        "quickActions", new JSONArray(Arrays.asList("launch_game", "open_play_store"))
      );
      main.post(() -> {
       Listener l = listener.get();
       if (l != null) l.event(Store.obj("type", "message", "data", guideData));
      });
      break;
     }
     case "recover": {
      JSONObject rec = patcher.recover();
      detectGame();
      String okMsg = rec.optString("message", "Đã phục hồi nhật ký chưa hoàn tất.");
      DiagnosticLog.log(this, "recover", okMsg);
      setMessage(okMsg);
      break;
     }
     case "checkUpdate": {
      updateMetadata = new ChannelClient(this).updateChannel();
      set("update", Store.obj("available", true, "downloaded", false, "versionName", updateMetadata.optString("version_name"), "versionCode", updateMetadata.getLong("version_code"), "message", "Có APK Local ADB mới hơn (v" + updateMetadata.optString("version_name") + "). Bấm tải để kiểm tra chữ ký và nội dung."));
      DiagnosticLog.log(this, "checkUpdate", "Phát hiện APK mới v" + updateMetadata.optString("version_name"));
      setMessage("Đã đọc kênh APK Local ADB riêng.");
      break;
     }
     case "prepareUpdate": {
      JSONObject info = new ChannelClient(this).updateChannel();
      File dir = new File(getCacheDir(), "updates");
      if (!dir.isDirectory() && !dir.mkdirs()) throw new IOException("Không tạo được vùng APK cập nhật.");
      File apk = new File(dir, "update.apk");
      if (apk.exists() && !Store.hash(apk).equalsIgnoreCase(info.getString("sha256"))) {
       apk.delete();
       File pending = Store.internal(this, "pending_update.json");
       if (pending.exists()) pending.delete();
      }
      if (!apk.isFile()) {
       ChannelClient.download(info.getString("apk_url"), apk, info.getLong("size"), info.getString("sha256"), (text, pct) -> progress(text, pct));
      }
      ChannelClient.verifyApk(this, apk, info);
      Store.write(Store.internal(this, "pending_update.json"), info);
      updateMetadata = info;
      set("update", Store.obj("available", true, "downloaded", true, "versionName", info.optString("version_name"), "versionCode", info.getLong("version_code"), "message", "APK đã đúng ứng dụng, phiên bản mới hơn và chữ ký. Bấm mở trình cài đặt Android để tự xác nhận."));
      DiagnosticLog.log(this, "prepareUpdate", "Đã tải và xác minh APK v" + info.optString("version_name"));
      setMessage("Đã chuẩn bị APK, sẵn sàng cài đặt.");
      emitUpdatePrepared = true;
      break;
     }
     default:
      throw new IOException("Thao tác không được hỗ trợ.");
    }
   } catch (Throwable e) {
    if (!(("pair".equals(action) || "connect".equals(action) || "autoConnect".equals(action)) && startedGeneration != generation)) {
     String error = ErrorReport.redact(Store.cleanError(e));
     String classified = ErrorReport.classify(e, action);
     String forcedCode = null;
     if ("pair".equals(action)) {
      awaitingCode = true;
      setPairing("waiting_code", "Ghép chưa thành công. Lấy mã mới rồi nhập lại, hoặc dùng cổng thủ công.");
      if ("E-UNKNOWN".equals(classified) || "E-ADB".equals(classified)) {
       forcedCode = "E-ADB-PAIR";
       error = "Ghép đôi chưa thành công. Hãy lấy mã mới trong Gỡ lỗi không dây; mã ghép khác cổng kết nối.";
      } else {
       forcedCode = classified;
      }
     } else if ("connect".equals(action) && (error.toLowerCase(Locale.ROOT).contains("unauthor") || error.contains("xác minh được danh tính"))) {
      forcedCode = "E-ADB-AUTH";
      error = "Thiết bị chưa chấp nhận khóa Local ADB (hoặc đã xoá thiết bị ghép đôi). Hãy ghép đôi lại một lần bằng mã 6 số.";
     }
     JSONObject report = ErrorReport.record(this, ErrorReport.build(this, action, "Chưa hoàn tất", error, e, forcedCode, snapshot(this)));
     setMessage(report.optString("errorTitle") + " [" + report.optString("code") + "]");
     if ("checkUpdate".equals(action) || "prepareUpdate".equals(action)) {
      set("update", Store.obj("available", false, "downloaded", false, "message", report.optString("errorTitle") + " [" + report.optString("code") + "]"));
     }
     message("Chưa hoàn tất", error, true, report);
    }
   } finally {
    boolean connectAfter = beginAutoConnect;
    boolean promptWireless = promptWirelessIfSlow;
    boolean notifyPrepared = emitUpdatePrepared;
    boolean runGuardRestoreAfter = continueGuardRestore;
    main.post(() -> {
     busy.set(false);
     mutating = false;
     set("phase", "idle");
     set("progress", Store.obj("percent", 0, "indeterminate", false, "label", state.optString("message")));
     if (wake.isHeld()) wake.release();
     try {
      set("recovery", Store.obj("pending", patcher.pending(), "message", patcher.pending() ? "Có thao tác chưa hoàn tất; hãy phục hồi trước khi cài tiếp." : ""));
      refreshPayload();
     } catch (Exception ignored) {}
     publish(true);
     if (notifyPrepared) {
      Listener l = listener.get();
      if (l != null) l.event(Store.obj("type", "updatePrepared", "data", Store.obj("ok", true)));
     }
     if (runGuardRestoreAfter && startedGeneration == generation && adb.verified) {
      runTask("guardRestore", new JSONObject());
      return;
     }
     if (connectAfter && startedGeneration == generation) startConnectDiscovery(promptWireless);
     finishIdle();
    });
   }
  });
 }

 private synchronized void recordConnectedEndpoint(String host, int port, long expectedGeneration) throws Exception {
  if (expectedGeneration != generation) {
   adb.cancelBroker();
   return;
  }
  String canonicalHost = AdbClient.ownHost(host);
  setAdb("host", canonicalHost);
  setAdb("connectionPort", port);
  setAdb("paired", true);
  setAdb("hasIdentity", KeyMaterial.hasIdentity(this));
  setAdb("status", "Đã xác nhận danh tính Local ADB.");
  JSONObject cfg = Store.config(this);
  cfg.put("host", canonicalHost);
  cfg.put("connection_port", port);
  Store.write(Store.internal(this, "config.json"), cfg);
  set("config", configState(cfg));
 }

 private void detectGame() throws Exception {
  JSONObject game = patcher.detect();
  set("game", game);
  JSONObject receipt = patcher.receiptState();
  set("receipt", receipt);
  UpdateNotice.installed(this, receipt.optBoolean("present") ? receipt.optString("version") : "");
  set("recovery", Store.obj("pending", patcher.pending(), "message", patcher.pending() ? "Có nhật ký cần phục hồi." : ""));
  refreshPayload();
 }

 private synchronized void refreshPayload() throws Exception {
  JSONObject game = state.getJSONObject("game");
  boolean available = manifest != null;
  String gVer = game.optString("gameVersion"), rVer = game.optString("resourceVersion");
  String mGame = available ? manifest.optString("client_game_version") : "", mRes = available ? manifest.optString("resource_version") : "";
  boolean versionsKnown = game.optBoolean("versionsKnown") && !gVer.trim().isEmpty() && !rVer.trim().isEmpty();
  VersionCompatibility.Diagnosis diag = (available && versionsKnown)
    ? VersionCompatibility.diagnose(mGame, mRes, gVer, rVer)
    : null;
  boolean strictMatch = diag != null && diag.isMatch();
  boolean compatible = available && adb.verified && game.optBoolean("installed") && strictMatch;
  String mismatchKind = (diag != null && !diag.isMatch()) ? diag.kind : "";
  String supportedGame = diag != null ? diag.declaredGameSummary : VersionCompatibility.summarizeDeclared(mGame, false);
  String supportedRes = diag != null ? diag.declaredResourceSummary : VersionCompatibility.summarizeDeclared(mRes, true);
  String wrongEdition = game.optString("wrongEdition", "");
  boolean noData = game.optBoolean("noData", false);
  String mismatchReason;
  if ("game_older".equals(mismatchKind)) {
   mismatchReason = "Game trên máy (v" + gVer + ") đang cũ hơn gói Việt hoá mới nhất (v" + supportedGame + "). Mở Stella Sora cập nhật lên v" + supportedGame + ", thoát hẳn game rồi quay lại cài.";
  } else if ("game_newer".equals(mismatchKind)) {
   mismatchReason = "Game trên máy (v" + gVer + ") mới hơn gói Việt hoá hiện tại (v" + supportedGame + "). Vui lòng chờ nhóm dịch phát hành bản tương thích.";
  } else if ("resource_mismatch".equals(mismatchKind)) {
   mismatchReason = "Tài nguyên game (RES " + rVer + ") chưa khớp gói hỗ trợ (" + supportedRes + "). Hãy mở game tải bản vá mới nhất hoặc đồng bộ lại GitHub.";
  } else {
   mismatchReason = "Gói (v" + supportedGame + " · " + supportedRes + ") chưa khớp máy (v" + gVer + " · RES " + rVer + ").";
  }
  String reason = !available ? state.getJSONObject("github").optString("message", "Chưa có gói Android tương thích.")
    : !adb.verified ? "Kết nối Local ADB trước khi cài."
    : !wrongEdition.isEmpty() ? game.optString("reason", "Phát hiện Stella Sora bản khu vực khác (" + wrongEdition + ").")
    : !game.optBoolean("installed") ? "Chưa tìm thấy game Stella Sora (Global EN) trên máy."
    : noData ? game.optString("reason", "Chưa thấy thư mục dữ liệu game. Hãy mở Stella Sora 1 lần tải dữ liệu rồi kiểm tra lại.")
    : !versionsKnown ? "Chưa đọc được phiên bản game và tài nguyên. Hãy mở game tải đủ dữ liệu rồi kiểm tra lại."
    : strictMatch ? "Gói Android khớp phiên bản đã đọc."
    : mismatchReason;

  JSONObject receipt = state.optJSONObject("receipt");
  boolean receiptPresent = receipt != null && receipt.optBoolean("present");
  boolean receiptStale = receiptPresent && receipt.optBoolean("stale");
  String manifestVer = available ? manifest.optString("version", "") : "";
  String receiptVer = receiptPresent ? receipt.optString("version", "") : "";
  String manifestSha = available ? manifest.optString("manifest_sha256", "") : "";
  String receiptSha = receiptPresent ? receipt.optString("manifestSha256", "") : "";
  boolean updateAvailable = available && receiptPresent && (
    receiptStale
    || UpdateNotice.compareVersions(manifestVer, receiptVer) > 0
    || (!manifestSha.isEmpty() && !manifestSha.equalsIgnoreCase(receiptSha))
  );

  String reasonCode = compatible ? ""
    : !available ? (state.getJSONObject("github").optString("errorCode").isEmpty() ? (state.getJSONObject("github").has("releaseStatus") ? "E-NO-PACKAGE" : "E-SYNC-PENDING") : state.getJSONObject("github").optString("errorCode"))
    : !adb.verified ? "E-ADB-NOT-CONNECTED"
    : !wrongEdition.isEmpty() ? "E-GAME-WRONG-EDITION"
    : !game.optBoolean("installed") ? "E-NO-GAME"
    : noData ? "E-GAME-NO-DATA"
    : !versionsKnown ? "E-GAME-VERSION"
    : "E-PKG-MISMATCH";
  state.put("payload", Store.obj(
    "available", available,
    "compatible", compatible,
    "updateAvailable", updateAvailable,
    "reason", reason,
    "reasonCode", reasonCode,
    "mismatchKind", mismatchKind,
    "supportedGameVersion", available ? supportedGame : "",
    "supportedResourceVersion", available ? supportedRes : "",
    "version", manifestVer,
    "manifestSha256", manifestSha,
    "fileCount", available ? manifest.getJSONArray("files").length() : 0
  ));
 }

 private void saveSettings(JSONObject input) throws Exception {
  JSONObject cfg;
  try {
   cfg = Store.config(this);
  } catch (Exception corrupt) {
   File f = Store.internal(this, "config.json");
   if (f.isFile()) {
    File copy = Store.internal(this, "config.corrupt." + System.currentTimeMillis() + ".json");
    java.nio.file.Files.copy(f.toPath(), copy.toPath());
   }
   cfg = Store.defaults();
  }
  String old = cfg.optString("repo") + "|" + cfg.optString("branch");
  cfg.put("repo", input.getString("repo").trim());
  cfg.put("branch", input.getString("branch").trim());
  cfg.put("host", AdbClient.ownHost(input.optString("host", "127.0.0.1")));
  int p = input.optInt("connectionPort", 0);
  if (p != 0) AdbClient.port(p);
  cfg.put("connection_port", p);
  if (input.has("theme")) cfg.put("theme", Store.normalizeTheme(input.optString("theme", "system")));
  Store.validateConfig(cfg);
  synchronized (UpdateNotice.class) {
   Store.write(Store.internal(this, "config.json"), cfg);
   if (!old.equals(cfg.getString("repo") + "|" + cfg.getString("branch"))) UpdateNotice.channelChanged(this);
  }
  set("config", configState(cfg));
  if (!old.equals(cfg.getString("repo") + "|" + cfg.getString("branch"))) {
   manifest = null;
   manifestSyncedAt = 0L;
   set("notifications", new JSONArray());
   set("github", Store.obj("repo", cfg.getString("repo"), "branch", cfg.getString("branch"), "announcementStatus", "unavailable", "manifestStatus", "unavailable", "message", "Kênh đã đổi. Hãy đồng bộ GitHub."));
  }
 }

 private static JSONObject configState(JSONObject cfg) {
  return Store.obj("repo", cfg.optString("repo"), "branch", cfg.optString("branch"), "host", cfg.optString("host"), "connectionPort", cfg.optInt("connection_port", 0), "theme", Store.normalizeTheme(cfg.optString("theme", "system")));
 }

 private void startQuickPair() {
  if (busy.get() || mutating) {
   message("Đang có thao tác", "Không bắt đầu ghép đôi khi có thao tác đang chạy.", true);
   return;
  }
  if (!ErrorReport.isWifiConnected(this)) {
   JSONObject rep = ErrorReport.record(this, ErrorReport.explain(this, "E-ADB-NO-WIFI", "startPairingNotification", snapshot(this)));
   message("Cần bật Wi-Fi", rep.optString("message"), true, rep);
   finishIdle();
   return;
  }
  if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
   JSONObject rep = ErrorReport.record(this, ErrorReport.explain(this, "E-NOTIF-PERMISSION", "startPairingNotification", snapshot(this)));
   setMessage("Chưa được phép hiện thông báo. Dùng ô ghép đôi thủ công hoặc cấp quyền thông báo.");
   message("Chưa được phép hiện thông báo", rep.optString("message"), true, rep);
   publish(true);
   finishIdle();
   return;
  }
  cancelQuick(false);
  quickActive = true;
  awaitingCode = true;
  DiagnosticLog.log(this, "pair", "Bắt đầu phiên ghép đôi qua thông báo (mDNS).");
  setMessage("Đang dò cổng ghép đôi trên chính điện thoại…");
  nonce = UUID.randomUUID().toString().replace("-", "");
  quickDeadline = SystemClock.elapsedRealtime() + 180000;
  pairPort = 0;
  pairHost = "";
  long session = ++generation;
  setPairing("discovering_pair", "Mở Gỡ lỗi không dây → Ghép nối thiết bị bằng mã. Có thể nhập mã ngay từ thông báo.");
  foreground("Đang tìm cổng ghép đôi trên điện thoại…");
  closeDiscovery();
  discovery = new PairingDiscovery(this, "_adb-tls-pairing._tcp.", new PairingDiscovery.Callback() {
   public void found(String host, int port) {
    main.post(() -> {
     if (session != generation || !quickActive) return;
     pairHost = host;
     pairPort = port;
     setAdb("host", host);
     setAdb("pairingPort", port);
     DiagnosticLog.log(LauncherService.this, "pair", "Đã tìm thấy cổng ghép đôi qua mDNS.");
     setPairing("waiting_code", "Đã thấy cổng ghép đôi. Kéo thanh thông báo xuống và bấm Nhập mã ghép đôi.");
     publish(true);
    });
   }
   public void failed(String message) {
    main.post(() -> {
     if (session == generation && quickActive) {
      DiagnosticLog.log(LauncherService.this, "pair", "mDNS ghép đôi thất bại: " + message);
      setPairing("manual_fallback", message);
      publish(true);
     }
    });
   }
  });
  discovery.start();
  main.postDelayed(() -> {
   if (session == generation && quickActive && !busy.get()) {
    cancelQuick();
    setMessage("Phiên ghép đôi từ thông báo đã hết hạn. Có thể bắt đầu lại.");
    publish(true);
    finishIdle();
   }
  }, 180000);
  publish(true);
 }

 static void notificationReply(String token, String code) {
  LauncherService s = live;
  if (s != null) s.main.post(() -> s.acceptCode(token, code));
 }

 static void notificationCancel(String token) {
  LauncherService s = live;
  if (s != null) s.main.post(() -> { if (s.validNonce(token)) s.cancelQuick(); });
 }

 private boolean validNonce(String token) {
  return quickActive && !nonce.isEmpty() && nonce.equals(token) && !mutating;
 }

 private void acceptCode(String token, String code) {
  if (!validNonce(token) || !awaitingCode || busy.get()) return;
  if (SystemClock.elapsedRealtime() >= quickDeadline) {
   setPairing("expired", "Mã ghép đôi đã hết phiên. Hãy hủy và bắt đầu lại.");
   publish(true);
   return;
  }
  String digits = code == null ? "" : code.replaceAll("\\s+", "");
  if (!digits.matches("[0-9]{6}")) {
   setPairing("waiting_code", "Mã cần đúng 6 chữ số. Hãy nhập lại từ thông báo.");
   publish(true);
   return;
  }
  if (pairPort == 0 || pairHost.isEmpty()) {
   setPairing("manual_fallback", "Chưa tìm thấy cổng ghép. Mở hộp mã ghép đôi hoặc dùng cổng nhập thủ công trong ứng dụng.");
   publish(true);
   return;
  }
  setPairing("pairing", "Đang ghép đôi, chưa kết nối…");
  runTask("pair", Store.obj("host", pairHost, "pairingPort", pairPort, "code", digits));
 }

 private void startConnectDiscovery(boolean promptWirelessIfSlow) {
  closeDiscovery();
  quickActive = true;
  awaitingCode = false;
  if (nonce.isEmpty()) {
   nonce = UUID.randomUUID().toString().replace("-", "");
   quickDeadline = SystemClock.elapsedRealtime() + 180000;
  }
  long session = ++generation;
  scheduleExpiry(session);
  String initialMsg = promptWirelessIfSlow
    ? "Đang tự dò cổng kết nối lại (không cần mã 6 số)…"
    : "Đã ghép đôi. Đang tìm cổng kết nối khác cổng ghép đôi…";
  setPairing("discovering_connect", initialMsg);
  foreground(initialMsg);
  discovery = new PairingDiscovery(this, "_adb-tls-connect._tcp.", new PairingDiscovery.Callback() {
   public void found(String host, int port) {
    main.post(() -> {
     if (session != generation || !quickActive || busy.get()) return;
     closeDiscovery();
     DiagnosticLog.log(LauncherService.this, "connect", "Đã tìm thấy cổng kết nối qua mDNS.");
     setPairing("connecting", "Đang kết nối và chờ phản hồi id…");
     runTask("connect", Store.obj("host", host, "connectionPort", port));
    });
   }
   public void failed(String message) {
    main.post(() -> {
     if (session == generation) {
      DiagnosticLog.log(LauncherService.this, "connect", "mDNS tìm cổng kết nối thất bại: " + message);
      setPairing("manual_fallback", message + " Xem cổng kết nối ở trang Gỡ lỗi không dây.");
      publish(true);
     }
    });
   }
  });
  discovery.start();
  if (promptWirelessIfSlow) {
   main.postDelayed(() -> {
    if (session != generation || !quickActive || adb.verified || busy.get()) return;
    setPairing("discovering_connect", "Hãy bật Gỡ lỗi không dây trong Cài đặt Android — launcher sẽ tự kết nối ngay khi thấy cổng (không cần nhập mã 6 số).");
    publish(true);
    Listener l = listener.get();
    if (l != null) {
     l.event(Store.obj("type", "openWirelessForReconnect", "data", Store.obj("message", "Cổng cũ đã đổi hoặc Gỡ lỗi không dây đang tắt.")));
    }
   }, 1500);
  }
  publish(true);
 }

 private void scheduleExpiry(long session) {
  main.postDelayed(new Runnable() {
   public void run() {
    if (session != generation || !quickActive) return;
    if (busy.get() || mutating) {
     main.postDelayed(this, 1000);
     return;
    }
    cancelQuick();
    setMessage("Phiên tìm cổng đã hết hạn. Hãy bắt đầu lại hoặc nhập cổng thủ công.");
    publish(true);
   }
  }, 180000);
 }

 private void cancelQuick() { cancelQuick(true); }
 private synchronized void cancelQuick(boolean finish) {
  if (mutating) {
   message("Đang ghi dữ liệu", "Không hủy giữa thao tác thay đổi game. Hãy chờ hoàn tất.", true);
   return;
  }
  generation++;
  quickActive = false;
  awaitingCode = false;
  pendingGuardRestore = false;
  nonce = "";
  closeDiscovery();
  adb.cancelBroker();
  setPairing("cancelled", "Đã dừng tìm cổng/ghép đôi. Có thể dùng kết nối thủ công.");
  setMessage("Đã hủy tìm cổng / ghép đôi.");
  publish(true);
  if (finish) finishIdle();
 }

 private void closeDiscovery() {
  if (discovery != null) {
   discovery.close();
   discovery = null;
  }
 }

 private synchronized void setPairing(String stage, String message) {
  try {
   state.put("message", message);
   state.getJSONObject("adb").put("notificationPairing", Store.obj("active", quickActive, "stage", stage, "message", message));
  } catch (JSONException ignored) {}
 }
 private synchronized void setAdb(String key, Object value) {
  try { state.getJSONObject("adb").put(key, value); } catch (JSONException ignored) {}
 }
 private synchronized void set(String key, Object value) {
  try { state.put(key, value); } catch (JSONException ignored) {}
 }
 private void setMessage(String message) { set("message", message); }
 private void progress(String text, int percent) {
  set("progress", Store.obj("percent", Math.max(0, Math.min(100, percent)), "indeterminate", percent < 0, "label", text));
  setMessage(text);
  publish(false);
 }

 private void publish(boolean force) {
  if (destroying) return;
  long now = SystemClock.elapsedRealtime();
  if (!force && now - lastPublish < 500) return;
  lastPublish = now;
  main.post(() -> {
   if (destroying) return;
   Listener l = listener.get();
   if (l != null) l.event(Store.obj("type", "state", "data", snapshot(this)));
   if (busy.get() || quickActive || adb.verified) foreground(state.optString("message", "Stella Sora Việt Hoá"));
  });
 }

 private void message(String title, String text, boolean error) {
  message(title, text, error, error ? ErrorReport.record(this, ErrorReport.build(this, null, title, text, null, null, snapshot(this))) : null);
 }
 private void message(String title, String text, boolean error, JSONObject report) {
  main.post(() -> {
   Listener l = listener.get();
   if (l != null) l.event(Store.obj("type", "message", "data", ErrorReport.attach(Store.obj("title", title, "message", text, "error", error), report)));
  });
 }

 private Notification notification(String text) {
  if (quickActive) {
   try { text = state.getJSONObject("adb").getJSONObject("notificationPairing").optString("message", text); } catch (Exception ignored) {}
  }
  Intent open = new Intent(this, MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_CLEAR_TOP);
  PendingIntent content = PendingIntent.getActivity(this, 1, open, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
  Notification.Builder b = new Notification.Builder(this, quickActive ? PAIR_CHANNEL : WORK_CHANNEL)
    .setSmallIcon(R.drawable.ic_notification)
    .setContentTitle("Stella Sora Việt Hoá")
    .setContentText(text)
    .setStyle(new Notification.BigTextStyle().bigText(text))
    .setContentIntent(content)
    .setOngoing(busy.get() || adb.verified || quickActive)
    .setOnlyAlertOnce(!quickActive)
    .setPriority(quickActive ? Notification.PRIORITY_HIGH : Notification.PRIORITY_LOW)
    .setVisibility(Notification.VISIBILITY_PRIVATE)
    .setCategory(quickActive ? Notification.CATEGORY_STATUS : Notification.CATEGORY_SERVICE);
  if (quickActive && !nonce.isEmpty() && !mutating) {
   Uri uri = Uri.parse("stella-localadb://pair/" + nonce);
   Intent reply = new Intent(this, PairingReceiver.class).setAction("stella.PAIR_REPLY").setData(uri);
   if (awaitingCode) {
    PendingIntent input = PendingIntent.getBroadcast(this, nonce.hashCode(), reply, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_MUTABLE);
    RemoteInput remote = new RemoteInput.Builder("pair_code").setLabel("Mã ghép đôi 6 chữ số").setAllowFreeFormInput(true).build();
    b.addAction(new Notification.Action.Builder(android.R.drawable.ic_input_add, "Nhập mã ghép đôi", input).addRemoteInput(remote).build());
   }
   Intent cancel = new Intent(this, PairingReceiver.class).setAction("stella.PAIR_CANCEL").setData(uri);
   PendingIntent stop = PendingIntent.getBroadcast(this, nonce.hashCode() + 1, cancel, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
   b.addAction(new Notification.Action.Builder(android.R.drawable.ic_menu_close_clear_cancel, awaitingCode ? "Hủy ghép đôi" : "Hủy tìm cổng", stop).build());
  }
  return b.build();
 }

 private void foreground(String text) {
  if (destroying) return;
  int types = android.content.pm.ServiceInfo.FOREGROUND_SERVICE_TYPE_CONNECTED_DEVICE;
  String phase = state.optString("phase");
  if (busy.get() && Arrays.asList("sync", "checkUpdate", "prepareUpdate", "install").contains(phase)) {
   types |= android.content.pm.ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC;
  }
  try {
   startForeground(NOTICE, notification(text), types);
  } catch (RuntimeException e) {
   DiagnosticLog.log(this, "service", "startForeground hạn chế: " + Store.cleanError(e));
   try {
    startForeground(NOTICE, notification(text));
   } catch (RuntimeException ignored) {}
  }
 }

 private void finishIdle() {
  if (destroying) return;
  if (!busy.get() && !quickActive && !adb.verified) {
   stopForeground(STOP_FOREGROUND_REMOVE);
   if (listener.get() == null) stopSelf();
  }
 }

 @Override public void onTimeout(int startId, int foregroundServiceType) {
  destroying = true;
  generation++;
  quickActive = false;
  awaitingCode = false;
  pendingGuardRestore = false;
  nonce = "";
  closeDiscovery();
  adb.cancelBroker();
  DiagnosticLog.log(this, "service", "Android dừng tác vụ nền theo giới hạn ForegroundService.");
  setAdb("status", "Hệ thống đã dừng tác vụ nền. Hãy kết nối lại.");
  setMessage("Tác vụ đã dừng theo giới hạn Android. Nhật ký được giữ để phục hồi; không báo hoàn tất.");
  stopForeground(STOP_FOREGROUND_REMOVE);
  stopSelf();
 }

 @Override public void onDestroy() {
  destroying = true;
  closeDiscovery();
  if (adb != null) adb.cancelBroker();
  if (wake != null && wake.isHeld()) wake.release();
  worker.shutdownNow();
  if (live == this) live = null;
  super.onDestroy();
 }
}
