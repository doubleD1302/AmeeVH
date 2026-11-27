package com.stellasora.viethoa.localadb;
import android.content.*;
import android.net.nsd.*;
import android.net.wifi.WifiManager;
import android.os.*;
import java.net.Inet4Address;
import java.net.InetAddress;
import java.util.*;

/**
 * Same-device mDNS discovery supporting Android 11–16 (API 30–36):
 * - Uses NsdManager.registerServiceInfoCallback on Android 14+ (API 34+) to resolve multi-address IPv4/IPv6 reliably.
 * - Uses queued resolveService with FAILURE_ALREADY_ACTIVE retry on Android 11–13 (API 30–33).
 */
final class PairingDiscovery implements AutoCloseable {
 interface Callback { void found(String host, int port); void failed(String message); }

 private final NsdManager manager;
 private final Handler main = new Handler(Looper.getMainLooper());
 private final ArrayDeque<NsdServiceInfo> queue = new ArrayDeque<>();
 private final List<Object> activeCallbacks = new ArrayList<>();
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
   if (wifi != null) {
    lock = wifi.createMulticastLock("StellaSora-mDNS");
    lock.setReferenceCounted(false);
    lock.acquire();
   }
  } catch (Exception ignored) {}
 }

 void start() {
  if (manager == null) {
   main.post(() -> {
    if (!closed) callback.failed("Thiết bị không hỗ trợ dò cổng mDNS. Hãy dùng mục Kết nối thủ công.");
    close();
   });
   return;
  }
  listener = new NsdManager.DiscoveryListener() {
   @Override public void onDiscoveryStarted(String t) {}
   @Override public void onDiscoveryStopped(String t) {}
   @Override public void onStopDiscoveryFailed(String t, int e) {}
   @Override public void onServiceLost(NsdServiceInfo s) {}
   @Override public void onStartDiscoveryFailed(String t, int e) {
    main.post(() -> {
     if (!closed) callback.failed("Không dò được cổng mDNS (mã " + e + "). Có thể nhập cổng thủ công.");
     close();
    });
   }
   @Override public void onServiceFound(NsdServiceInfo service) {
    if (closed || service == null) return;
    main.post(() -> {
     if (closed) return;
     if (Build.VERSION.SDK_INT >= 34) {
      resolveModern(service);
     } else {
      for (NsdServiceInfo pending : queue) {
       if (Objects.equals(pending.getServiceName(), service.getServiceName())) return;
      }
      queue.addLast(service);
      resolveNext();
     }
    });
   }
  };
  try {
   manager.discoverServices(type, NsdManager.PROTOCOL_DNS_SD, listener);
   timeout = () -> {
    if (!closed) callback.failed("Chưa tìm thấy cổng trong 60 giây. Hãy kiểm tra Wi-Fi, mở đúng màn hình Gỡ lỗi không dây hoặc nhập cổng thủ công.");
    close();
   };
   main.postDelayed(timeout, 60000);
  } catch (Exception e) {
   callback.failed("Không dùng được mDNS trên máy này. Hãy nhập cổng thủ công.");
   close();
  }
 }

 @SuppressWarnings("NewApi")
 private void resolveModern(NsdServiceInfo service) {
  if (closed || manager == null) return;
  try {
   NsdManager.ServiceInfoCallback cb = new NsdManager.ServiceInfoCallback() {
    @Override public void onServiceInfoCallbackRegistrationFailed(int errorCode) {}
    @Override public void onServiceUpdated(NsdServiceInfo info) {
     main.post(() -> {
      if (closed || info == null) return;
      String matched = pickOwnHost(info);
      if (matched != null) {
       try {
        int port = AdbClient.port(info.getPort());
        callback.found(matched, port);
       } catch (Exception ignored) {}
      }
     });
    }
    @Override public void onServiceLost() {}
    @Override public void onServiceInfoCallbackUnregistered() {}
   };
   activeCallbacks.add(cb);
   manager.registerServiceInfoCallback(service, main::post, cb);
  } catch (Throwable ignored) {
   // Fall back to legacy resolveService if OEM Android 14 ROM breaks callback API
   queue.addLast(service);
   resolveNext();
  }
 }

 @SuppressWarnings("NewApi")
 private static String pickOwnHost(NsdServiceInfo info) {
  List<InetAddress> addrs = new ArrayList<>();
  try {
   if (Build.VERSION.SDK_INT >= 34) {
    List<InetAddress> list = info.getHostAddresses();
    if (list != null) addrs.addAll(list);
   }
  } catch (Throwable ignored) {}
  if (addrs.isEmpty() && info.getHost() != null) addrs.add(info.getHost());
  // Prefer IPv4 own address first, then loopback/IPv6 own address
  for (InetAddress a : addrs) {
   if (a instanceof Inet4Address) {
    try { return AdbClient.ownHost(a.getHostAddress()); } catch (Exception ignored) {}
   }
  }
  for (InetAddress a : addrs) {
   try { return AdbClient.ownHost(a.getHostAddress()); } catch (Exception ignored) {}
  }
  return null;
 }

 @SuppressWarnings("deprecation")
 private void resolveNext() {
  if (closed || resolving || manager == null) return;
  NsdServiceInfo next = queue.pollFirst();
  if (next == null) return;
  resolving = true;
  resolveLegacy(next, false);
 }

 @SuppressWarnings("deprecation")
 private void resolveLegacy(NsdServiceInfo target, boolean retried) {
  if (closed || manager == null) { resolving = false; return; }
  try {
   manager.resolveService(target, new NsdManager.ResolveListener() {
    @Override public void onResolveFailed(NsdServiceInfo s, int e) {
     main.post(() -> {
      if (!closed && !retried && e == NsdManager.FAILURE_ALREADY_ACTIVE) {
       main.postDelayed(() -> resolveLegacy(target, true), 350);
       return;
      }
      resolving = false;
      resolveNext();
     });
    }
    @Override public void onServiceResolved(NsdServiceInfo s) {
     main.post(() -> {
      resolving = false;
      if (closed) return;
      if (s != null) {
       String host = pickOwnHost(s);
       if (host != null) {
        try {
         int port = AdbClient.port(s.getPort());
         callback.found(host, port);
         if (closed) return;
        } catch (Exception ignored) {}
       }
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

 @SuppressWarnings("NewApi")
 @Override public void close() {
  if (closed) return;
  closed = true;
  main.post(() -> {
   queue.clear();
   if (Build.VERSION.SDK_INT >= 34 && manager != null) {
    for (Object obj : activeCallbacks) {
     try { manager.unregisterServiceInfoCallback((NsdManager.ServiceInfoCallback) obj); } catch (Throwable ignored) {}
    }
   }
   activeCallbacks.clear();
  });
  if (timeout != null) main.removeCallbacks(timeout);
  if (listener != null && manager != null) {
   try { manager.stopServiceDiscovery(listener); } catch (Exception ignored) {}
  }
  if (lock != null && lock.isHeld()) {
   try { lock.release(); } catch (Exception ignored) {}
  }
 }
}
