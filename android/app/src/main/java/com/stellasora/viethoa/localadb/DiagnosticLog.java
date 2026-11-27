package com.stellasora.viethoa.localadb;

import android.content.Context;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.regex.Pattern;

/**
 * Lightweight, PII-redacted rolling diagnostic log (mirrors PC launcher.log tail in error reports).
 * Never stores ADB host/ports, pairing codes, device IDs, or URL query strings.
 */
final class DiagnosticLog {
 private static final int MAX_MEMORY_LINES = 80;
 private static final int MAX_FILE_BYTES = 32768;
 private static final Object LOCK = new Object();
 private static final ArrayDeque<String> RING = new ArrayDeque<>(MAX_MEMORY_LINES + 4);
 private static boolean loadedFromDisk = false;

 private static final Pattern LOCAL_ENDPOINT = Pattern.compile(
   "(?:127\\.0\\.0\\.1|localhost|10\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}|192\\.168\\.\\d{1,3}\\.\\d{1,3}|172\\.(?:1[6-9]|2\\d|3[01])\\.\\d{1,3}\\.\\d{1,3}|\\[::1\\]):\\d{2,5}"
 );
 private static final Pattern URL_AUTH = Pattern.compile("(https?://)[^\\s/@]+@");
 private static final Pattern URL_QUERY = Pattern.compile("(https?://[^\\s?#]+)[?#][^\\s\"'<>)]*");

 private DiagnosticLog() {}

 static String redact(String raw) {
  if (raw == null || raw.isEmpty()) return "";
  String s = raw.replace('\r', ' ').replace('\n', ' ').trim();
  s = URL_AUTH.matcher(s).replaceAll("$1");
  s = URL_QUERY.matcher(s).replaceAll("$1");
  s = LOCAL_ENDPOINT.matcher(s).replaceAll("<local-adb>");
  if (s.length() > 260) s = s.substring(0, 260) + "…";
  return s;
 }

 static void log(Context c, String tag, String msg) {
  String clean = redact(msg);
  if (clean.isEmpty()) return;
  String ts = new SimpleDateFormat("HH:mm:ss", Locale.ROOT).format(new Date());
  String line = ts + " [" + (tag == null || tag.isEmpty() ? "app" : tag) + "] " + clean;
  synchronized (LOCK) {
   ensureLoaded(c);
   if (!RING.isEmpty() && RING.peekLast().equals(line)) return;
   RING.addLast(line);
   while (RING.size() > MAX_MEMORY_LINES) RING.removeFirst();
   if (c != null) persistLocked(c);
  }
 }

 static void log(String tag, String msg) {
  log(null, tag, msg);
 }

 static List<String> tail(Context c, int maxLines) {
  int limit = Math.max(1, Math.min(MAX_MEMORY_LINES, maxLines));
  synchronized (LOCK) {
   ensureLoaded(c);
   List<String> all = new ArrayList<>(RING);
   int start = Math.max(0, all.size() - limit);
   return new ArrayList<>(all.subList(start, all.size()));
  }
 }

 private static void ensureLoaded(Context c) {
  if (loadedFromDisk || c == null) return;
  loadedFromDisk = true;
  try {
   File f = Store.internal(c, "state/launcher_ring.log");
   if (!f.isFile()) return;
   String raw = Store.text(f);
   for (String line : raw.split("\\r?\\n")) {
    String trimmed = line.trim();
    if (!trimmed.isEmpty()) {
     RING.addLast(trimmed);
     while (RING.size() > MAX_MEMORY_LINES) RING.removeFirst();
    }
   }
  } catch (Exception ignored) {}
 }

 private static void persistLocked(Context c) {
  try {
   File f = Store.internal(c, "state/launcher_ring.log");
   File p = f.getParentFile();
   if (p != null && !p.isDirectory()) p.mkdirs();
   StringBuilder sb = new StringBuilder();
   for (String line : RING) {
    sb.append(line).append('\n');
   }
   byte[] bytes = sb.toString().getBytes(StandardCharsets.UTF_8);
   if (bytes.length > MAX_FILE_BYTES) {
    int cut = bytes.length - MAX_FILE_BYTES;
    while (cut < bytes.length && bytes[cut] != '\n') cut++;
    if (cut < bytes.length) cut++;
    bytes = Arrays.copyOfRange(bytes, cut, bytes.length);
   }
   try (FileOutputStream fos = new FileOutputStream(f, false)) {
    fos.write(bytes);
   }
  } catch (Exception ignored) {}
 }
}
