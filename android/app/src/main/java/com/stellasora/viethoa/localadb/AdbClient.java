package com.stellasora.viethoa.localadb;
import android.app.*;
import android.content.*;
import android.os.*;
import org.json.*;
import java.io.*;
import java.net.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicLong;

/** Private typed IPC; neither device commands nor paths are accepted from JS. */
final class AdbClient {
 private final Context context;
 private volatile Messenger broker;
 private volatile ServiceConnection connection;
 volatile boolean verified;
 volatile String lastLossReason = "";
 volatile Runnable onLoss;
 private final Handler main = new Handler(Looper.getMainLooper());
 private final AtomicLong sequence = new AtomicLong(), epoch = new AtomicLong();
 private final ConcurrentHashMap<Long, CompletableFuture<Bundle>> pending = new ConcurrentHashMap<>();
 private final Messenger replies = new Messenger(new Handler(Looper.getMainLooper()) {
  @Override public void handleMessage(Message m) {
   Bundle b = m.getData();
   CompletableFuture<Bundle> f = pending.remove(b.getLong("request_id"));
   if (f != null) f.complete(b);
  }
 });

 AdbClient(Context c) { context = c.getApplicationContext(); }

 static int port(int p) throws IOException {
  if (p < 1024 || p > 65535) throw new IOException("Cổng cần nằm trong 1024–65535.");
  return p;
 }

 static String ownHost(String input) throws Exception {
  String h = input == null ? "" : input.trim();
  if (h.isEmpty() || h.equals("localhost")) h = "127.0.0.1";
  if (h.startsWith("[") && h.endsWith("]")) h = h.substring(1, h.length() - 1);
  if (!(h.matches("[0-9.]+") || (h.contains(":") && h.matches("[0-9a-fA-F:.]+(%[A-Za-z0-9_.-]+)?")))) {
   throw new IOException("Chỉ dùng địa chỉ của chính điện thoại.");
  }
  InetAddress a = InetAddress.getByName(h);
  if (a.isAnyLocalAddress() || (!a.isLoopbackAddress() && NetworkInterface.getByInetAddress(a) == null)) {
   throw new IOException("Không kết nối ADB tới thiết bị khác.");
  }
  return a.getHostAddress();
 }

 static JSONArray ownAddresses() {
  JSONArray a = new JSONArray();
  LinkedHashSet<String> seen = new LinkedHashSet<>();
  seen.add("127.0.0.1");
  try {
   Enumeration<NetworkInterface> all = NetworkInterface.getNetworkInterfaces();
   if (all != null) {
    while (all.hasMoreElements()) {
     NetworkInterface n = all.nextElement();
     if (!n.isUp()) continue;
     Enumeration<InetAddress> addresses = n.getInetAddresses();
     while (addresses.hasMoreElements()) {
      InetAddress ip = addresses.nextElement();
      if (!ip.isLoopbackAddress() && ip instanceof Inet4Address) {
       seen.add(ip.getHostAddress());
      }
     }
    }
   }
  } catch (Exception ignored) {}
  for (String s : seen) a.put(s);
  return a;
 }

 private void ensureBound() throws Exception {
  if (broker != null) return;
  long token = epoch.incrementAndGet();
  CountDownLatch latch = new CountDownLatch(1);
  main.post(() -> {
   if (epoch.get() != token) { latch.countDown(); return; }
   ServiceConnection old = connection;
   if (old != null) try { context.unbindService(old); } catch (Exception ignored) {}
   ServiceConnection next = new ServiceConnection() {
    @Override public void onServiceConnected(ComponentName n, IBinder binder) {
     if (epoch.get() != token) return;
     broker = new Messenger(binder);
     try {
      binder.linkToDeath(() -> { if (epoch.get() == token) lost("Tiến trình ADB đã dừng."); }, 0);
     } catch (RemoteException e) {
      lost("ADB chưa sẵn sàng.");
     }
     latch.countDown();
    }
    @Override public void onServiceDisconnected(ComponentName n) {
     if (epoch.get() == token) lost("Kết nối ADB đã đóng.");
    }
    @Override public void onBindingDied(ComponentName n) {
     if (epoch.get() == token) lost("Tiến trình ADB đã đóng.");
    }
   };
   connection = next;
   boolean bound = false;
   try {
    bound = context.bindService(new Intent(context, AdbBrokerService.class), next, Context.BIND_AUTO_CREATE | Context.BIND_IMPORTANT);
   } catch (SecurityException se) {
    bound = false;
   }
   if (!bound) {
    connection = null;
    latch.countDown();
   }
  });
  if (!latch.await(8, TimeUnit.SECONDS) || broker == null || epoch.get() != token) {
   throw new StellaException("E-ADB-START", "Chưa khởi động được Local ADB.", null, "adbAction", "bind");
  }
 }

