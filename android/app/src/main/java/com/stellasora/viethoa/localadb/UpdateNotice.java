package com.stellasora.viethoa.localadb;

import android.Manifest;
import android.app.*;
import android.app.job.*;
import android.content.*;
import android.content.pm.PackageManager;
import android.os.Build;
import org.json.JSONObject;
import java.util.Locale;

/** Release notices are scoped to a repository, and never install anything. */
final class UpdateNotice {
 private static final String PREF="translation_notice", CHANNEL="translation_updates";
 private static final int JOB=10401, NOTIFICATION=10402;
 private static android.content.SharedPreferences prefs(Context c){return c.getSharedPreferences(PREF,Context.MODE_PRIVATE);}
 static void schedule(Context c){
  JobScheduler s=(JobScheduler)c.getSystemService(Context.JOB_SCHEDULER_SERVICE);
  JobInfo job=new JobInfo.Builder(JOB,new ComponentName(c,UpdateCheckJob.class)).setRequiredNetworkType(JobInfo.NETWORK_TYPE_ANY).setPeriodic(6L*60*60*1000).setPersisted(true).build();
  s.schedule(job);
 }
 private static int compareVersions(String a,String b){
  if(!a.matches("[vV]?[0-9]+(\\.[0-9]+)*")||!b.matches("[vV]?[0-9]+(\\.[0-9]+)*"))return 0;
  String[] x=a.replaceFirst("^[vV]","").split("\\."),y=b.replaceFirst("^[vV]","").split("\\.");
  try{for(int i=0;i<Math.max(x.length,y.length);i++){long p=i<x.length?Long.parseLong(x[i]):0,q=i<y.length?Long.parseLong(y[i]):0;if(p!=q)return Long.compare(p,q);}}catch(NumberFormatException e){return 0;}return 0;
 }
 static synchronized void installed(Context c,String version){c.getSharedPreferences("installed_translation",Context.MODE_PRIVATE).edit().putString("version",version==null?"":version).apply();if(version==null||version.isEmpty()){prefs(c).edit().remove("pending").remove("notified").remove("dismissed").apply();((NotificationManager)c.getSystemService(Context.NOTIFICATION_SERVICE)).cancel(NOTIFICATION);}}
 static String installed(Context c){
  android.content.SharedPreferences cached=c.getSharedPreferences("installed_translation",Context.MODE_PRIVATE);if(cached.contains("version"))return cached.getString("version","");
  java.io.File dir=Store.internal(c,"receipts"),files[]=dir.listFiles((d,n)->n.matches("[0-9a-f]{64}\\.json"));
  if(files==null||files.length!=1)return "";
  try{JSONObject receipt=Store.read(files[0]);String binding=receipt.optString("binding"),v=receipt.optString("version");if(!files[0].getName().equals(binding+".json")||!Store.GAME.equals(receipt.optString("package"))||receipt.optJSONArray("files")==null||receipt.getJSONArray("files").length()==0||!v.matches("[vV]?[0-9]+(\\.[0-9]+)*"))return "";return v;}catch(Exception ignored){return "";}
 }
 static boolean currentChannel(Context c,String repo){try{JSONObject cfg=Store.config(c);Store.validateConfig(cfg);return (cfg.getString("repo")+"/"+cfg.getString("branch")).equals(repo);}catch(Exception e){return false;}}
 static synchronized void channelChanged(Context c){
  android.content.SharedPreferences p=prefs(c);boolean offered=p.getBoolean("permission_offered",false);p.edit().clear().putBoolean("permission_offered",offered).apply();c.getSharedPreferences("launcher_notice",Context.MODE_PRIVATE).edit().clear().apply();NotificationManager nm=(NotificationManager)c.getSystemService(Context.NOTIFICATION_SERVICE);nm.cancel(NOTIFICATION);nm.cancel(10403);
 }
 static synchronized void clearIfCurrent(Context c,String repo){
  if(!currentChannel(c,repo))return;android.content.SharedPreferences p=prefs(c);if(!repo.equals(p.getString("repo","")))return;p.edit().remove("pending").remove("summary").remove("notified").remove("dismissed").apply();((NotificationManager)c.getSystemService(Context.NOTIFICATION_SERVICE)).cancel(NOTIFICATION);
 }
 static synchronized void observe(Context c,String repo,String version,String changes,String installed,boolean background){
  if(repo==null||!currentChannel(c,repo)||version==null||!version.matches("[vV]?[0-9]+(\\.[0-9]+)*"))return;
  android.content.SharedPreferences p=prefs(c);String oldRepo=p.getString("repo","");
  if(!repo.equals(oldRepo)){boolean offered=p.getBoolean("permission_offered",false);p.edit().clear().putBoolean("permission_offered",offered).putString("repo",repo).apply();}
  if(installed!=null&&!installed.isEmpty()&&compareVersions(version,installed)<=0&&version.equals(p.getString("pending",""))){p.edit().remove("pending").remove("notified").remove("dismissed").apply();((NotificationManager)c.getSystemService(Context.NOTIFICATION_SERVICE)).cancel(NOTIFICATION);}
  String pending=p.getString("pending","");
  if(!pending.isEmpty()&&compareVersions(version,pending)<0){clearIfCurrent(c,repo);p.edit().putString("baseline",version).apply();}
  String baseline=p.getString("baseline","");
  if(baseline.isEmpty()){
   p.edit().putString("baseline",version).apply();
   if(installed==null||installed.isEmpty()||compareVersions(version,installed)<=0)return;
  }
  boolean newRelease=compareVersions(version,baseline)>0 && (installed==null||installed.isEmpty()||compareVersions(version,installed)>0);
  boolean newerThanInstalled=installed!=null&&!installed.isEmpty()&&compareVersions(version,installed)>0;
  if(newRelease||newerThanInstalled){
   String summary=changes==null?"":changes.replaceAll("[\\r\\n]+"," ").replaceAll("[#*`]+","").trim();if(summary.length()>900)summary=summary.substring(0,900)+"…";
   if(summary.isEmpty())summary="Mở launcher để xem thông tin bản Việt hoá mới.";else summary="Ghi chú bản phát hành chung: "+summary;
   p.edit().putString("baseline",version).putString("pending",version).putString("summary",summary).apply();
  }
  if(background)notifyIfNeeded(c);
 }
 static synchronized void notifyIfNeeded(Context c){
  android.content.SharedPreferences p=prefs(c);if(!currentChannel(c,p.getString("repo","")))return;String version=p.getString("pending","");
  if(version.isEmpty()||System.currentTimeMillis()<p.getLong("snooze_until",0)||version.equals(p.getString("notified","")))return;
  if(Build.VERSION.SDK_INT>=33&&c.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED)return;
  NotificationManager nm=(NotificationManager)c.getSystemService(Context.NOTIFICATION_SERVICE);
  nm.createNotificationChannel(new NotificationChannel(CHANNEL,"Cập nhật Việt hoá",NotificationManager.IMPORTANCE_DEFAULT));
  if(!nm.areNotificationsEnabled()||nm.getNotificationChannel(CHANNEL).getImportance()==NotificationManager.IMPORTANCE_NONE)return;
  Intent i=new Intent(c,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP|Intent.FLAG_ACTIVITY_SINGLE_TOP);
  PendingIntent open=PendingIntent.getActivity(c,NOTIFICATION,i,PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
  String summary=p.getString("summary","");
  Notification n=new Notification.Builder(c,CHANNEL).setSmallIcon(R.drawable.ic_notification).setContentTitle("Có bản Việt hoá "+version).setContentText(summary).setStyle(new Notification.BigTextStyle().bigText(summary)).setAutoCancel(true).setContentIntent(open).build();
  nm.notify(NOTIFICATION,n);p.edit().putString("notified",version).apply();
 }
 static synchronized String[] pending(Context c){android.content.SharedPreferences p=prefs(c);String v=p.getString("pending","");try{JSONObject cfg=Store.config(c);if(!(cfg.optString("repo")+"/"+cfg.optString("branch")).equals(p.getString("repo","")))return null;}catch(Exception e){return null;}if(v.isEmpty()||v.equals(p.getString("dismissed",""))||System.currentTimeMillis()<p.getLong("snooze_until",0))return null;return new String[]{v,p.getString("summary","")};}
 static synchronized void dismiss(Context c,String v){prefs(c).edit().putString("dismissed",v).apply();}
 static synchronized void snooze(Context c){prefs(c).edit().putLong("snooze_until",System.currentTimeMillis()+24L*60*60*1000).remove("notified").apply();}
}
