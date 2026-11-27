package com.stellasora.viethoa.localadb;

import android.Manifest;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.content.pm.ShortcutInfo;
import android.content.pm.ShortcutManager;
import android.graphics.drawable.Icon;
import android.os.Build;
import android.provider.Settings;
import org.json.JSONObject;
import java.util.Collections;
import java.util.List;

/**
 * Manages the unmistakable "Chơi Stella VH" Home Screen guard shortcut:
 * - Adaptive bitmap icon (ic_shortcut_play_vh) safe on every Android launcher mask
 * - Live verification via ShortcutManager.getPinnedShortcuts() + system pin callback
 * - Auto-upgrade of previously pinned v2.1.x shortcuts in-place via updateShortcuts()
 * - Wireless Debugging (adb_wifi_enabled) status read helper
 */
final class ShortcutGuardHelper {
 static final String SHORTCUT_ID = "stella_sora_guard_launch";
 static final String ACTION_SHORTCUT_PINNED = "com.stellasora.viethoa.localadb.SHORTCUT_PINNED";
 private static final String PREF = "shortcut_guard_prefs";
 private static final long CALLBACK_GRACE_MS = 20_000L;

 private static volatile long sessionCallbackMs = 0L;

 private ShortcutGuardHelper() {}

 private static SharedPreferences prefs(Context c) {
  return c.getApplicationContext().getSharedPreferences(PREF, Context.MODE_PRIVATE);
 }

 static boolean isPinSupported(Context c) {
  try {
   ShortcutManager sm = c.getSystemService(ShortcutManager.class);
   return sm != null && sm.isRequestPinShortcutSupported();
  } catch (Throwable ignored) {
   return false;
  }
 }

 static boolean isPinnedInOs(Context c) {
  try {
   ShortcutManager sm = c.getSystemService(ShortcutManager.class);
   if (sm == null) return false;
   List<ShortcutInfo> pinned = sm.getPinnedShortcuts();
   if (pinned == null) return false;
   for (ShortcutInfo info : pinned) {
    if (info != null && SHORTCUT_ID.equals(info.getId()) && info.isPinned() && info.isEnabled()) {
     return true;
    }
   }
  } catch (Throwable ignored) {}
  return false;
 }

 static boolean areNotificationsEnabled(Context c) {
  try {
   if (Build.VERSION.SDK_INT >= 33
     && c.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
    return false;
   }
   NotificationManager nm = (NotificationManager) c.getSystemService(Context.NOTIFICATION_SERVICE);
   return nm != null && nm.areNotificationsEnabled();
  } catch (Throwable ignored) {
   return false;
  }
 }

 /** Returns 1 if Wireless Debugging is ON, 0 if OFF, -1 if unavailable/restricted. */
 static int readWirelessDebuggingState(Context c) {
  try {
   return Settings.Global.getInt(c.getContentResolver(), "adb_wifi_enabled", -1);
  } catch (Throwable ignored) {
   return -1;
  }
 }

 static Icon buildShortcutIcon(Context c) {
  // Transparent big round emblem icon: use direct resource icon so Android does not zoom-crop it as an adaptive square.
  return Icon.createWithResource(c, R.drawable.ic_shortcut_play_vh);
 }

 static ShortcutInfo buildShortcutInfo(Context c) {
  Intent target = new Intent(c, LaunchGuardActivity.class)
    .setAction(Intent.ACTION_VIEW)
    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
  return new ShortcutInfo.Builder(c, SHORTCUT_ID)
    .setShortLabel("Chơi Stella VH")
    .setLongLabel("Chơi Stella Sora (Việt Hoá · Bảo vệ cập nhật)")
    .setIcon(buildShortcutIcon(c))
    .setIntent(target)
    .build();
 }

 /** Upgrades any previously pinned shortcut (e.g. from v2.1.7) to the new unmistakable icon & label. */
 static void upgradeExistingShortcutIfPinned(Context c) {
  try {
   ShortcutManager sm = c.getSystemService(ShortcutManager.class);
   if (sm == null || !isPinnedInOs(c)) return;
   sm.updateShortcuts(Collections.singletonList(buildShortcutInfo(c)));
  } catch (Throwable err) {
   DiagnosticLog.log(c, "shortcut", "Không cập nhật được icon lối tắt cũ: " + Store.cleanError(err));
  }
 }

