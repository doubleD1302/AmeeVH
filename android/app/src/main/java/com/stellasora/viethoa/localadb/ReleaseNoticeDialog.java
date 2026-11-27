package com.stellasora.viethoa.localadb;

import android.app.AlertDialog;
import android.content.Context;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

/** Presentation only; styled with authentic Stella Sora Navy Header, halftone, star & luminous divider. */
final class ReleaseNoticeDialog {
 private static final int LIGHT_INK = Color.rgb(30, 46, 74);
 private static final int LIGHT_MUTED = Color.rgb(83, 113, 128);
 private static final int LIGHT_ACCENT = Color.rgb(18, 152, 168);

 private static final int DARK_INK = Color.rgb(234, 242, 250);
 private static final int DARK_MUTED = Color.rgb(155, 178, 199);
 private static final int DARK_ACCENT = Color.rgb(90, 210, 214);

 private static final int NAVY_TL = Color.rgb(38, 66, 120);
 private static final int NAVY_BR = Color.rgb(27, 50, 96);
 private static final int CYAN_LINE = Color.rgb(18, 184, 196);

 private ReleaseNoticeDialog() {}

 private static int dp(Context c, float value) {
  return Math.round(value * c.getResources().getDisplayMetrics().density);
 }

 private static TextView text(Context c, String value, float size, int color, boolean bold) {
  TextView view = new TextView(c);
  view.setText(value);
  view.setTextSize(size);
  view.setTextColor(color);
  if (bold) view.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
  view.setIncludeFontPadding(true);
  return view;
 }

 private static GradientDrawable rounded(int fill, int stroke, int radius) {
  GradientDrawable shape = new GradientDrawable();
  shape.setColor(fill);
  shape.setCornerRadius(radius);
  shape.setStroke(1, stroke);
  return shape;
 }

 private static void add(LinearLayout box, View view, int topMargin) {
  LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
    LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
  params.topMargin = topMargin;
  box.addView(view, params);
 }

 static AlertDialog.Builder builder(Context c, boolean launcher, String version, String notes) {
  return builder(c, launcher, version, notes, false);
 }

 static AlertDialog.Builder builder(Context c, boolean launcher, String version, String notes, boolean dark) {
  int ink = dark ? DARK_INK : LIGHT_INK;
  int muted = dark ? DARK_MUTED : LIGHT_MUTED;
  int accent = dark ? DARK_ACCENT : LIGHT_ACCENT;
  int badgeFill = dark ? Color.rgb(22, 46, 62) : Color.rgb(233, 246, 243);
  int badgeStroke = dark ? Color.rgb(44, 96, 112) : Color.rgb(185, 224, 222);
  int noteFill = dark ? Color.rgb(15, 28, 45) : Color.rgb(245, 249, 250);
  int noteStroke = dark ? Color.rgb(38, 61, 87) : Color.rgb(213, 224, 238);

  LinearLayout outer = new LinearLayout(c);
  outer.setOrientation(LinearLayout.VERTICAL);

  // Authentic Stella Sora Navy header bar with mirrored halftone + star emblem
  FrameLayout header = new FrameLayout(c);
  header.setBackground(new GradientDrawable(GradientDrawable.Orientation.TL_BR, new int[]{NAVY_TL, NAVY_BR}));

  ImageView halftone = new ImageView(c);
  halftone.setImageResource(R.drawable.game_pop_halftone);
  halftone.setScaleType(ImageView.ScaleType.CENTER_CROP);
  halftone.setScaleX(-1f);
  halftone.setAlpha(0.13f);
  header.addView(halftone, new FrameLayout.LayoutParams(dp(c, 140), ViewGroup.LayoutParams.MATCH_PARENT, Gravity.END));

  View accentBar = new View(c);
  accentBar.setBackgroundColor(CYAN_LINE);
  header.addView(accentBar, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(c, 2), Gravity.BOTTOM));

