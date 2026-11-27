package com.stellasora.viethoa.localadb;

import android.Manifest;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.job.JobInfo;
import android.app.job.JobScheduler;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.os.Build;
import org.json.JSONObject;

/**
 * Layer C (Passive Guard): 30-minute background JobScheduler + Heads-Up Notification
 * decorated with authentic Stella Sora Tyrant popup art (game_tyrant_head.png) and 1-tap restore action.
 */
final class OfficialUpdateNotice {
 static final String PREF = "official_game_guard";
 static final String CHANNEL = "official_game_updates_v1";
 static final int JOB_ID = 10405;
 static final int NOTIFICATION_ID = 10406;

 private OfficialUpdateNotice() {}

 private static SharedPreferences prefs(Context c) {
  return c.getSharedPreferences(PREF, Context.MODE_PRIVATE);
 }

 static void schedule(Context c) {
  try {
   JobScheduler js = (JobScheduler) c.getSystemService(Context.JOB_SCHEDULER_SERVICE);
   if (js == null) return;
   JobInfo job = new JobInfo.Builder(JOB_ID, new ComponentName(c, OfficialUpdateCheckJob.class))
     .setRequiredNetworkType(JobInfo.NETWORK_TYPE_ANY)
     .setPeriodic(30L * 60L * 1000L)
     .setPersisted(true)
     .build();
   js.schedule(job);
  } catch (Exception ignored) {}
 }

 static void cancel(Context c) {
  try {
   NotificationManager nm = (NotificationManager) c.getSystemService(Context.NOTIFICATION_SERVICE);
   if (nm != null) nm.cancel(NOTIFICATION_ID);
   prefs(c).edit().remove("notified_res").apply();
  } catch (Exception ignored) {}
 }

 static synchronized void forceNotify(Context c, JSONObject state) {
  try { prefs(c).edit().remove("notified_res").apply(); } catch (Exception ignored) {}
  notifyIfNeeded(c, state);
 }

 static synchronized void notifyIfNeeded(Context c, JSONObject state) {
  if (state == null || !state.optBoolean("needsRestore", false)) {
   cancel(c);
   return;
  }
  String latestRes = state.optString("latestResourceVersion", "");
  String latestGame = state.optString("latestGameVersion", "");
  String localRes = state.optString("localResourceVersion", "");
  String key = latestGame + "|" + latestRes;
  if (key.equals(prefs(c).getString("notified_res", ""))) return;

  if (Build.VERSION.SDK_INT >= 33
    && c.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
   return;
  }
  NotificationManager nm = (NotificationManager) c.getSystemService(Context.NOTIFICATION_SERVICE);
  if (nm == null || !nm.areNotificationsEnabled()) return;

  NotificationChannel ch = new NotificationChannel(
    CHANNEL,
    "Cảnh báo cập nhật Stella Sora",
    NotificationManager.IMPORTANCE_HIGH
  );
  ch.setDescription("Cảnh báo ngay khi Yostar có bản cập nhật mới để khôi phục dữ liệu gốc trước khi vào game.");
  ch.enableVibration(true);
  nm.createNotificationChannel(ch);
  if (nm.getNotificationChannel(CHANNEL).getImportance() == NotificationManager.IMPORTANCE_NONE) return;

  Intent restoreIntent = new Intent(c, MainActivity.class)
    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP)
    .putExtra(MainActivity.EXTRA_GUARD_RESTORE, true);
  PendingIntent restorePi = PendingIntent.getActivity(
    c, NOTIFICATION_ID, restoreIntent, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
  );

  Intent alertIntent = new Intent(c, GameUpdateGuardActivity.class)
    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
  PendingIntent alertPi = PendingIntent.getActivity(
    c, NOTIFICATION_ID + 1, alertIntent, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
  );

  String verLine = (!localRes.isEmpty() && !latestRes.isEmpty())
    ? ("Tài nguyên " + localRes + " → " + latestRes)
    : ("Phiên bản mới " + (latestGame.isEmpty() ? latestRes : latestGame));
  String body = verLine
    + ". KHÔNG bấm tải bản vá trong game khi còn bản Việt hoá! Chạm \"Khôi phục gốc ngay\" để đưa game về bản gốc an toàn.";

  Notification.Builder b = new Notification.Builder(c, CHANNEL)
    .setSmallIcon(R.drawable.ic_notification)
    .setColor(0xFFE11D48)
    .setContentTitle("DỪNG LẠI — Stella Sora có bản cập nhật mới!")
    .setContentText(body)
    .setStyle(new Notification.BigTextStyle().bigText(body))
    .setCategory(Notification.CATEGORY_ALARM)
    .setPriority(Notification.PRIORITY_HIGH)
    .setAutoCancel(false)
    .setContentIntent(alertPi)
    .addAction(new Notification.Action.Builder(R.drawable.game_icon_restore, "Khôi phục gốc ngay", restorePi).build())
    .addAction(new Notification.Action.Builder(R.drawable.game_warning_sm, "Xem cảnh báo", alertPi).build());

  try {
   Bitmap large = BitmapFactory.decodeResource(c.getResources(), R.drawable.game_tyrant_head);
   if (large != null) b.setLargeIcon(large);
  } catch (Exception ignored) {}

  nm.notify(NOTIFICATION_ID, b.build());
  prefs(c).edit().putString("notified_res", key).apply();
 }
}
