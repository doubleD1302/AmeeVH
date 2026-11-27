package com.stellasora.viethoa.localadb;

import java.util.ArrayList;
import java.util.List;

/** Explicitly declared versions match, with wildcard '*' authorization and direction-aware mismatch diagnosis. */
final class VersionCompatibility {
 private VersionCompatibility() {}

 static final class Diagnosis {
  final String kind; // "match" | "game_older" | "game_newer" | "resource_mismatch" | "unknown"
  final String observedGame;
  final String observedResource;
  final String declaredGame;
  final String declaredResource;
  final String declaredGameSummary;
  final String declaredResourceSummary;

  Diagnosis(String kind, String observedGame, String observedResource, String declaredGame, String declaredResource) {
   this.kind = kind;
   this.observedGame = observedGame == null ? "" : observedGame.trim();
   this.observedResource = observedResource == null ? "" : observedResource.trim();
   this.declaredGame = declaredGame == null ? "" : declaredGame.trim();
   this.declaredResource = declaredResource == null ? "" : declaredResource.trim();
   this.declaredGameSummary = summarizeDeclared(this.declaredGame, false);
   this.declaredResourceSummary = summarizeDeclared(this.declaredResource, true);
  }

  boolean isMatch() { return "match".equals(kind); }
 }

 static boolean matches(String declared, String observed) {
  if (declared == null || observed == null) return false;
  String actual = observed.trim();
  if (!valid(actual)) return false;
  for (String version : declared.split("[,;|]")) {
   String candidate = version.trim();
   if (!valid(candidate) && !candidate.equals("*")) continue;
   if (candidate.equals("*") || candidate.equals(actual)) return true;
  }
  return false;
 }

 private static boolean valid(String value) {
  return value != null && value.matches("[0-9][0-9A-Za-z_.-]*");
 }

 static boolean matchesBoth(String declaredGame, String declaredResource, String game, String resource) {
  return matches(declaredGame, game) && matches(declaredResource, resource);
 }

 static int compareDotted(String a, String b) {
  if (a == null || b == null) return 0;
  String ca = a.trim().replaceFirst("^[vV]", "");
  String cb = b.trim().replaceFirst("^[vV]", "");
  if (!ca.matches("[0-9]+(\\.[0-9]+)*") || !cb.matches("[0-9]+(\\.[0-9]+)*")) return 0;
  String[] pa = ca.split("\\.");
  String[] pb = cb.split("\\.");
  int len = Math.max(pa.length, pb.length);
  for (int i = 0; i < len; i++) {
   long va = i < pa.length ? Long.parseLong(pa[i]) : 0L;
   long vb = i < pb.length ? Long.parseLong(pb[i]) : 0L;
   if (va != vb) return Long.compare(va, vb);
  }
  return 0;
 }

 static String summarizeDeclared(String declared, boolean forResource) {
  if (declared == null || declared.trim().isEmpty()) return "?";
  List<String> items = new ArrayList<>();
  boolean hasWildcard = false;
  for (String raw : declared.split("[,;|]")) {
   String s = raw.trim();
   if (s.isEmpty()) continue;
   if ("*".equals(s)) {
    hasWildcard = true;
   } else if (valid(s)) {
    items.add(s);
   }
  }
  if (forResource && hasWildcard) {
   return items.isEmpty() ? "mọi phiên bản tài nguyên" : (items.get(items.size() - 1) + " · mọi hotfix");
  }
  if (items.isEmpty()) return hasWildcard ? "mọi phiên bản" : declared.trim();
  if (items.size() <= 2) {
   StringBuilder sb = new StringBuilder();
   for (int i = 0; i < items.size(); i++) {
    if (i > 0) sb.append(", ");
    sb.append(items.get(i));
   }
   return sb.toString();
  }
  return items.get(0) + " … " + items.get(items.size() - 1);
 }

 static Diagnosis diagnose(String declaredGame, String declaredResource, String observedGame, String observedResource) {
  String g = observedGame == null ? "" : observedGame.trim();
  String r = observedResource == null ? "" : observedResource.trim();
  String dg = declaredGame == null ? "" : declaredGame.trim();
  String dr = declaredResource == null ? "" : declaredResource.trim();
  if (!valid(g) || !valid(r) || dg.isEmpty() || dr.isEmpty()) {
   return new Diagnosis("unknown", g, r, dg, dr);
  }
  if (matchesBoth(dg, dr, g, r)) {
   return new Diagnosis("match", g, r, dg, dr);
  }
  if (!matches(dg, g)) {
   List<String> dotted = new ArrayList<>();
   for (String tok : dg.split("[,;|]")) {
    String s = tok.trim().replaceFirst("^[vV]", "");
    if (s.matches("[0-9]+(\\.[0-9]+)*")) dotted.add(s);
   }
   String normG = g.replaceFirst("^[vV]", "");
   if (!dotted.isEmpty() && normG.matches("[0-9]+(\\.[0-9]+)*")) {
    String minSupported = dotted.get(0);
    String maxSupported = dotted.get(0);
    for (String cand : dotted) {
     if (compareDotted(cand, minSupported) < 0) minSupported = cand;
     if (compareDotted(cand, maxSupported) > 0) maxSupported = cand;
    }
    if (compareDotted(normG, minSupported) < 0) {
     return new Diagnosis("game_older", g, r, dg, dr);
    }
    if (compareDotted(normG, maxSupported) > 0) {
     return new Diagnosis("game_newer", g, r, dg, dr);
    }
   }
   return new Diagnosis("game_older", g, r, dg, dr);
  }
  return new Diagnosis("resource_mismatch", g, r, dg, dr);
 }
}