  LinearLayout headRow = new LinearLayout(c);
  headRow.setOrientation(LinearLayout.HORIZONTAL);
  headRow.setGravity(Gravity.CENTER_VERTICAL);
  headRow.setPadding(dp(c, 20), dp(c, 16), dp(c, 20), dp(c, 16));

  ImageView star = new ImageView(c);
  star.setImageResource(R.drawable.game_star_gold);
  LinearLayout.LayoutParams sLp = new LinearLayout.LayoutParams(dp(c, 22), dp(c, 22));
  sLp.rightMargin = dp(c, 10);
  headRow.addView(star, sLp);

  LinearLayout hCol = new LinearLayout(c);
  hCol.setOrientation(LinearLayout.VERTICAL);
  TextView eyebrow = text(c, "THÔNG BÁO CẬP NHẬT", 10.5f, Color.rgb(150, 238, 244), true);
  eyebrow.setLetterSpacing(.08f);
  hCol.addView(eyebrow);

  TextView title = text(c, launcher ? "Có launcher mới" : "Có bản Việt hoá mới", 18, Color.WHITE, true);
  title.setAccessibilityHeading(true);
  hCol.addView(title);
  headRow.addView(hCol, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

  header.addView(headRow, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
  outer.addView(header, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

  ScrollView scroll = new ScrollView(c);
  scroll.setFillViewport(false);
  scroll.setClipToPadding(false);
  scroll.setAccessibilityPaneTitle((launcher ? "Có launcher mới " : "Có bản Việt hoá mới ") + String.valueOf(version));
  LinearLayout content = new LinearLayout(c);
  content.setOrientation(LinearLayout.VERTICAL);
  content.setPadding(dp(c, 20), dp(c, 16), dp(c, 20), dp(c, 8));
  scroll.addView(content, new ScrollView.LayoutParams(
    ScrollView.LayoutParams.MATCH_PARENT, ScrollView.LayoutParams.WRAP_CONTENT));

  TextView versionLabel = text(c, "Phiên bản " + String.valueOf(version), 14, accent, true);
  versionLabel.setGravity(Gravity.START | Gravity.CENTER_VERTICAL);
  versionLabel.setPadding(dp(c, 12), dp(c, 7), dp(c, 12), dp(c, 7));
  versionLabel.setBackground(rounded(badgeFill, badgeStroke, dp(c, 10)));
  add(content, versionLabel, 0);

  ImageView divider = new ImageView(c);
  divider.setImageResource(R.drawable.game_line_divider);
  divider.setScaleType(ImageView.ScaleType.FIT_XY);
  LinearLayout.LayoutParams divLp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(c, 8));
  divLp.topMargin = dp(c, 12);
  content.addView(divider, divLp);

  TextView notesHeading = text(c, "Nội dung bản phát hành", 14, ink, true);
  notesHeading.setAccessibilityHeading(true);
  add(content, notesHeading, dp(c, 10));
  String noteText = notes == null || notes.trim().isEmpty()
    ? "Bản phát hành chưa cung cấp nội dung." : notes;
  TextView noteBody = text(c, noteText, 14.5f, ink, false);
  noteBody.setLineSpacing(dp(c, 3), 1f);
  noteBody.setTextIsSelectable(true);
  noteBody.setAutoLinkMask(0);
  noteBody.setPadding(dp(c, 14), dp(c, 12), dp(c, 14), dp(c, 12));
  noteBody.setBackground(rounded(noteFill, noteStroke, dp(c, 10)));
  add(content, noteBody, dp(c, 8));

  String hint = launcher
    ? "Mở phần cập nhật launcher để kiểm tra và cài phiên bản mới."
    : "Mở phần cài đặt để kiểm tra khả năng cập nhật.";
  TextView help = text(c, hint, 13, muted, false);
  help.setLineSpacing(dp(c, 2), 1f);
  add(content, help, dp(c, 14));

  outer.addView(scroll, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
  int themeRes = dark ? android.R.style.Theme_Material_Dialog_Alert : android.R.style.Theme_Material_Light_Dialog_Alert;
  return new AlertDialog.Builder(c, themeRes).setView(outer);
 }
}