 private String request(String action, JSONObject args, long timeout) throws Exception {
  ensureBound();
  long id = sequence.incrementAndGet();
  CompletableFuture<Bundle> future = new CompletableFuture<>();
  pending.put(id, future);
  Message m = Message.obtain();
  Bundle b = new Bundle();
  b.putString("action", action);
  b.putString("args", args.toString());
  b.putLong("request_id", id);
  b.putLong("timeout_ms", timeout);
  m.setData(b);
  m.replyTo = replies;
  try {
   broker.send(m);
   Bundle result = future.get(timeout + 2500, TimeUnit.MILLISECONDS);
   if (!result.getBoolean("ok")) {
    String val = result.getString("value", "ADB thất bại.");
    String errCode = result.getString("error_code", "");
    String errClass = result.getString("error_class", "");
    String errDetail = result.getString("error_detail", "");
    boolean brokerConnected = result.getBoolean("connected", false);
    boolean keepSession = "exec".equals(action)
      && brokerConnected
      && !"E-ADB-DISCONNECTED".equals(errCode)
      && !"E-ADB-NOT-CONNECTED".equals(errCode)
      && !"E-ADB-TIMEOUT".equals(errCode)
      && !"E-ADB-AUTH".equals(errCode)
      && !"E-ADB-CONN-REFUSED".equals(errCode)
      && !"E-ADB-NO-WIFI".equals(errCode);
    if (!keepSession) {
     transportFailure(errCode.isEmpty() ? val : (errCode + ": " + val));
    }
    if (!errCode.isEmpty()) {
     throw new StellaException(errCode, val, null, "adbAction", action, "brokerErrorClass", errClass, "brokerErrorDetail", errDetail);
    }
    throw new IOException(val);
   }
   return result.getString("value", "");
  } catch (RemoteException | ExecutionException e) {
   transportFailure("Kênh ADB đã đóng hoặc không trả phản hồi hợp lệ.");
   throw new StellaException("E-ADB-DISCONNECTED", "Kênh ADB đã đóng hoặc không trả phản hồi hợp lệ.", e, "adbAction", action);
  } catch (TimeoutException e) {
   cancelBroker();
   throw new StellaException("E-ADB-TIMEOUT", "ADB quá thời hạn, kết nối đã đóng.", e, "adbAction", action);
  } finally {
   pending.remove(id);
  }
 }

 void pair(String host, int p, String code) throws Exception {
  verified = false;
  request("pair", Store.obj("host", ownHost(host), "port", port(p), "code", code), 25000);
  KeyMaterial.markPaired(context);
 }

 void connect(String host, int p) throws Exception { connect(host, p, 25000); }

 void connect(String host, int p, long connectTimeoutMs) throws Exception {
  verified = false;
  request("connect", Store.obj("host", ownHost(host), "port", port(p)), connectTimeoutMs);
  String id = execUnchecked("id", 12000);
  if (!id.matches("(?s).*uid=(2000|0)\\b.*")) {
   cancelBroker();
   throw new StellaException("E-ADB-AUTH", "ADB chưa xác minh được danh tính shell.", null, "adbAction", "id");
  }
  lastLossReason = "";
  verified = true;
  KeyMaterial.markPaired(context);
 }

