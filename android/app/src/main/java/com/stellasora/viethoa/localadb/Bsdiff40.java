package com.stellasora.viethoa.localadb;

import java.io.BufferedOutputStream;
import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.RandomAccessFile;

/**
 * Bounded, streaming BSDIFF40 patcher for reconstructing official Stella Sora Android files
 * from publisher-signed base + delta chains. Mirrors launcher_v2/core/bsdiff40.py.
 */
final class Bsdiff40 {
 private static final int BLOCK = 65536;

 private Bsdiff40() {}

 private static long readOfftin(byte[] buf, int off) {
  long y = (buf[off + 7] & 0x7FL);
  y = (y << 8) | (buf[off + 6] & 0xFFL);
  y = (y << 8) | (buf[off + 5] & 0xFFL);
  y = (y << 8) | (buf[off + 4] & 0xFFL);
  y = (y << 8) | (buf[off + 3] & 0xFFL);
  y = (y << 8) | (buf[off + 2] & 0xFFL);
  y = (y << 8) | (buf[off + 1] & 0xFFL);
  y = (y << 8) | (buf[off] & 0xFFL);
  if ((buf[off + 7] & 0x80) != 0) y = -y;
  return y;
 }

 private static int readFully(InputStream in, byte[] buf, int off, int len) throws IOException {
  int total = 0;
  while (total < len) {
   int r = in.read(buf, off + total, len - total);
   if (r < 0) break;
   total += r;
  }
  return total;
 }

 private static byte[] readFileBytes(File f, int maxBytes) throws IOException {
  long len = f.length();
  if (len < 32 || len > maxBytes) {
   throw new IOException("Invalid BSDIFF40 patch file size: " + len);
  }
  byte[] out = new byte[(int) len];
  try (FileInputStream fis = new FileInputStream(f)) {
   int got = readFully(fis, out, 0, out.length);
   if (got != out.length) throw new IOException("Truncated BSDIFF40 patch file.");
  }
  return out;
 }

 static void apply(File oldFile, File patchFile, File outputFile, long expectedSize) throws IOException {
  byte[] patch = readFileBytes(patchFile, 256 * 1024 * 1024);
  if (patch[0] != 'B' || patch[1] != 'S' || patch[2] != 'D' || patch[3] != 'I'
    || patch[4] != 'F' || patch[5] != 'F' || patch[6] != '4' || patch[7] != '0') {
   throw new IOException("Unsupported delta format (expected BSDIFF40).");
  }
  long ctrlSize = readOfftin(patch, 8);
  long diffSize = readOfftin(patch, 16);
  long newSize = readOfftin(patch, 24);
  if (ctrlSize < 0 || diffSize < 0 || newSize < 0 || newSize != expectedSize
    || 32L + ctrlSize + diffSize > patch.length) {
   throw new IOException("Invalid BSDIFF40 header lengths.");
  }

  long oldSize = oldFile.length();
  byte[] ctrlRaw = new byte[24];
  byte[] deltaBuf = new byte[BLOCK];
  byte[] oldBuf = new byte[BLOCK];
  boolean created = false;

  try (
    InputStream ctrl = new BZip2InputStream(new ByteArrayInputStream(patch, 32, (int) ctrlSize));
    InputStream diff = new BZip2InputStream(new ByteArrayInputStream(patch, 32 + (int) ctrlSize, (int) diffSize));
    InputStream extra = new BZip2InputStream(new ByteArrayInputStream(patch, 32 + (int) ctrlSize + (int) diffSize, patch.length - 32 - (int) ctrlSize - (int) diffSize));
    RandomAccessFile oldRaf = new RandomAccessFile(oldFile, "r");
    FileOutputStream fos = new FileOutputStream(outputFile);
    BufferedOutputStream out = new BufferedOutputStream(fos, BLOCK)
  ) {
   created = true;
   long oldPos = 0;
   long newPos = 0;
   long ops = 0;
   while (newPos < newSize) {
    if (++ops > newSize + 1024L) {
     throw new IOException("Too many BSDIFF40 control records.");
    }
    if (readFully(ctrl, ctrlRaw, 0, 24) != 24) {
     throw new IOException("Truncated BSDIFF40 control stream.");
    }
    long addLen = readOfftin(ctrlRaw, 0);
    long insertLen = readOfftin(ctrlRaw, 8);
    long seekLen = readOfftin(ctrlRaw, 16);
    if (addLen < 0 || insertLen < 0 || newPos + addLen + insertLen > newSize) {
     throw new IOException("BSDIFF40 output bounds exceeded.");
    }

    long rem = addLen;
    while (rem > 0) {
     int chunk = (int) Math.min(rem, BLOCK);
     if (readFully(diff, deltaBuf, 0, chunk) != chunk) {
      throw new IOException("Truncated BSDIFF40 diff stream.");
     }
     long start = Math.max(0L, oldPos);
     long end = Math.min(oldSize, oldPos + chunk);
     if (end > start) {
      int dstOff = (int) (start - oldPos);
      int toRead = (int) (end - start);
      if (dstOff > 0) java.util.Arrays.fill(oldBuf, 0, dstOff, (byte) 0);
      oldRaf.seek(start);
      int got = 0;
      while (got < toRead) {
       int r = oldRaf.read(oldBuf, dstOff + got, toRead - got);
       if (r < 0) break;
       got += r;
      }
      if (dstOff + got < chunk) java.util.Arrays.fill(oldBuf, dstOff + got, chunk, (byte) 0);
     } else {
      java.util.Arrays.fill(oldBuf, 0, chunk, (byte) 0);
     }
     for (int i = 0; i < chunk; i++) {
      oldBuf[i] = (byte) ((oldBuf[i] & 0xFF) + (deltaBuf[i] & 0xFF));
     }
     out.write(oldBuf, 0, chunk);
     rem -= chunk;
     oldPos += chunk;
     newPos += chunk;
    }

    rem = insertLen;
    while (rem > 0) {
     int chunk = (int) Math.min(rem, BLOCK);
     int got = readFully(extra, deltaBuf, 0, chunk);
     if (got != chunk) {
      throw new IOException("Truncated BSDIFF40 extra stream.");
     }
     out.write(deltaBuf, 0, chunk);
     rem -= chunk;
     newPos += chunk;
    }

    oldPos += seekLen;
   }
   if (ctrl.read() != -1 || diff.read() != -1 || extra.read() != -1) {
    throw new IOException("Unexpected trailing BSDIFF40 data.");
   }
   out.flush();
  } catch (IOException | RuntimeException e) {
   if (created) {
    try { outputFile.delete(); } catch (Exception ignored) {}
   }
   throw e;
  }
 }
}
