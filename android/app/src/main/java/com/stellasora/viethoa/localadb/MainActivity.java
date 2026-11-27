package com.stellasora.viethoa.localadb;
import android.Manifest;
import android.app.*;
import android.content.*;
import android.content.pm.*;
import android.content.res.Configuration;
import android.graphics.Color;
import android.net.*;
import android.os.*;
import android.provider.Settings;
import android.service.quicksettings.TileService;
import android.view.*;
import android.webkit.*;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;
import org.json.*;
import java.io.*;
import java.util.*;

/** Trusted local HTTPS asset origin, dark/light system chrome sync, and explicit-action native bridge. */
public final class MainActivity extends Activity implements LauncherService.Listener {
 static final String EXTRA_GUARD_RESTORE = "guard_restore";
 private static final String HOST = "stella.local.invalid", HOME = "https://stella.local.invalid/index.html";
 private static final int LIGHT_BG = Color.rgb(255, 255, 255);
 private static final int LIGHT_CANVAS = Color.rgb(238, 245, 249);
 private static final int DARK_BG = Color.rgb(18, 32, 51);
 private static final int DARK_CANVAS = Color.rgb(13, 23, 36);
 private static final int DARK_NAV = Color.rgb(18, 32, 51);

 private FrameLayout container;
 private WebView web;
 private boolean loaded, autoSynced, resumed;
 private boolean pendingGuardRestoreIntent;
 private String afterPermission;
 private boolean updateDialogShowing;
 private AlertDialog reconnectDialog;

 private final Set<String> allowed = new HashSet<>(Arrays.asList(
   "state", "sync", "saveSettings", "setTheme", "resetChannel", "probeNetwork",
   "pair", "connect", "autoConnect", "disconnect",
   "startPairingNotification", "cancelPairing", "detect", "install", "verify", "restore", "recover",
   "checkUpdate", "installUpdate", "checkOfficialUpdate", "guardRestore",
   "pinGuardShortcut", "openAccessibilitySettings", "openOverlaySettings", "openAppInfoSettings", "openGuardAlert",
   "openWirelessSettings", "openWifiSettings",
   "openAppNotifications", "openBatterySettings", "openUnknownSources", "launchGame",
   "copyDiagnostics", "copyError", "copyAiPrompt", "openSourceCode", "explain", "openLastError", "copyAccount", "openIssues",
   "openDeviceInfo", "openDevSettings"
 ));

 private boolean isDarkTheme() {
  return "dark".equals(LauncherService.resolveTheme(this, Store.theme(this)));
 }

 private AlertDialog.Builder dialogBuilder() {
  return new AlertDialog.Builder(this, isDarkTheme()
    ? android.R.style.Theme_Material_Dialog_Alert
    : android.R.style.Theme_Material_Light_Dialog_Alert);
 }

 private void applySystemChromeTheme() {
  boolean dark = isDarkTheme();
  int barBg = dark ? DARK_BG : LIGHT_BG;
  int nav = dark ? DARK_NAV : LIGHT_BG;
  int canvas = dark ? DARK_CANVAS : LIGHT_CANVAS;
  Window win = getWindow();
  if (win != null) {
   win.setStatusBarColor(barBg);
   win.setNavigationBarColor(nav);
  }
  if (container != null) container.setBackgroundColor(canvas);
  if (web != null) web.setBackgroundColor(canvas);
  if (win != null && win.peekDecorView() != null) {
   try {
    WindowInsetsController barAppearance = win.getInsetsController();
    if (barAppearance != null) {
     int mask = WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS | WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS;
     barAppearance.setSystemBarsAppearance(dark ? 0 : mask, mask);
    }
   } catch (Throwable ignored) {}
  }
 }

