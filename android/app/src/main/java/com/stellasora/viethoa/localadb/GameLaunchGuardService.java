package com.stellasora.viethoa.localadb;

import android.accessibilityservice.AccessibilityService;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.graphics.PixelFormat;
import android.hardware.display.DisplayManager;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.provider.Settings;
import android.text.TextUtils;
import android.view.Display;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.View;
import android.view.WindowManager;
import android.view.accessibility.AccessibilityEvent;
import org.json.JSONObject;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Layer A (Proactive Guard): Scoped strictly to com.YoStarEN.StellaSora (canRetrieveWindowContent=false).
 * When the player opens or resumes the original Stella Sora icon while Vietnamese patch is active
 * and Yostar has released a newer update, immediately blocks interaction with an authentic game-asset
 * overlay (WindowContext TYPE_ACCESSIBILITY_OVERLAY -> TYPE_APPLICATION_OVERLAY fallback -> Home + Activity/Heads-up).
 */
public final class GameLaunchGuardService extends AccessibilityService {
 private final Handler main = new Handler(Looper.getMainLooper());
 private final ExecutorService netExecutor = Executors.newSingleThreadExecutor();
 private View overlayView;
 private WindowManager overlayWm;
 private volatile boolean gameInForeground;
 private volatile long lastLiveCheckElapsed;
 private volatile long lastTriggerElapsed;

 static boolean isEnabled(Context c) {
  try {
   String enabled = Settings.Secure.getString(c.getContentResolver(), Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES);
   if (enabled == null || enabled.isEmpty()) return false;
   ComponentName expected = new ComponentName(c, GameLaunchGuardService.class);
   String flat = expected.flattenToString();
   String shortFlat = expected.flattenToShortString();
   TextUtils.SimpleStringSplitter splitter = new TextUtils.SimpleStringSplitter(':');
   splitter.setString(enabled);
   while (splitter.hasNext()) {
    String item = splitter.next();
    if (flat.equalsIgnoreCase(item) || shortFlat.equalsIgnoreCase(item)) return true;
   }
  } catch (Exception ignored) {}
  return false;
 }

 static boolean canDrawOverlay(Context c) {
  try {
   return Settings.canDrawOverlays(c);
  } catch (Exception ignored) {
   return false;
  }
 }

 @Override protected void onServiceConnected() {
  super.onServiceConnected();
  DiagnosticLog.log(this, "guard", "Dịch vụ Trợ năng bảo vệ cập nhật đã kết nối (Android " + Build.VERSION.RELEASE + ").");
 }

 @Override public void onAccessibilityEvent(AccessibilityEvent event) {
  if (event == null) return;
  int type = event.getEventType();
  if (type != AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED
    && type != AccessibilityEvent.TYPE_WINDOWS_CHANGED) {
   return;
  }
  CharSequence pkgCs = event.getPackageName();
  String pkg = pkgCs == null ? "" : pkgCs.toString();
  if (!Store.GAME.equals(pkg)) return;

  long now = SystemClock.elapsedRealtime();
  if (now - lastTriggerElapsed < 350L && overlayView != null && overlayView.isAttachedToWindow()) {
   return;
  }
  lastTriggerElapsed = now;
  gameInForeground = true;

  // 1. Instant 0 ms local check from persisted official_guard_state.json + receipt
  JSONObject cached = OfficialAndroidClient.readCachedGuardState(this);
  if (!cached.optBoolean("vhModified", false)) {
   return;
  }

  if (cached.optBoolean("needsRestore", false)) {
   DiagnosticLog.log(this, "guard", "Phát hiện mở Stella Sora khi đang cần khôi phục gốc (cached RES "
     + cached.optString("localResourceVersion") + " -> " + cached.optString("latestResourceVersion") + ").");
   main.post(() -> showBlockingOverlay(cached));
   return;
  }

  // 2. Live 432-byte serverlist.html check (throttled to 30s) in case Yostar pushed a fresh patch
  if (now - lastLiveCheckElapsed < 30_000L) return;
  lastLiveCheckElapsed = now;

  netExecutor.execute(() -> {
   try {
    JSONObject fresh = OfficialAndroidClient.checkAndSave(this, 6000);
    if (fresh.optBoolean("needsRestore", false)) {
     DiagnosticLog.log(this, "guard", "Phát hiện cập nhật Yostar trực tiếp khi mở game (RES "
       + fresh.optString("localResourceVersion") + " -> " + fresh.optString("latestResourceVersion") + ").");
     OfficialUpdateNotice.notifyIfNeeded(this, fresh);
     main.post(() -> {
      if (gameInForeground) showBlockingOverlay(fresh);
     });
    }
   } catch (Exception err) {
    DiagnosticLog.log(this, "guard", "Kiểm tra trực tiếp serverlist thất bại: " + Store.cleanError(err));
   }
  });
 }

 private Context createOverlayContext(int windowType) {
  try {
   if (Build.VERSION.SDK_INT >= 30) {
    DisplayManager dm = (DisplayManager) getSystemService(DISPLAY_SERVICE);
    Display display = dm != null ? dm.getDisplay(Display.DEFAULT_DISPLAY) : null;
    if (display != null) {
     return createDisplayContext(display).createWindowContext(windowType, null);
    }
   }
  } catch (Throwable err) {
   DiagnosticLog.log(this, "guard", "createWindowContext(" + windowType + ") fallback: " + Store.cleanError(err));
  }
  return this;
 }

