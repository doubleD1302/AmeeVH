package com.stellasora.viethoa.localadb;

import android.accessibilityservice.AccessibilityService;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.graphics.PixelFormat;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.provider.Settings;
import android.text.TextUtils;
import android.view.Gravity;
import android.view.View;
import android.view.WindowManager;
import android.view.accessibility.AccessibilityEvent;
import org.json.JSONObject;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Layer A (Proactive Guard): Scoped strictly to com.YoStarEN.StellaSora (canRetrieveWindowContent=false).
 * When the player taps the original Stella Sora icon while Vietnamese patch is active and Yostar
 * has released a newer update, immediately blocks screen interaction with an authentic game-asset
 * TYPE_ACCESSIBILITY_OVERLAY forcing restore before updating.
 */
public final class GameLaunchGuardService extends AccessibilityService {
 private final Handler main = new Handler(Looper.getMainLooper());
 private final ExecutorService netExecutor = Executors.newSingleThreadExecutor();
 private View overlayView;
 private volatile boolean gameInForeground;
 private volatile long lastLiveCheckElapsed;

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

 @Override public void onAccessibilityEvent(AccessibilityEvent event) {
  if (event == null || event.getEventType() != AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED) return;
  CharSequence pkgCs = event.getPackageName();
  String pkg = pkgCs == null ? "" : pkgCs.toString();
  if (!Store.GAME.equals(pkg)) return;

  gameInForeground = true;

  // 1. Instant 0 ms local check from persisted official_guard_state.json + receipt
  JSONObject cached = OfficialAndroidClient.readCachedGuardState(this);
  if (!cached.optBoolean("vhModified", false)) {
   // Vanilla game — never disturb the player
   return;
  }

  if (cached.optBoolean("needsRestore", false)) {
   showBlockingOverlay(cached);
   return;
  }

  // 2. Live 432-byte serverlist.html check (throttled to 30s) in case Yostar pushed a fresh patch
  long now = SystemClock.elapsedRealtime();
  if (now - lastLiveCheckElapsed < 30_000L) return;
  lastLiveCheckElapsed = now;

  netExecutor.execute(() -> {
   try {
    JSONObject fresh = OfficialAndroidClient.checkAndSave(this, 6000);
    if (fresh.optBoolean("needsRestore", false)) {
     OfficialUpdateNotice.notifyIfNeeded(this, fresh);
     main.post(() -> {
      if (gameInForeground) showBlockingOverlay(fresh);
     });
    }
   } catch (Exception ignored) {}
  });
 }

 private void showBlockingOverlay(JSONObject state) {
  if (overlayView != null) return;
  WindowManager wm = (WindowManager) getSystemService(WINDOW_SERVICE);
  if (wm == null) return;

  View view = GameAlertViewBuilder.buildMandatoryUpdateAlert(
    this,
    state,
    "Trợ năng bảo vệ trực tiếp",
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
      } catch (Exception ignored) {}
     }, 160);
    },
    () -> {
     removeOverlay();
     gameInForeground = false;
     performGlobalAction(GLOBAL_ACTION_HOME);
    }
  );

  WindowManager.LayoutParams lp = new WindowManager.LayoutParams(
    WindowManager.LayoutParams.MATCH_PARENT,
    WindowManager.LayoutParams.MATCH_PARENT,
    WindowManager.LayoutParams.TYPE_ACCESSIBILITY_OVERLAY,
    WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN | WindowManager.LayoutParams.FLAG_FULLSCREEN,
    PixelFormat.TRANSLUCENT
  );
  lp.gravity = Gravity.CENTER;

  try {
   wm.addView(view, lp);
   overlayView = view;
  } catch (Exception ignored) {
   // Fallback to translucent Activity if OEM blocks overlay window
   try {
    Intent fallback = new Intent(this, GameUpdateGuardActivity.class)
      .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
    startActivity(fallback);
   } catch (Exception ignored2) {}
  }
 }

 private void removeOverlay() {
  View v = overlayView;
  overlayView = null;
  if (v != null) {
   try {
    WindowManager wm = (WindowManager) getSystemService(WINDOW_SERVICE);
    if (wm != null) wm.removeViewImmediate(v);
   } catch (Exception ignored) {}
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
