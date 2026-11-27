package com.stellasora.viethoa.localadb;

import android.app.job.JobParameters;
import android.app.job.JobService;
import org.json.JSONObject;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Periodic 30-minute lightweight check (432-byte serverlist.html) for official Stella Sora updates. */
public final class OfficialUpdateCheckJob extends JobService {
 private final ExecutorService executor = Executors.newSingleThreadExecutor();
 private long generation;

 @Override public synchronized boolean onStartJob(JobParameters params) {
  final long token = ++generation;
  executor.execute(() -> {
   try {
    JSONObject state = OfficialAndroidClient.checkAndSave(this, 10000);
    synchronized (this) {
     if (token == generation) {
      OfficialUpdateNotice.notifyIfNeeded(this, state);
     }
    }
   } catch (Exception ignored) {
   } finally {
    synchronized (this) {
     if (token == generation) jobFinished(params, false);
    }
   }
  });
  return true;
 }

 @Override public synchronized boolean onStopJob(JobParameters params) {
  generation++;
  return true;
 }

 @Override public synchronized void onDestroy() {
  generation++;
  executor.shutdownNow();
  super.onDestroy();
 }
}