 String exec(String cmd, long timeout) throws Exception {
  if (!verified) throw new StellaException("E-ADB-NOT-CONNECTED", "Hãy kết nối và xác minh Local ADB trước.", null);
  return execUnchecked(cmd, timeout);
 }

 private String execUnchecked(String cmd, long timeout) throws Exception {
  String marker = "STELLA_EXIT_" + UUID.randomUUID().toString().replace("-", "");
  long seconds = Math.max(2, Math.min(110, (timeout - 1000) / 1000));
  String qCmd = Store.q(cmd);
  String wrapped = "if command -v timeout >/dev/null 2>&1; then timeout " + seconds + " sh -c " + qCmd + "; else sh -c " + qCmd + "; fi; status=$?; printf '\\n" + marker + "%s\\n' \"$status\"";
  String output = request("exec", Store.obj("command", wrapped, "marker", marker), Math.max(4000, timeout));
  int index = output.lastIndexOf(marker);
  if (index < 0) {
   transportFailure("ADB không trả mã kết thúc.");
   throw new StellaException("E-ADB-DISCONNECTED", "ADB không trả mã kết thúc.", null);
  }
  String codeStr = output.substring(index + marker.length()).trim();
  if (!codeStr.equals("0")) {
   int exitCode = -1;
   try { exitCode = Integer.parseInt(codeStr); } catch (NumberFormatException ignored) {}
   String snippet = ErrorReport.redact(output.substring(0, Math.min(index, 500)).trim());
   String low = snippet.toLowerCase(Locale.ROOT);
   String errCode = "E-ADB";
   if (low.contains("permission denied") || low.contains("operation not permitted") || low.contains("securityexception") || low.contains("eacces")) {
    errCode = "E-ADB-PERM";
   } else if (low.contains("no space left") || low.contains("enospc")) {
    errCode = "E-STORAGE";
   } else if (exitCode == 124 || exitCode == 137) {
    errCode = "E-ADB-TIMEOUT";
   }
   throw new StellaException(errCode, "ADB dừng (" + codeStr + "): " + snippet, null, "exitCode", exitCode, "stderr", snippet);
  }
  return output.substring(0, index).trim();
 }

 void disconnect() { cancelBroker(); }

 void cancelBroker() {
  long token = epoch.incrementAndGet();
  ServiceConnection old = connection;
  connection = null;
  verified = false;
  lost("ADB đã được dừng.");
  CountDownLatch done = new CountDownLatch(1);
  Runnable cleanup = () -> {
   try {
    if (old != null) try { context.unbindService(old); } catch (Exception ignored) {}
    if (epoch.get() == token) {
     context.stopService(new Intent(context, AdbBrokerService.class));
     ActivityManager am = (ActivityManager) context.getSystemService(Context.ACTIVITY_SERVICE);
     List<ActivityManager.RunningAppProcessInfo> processes = am == null ? null : am.getRunningAppProcesses();
     if (processes != null) {
      for (ActivityManager.RunningAppProcessInfo p : processes) {
       if (p.uid == android.os.Process.myUid() && p.processName.equals(context.getPackageName() + ":adb")) {
        android.os.Process.killProcess(p.pid);
       }
      }
     }
    }
   } finally {
    done.countDown();
   }
  };
  if (Looper.myLooper() == Looper.getMainLooper()) cleanup.run();
  else {
   main.post(cleanup);
   try { done.await(3, TimeUnit.SECONDS); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
  }
 }

 private void transportFailure(String reason) {
  lastLossReason = reason == null ? "" : reason;
  verified = false;
  Runnable callback = onLoss;
  if (callback != null) main.post(callback);
 }

 private void lost(String reason) {
  lastLossReason = reason == null ? "" : reason;
  verified = false;
  broker = null;
  for (CompletableFuture<Bundle> f : pending.values()) f.completeExceptionally(new IOException(reason));
  pending.clear();
  Runnable callback = onLoss;
  if (callback != null) main.post(callback);
 }
}
