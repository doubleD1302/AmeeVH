package com.stellasora.viethoa.localadb;
import android.content.*;
import android.net.nsd.*;
import android.net.wifi.WifiManager;
import android.os.*;
import java.util.ArrayDeque;
import java.util.Objects;

/** Same-device mDNS discovery; queues candidates so foreign Wi-Fi devices never drop local resolution. */
final class PairingDiscovery implements AutoCloseable {
 interface Callback { void found(String host, int port); void failed(String message); }
 private final NsdManager manager;
 private final Handler main = new Handler(Looper.getMainLooper());
 private final ArrayDeque<NsdServiceInfo> queue = new ArrayDeque<>();
 private final Callback callback;
 private final String type;
 private NsdManager.DiscoveryListener listener;
 private WifiManager.MulticastLock lock;
 private volatile boolean closed;
 private boolean resolving;
 private Runnable timeout;

 PairingDiscovery(Context context, String serviceType, Callback cb) {
  manager = (NsdManager) context.getSystemService(Context.NSD_SERVICE);
  type = serviceType;
  callback = cb;
  try {
   WifiManager wifi = (WifiManager) context.getApplicationContext().getSystemService(Context.WIFI_SERVICE);
   lock = wifi.createMulticastLock("StellaSora-mDNS");
   lock.setReferenceCounted(false);
   lock.acquire();
  } catch (Exception ignored) {}
 }

 void start() {
  listener = new NsdManager.DiscoveryListener() {
   @Override public void onDiscoveryStarted(String t) {}
   @Override public void onDiscoveryStopped(String t) {}
   @Override public void onStopDiscoveryFailed(String t, int e) {}
   @Override public void onServiceLost(NsdServiceInfo s) {}
   @Override public void onStartDiscoveryFailed(String t, int e) {
    main.post(() -> {
     if (!closed) callback.failed("Không dò được cổng mDNS. Có thể nhập cổng thủ công.");
     close();
    });
   }
   @Override public void onServiceFound(NsdServiceInfo service) {
    if (closed || service == null) return;
    main.post(() -> {
     if (closed) return;
     for (NsdServiceInfo pending : queue) {
      if (Objects.equals(pending.getServiceName(), service.getServiceName())) return;
     }
     queue.addLast(service);
     resolveNext();
    });
   }
  };
  try {
   manager.discoverServices(type, NsdManager.PROTOCOL_DNS_SD, listener);
   timeout = () -> {
    if (!closed) callback.failed("Chưa tìm thấy cổng trong 60 giây. Hãy mở đúng màn hình Gỡ lỗi không dây hoặc nhập cổng thủ công.");
    close();
   };
   main.postDelayed(timeout, 60000);
  } catch (Exception e) {
   callback.failed("Không dùng được mDNS. Hãy nhập cổng thủ công.");
   close();
  }
 }

 private void resolveNext() {
  if (closed || resolving) return;
  NsdServiceInfo next = queue.pollFirst();
  if (next == null) return;
  resolving = true;
  try {
   manager.resolveService(next, new NsdManager.ResolveListener() {
    @Override public void onResolveFailed(NsdServiceInfo s, int e) {
     main.post(() -> {
      resolving = false;
      resolveNext();
     });
    }
    @Override public void onServiceResolved(NsdServiceInfo s) {
     main.post(() -> {
      resolving = false;
      if (closed) return;
      if (s != null && s.getHost() != null) {
       try {
        String host = AdbClient.ownHost(s.getHost().getHostAddress());
        int port = AdbClient.port(s.getPort());
        callback.found(host, port);
        if (closed) return;
       } catch (Exception ignored) {}
      }
      resolveNext();
     });
    }
   });
  } catch (Exception e) {
   resolving = false;
   resolveNext();
  }
 }

 @Override public void close() {
  if (closed) return;
  closed = true;
  main.post(queue::clear);
  if (timeout != null) main.removeCallbacks(timeout);
  if (listener != null) {
   try { manager.stopServiceDiscovery(listener); } catch (Exception ignored) {}
  }
  if (lock != null && lock.isHeld()) lock.release();
 }
}
