package com.stellasora.viethoa.localadb;
import android.app.*;
import android.content.*;
import android.os.*;
import org.json.*;
import org.conscrypt.Conscrypt;
import io.github.muntashirakon.adb.*;
import java.io.*;
import java.security.*;
import java.security.cert.Certificate;
import java.util.Locale;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;

/** App-private broker; its main handler enforces an absolute process deadline and preserves exact error classifications. */
public final class AdbBrokerService extends Service {
 private final ExecutorService worker = Executors.newSingleThreadExecutor();
 private final Handler main = new Handler(Looper.getMainLooper());
 private final AtomicBoolean busy = new AtomicBoolean();
 private long active;
 private Session session;
 private final Messenger messenger = new Messenger(new Handler(Looper.getMainLooper()) {
  @Override public void handleMessage(Message m) { accept(m); }
 });

 private static final class Session extends AbsAdbConnectionManager {
  final KeyMaterial keys;
  Session(KeyMaterial k) {
   keys = k;
   setApi(Build.VERSION.SDK_INT);
   setTimeout(18, TimeUnit.SECONDS);
   setThrowOnUnauthorised(true);
  }
  @Override protected PrivateKey getPrivateKey() { return keys.privateKey; }
  @Override protected Certificate getCertificate() { return keys.certificate; }
  @Override protected String getDeviceName() { return "StellaSora_LocalADB"; }
 }

 @Override public IBinder onBind(Intent i) { return messenger.getBinder(); }

 private void accept(Message message) {
  if (message.sendingUid != android.os.Process.myUid()) return;
  Bundle b = message.getData();
  long id = b.getLong("request_id");
  String action = b.getString("action", "");
  Messenger reply = message.replyTo;
  if (!busy.compareAndSet(false, true)) {
   respond(reply, id, false, "ADB đang có thao tác.", "E-BUSY", "Busy", "");
   return;
  }
  active = id;
  long duration = Math.max(1000, Math.min(125000, b.getLong("timeout_ms", 25000)));
  Runnable deadline = () -> {
   if (busy.get() && active == id) {
    respond(reply, id, false, "ADB quá thời hạn. Hãy kết nối lại.", "E-ADB-TIMEOUT", "DeadlineExceeded", "broker deadline " + duration + "ms");
    killOwnBroker();
   }
  };
  main.postDelayed(deadline, duration);
  worker.execute(() -> {
   boolean ok = false;
   String value;
   String errCode = "";
   String errClass = "";
   String errDetail = "";
   try {
    if (session == null) {
     try {
      if (Security.getProvider("Conscrypt") == null) {
       Security.insertProviderAt(Conscrypt.newProvider(), 1);
      }
     } catch (Throwable ignored) {}
     session = new Session(KeyMaterial.load(this));
    }
    JSONObject args = new JSONObject(b.getString("args", "{}"));
    switch (action) {
     case "pair": {
      String host = AdbClient.ownHost(args.getString("host"));
      int port = AdbClient.port(args.getInt("port"));
      String code = args.getString("code");
      if (!code.matches("[0-9]{6}")) throw new StellaException("E-ADB-INPUT", "Mã cần 6 số.", null);
      if (!session.pair(host, port, code)) throw new StellaException("E-ADB-PAIR", "Ghép nối chưa thành công.", null);
      KeyMaterial.markPaired(this);
      value = "Đã ghép nối; chưa kết nối.";
      break;
     }
     case "connect": {
      String host = AdbClient.ownHost(args.getString("host"));
      int port = AdbClient.port(args.getInt("port"));
      if (session.isConnected()) {
       try { session.disconnect(); } catch (Throwable ignored) {}
      }
      if (!session.connect(host, port)) {
       throw new StellaException("E-ADB-CONN-REFUSED", "Chưa kết nối được ADB. Gỡ lỗi không dây có thể đang tắt hoặc cổng kết nối đã đổi.", null);
      }
      KeyMaterial.markPaired(this);
      value = "transport_connected";
      break;
     }
     case "exec": {
      if (!session.isConnected()) throw new StellaException("E-ADB-NOT-CONNECTED", "Chưa kết nối ADB.", null);
      String command = args.getString("command");
      if (command.length() > 64000 || command.indexOf(0) >= 0) throw new IOException("Lệnh nội bộ vượt giới hạn.");
      value = readCommand(command, duration - 800, args.getString("marker"));
      break;
     }
     case "disconnect":
      try { session.disconnect(); } catch (Throwable ignored) {}
      value = "Đã ngắt ADB.";
      break;
     default:
      throw new IOException("Thao tác ADB không hợp lệ.");
    }
    ok = true;
   } catch (Throwable e) {
    errClass = e.getClass().getSimpleName();
    errDetail = ErrorReport.redact(Store.cleanError(e));
    errCode = ErrorCatalog.classify(e, action);
    if ("pair".equals(action)) {
     if ("E-ADB-NO-WIFI".equals(errCode)) {
      value = "Điện thoại chưa kết nối Wi-Fi (Gỡ lỗi không dây cần Wi-Fi).";
     } else if ("E-ADB-CONN-REFUSED".equals(errCode)) {
      value = "Không kết nối được tới cổng ghép đôi (cửa sổ mã 6 số có thể đã đóng hoặc sai số cổng ghép đôi).";
     } else if ("E-ADB-TIMEOUT".equals(errCode)) {
      value = "Ghép đôi quá thời hạn chờ phản hồi từ điện thoại.";
     } else if ("E-ADB-INPUT".equals(errCode)) {
      value = Store.cleanError(e);
     } else {
      errCode = "E-ADB-PAIR";
      value = "Ghép nối thất bại. Kiểm tra mã 6 số mới và cổng ghép đôi trong Gỡ lỗi không dây.";
     }
    } else if ("connect".equals(action)) {
     String low = errDetail.toLowerCase(Locale.ROOT);
     if ("E-ADB-AUTH".equals(errCode) || low.contains("unauthor") || low.contains("pairing")) {
      errCode = "E-ADB-AUTH";
      value = "Điện thoại chưa chấp nhận khoá Local ADB. Hãy ghép đôi lại một lần bằng mã 6 số.";
     } else if ("E-ADB-CONN-REFUSED".equals(errCode)) {
      value = "Gỡ lỗi không dây đang tắt hoặc cổng kết nối đã đổi.";
     } else if ("E-ADB-NO-WIFI".equals(errCode)) {
      value = "Điện thoại chưa kết nối Wi-Fi nên chưa dùng được Gỡ lỗi không dây.";
     } else {
      value = errDetail.isEmpty() ? "Chưa kết nối được ADB." : errDetail;
     }
    } else {
     value = errDetail.isEmpty() ? errClass : errDetail;
    }
   }
   boolean result = ok;
   String output = value;
   String fCode = errCode, fClass = errClass, fDetail = errDetail;
   main.post(() -> {
    if (active != id) return;
    main.removeCallbacks(deadline);
    busy.set(false);
    respond(reply, id, result, output, fCode, fClass, fDetail);
   });
  });
 }