 static boolean requestPin(Context c) {
  SharedPreferences p = prefs(c);
  int attempts = p.getInt("pin_attempts", 0) + 1;
  p.edit().putInt("pin_attempts", attempts).apply();

  ShortcutManager sm = c.getSystemService(ShortcutManager.class);
  if (sm == null || !sm.isRequestPinShortcutSupported()) {
   DiagnosticLog.log(c, "shortcut", "Launcher hệ thống không hỗ trợ requestPinShortcut.");
   return false;
  }

  // If already pinned in OS, simply refresh its icon/label and mark confirmed!
  if (isPinnedInOs(c)) {
   upgradeExistingShortcutIfPinned(c);
   onPinCallbackReceived(c);
   return true;
  }

  Intent callbackIntent = new Intent(c, ShortcutPinnedReceiver.class)
    .setAction(ACTION_SHORTCUT_PINNED);
  PendingIntent successPi = PendingIntent.getBroadcast(
    c,
    10420,
    callbackIntent,
    PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
  );
  try {
   boolean ok = sm.requestPinShortcut(buildShortcutInfo(c), successPi.getIntentSender());
   DiagnosticLog.log(c, "shortcut", "Đã gửi yêu cầu ghim lối tắt Chơi Stella VH (lần " + attempts + ", result=" + ok + ").");
   return ok;
  } catch (Throwable err) {
   DiagnosticLog.log(c, "shortcut", "Lỗi gửi yêu cầu ghim lối tắt: " + Store.cleanError(err));
   return false;
  }
 }

 static void onPinCallbackReceived(Context c) {
  sessionCallbackMs = System.currentTimeMillis();
  prefs(c).edit()
    .putLong("last_callback_ms", sessionCallbackMs)
    .putBoolean("callback_confirmed", true)
    .putInt("pin_attempts", 0)
    .apply();
  DiagnosticLog.log(c, "shortcut", "Android xác nhận đã ghim lối tắt Chơi Stella VH ra màn hình chính.");
 }

 static void markManualQuirkAck(Context c, boolean ack) {
  prefs(c).edit().putBoolean("manual_quirk_ack", ack).apply();
  DiagnosticLog.log(c, "shortcut", "Người dùng xác nhận lối tắt thủ công trên ROM không báo trạng thái: " + ack);
 }

 static boolean isPinnedEffective(Context c) {
  boolean osPinned = isPinnedInOs(c);
  SharedPreferences p = prefs(c);
  if (osPinned) {
   if (!p.getBoolean("os_verified_ever", false) || p.getInt("pin_attempts", 0) != 0) {
    p.edit().putBoolean("os_verified_ever", true).putInt("pin_attempts", 0).apply();
   }
   return true;
  }
  long now = System.currentTimeMillis();
  if (sessionCallbackMs > 0 && (now - sessionCallbackMs) <= CALLBACK_GRACE_MS) {
   return true;
  }
  // If OS previously reported pinned and now does NOT, the user removed it from Home Screen -> require re-pinning!
  if (p.getBoolean("os_verified_ever", false)) {
   return false;
  }
  // On launchers that never populate getPinnedShortcuts(), respect either explicit system callback or manual ack.
  return p.getBoolean("callback_confirmed", false) || p.getBoolean("manual_quirk_ack", false);
 }

 static JSONObject statusJson(Context c) {
  boolean canPin = isPinSupported(c);
  boolean osPinned = isPinnedInOs(c);
  boolean effective = isPinnedEffective(c);
  SharedPreferences p = prefs(c);
  int attempts = effective ? 0 : p.getInt("pin_attempts", 0);
  boolean recentCb = sessionCallbackMs > 0 && (System.currentTimeMillis() - sessionCallbackMs) <= CALLBACK_GRACE_MS;
  return Store.obj(
    "shortcutPinned", effective,
    "shortcutPinnedByOs", osPinned,
    "shortcutCallbackReceived", recentCb || p.getBoolean("callback_confirmed", false),
    "shortcutPinAttempts", attempts,
    "canPinShortcut", canPin,
    "notificationsEnabled", areNotificationsEnabled(c),
    "accessibilityEnabled", GameLaunchGuardService.isEnabled(c),
    "overlayEnabled", GameLaunchGuardService.canDrawOverlay(c),
    "wirelessDebuggingState", readWirelessDebuggingState(c),
    "oemFamily", ErrorReport.oemFamily()
  );
 }
}
