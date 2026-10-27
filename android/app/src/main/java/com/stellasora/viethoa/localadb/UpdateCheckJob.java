package com.stellasora.viethoa.localadb;

import android.app.job.JobParameters;
import android.app.job.JobService;
import org.json.JSONObject;
import java.util.concurrent.*;

/** Android may defer this periodic network job for power or policy reasons. */
public final class UpdateCheckJob extends JobService {
 private final ExecutorService executor=Executors.newSingleThreadExecutor();
 private long generation;
 @Override public synchronized boolean onStartJob(JobParameters params){
  final long token=++generation;
  executor.execute(()->{
   try{
    ChannelClient channel=new ChannelClient(this);JSONObject release=channel.freshRelease();String identity=channel.repo+"/"+channel.branch;
    try{JSONObject status=channel.launcherAvailability(release);synchronized(this){if(token==generation){if("available".equals(status.optString("status")))LauncherUpdateNotice.observe(this,identity,status.getJSONObject("metadata"),release.optString("body"),true);else if("none".equals(status.optString("status")))LauncherUpdateNotice.clearIfCurrent(this,identity);}}}catch(Exception ignored){}
    if(!channel.hasAndroidManifest(release)){synchronized(this){if(token==generation)UpdateNotice.clearIfCurrent(this,identity);}}else{JSONObject manifest=channel.androidManifest(release);synchronized(this){if(token==generation)UpdateNotice.observe(this,identity,manifest.getString("version"),release.optString("body"),UpdateNotice.installed(this),true);}}
   }catch(Exception ignored){}finally{synchronized(this){if(token==generation)jobFinished(params,false);}}
  });return true;
 }
 @Override public synchronized boolean onStopJob(JobParameters params){generation++;return true;}
 @Override public synchronized void onDestroy(){generation++;executor.shutdownNow();super.onDestroy();}
}