 private String readCommand(String command, long timeout, String marker) throws Exception {
  if (!marker.matches("STELLA_EXIT_[0-9a-f]{32}")) throw new IOException("Marker nội bộ không hợp lệ.");
  java.util.regex.Pattern complete = java.util.regex.Pattern.compile("(?:\\r?\\n)" + marker + "[0-9]+\\r?\\n");
  long end = SystemClock.elapsedRealtime() + Math.max(500, timeout);
  try (AdbStream stream = session.openStream("shell:" + command)) {
   ByteArrayOutputStream out = new ByteArrayOutputStream();
   byte[] buffer = new byte[8192];
   while (true) {
    int n = stream.read(buffer, 0, buffer.length);
    if (n < 0) throw new StellaException("E-ADB-DISCONNECTED", "ADB đóng trước phản hồi kết thúc.", null);
    if (n > 0) out.write(buffer, 0, n);
    if (out.size() > 131072) throw new IOException("Đầu ra ADB vượt giới hạn 128 KiB của kênh nội bộ.");
    String data = out.toString("UTF-8");
    if (complete.matcher(data).find()) return data;
    if (SystemClock.elapsedRealtime() > end) throw new StellaException("E-ADB-TIMEOUT", "Lệnh ADB quá thời hạn.", null);
   }
  }
 }

 private static void respond(Messenger to, long id, boolean ok, String value, String errCode, String errClass, String errDetail) {
  if (to == null) return;
  try {
   Message m = Message.obtain();
   Bundle b = new Bundle();
   b.putLong("request_id", id);
   b.putBoolean("ok", ok);
   b.putString("value", value);
   if (errCode != null && !errCode.isEmpty()) b.putString("error_code", errCode);
   if (errClass != null && !errClass.isEmpty()) b.putString("error_class", errClass);
   if (errDetail != null && !errDetail.isEmpty()) b.putString("error_detail", errDetail);
   m.setData(b);
   to.send(m);
  } catch (RemoteException ignored) {}
 }

 private void killOwnBroker() {
  try {
   if (Application.getProcessName().equals(getPackageName() + ":adb")) {
    android.os.Process.killProcess(android.os.Process.myPid());
   }
  } catch (Throwable ignored) {}
 }

 @Override public void onDestroy() {
  worker.shutdownNow();
  killOwnBroker();
  super.onDestroy();
 }
}