 @Override public void onCreate(Bundle saved) {
  super.onCreate(saved);
  getWindow().setDecorFitsSystemWindows(false);
  container = new FrameLayout(this);
  setContentView(container);
  applySystemChromeTheme();

  container.setOnApplyWindowInsetsListener((v, insets) -> {
   android.graphics.Insets bars = insets.getInsets(WindowInsets.Type.systemBars() | WindowInsets.Type.displayCutout());
   android.graphics.Insets ime = insets.getInsets(WindowInsets.Type.ime());
   v.setPadding(bars.left, bars.top, bars.right, Math.max(bars.bottom, ime.bottom));
   return WindowInsets.CONSUMED;
  });
  container.requestApplyInsets();

  try {
   web = new WebView(this);
  } catch (Throwable webViewError) {
   showMissingWebViewFallback(webViewError);
   return;
  }
  applySystemChromeTheme();
  web.setLayerType(View.LAYER_TYPE_HARDWARE, null);
  web.setOverScrollMode(View.OVER_SCROLL_NEVER);
  web.setVerticalScrollBarEnabled(false);
  web.setHorizontalScrollBarEnabled(false);
  container.addView(web, new FrameLayout.LayoutParams(-1, -1));

  WebView.setWebContentsDebuggingEnabled(false);
  WebSettings settings = web.getSettings();
  settings.setJavaScriptEnabled(true);
  settings.setDomStorageEnabled(false);
  settings.setAllowFileAccess(false);
  settings.setAllowContentAccess(false);
  settings.setAllowFileAccessFromFileURLs(false);
  settings.setAllowUniversalAccessFromFileURLs(false);
  settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
  settings.setSupportMultipleWindows(false);
  settings.setJavaScriptCanOpenWindowsAutomatically(false);
  settings.setMediaPlaybackRequiresUserGesture(true);
  settings.setTextZoom(100);

  web.addJavascriptInterface(new NativeBridge(), "StellaNative");
  web.setWebViewClient(new WebViewClient() {
   @Override public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r) { return !trusted(r.getUrl()); }
   @Override public WebResourceResponse shouldInterceptRequest(WebView v, WebResourceRequest request) {
    try {
     Uri uri = request.getUrl();
     if (!trusted(uri)) return denied();
     String path = uri.getPath();
     if (path == null || path.equals("/")) path = "/index.html";
     if (path.contains("..") || path.contains("\\") || !path.matches("/[A-Za-z0-9_./\\[\\]-]+")) return denied();
     String file = path.substring(1);
     String mime = file.endsWith(".html") ? "text/html"
       : file.endsWith(".css") ? "text/css"
       : file.endsWith(".js") ? "text/javascript"
       : file.endsWith(".webp") ? "image/webp"
       : file.endsWith(".png") ? "image/png"
       : file.endsWith(".svg") ? "image/svg+xml"
       : file.endsWith(".ttf") ? "font/ttf"
       : file.endsWith(".json") ? "application/json" : "text/plain";
     WebResourceResponse out = new WebResourceResponse(mime, mime.startsWith("image/") || mime.startsWith("font/") ? null : "UTF-8", getAssets().open("ui/" + file));
     out.setResponseHeaders(Collections.singletonMap("X-Content-Type-Options", "nosniff"));
     return out;
    } catch (Exception e) {
     return denied();
    }
   }
   @Override public void onReceivedSslError(WebView v, android.webkit.SslErrorHandler handler, android.net.http.SslError error) { handler.cancel(); }
   @Override public void onPageFinished(WebView v, String url) {
    if (url.equals(HOME)) {
     loaded = true;
     emitState();
     maybeAutoSync();
     consumeGuardRestoreIntent();
    }
   }
  });
  web.setWebChromeClient(new WebChromeClient());
  web.setDownloadListener((url, userAgent, disposition, mime, length) -> showMessage("Tải bị chặn", "Chỉ tải gói qua chức năng có xác minh của launcher.", true));
  LauncherService.listen(this);
  try { UpdateNotice.schedule(this); } catch (RuntimeException ignored) {}
  try { OfficialUpdateNotice.schedule(this); } catch (RuntimeException ignored) {}
  if (getIntent() != null && getIntent().getBooleanExtra(EXTRA_GUARD_RESTORE, false)) {
   pendingGuardRestoreIntent = true;
  }
  web.loadUrl(HOME);
 }

 @Override protected void onNewIntent(Intent intent) {
  super.onNewIntent(intent);
  setIntent(intent);
  if (intent != null && intent.getBooleanExtra(EXTRA_GUARD_RESTORE, false)) {
   pendingGuardRestoreIntent = true;
   if (loaded && resumed) consumeGuardRestoreIntent();
  }
 }

 private void showMissingWebViewFallback(Throwable err) {
  boolean dark = isDarkTheme();
  LinearLayout box = new LinearLayout(this);
  box.setOrientation(LinearLayout.VERTICAL);
  int pad = Math.round(24 * getResources().getDisplayMetrics().density);
  box.setPadding(pad, pad * 2, pad, pad);
  TextView title = new TextView(this);
  title.setText("Thiếu thành phần Android System WebView");
  title.setTextSize(20);
  title.setTextColor(dark ? Color.rgb(234, 242, 250) : Color.rgb(48, 78, 101));
  TextView body = new TextView(this);
  body.setText("\nThiết bị này đang tắt hoặc bị lỗi Android System WebView nên chưa hiển thị được giao diện launcher.\n\nCách khắc phục:\n1. Mở Google Play Store → tìm \"Android System WebView\" → Bật hoặc Cập nhật.\n2. Khởi động lại launcher.\n\nChi tiết: " + Store.cleanError(err));
  body.setTextSize(15);
  body.setTextColor(dark ? Color.rgb(155, 178, 199) : Color.rgb(87, 115, 136));
  box.addView(title);
  box.addView(body);
  container.addView(box, new FrameLayout.LayoutParams(-1, -1));
 }

 @Override public void onConfigurationChanged(Configuration newConfig) {
  super.onConfigurationChanged(newConfig);
  applySystemChromeTheme();
  if (loaded) emitState();
 }

 private static boolean trusted(Uri uri) {
  return "https".equals(uri.getScheme()) && HOST.equals(uri.getHost()) && (uri.getPort() == -1 || uri.getPort() == 443);
 }
 private static WebResourceResponse denied() {
  return new WebResourceResponse("text/plain", "UTF-8", 403, "Blocked", Collections.emptyMap(), new ByteArrayInputStream(new byte[0]));
 }

 private final class NativeBridge {
  @JavascriptInterface public void haptic() {
   runOnUiThread(() -> {
    if (container != null) {
     try { container.performHapticFeedback(HapticFeedbackConstants.CLOCK_TICK); } catch (Throwable ignored) {}
    }
   });
  }
  @JavascriptInterface public void request(String action, String payload) {
   if (action == null || !allowed.contains(action) || payload == null || payload.length() > 65536) {
    runOnUiThread(() -> showMessage("Yêu cầu bị chặn", "Thao tác không thuộc giao diện tin cậy.", true));
    return;
   }
   try {
    JSONObject args = new JSONObject(payload);
    runOnUiThread(() -> handle(action, args));
   } catch (JSONException e) {
    runOnUiThread(() -> showMessage("Dữ liệu chưa hợp lệ", "Không đọc được yêu cầu từ giao diện.", true));
   }
  }
 }

 private void handle(String action, JSONObject args) {
  try {
   switch (action) {
    case "state": emitState(); break;
    case "setTheme": {
     String theme = Store.normalizeTheme(args.optString("theme", "system"));
     Store.saveTheme(this, theme);
     applySystemChromeTheme();
     emitState();
     break;
    }
    case "probeNetwork": {
     LauncherService.probeNetwork(this, args.optString("id", ""));
     break;
    }
    case "openDeviceInfo": openDeviceInfo(); break;
    case "openDevSettings": openDevSettings(); break;
    case "openWirelessSettings": openWireless(); break;
    case "openWifiSettings": openWifi(); break;
    case "openAppNotifications": openAppNotifications(); break;
    case "openBatterySettings": openBatterySettings(); break;
    case "openUnknownSources": openUnknownSources(); break;
    case "openAccessibilitySettings": openAccessibilitySettings(); break;
    case "openOverlaySettings": openOverlaySettings(); break;
    case "openAppInfoSettings": openAppInfoSettings(); break;
    case "pinGuardShortcut": pinGuardShortcut(); break;
    case "openGuardAlert": {
     Intent guard = new Intent(this, GameUpdateGuardActivity.class)
       .putExtra(GameUpdateGuardActivity.EXTRA_SOURCE, "Cảnh báo cập nhật Yostar");
     startActivity(guard);
     break;
    }
    case "guardRestore": {
     startGuardRestoreFlow();
     break;
    }
    case "autoConnect":
     if (!LauncherService.isDevOptions(this)) {
      showDevModeGuideDialog();
      break;
     }
     LauncherService.dispatch(this, action, args);
     break;
    case "startPairingNotification":
     if (!LauncherService.isDevOptions(this)) {
      showDevModeGuideDialog();
      break;
     }
     if (!ErrorReport.isWifiConnected(this)) {
      JSONObject rep = ErrorReport.record(this, ErrorReport.explain(this, "E-ADB-NO-WIFI", action, LauncherService.snapshot(this)));
      event(Store.obj("type", "message", "data", ErrorReport.attach(Store.obj("title", rep.optString("errorTitle"), "message", rep.optString("message"), "error", true), rep)));
      break;
     }
     if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
      afterPermission = action;
      requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, 71);
     } else {
      LauncherService.dispatch(this, action, args);
      openWireless();
     }
     break;
    case "openIssues": {
     JSONObject cfg = Store.config(this);
     Store.validateConfig(cfg);
     external("https://github.com/" + cfg.getString("repo") + "/issues");
     break;
    }
    case "openSourceCode": {
     JSONObject cfg = Store.config(this);
     Store.validateConfig(cfg);
     String relPath = args.optString("path", "").trim();
     String base = "https://github.com/" + cfg.getString("repo");
     if (relPath.matches("[A-Za-z0-9_./-]+") && !relPath.contains("..")) {
      external(base + "/blob/" + Uri.encode(cfg.optString("branch", "main")) + "/" + relPath);
     } else {
      external(base);
     }
     break;
    }
    case "copyAiPrompt": {
     String text = args.optString("text", "").trim();
     if (text.isEmpty() || text.length() > 8192) {
      showMessage("Chưa sao chép được", "Nội dung prompt kiểm tra chưa hợp lệ.", true);
      break;
     }
     clipboard("Prompt kiểm tra an toàn Stella Sora", text);
     event(Store.obj("type", "copied", "data", Store.obj("ok", true, "kind", "ai_prompt")));
     break;
    }
    case "copyAccount":
     showMessage("Tính năng đang bảo trì", "Bản Việt hoá luôn luôn miễn phí.", false);
     break;
    case "copyDiagnostics": {
     JSONObject s = LauncherService.snapshot(this);
     String text = ErrorReport.buildDiagnosticsText(this, s);
     clipboard("Chẩn đoán Stella Sora", text);
     event(Store.obj("type", "copied", "data", Store.obj("ok", true, "kind", "diagnostics")));
     break;
    }
    case "openLastError": {
     JSONObject report = ErrorReport.findReport(this, args.optString("id", ""));
     if (report == null) {
      showMessage("Chưa có lỗi nào", "Chưa có mã lỗi nào được ghi nhận gần đây.", false);
      break;
     }
     JSONObject data = Store.obj("title", report.optString("errorTitle", "Chi tiết lỗi gần nhất"), "message", report.optString("message"), "error", !"info".equals(report.optString("level")));
     event(Store.obj("type", "message", "data", ErrorReport.attach(data, report)));
     break;
    }
    case "explain": {
     String id = args.optString("id");
     JSONObject report = id.isEmpty() ? null : ErrorReport.findReport(this, id);
     if (report == null || !report.optString("code").equals(args.optString("code", report.optString("code")))) {
      report = ErrorReport.explain(this, args.optString("code", "E-UNKNOWN"), "explain", LauncherService.snapshot(this));
     }
     ErrorReport.record(this, report);
     JSONObject data = Store.obj("title", "Vì sao chưa cài được?", "message", report.optString("message"), "error", !"info".equals(report.optString("level")) && !"warning".equals(report.optString("level")));
     event(Store.obj("type", "message", "data", ErrorReport.attach(data, report)));
     break;
    }
    case "copyError": {
     String id = args.optString("id");
     String text = ErrorReport.find(this, id);
     if (text == null) {
      showMessage("Chưa có mã lỗi", "Chưa có lỗi nào được ghi nhận để sao chép.", false);
      break;
     }
     JSONObject rep = ErrorReport.findReport(this, id);
     clipboard("Báo lỗi Stella Sora", text);
     event(Store.obj("type", "copied", "data", Store.obj("ok", true, "kind", "error", "code", rep == null ? "" : rep.optString("code"), "reportId", rep == null ? "" : rep.optString("reportId"))));
     break;
    }
    case "launchGame": {
     if (LauncherService.snapshot(this).optBoolean("busy")) throw new IOException("Hãy chờ thao tác đang chạy hoàn tất trước khi mở game.");
     Intent launch = getPackageManager().getLaunchIntentForPackage(Store.GAME);
     if (launch == null) throw new IOException("Chưa tìm thấy ứng dụng Stella Sora Android.");
     startActivity(new Intent(this, LaunchGuardActivity.class));
     break;
    }
    case "install":
    case "restore":
    case "recover": {
     JSONObject state = LauncherService.snapshot(this);
     if (state.optBoolean("busy")) throw new IOException("Đang có thao tác. Hãy chờ hoàn tất.");
     String root = state.getJSONObject("game").optString("root", "Chưa xác định");
     String text = action.equals("install") ? "Chỉ cài các tệp Android khớp phiên bản và SHA256. Gói Windows sẽ bị từ chối."
       : action.equals("restore") ? "Khôi phục toàn bộ tệp gốc đã xác minh SHA256 cho đúng phiên bản game hiện tại. Bỏ qua các tệp đã ở bản gốc."
       : "Đọc nhật ký và phục hồi thao tác bị ngắt. Không dùng backup của thiết bị khác.";
     dialogBuilder()
       .setTitle(action.equals("install") ? "Cài Việt hoá Android" : action.equals("restore") ? "Khôi phục bản trước cài" : "Phục hồi thao tác")
       .setMessage(root + "\n\n" + text + "\n\nHãy thoát game và chờ thao tác hoàn tất.")
       .setNegativeButton("Để sau", null)
       .setPositiveButton("Tiếp tục", (d, w) -> LauncherService.dispatch(this, action, args))
       .show();
     break;
    }
    case "installUpdate": installUpdate(); break;
    default: LauncherService.dispatch(this, action, args);
   }
  } catch (Exception e) {
   showMessage("Chưa thực hiện được", Store.cleanError(e), true, action, e);
  }
 }

 private void installUpdate() throws Exception {
  JSONObject state = LauncherService.snapshot(this);
  if (state.optBoolean("busy")) throw new IOException("Hãy chờ thao tác đang chạy.");
  File apk = new File(getCacheDir(), "updates/update.apk"), metadata = Store.internal(this, "pending_update.json");
  PackageInfo current = getPackageManager().getPackageInfo(Store.APP, 0);
  boolean needsDownload = !apk.isFile() || !metadata.isFile();
  if (!needsDownload) {
   try {
    JSONObject meta = Store.read(metadata);
    if (meta.optLong("version_code", 0) <= current.getLongVersionCode() || !Store.hash(apk).equalsIgnoreCase(meta.optString("sha256"))) {
     needsDownload = true;
    }
   } catch (Exception e) {
    needsDownload = true;
   }
  }
  if (needsDownload) {
   try { apk.delete(); } catch (Exception ignored) {}
   try { metadata.delete(); } catch (Exception ignored) {}
   LauncherService.dispatch(this, "prepareUpdate", new JSONObject());
   return;
  }
  try {
   ChannelClient.verifyApk(this, apk, Store.read(metadata));
  } catch (Exception e) {
   try { apk.delete(); } catch (Exception ignored) {}
   try { metadata.delete(); } catch (Exception ignored) {}
   throw e;
  }
  if (!getPackageManager().canRequestPackageInstalls()) {
   JSONObject rep = ErrorReport.record(this, ErrorReport.explain(this, "E-APK-INSTALL-PERMISSION", "installUpdate", state));
   event(Store.obj("type", "message", "data", ErrorReport.attach(Store.obj("title", rep.optString("errorTitle"), "message", rep.optString("message"), "error", false), rep)));
   return;
  }
  dialogBuilder()
    .setTitle("Mở trình cài đặt Android")
    .setMessage("APK đã đúng ứng dụng Local ADB, là bản mới hơn và có cùng chữ ký. Android vẫn yêu cầu bạn tự xác nhận cài đặt.")
    .setNegativeButton("Để sau", null)
    .setPositiveButton("Mở trình cài đặt", (d, w) -> {
     Uri uri = Uri.parse("content://" + Store.APP + ".updates/update.apk");
     Intent install = new Intent(Intent.ACTION_VIEW).setDataAndType(uri, "application/vnd.android.package-archive").addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
     startActivity(install);
    })
    .show();
 }

 private void openWireless() {
  String settingsPackage = "com.android.settings";
  Intent direct = new Intent("android.settings.WIRELESS_DEBUGGING_SETTINGS").setPackage(settingsPackage);
  if (tryOpenSettings(direct)) return;

  // Some Xiaomi/HyperOS ROMs crash in Settings when handling the Wireless debugging tile shortcut.
  String oem = ErrorReport.oemFamily();
  if (!"xiaomi".equals(oem)) {
   Intent tile = new Intent(TileService.ACTION_QS_TILE_PREFERENCES)
     .setPackage(settingsPackage)
     .putExtra(Intent.EXTRA_COMPONENT_NAME, new ComponentName(settingsPackage,
       "com.android.settings.development.qstile.DevelopmentTiles$WirelessDebugging"));
   if (tryOpenSettings(tile)) return;
  }

  String highlightKey = ":settings:fragment_args_key";
  String wirelessPreference = "toggle_adb_wireless";
  Bundle fragmentArgs = new Bundle();
  fragmentArgs.putString(highlightKey, wirelessPreference);
  Intent developerOptions = new Intent(Settings.ACTION_APPLICATION_DEVELOPMENT_SETTINGS)
    .putExtra(highlightKey, wirelessPreference)
    .putExtra(":settings:show_fragment_args", fragmentArgs);
  if (tryOpenSettings(developerOptions)) return;

  String guide = "Vào Cài đặt → Tuỳ chọn nhà phát triển → Gỡ lỗi không dây.";
  dialogBuilder()
    .setTitle("Mở Gỡ lỗi không dây")
    .setMessage(guide)
    .setPositiveButton("Mở Cài đặt", (dialog, which) -> {
     if (!tryOpenSettings(new Intent(Settings.ACTION_SETTINGS))) {
      showMessage("Mở Gỡ lỗi không dây", guide, false);
     }
    })
    .setNegativeButton("Đóng", null)
    .show();
 }

 private void openWifi() {
  if (tryOpenSettings(new Intent(Settings.ACTION_WIFI_SETTINGS))) return;
  if (tryOpenSettings(new Intent(Settings.ACTION_WIRELESS_SETTINGS))) return;
  if (tryOpenSettings(new Intent(Settings.ACTION_SETTINGS))) return;
  showMessage("Mở cài đặt Wi-Fi", "Vào Cài đặt Android → Wi-Fi và kết nối vào mạng Wi-Fi.", false);
 }

 private void openAppNotifications() {
  Intent notif = new Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS).putExtra(Settings.EXTRA_APP_PACKAGE, getPackageName());
  if (tryOpenSettings(notif)) return;
  Intent details = new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.parse("package:" + getPackageName()));
  if (tryOpenSettings(details)) return;
  tryOpenSettings(new Intent(Settings.ACTION_SETTINGS));
 }

 private void openBatterySettings() {
  Intent opt = new Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS);
  if (tryOpenSettings(opt)) return;
  Intent details = new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.parse("package:" + getPackageName()));
  if (tryOpenSettings(details)) return;
  tryOpenSettings(new Intent(Settings.ACTION_SETTINGS));
 }

 private void openUnknownSources() {
  Intent unk = new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES, Uri.parse("package:" + getPackageName()));
  if (tryOpenSettings(unk)) return;
  Intent details = new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.parse("package:" + getPackageName()));
  tryOpenSettings(details);
 }

 private void openAccessibilitySettings() {
  if (tryOpenSettings(new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))) return;
  if (tryOpenSettings(new Intent(Settings.ACTION_SETTINGS))) return;
  showMessage("Mở Trợ năng", "Hãy vào Cài đặt Android → Trợ năng → Ứng dụng đã tải xuống → bật \"Bảo vệ cập nhật Stella Sora\".", false);
 }

 private void openOverlaySettings() {
  Intent ov = new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:" + getPackageName()));
  if (tryOpenSettings(ov)) return;
  Intent details = new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.parse("package:" + getPackageName()));
  if (tryOpenSettings(details)) return;
  tryOpenSettings(new Intent(Settings.ACTION_SETTINGS));
 }

 private void openAppInfoSettings() {
  Intent details = new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.parse("package:" + getPackageName()));
  if (tryOpenSettings(details)) return;
  tryOpenSettings(new Intent(Settings.ACTION_SETTINGS));
 }

 private void pinGuardShortcut() {
  try {
   android.content.pm.ShortcutManager sm = getSystemService(android.content.pm.ShortcutManager.class);
   if (sm == null || !sm.isRequestPinShortcutSupported()) {
    showMessage("Ghim lối tắt bảo vệ", "Trình khởi chạy (Launcher) trên điện thoại không hỗ trợ tự ghim lối tắt. Bạn có thể mở Stella Sora trực tiếp qua nút \"Mở game\" trong ứng dụng này.", false);
    return;
   }
   Intent target = new Intent(this, LaunchGuardActivity.class).setAction(Intent.ACTION_VIEW);
   android.content.pm.ShortcutInfo info = new android.content.pm.ShortcutInfo.Builder(this, "stella_sora_guard_launch")
     .setShortLabel("Stella Sora Việt Hoá")
     .setLongLabel("Mở Stella Sora (Bảo vệ cập nhật)")
     .setIcon(android.graphics.drawable.Icon.createWithResource(this, R.drawable.app_icon))
     .setIntent(target)
     .build();
   sm.requestPinShortcut(info, null);
   showMessage("Đã gửi yêu cầu ghim lối tắt", "Hãy bấm \"Thêm\" trên hộp thoại của Android để đặt biểu tượng \"Stella Sora Việt Hoá\" ra màn hình chính. Khi mở game bằng biểu tượng này, launcher sẽ tự kiểm tra bản vá Yostar trước khi vào game.", false);
  } catch (Exception e) {
   showMessage("Chưa ghim được lối tắt", Store.cleanError(e), false);
  }
 }

 private void startGuardRestoreFlow() {
  JSONObject snap = LauncherService.snapshot(this);
  if (snap.optBoolean("busy")) {
   showMessage("Đang có thao tác", "Hãy chờ thao tác hiện tại hoàn tất rồi thử lại.", false);
   return;
  }
  JSONObject adbObj = snap.optJSONObject("adb");
  boolean connected = adbObj != null && adbObj.optBoolean("connected");
  boolean hasId = adbObj != null && adbObj.optBoolean("hasIdentity");
  if (!connected) {
   if (!LauncherService.isDevOptions(this)) {
    showDevModeGuideDialog();
    return;
   }
   if (!ErrorReport.isWifiConnected(this)) {
    JSONObject rep = ErrorReport.record(this, ErrorReport.explain(this, "E-ADB-NO-WIFI", "guardRestore", snap));
    event(Store.obj("type", "message", "data", ErrorReport.attach(Store.obj("title", rep.optString("errorTitle"), "message", rep.optString("message"), "error", true), rep)));
    return;
   }
   if (!hasId) {
    navigateWeb("adb");
    showMessage("Cần ghép đôi Local ADB 1 lần", "Để đóng Stella Sora và khôi phục dữ liệu gốc an toàn, hãy ghép đôi Local ADB trên máy (chỉ làm 1 lần duy nhất).", false);
    return;
   }
  }
  navigateWeb("overview");
  LauncherService.dispatch(this, "guardRestore", new JSONObject());
 }

 private void consumeGuardRestoreIntent() {
  if (!pendingGuardRestoreIntent || !loaded || !resumed) return;
  pendingGuardRestoreIntent = false;
  startGuardRestoreFlow();
 }

 private boolean tryOpenSettings(Intent intent) {
  try {
   startActivity(intent);
   return true;
  } catch (ActivityNotFoundException | SecurityException ignored) {
   return false;
  }
 }

 private void showWirelessReconnectPrompt() {
  if (!resumed || isFinishing()) return;
  if (reconnectDialog != null && reconnectDialog.isShowing()) return;
  reconnectDialog = dialogBuilder()
    .setTitle("Bật Gỡ lỗi không dây để kết nối nhanh")
    .setMessage("Máy đã ghép đôi trước đó nên KHÔNG cần nhập lại mã 6 số.\n\nHãy bấm nút bên dưới để mở Gỡ lỗi không dây và gạt Bật (hoặc tắt rồi bật lại) — launcher đang dò ngầm và sẽ tự kết nối ngay.")
    .setPositiveButton("Mở Gỡ lỗi không dây", (d, w) -> openWireless())
    .setNegativeButton("Đợi tại đây", null)
    .create();
  reconnectDialog.show();
 }

 private void navigateWeb(String page) {
  if (web != null && loaded) {
   web.evaluateJavascript("window.Stella&&window.Stella.navigate(" + JSONObject.quote(page) + ")", null);
  }
 }

 private void external(String url) throws Exception {
  Uri uri = Uri.parse(url);
  if (!"https".equals(uri.getScheme()) || uri.getHost() == null) throw new IOException("Liên kết không hợp lệ.");
  startActivity(new Intent(Intent.ACTION_VIEW, uri));
 }
 private void clipboard(String label, String text) {
  ClipboardManager cm = (ClipboardManager) getSystemService(CLIPBOARD_SERVICE);
  if (cm != null) cm.setPrimaryClip(ClipData.newPlainText(label, text));
 }
 private void maybeAutoSync() {
  if (!loaded || !resumed || autoSynced) return;
  try {
   JSONObject snapshot = LauncherService.snapshot(this);
   if (!snapshot.optBoolean("busy")) {
    LauncherService.dispatch(this, "sync", new JSONObject());
    autoSynced = true;
   }
  } catch (RuntimeException error) {
   showMessage("Chưa đồng bộ tự động", "Hãy mở ứng dụng và bấm Đồng bộ GitHub để thử lại.", true, "sync", error);
  }
 }
 private void emitState() { event(Store.obj("type", "state", "data", LauncherService.snapshot(this))); }
 private void showMessage(String title, String message, boolean error) { showMessage(title, message, error, null, null); }
 private void showMessage(String title, String message, boolean error, String action, Throwable cause) {
  JSONObject data = Store.obj("title", title, "message", message, "error", error);
  if (error) ErrorReport.attach(data, ErrorReport.record(this, ErrorReport.build(this, action, title, message, cause, null, LauncherService.snapshot(this))));
  event(Store.obj("type", "message", "data", data));
 }

 @Override public void event(JSONObject e) {
  runOnUiThread(() -> {
   String type = e.optString("type");
   if ("openWirelessForReconnect".equals(type)) {
    showWirelessReconnectPrompt();
    return;
   }
   if ("updatePrepared".equals(type)) {
    if (resumed && !isFinishing()) {
     try { installUpdate(); } catch (Exception ex) { showMessage("Chưa thực hiện được", Store.cleanError(ex), true, "installUpdate", ex); }
    }
    return;
   }
   if (web != null && loaded) {
    web.evaluateJavascript("window.Stella&&window.Stella.onEvent(JSON.parse(" + JSONObject.quote(e.toString()) + "))", null);
   }
   if ("state".equals(type)) {
    JSONObject s = e.optJSONObject("data");
    if (s != null) {
     JSONObject adbObj = s.optJSONObject("adb");
     if (adbObj != null && adbObj.optBoolean("connected") && reconnectDialog != null && reconnectDialog.isShowing()) {
      try { reconnectDialog.dismiss(); } catch (Exception ignored) {}
      reconnectDialog = null;
     }
     JSONObject g = s.optJSONObject("github"), r = s.optJSONObject("receipt");
     if (g != null && "online".equals(g.optString("releaseStatus")) && "none".equals(g.optString("launcherStatus"))) {
      LauncherUpdateNotice.clearIfCurrent(this, g.optString("repo") + "/" + g.optString("branch"));
     }
     if (g != null && "online".equals(g.optString("releaseStatus")) && g.optJSONObject("launcherUpdate") != null) {
      LauncherUpdateNotice.observe(this, g.optString("repo") + "/" + g.optString("branch"), g.optJSONObject("launcherUpdate"), g.optString("releaseNotes"), false);
     }
     if (g != null && "online".equals(g.optString("releaseStatus")) && "none".equals(g.optString("manifestStatus"))) {
      UpdateNotice.clearIfCurrent(this, g.optString("repo") + "/" + g.optString("branch"));
     }
     if (g != null && "online".equals(g.optString("releaseStatus")) && "available".equals(g.optString("manifestStatus"))) {
      UpdateNotice.observe(this, g.optString("repo") + "/" + g.optString("branch"), g.optString("translationVersion"), g.optString("releaseNotes"), r != null && r.optBoolean("present") ? r.optString("version") : UpdateNotice.installed(this), false);
     }
    }
    showUpdateNotice();
   }
  });
 }

 private void showUpdateNotice() {
  if (!resumed || !loaded || updateDialogShowing) return;
  String[] notice = UpdateNotice.pending(this);
  if (notice == null) {
   showLauncherUpdateNotice();
   return;
  }
  updateDialogShowing = true;
  ReleaseNoticeDialog.builder(this, false, notice[0], notice[1], isDarkTheme())
    .setPositiveButton("Xem & Cập nhật", (d, w) -> {
     UpdateNotice.dismiss(this, notice[0]);
     navigateWeb("overview");
    })
    .setNegativeButton("Đóng", (d, w) -> UpdateNotice.dismiss(this, notice[0]))
    .setNeutralButton("Tắt trong 24 giờ", (d, w) -> UpdateNotice.snooze(this))
    .setOnCancelListener(d -> UpdateNotice.dismiss(this, notice[0]))
    .setOnDismissListener(d -> {
     updateDialogShowing = false;
     showLauncherUpdateNotice();
    })
    .show();
 }

 private void showLauncherUpdateNotice() {
  if (!resumed || !loaded || updateDialogShowing) return;
  String[] notice = LauncherUpdateNotice.pending(this);
  if (notice == null) return;
  long code = Long.parseLong(notice[2]);
  updateDialogShowing = true;
  ReleaseNoticeDialog.builder(this, true, notice[0], notice[1], isDarkTheme())
    .setPositiveButton("Cập nhật ngay", (d, w) -> {
     LauncherUpdateNotice.dismiss(this, code);
     navigateWeb("settings");
     try { installUpdate(); } catch (Exception e) { showMessage("Chưa thực hiện được", Store.cleanError(e), true, "installUpdate", e); }
    })
    .setNegativeButton("Đóng", (d, w) -> LauncherUpdateNotice.dismiss(this, code))
    .setNeutralButton("Tắt trong 24 giờ", (d, w) -> LauncherUpdateNotice.snooze(this))
    .setOnCancelListener(d -> LauncherUpdateNotice.dismiss(this, code))
    .setOnDismissListener(d -> updateDialogShowing = false)
    .show();
 }

 private void offerUpdateNotifications() {
  if (Build.VERSION.SDK_INT < 33 || checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED) return;
  android.content.SharedPreferences p = getSharedPreferences("translation_notice", MODE_PRIVATE);
  if (p.getBoolean("permission_offered", false)) return;
  p.edit().putBoolean("permission_offered", true).apply();
  dialogBuilder()
    .setTitle("Thông báo bản Việt hoá mới")
    .setMessage("Cho phép thông báo để nhận tin khi có bản Việt hoá mới, kể cả khi bạn không mở launcher.")
    .setNegativeButton("Để sau", null)
    .setPositiveButton("Cho phép", (d, w) -> requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, 72))
    .show();
 }

 @Override protected void onResume() {
  super.onResume();
  resumed = true;
  applySystemChromeTheme();
  LauncherService.listen(this);
  if (loaded) {
   emitState();
   maybeAutoSync();
   showUpdateNotice();
   consumeGuardRestoreIntent();
  }
  new Handler(Looper.getMainLooper()).postDelayed(() -> {
   if (resumed && !updateDialogShowing) offerUpdateNotifications();
  }, 1200);
 }

 @Override protected void onPause() {
  resumed = false;
  super.onPause();
 }

 @Override public void onRequestPermissionsResult(int request, String[] permissions, int[] grants) {
  super.onRequestPermissionsResult(request, permissions, grants);
  if (request == 71) {
   String action = afterPermission;
   afterPermission = null;
   if (grants.length > 0 && grants[0] == PackageManager.PERMISSION_GRANTED && action != null) {
    LauncherService.dispatch(this, action, new JSONObject());
    if ("startPairingNotification".equals(action)) openWireless();
   } else {
    JSONObject rep = ErrorReport.record(this, ErrorReport.explain(this, "E-NOTIF-PERMISSION", "startPairingNotification", LauncherService.snapshot(this)));
    event(Store.obj("type", "message", "data", ErrorReport.attach(Store.obj("title", rep.optString("errorTitle"), "message", rep.optString("message"), "error", false), rep)));
   }
  }
 }

 @Override public void onBackPressed() {
  if (web == null || !loaded) {
   super.onBackPressed();
   return;
  }
  web.evaluateJavascript("window.Stella?window.Stella.goBack():false", result -> {
   if (!"true".equals(result)) finish();
  });
 }

 @Override protected void onDestroy() {
  if (reconnectDialog != null && reconnectDialog.isShowing()) {
   try { reconnectDialog.dismiss(); } catch (Exception ignored) {}
  }
  LauncherService.unlisten(this);
  if (web != null) {
   web.removeJavascriptInterface("StellaNative");
   web.destroy();
   web = null;
  }
  super.onDestroy();
 }

 private void openDeviceInfo() {
  String[] actions = new String[]{Settings.ACTION_DEVICE_INFO_SETTINGS, "android.settings.DEVICE_INFO_SETTINGS", Settings.ACTION_SETTINGS};
  for (String action : actions) {
   if (tryOpenSettings(new Intent(action))) return;
  }
  showMessage("Mở Cài đặt", "Hãy mở Cài đặt hệ thống → Thông tin điện thoại để chạm 7 lần bật Chế độ nhà phát triển.", false);
 }

 private void openDevSettings() {
  String[] actions = new String[]{Settings.ACTION_APPLICATION_DEVELOPMENT_SETTINGS, "android.settings.APPLICATION_DEVELOPMENT_SETTINGS", Settings.ACTION_SETTINGS};
  for (String action : actions) {
   if (tryOpenSettings(new Intent(action))) return;
  }
  showMessage("Mở Tuỳ chọn nhà phát triển", "Hãy mở Cài đặt → Tuỳ chọn nhà phát triển.", false);
 }

 private void showDevModeGuideDialog() {
  String oem = ErrorReport.oemFamily();
  String oemHint;
  if ("xiaomi".equals(oem)) {
   oemHint = "1. Bấm \"Mở Thông tin điện thoại\".\n2. Chạm liên tiếp 7 lần vào \"Phiên bản OS / HyperOS / MIUI\".\n3. Trong Tuỳ chọn nhà phát triển, nhớ bật thêm \"Gỡ lỗi USB (Cài đặt bảo mật)\".";
  } else if ("samsung".equals(oem)) {
   oemHint = "1. Bấm \"Mở Thông tin điện thoại\" → chọn \"Thông tin phần mềm\".\n2. Chạm liên tiếp 7 lần vào \"Số hiệu bản tạo\".\n3. Quay lại Cài đặt → Tuỳ chọn nhà phát triển → bật Gỡ lỗi không dây.";
  } else if ("oppo".equals(oem)) {
   oemHint = "1. Bấm \"Mở Thông tin điện thoại\" → chọn \"Phiên bản\" (Version).\n2. Chạm liên tiếp 7 lần vào \"Số bản dựng\" (Build number).\n3. Trong Tuỳ chọn nhà phát triển, cuộn xuống cuối và BẬT \"Tắt giám sát quyền\".";
  } else if ("vivo".equals(oem)) {
   oemHint = "1. Bấm \"Mở Thông tin điện thoại\" → chọn \"Thông tin phần mềm\".\n2. Chạm liên tiếp 7 lần vào \"Số bản dựng\".\n3. Quay lại Hệ thống → Tuỳ chọn nhà phát triển → bật Gỡ lỗi không dây.";
  } else {
   oemHint = "1. Bấm \"Mở Thông tin điện thoại\" bên dưới.\n2. Tìm dòng \"Số bản dựng\" (Build Number) hoặc \"Phiên bản phần mềm\".\n3. Chạm liên tiếp 7 lần cho đến khi máy báo \"Bạn đã là nhà phát triển!\".";
  }
  dialogBuilder()
    .setTitle("Chưa bật Tuỳ chọn nhà phát triển")
    .setMessage("Để dùng Gỡ lỗi không dây, hãy kích hoạt Chế độ nhà phát triển (chỉ làm 1 lần):\n\n" + oemHint + "\n\nSau khi kích hoạt xong, quay lại ứng dụng để kết nối.")
    .setPositiveButton("Mở Thông tin điện thoại", (d, w) -> openDeviceInfo())
    .setNeutralButton("Mở Cài đặt", (d, w) -> tryOpenSettings(new Intent(Settings.ACTION_SETTINGS)))
    .setNegativeButton("Đóng", null)
    .show();
 }
}
