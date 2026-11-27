package com.stellasora.viethoa.localadb;

import java.io.IOException;
import java.io.InputStream;
import java.util.Arrays;

/**
 * Self-contained pure-Java BZip2 stream decompressor (BZh1..BZh9) with full CRC-32 verification.
 * Used exclusively to reconstruct publisher-signed BSDIFF40 deltas during Android official restore.
 */
final class BZip2InputStream extends InputStream {
 private static final int BASE_BLOCK_SIZE = 100000;
 private static final int MAX_ALPHA_SIZE = 258;
 private static final int MAX_CODE_LEN = 23;
 private static final int RUNA = 0;
 private static final int RUNB = 1;
 private static final int N_GROUPS = 6;
 private static final int G_SIZE = 50;
 private static final int MAX_SELECTORS = 2 + (900000 / G_SIZE);

 private static final int[] CRC32_TABLE = new int[256];
 static {
  for (int i = 0; i < 256; i++) {
   int r = i << 24;
   for (int j = 0; j < 8; j++) {
    if ((r & 0x80000000) != 0) r = (r << 1) ^ 0x04C11DB7;
    else r <<= 1;
   }
   CRC32_TABLE[i] = r;
  }
 }

 private InputStream in;
 private int bsBuff;
 private int bsLive;

 private int blockSize100k;
 private int combinedCrc;
 private int storedBlockCrc;
 private int computedBlockCrc;
 private boolean eof;

 // Block buffers (reused across blocks)
 private byte[] ll8;
 private int[] tt;
 private final int[] unzftab = new int[256];
 private final int[] cftab = new int[257];
 private final byte[] seqToUnseq = new byte[256];
 private final byte[] selector = new byte[MAX_SELECTORS];
 private final byte[] selectorMtf = new byte[MAX_SELECTORS];
 private final int[][] limit = new int[N_GROUPS][MAX_CODE_LEN];
 private final int[][] base = new int[N_GROUPS][MAX_CODE_LEN];
 private final int[][] perm = new int[N_GROUPS][MAX_ALPHA_SIZE];
 private final int[] minLens = new int[N_GROUPS];

 // Current block BWT + RLE1 emission state
 private int last = -1;
 private int origPtr;
 private int tPos;
 private int bwtReadCount;
 private int rlePrev = -1;
 private int rleRunCount;
 private int rlePendingRepeats;
 private boolean hasBlock;

 BZip2InputStream(InputStream source) throws IOException {
  if (source == null) throw new IOException("BZip2 input stream is null.");
  this.in = source;
  int b0 = source.read();
  int b1 = source.read();
  int b2 = source.read();
  int b3 = source.read();
  if (b0 != 'B' || b1 != 'Z' || b2 != 'h' || b3 < '1' || b3 > '9') {
   throw new IOException("Invalid BZip2 header.");
  }
  this.blockSize100k = b3 - '0';
  int n = BASE_BLOCK_SIZE * blockSize100k;
  this.ll8 = new byte[n];
  this.tt = new int[n];
  initNextBlock();
 }

 @Override
 public int read() throws IOException {
  if (eof) return -1;
  while (true) {
   if (rlePendingRepeats > 0) {
    rlePendingRepeats--;
    updateBlockCrc(rlePrev);
    return rlePrev;
   }
   if (!hasBlock) {
    if (eof) return -1;
    initNextBlock();
    if (eof) return -1;
   }
   if (bwtReadCount > last) {
    finishBlock();
    continue;
   }
   int b = nextBwtByte();
   if (rleRunCount == 4) {
    // 5th byte in RLE1 is the extra repeat count (0..255) of rlePrev
    rleRunCount = 0;
    if (b > 0) {
     rlePendingRepeats = b - 1;
     updateBlockCrc(rlePrev);
     return rlePrev;
    }
    // 0 extra repeats -> immediately continue to next byte
    continue;
   }
   if (b == rlePrev) {
    rleRunCount++;
   } else {
    rlePrev = b;
    rleRunCount = 1;
   }
   updateBlockCrc(b);
   return b;
  }
 }

 @Override
 public int read(byte[] dest, int off, int len) throws IOException {
  if (dest == null) throw new NullPointerException();
  if (off < 0 || len < 0 || off + len > dest.length) throw new IndexOutOfBoundsException();
  if (len == 0) return 0;
  if (eof) return -1;
  int n = 0;
  while (n < len) {
   int v = read();
   if (v < 0) break;
   dest[off + n++] = (byte) v;
  }
  return n == 0 ? -1 : n;
 }

 @Override
 public void close() throws IOException {
  InputStream s = in;
  in = null;
  ll8 = null;
  tt = null;
  if (s != null) s.close();
 }

 private int nextBwtByte() {
  int b = ll8[tPos] & 0xFF;
  tPos = tt[tPos];
  bwtReadCount++;
  return b;
 }

 private void updateBlockCrc(int ch) {
  int idx = ((computedBlockCrc >>> 24) ^ (ch & 0xFF)) & 0xFF;
  computedBlockCrc = (computedBlockCrc << 8) ^ CRC32_TABLE[idx];
 }