 private WindowManager.LayoutParams buildOverlayParams(int windowType) {
  int flags = WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN
    | WindowManager.LayoutParams.FLAG_LAYOUT_INSET_DECOR
    | WindowManager.LayoutParams.FLAG_WATCH_OUTSIDE_TOUCH;
  WindowManager.LayoutParams lp = new WindowManager.LayoutParams(
    WindowManager.LayoutParams.MATCH_PARENT,
    WindowManager.LayoutParams.MATCH_PARENT,
    windowType,
    flags,
    PixelFormat.TRANSLUCENT
  );
  lp.gravity = Gravity.CENTER;
  lp.layoutInDisplayCutoutMode = WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES;
  return lp;
 }

 private boolean tryAttachOverlay(JSONObject state, int windowType, String modeLabel) {
  Context uiCtx = createOverlayContext(windowType);
  WindowManager wm = (WindowManager) uiCtx.getSystemService(WINDOW_SERVICE);
  if (wm == null) return false;

  View view = GameAlertViewBuilder.buildMandatoryUpdateAlert(
    uiCtx,
    state,
    modeLabel,
    "Thoát về màn hình chính",
    () -> {
     removeOverlay();
     gameInForeground = false;
     performGlobalAction(GLOBAL_ACTION_HOME);
     main.postDelayed(() -> {
      try {
       Intent i = new Intent(this, MainActivity.class)
         .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP)
         .putExtra(MainActivity.EXTRA_GUARD_RESTORE, true);
       startActivity(i);
      } catch (Throwable ignored) {}
     }, 180);
    },
    () -> {
     removeOverlay();
     gameInForeground = false;
     performGlobalAction(GLOBAL_ACTION_HOME);
    }
  );

  // Clean up automatically if OS/OEM detaches the window, and treat Back key as safe exit to Home.
  view.addOnAttachStateChangeListener(new View.OnAttachStateChangeListener() {
   @Override public void onViewAttachedToWindow(View v) {}
   @Override public void onViewDetachedFromWindow(View v) {
    if (overlayView == v) {
     overlayView = null;
     overlayWm = null;
     gameInForeground = false;
    }
   }
  });
  view.setFocusableInTouchMode(true);
  view.setOnKeyListener((v, keyCode, keyEvent) -> {
   if (keyCode == KeyEvent.KEYCODE_BACK && keyEvent != null && keyEvent.getAction() == KeyEvent.ACTION_UP) {
    removeOverlay();
    gameInForeground = false;
    performGlobalAction(GLOBAL_ACTION_HOME);
    return true;
   }
   return false;
  });

  try {
   wm.addView(view, buildOverlayParams(windowType));
   overlayView = view;
   overlayWm = wm;
   view.requestFocus();
   DiagnosticLog.log(this, "guard", "Đã hiển thị popup chặn cập nhật (" + modeLabel + ").");
   return true;
  } catch (Throwable err) {
   DiagnosticLog.log(this, "guard", "Không gắn được overlay " + modeLabel + ": " + Store.cleanError(err));
   return false;
  }
 }

 private void showBlockingOverlay(JSONObject state) {
  if (overlayView != null) {
   if (overlayView.isAttachedToWindow()) return;
   removeOverlay();
  }

  // Tier 1: Accessibility overlay (works without SYSTEM_ALERT_WINDOW on standard Android 11-16)
  if (tryAttachOverlay(state, WindowManager.LayoutParams.TYPE_ACCESSIBILITY_OVERLAY, "Trợ năng bảo vệ trực tiếp")) {
   return;
  }

  // Tier 2: Standard Application Overlay if user granted SYSTEM_ALERT_WINDOW (reliable on Xiaomi/OPPO/Vivo)
  if (canDrawOverlay(this)
    && tryAttachOverlay(state, WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY, "Lớp phủ bảo vệ trực tiếp")) {
   return;
  }

  // Tier 3: Kick user safely out of Stella Sora first so they cannot accidentally tap Update, then raise alert Activity + Heads-Up Notification
  DiagnosticLog.log(this, "guard", "Chuyển sang phương án dự phòng: thoát về Home + mở màn hình cảnh báo & thông báo.");
  gameInForeground = false;
  try { performGlobalAction(GLOBAL_ACTION_HOME); } catch (Throwable ignored) {}
  try { OfficialUpdateNotice.forceNotify(this, state); } catch (Throwable ignored) {}
  main.postDelayed(() -> {
   try {
    Intent fallback = new Intent(this, GameUpdateGuardActivity.class)
      .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP)
      .putExtra(GameUpdateGuardActivity.EXTRA_SOURCE, "Trợ năng bảo vệ (dự phòng)");
    startActivity(fallback);
   } catch (Throwable err) {
    DiagnosticLog.log(this, "guard", "Fallback GameUpdateGuardActivity bị chặn nền: " + Store.cleanError(err));
   }
  }, 150);
 }

 private void removeOverlay() {
  View v = overlayView;
  WindowManager wm = overlayWm;
  overlayView = null;
  overlayWm = null;
  if (v != null) {
   try {
    WindowManager targetWm = wm != null ? wm : (WindowManager) getSystemService(WINDOW_SERVICE);
    if (targetWm != null && v.isAttachedToWindow()) {
     targetWm.removeViewImmediate(v);
    }
   } catch (Throwable ignored) {}
  }
 }

 @Override public void onInterrupt() {
  gameInForeground = false;
  removeOverlay();
 }

 @Override public void onDestroy() {
  gameInForeground = false;
  removeOverlay();
  netExecutor.shutdownNow();
  super.onDestroy();
 }
}