 private void finishBlock() throws IOException {
  int finalCrc = ~computedBlockCrc;
  if (finalCrc != storedBlockCrc) {
   throw new IOException("BZip2 block CRC mismatch.");
  }
  combinedCrc = ((combinedCrc << 1) | (combinedCrc >>> 31)) ^ finalCrc;
  hasBlock = false;
  rlePrev = -1;
  rleRunCount = 0;
  rlePendingRepeats = 0;
 }

 private int bsR(int n) throws IOException {
  int live = bsLive;
  int buff = bsBuff;
  while (live < n) {
   int next = in.read();
   if (next < 0) throw new IOException("Unexpected EOF in BZip2 stream.");
   buff = (buff << 8) | next;
   live += 8;
  }
  live -= n;
  bsLive = live;
  bsBuff = buff;
  return (buff >>> live) & ((1 << n) - 1);
 }

 private int bsGetInt32() throws IOException {
  int u = bsR(8);
  u = (u << 8) | bsR(8);
  u = (u << 8) | bsR(8);
  u = (u << 8) | bsR(8);
  return u;
 }

 private void initNextBlock() throws IOException {
  int m0 = bsR(8);
  int m1 = bsR(8);
  int m2 = bsR(8);
  int m3 = bsR(8);
  int m4 = bsR(8);
  int m5 = bsR(8);

  if (m0 == 0x17 && m1 == 0x72 && m2 == 0x45 && m3 == 0x38 && m4 == 0x50 && m5 == 0x90) {
   int storedCombined = bsGetInt32();
   if (storedCombined != combinedCrc) {
    throw new IOException("BZip2 stream CRC mismatch.");
   }
   eof = true;
   hasBlock = false;
   return;
  }
  if (m0 != 0x31 || m1 != 0x41 || m2 != 0x59 || m3 != 0x26 || m4 != 0x53 || m5 != 0x59) {
   throw new IOException("Corrupt BZip2 block header magic.");
  }

  storedBlockCrc = bsGetInt32();
  computedBlockCrc = 0xFFFFFFFF;
  int randomised = bsR(1);
  if (randomised != 0) {
   throw new IOException("Randomised BZip2 blocks are not supported.");
  }
  origPtr = bsR(24);
  if (origPtr < 0 || origPtr >= ll8.length + 10) {
   throw new IOException("Invalid BZip2 origPtr.");
  }

  // Symbol map
  int inUse16 = bsR(16);
  int nInUse = 0;
  for (int i = 0; i < 16; i++) {
   if ((inUse16 & (1 << (15 - i))) != 0) {
    int mask = bsR(16);
    for (int j = 0; j < 16; j++) {
     if ((mask & (1 << (15 - j))) != 0) {
      seqToUnseq[nInUse++] = (byte) (i * 16 + j);
     }
    }
   }
  }
  if (nInUse == 0) throw new IOException("BZip2 empty symbol table.");
  int alphaSize = nInUse + 2;
  int eob = nInUse + 1;

  // Huffman groups & selectors
  int nGroups = bsR(3);
  int nSelectors = bsR(15);
  if (nGroups < 2 || nGroups > N_GROUPS || nSelectors < 1) {
   throw new IOException("Invalid BZip2 Huffman header.");
  }
  for (int i = 0; i < nSelectors; i++) {
   int j = 0;
   while (bsR(1) != 0) {
    j++;
    if (j >= nGroups) throw new IOException("Corrupt BZip2 selector.");
   }
   if (i < MAX_SELECTORS) selectorMtf[i] = (byte) j;
  }
  byte[] pos = new byte[nGroups];
  for (int i = 0; i < nGroups; i++) pos[i] = (byte) i;
  int selCount = Math.min(nSelectors, MAX_SELECTORS);
  for (int i = 0; i < selCount; i++) {
   int v = selectorMtf[i] & 0xFF;
   byte tmp = pos[v];
   while (v > 0) {
    pos[v] = pos[v - 1];
    v--;
   }
   pos[0] = tmp;
   selector[i] = tmp;
  }

  // Coding tables
  byte[][] len = new byte[nGroups][alphaSize];
  for (int t = 0; t < nGroups; t++) {
   int curr = bsR(5);
   for (int i = 0; i < alphaSize; i++) {
    while (bsR(1) != 0) {
     curr += (bsR(1) == 0) ? 1 : -1;
     if (curr < 1 || curr > 20) throw new IOException("Corrupt BZip2 Huffman code length.");
    }
    len[t][i] = (byte) curr;
   }
  }
  for (int t = 0; t < nGroups; t++) {
   int minLen = 32;
   int maxLen = 0;
   for (int i = 0; i < alphaSize; i++) {
    int l = len[t][i] & 0xFF;
    if (l > maxLen) maxLen = l;
    if (l < minLen) minLen = l;
   }
   hbCreateDecodeTables(limit[t], base[t], perm[t], len[t], minLen, maxLen, alphaSize);
   minLens[t] = minLen;
  }

  // Decode MTF + RLE2 into ll8
  int limitLast = BASE_BLOCK_SIZE * blockSize100k;
  Arrays.fill(unzftab, 0);
  byte[] yy = new byte[256];
  for (int i = 0; i < 256; i++) yy[i] = (byte) i;

  int groupNo = 0;
  int groupPos = G_SIZE - 1;
  int zt = selector[0] & 0xFF;
  int[] baseT = base[zt];
  int[] limitT = limit[zt];
  int[] permT = perm[zt];
  int minLenT = minLens[zt];

  last = -1;
  int nextSym = decodeSymbol(minLenT, limitT, baseT, permT, alphaSize);

  while (nextSym != eob) {
   if (nextSym == RUNA || nextSym == RUNB) {
    int es = -1;
    int n = 1;
    do {
     if (nextSym == RUNA) es += n;
     else es += (n << 1);
     n <<= 1;
     if (es > limitLast) throw new IOException("BZip2 RLE overflow.");

     if (groupPos == 0) {
      groupPos = G_SIZE - 1;
      groupNo++;
      if (groupNo >= selCount) throw new IOException("BZip2 selector overrun.");
      zt = selector[groupNo] & 0xFF;
      baseT = base[zt];
      limitT = limit[zt];
      permT = perm[zt];
      minLenT = minLens[zt];
     } else {
      groupPos--;
     }
     nextSym = decodeSymbol(minLenT, limitT, baseT, permT, alphaSize);
    } while (nextSym == RUNA || nextSym == RUNB);

    es++;
    byte ch = seqToUnseq[yy[0] & 0xFF];
    unzftab[ch & 0xFF] += es;
    if (last + es >= limitLast) throw new IOException("BZip2 block size overrun.");
    while (es-- > 0) {
     ll8[++last] = ch;
    }
   } else {
    if (++last >= limitLast) throw new IOException("BZip2 block size overrun.");
    int idx = nextSym - 1;
    if (idx < 0 || idx >= nInUse) throw new IOException("BZip2 invalid MTF index.");
    byte tmp = yy[idx];
    System.arraycopy(yy, 0, yy, 1, idx);
    yy[0] = tmp;
    byte ch = seqToUnseq[tmp & 0xFF];
    unzftab[ch & 0xFF]++;
    ll8[last] = ch;

    if (groupPos == 0) {
     groupPos = G_SIZE - 1;
     groupNo++;
     if (groupNo >= selCount) throw new IOException("BZip2 selector overrun.");
     zt = selector[groupNo] & 0xFF;
     baseT = base[zt];
     limitT = limit[zt];
     permT = perm[zt];
     minLenT = minLens[zt];
    } else {
     groupPos--;
    }
    nextSym = decodeSymbol(minLenT, limitT, baseT, permT, alphaSize);
   }
  }

  if (origPtr < 0 || origPtr > last) {
   throw new IOException("BZip2 origPtr out of bounds.");
  }

  // Inverse BWT setup
  cftab[0] = 0;
  for (int i = 1; i <= 256; i++) {
   cftab[i] = cftab[i - 1] + unzftab[i - 1];
  }
  for (int i = 0; i <= last; i++) {
   int ch = ll8[i] & 0xFF;
   tt[cftab[ch]++] = i;
  }
  tPos = tt[origPtr];
  bwtReadCount = 0;
  rlePrev = -1;
  rleRunCount = 0;
  rlePendingRepeats = 0;
  hasBlock = true;
 }

 private int decodeSymbol(int zn, int[] limitT, int[] baseT, int[] permT, int alphaSize) throws IOException {
  int zvec = bsR(zn);
  while (zvec > limitT[zn]) {
   zn++;
   if (zn > 20) throw new IOException("Corrupt BZip2 Huffman stream.");
   zvec = (zvec << 1) | bsR(1);
  }
  int idx = zvec - baseT[zn];
  if (idx < 0 || idx >= alphaSize) throw new IOException("Corrupt BZip2 Huffman symbol index.");
  return permT[idx];
 }

 private static void hbCreateDecodeTables(int[] limit, int[] base, int[] perm, byte[] length, int minLen, int maxLen, int alphaSize) {
  int pp = 0;
  for (int i = minLen; i <= maxLen; i++) {
   for (int j = 0; j < alphaSize; j++) {
    if ((length[j] & 0xFF) == i) {
     perm[pp++] = j;
    }
   }
  }
  Arrays.fill(base, 0);
  Arrays.fill(limit, 0);
  for (int i = 0; i < alphaSize; i++) {
   base[(length[i] & 0xFF) + 1]++;
  }
  for (int i = 1; i < MAX_CODE_LEN; i++) {
   base[i] += base[i - 1];
  }
  int vec = 0;
  for (int i = minLen; i <= maxLen; i++) {
   vec += (base[i + 1] - base[i]);
   limit[i] = vec - 1;
   vec <<= 1;
  }
  for (int i = minLen + 1; i <= maxLen; i++) {
   base[i] = ((limit[i - 1] + 1) << 1) - base[i];
  }
 }
}
