package com.stellasora.viethoa.localadb;

import android.app.AlertDialog;
import android.content.Context;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

/** Presentation only; callers own notice state, dismissal and sequencing. */
final class ReleaseNoticeDialog {
 private static final int INK = Color.rgb(43, 69, 88);
 private static final int MUTED = Color.rgb(83, 113, 128);
 private static final int ACCENT = Color.rgb(58, 112, 108);

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
  // The entire content can scroll at high font scales, leaving native actions accessible.
  ScrollView scroll = new ScrollView(c);
  scroll.setFillViewport(false);
  scroll.setClipToPadding(false);
  scroll.setAccessibilityPaneTitle((launcher ? "Có launcher mới " : "Có bản Việt hoá mới ") + String.valueOf(version));
  LinearLayout content = new LinearLayout(c);
  content.setOrientation(LinearLayout.VERTICAL);
  content.setPadding(dp(c, 24), dp(c, 24), dp(c, 24), dp(c, 8));
  scroll.addView(content, new ScrollView.LayoutParams(
    ScrollView.LayoutParams.MATCH_PARENT, ScrollView.LayoutParams.WRAP_CONTENT));

  TextView eyebrow = text(c, "THÔNG BÁO CẬP NHẬT", 11, ACCENT, true);
  eyebrow.setLetterSpacing(.08f);
  add(content, eyebrow, 0);
  TextView title = text(c, launcher ? "Có launcher mới" : "Có bản Việt hoá mới", 22, INK, true);
  title.setAccessibilityHeading(true);
  add(content, title, dp(c, 6));
  TextView versionLabel = text(c, "Phiên bản " + String.valueOf(version), 14, ACCENT, true);
  versionLabel.setGravity(Gravity.START | Gravity.CENTER_VERTICAL);
  versionLabel.setPadding(dp(c, 12), dp(c, 7), dp(c, 12), dp(c, 7));
  versionLabel.setBackground(rounded(Color.rgb(233, 246, 243), Color.rgb(205, 226, 222), dp(c, 10)));
  add(content, versionLabel, dp(c, 12));

  TextView notesHeading = text(c, "Nội dung bản phát hành", 14, INK, true);
  notesHeading.setAccessibilityHeading(true);
  add(content, notesHeading, dp(c, 20));
  String noteText = notes == null || notes.trim().isEmpty()
    ? "Bản phát hành chưa cung cấp nội dung." : notes;
  TextView noteBody = text(c, noteText, 15, INK, false);
  noteBody.setLineSpacing(dp(c, 3), 1f);
  noteBody.setTextIsSelectable(true);
  noteBody.setAutoLinkMask(0); // Release notes are untrusted plain text.
  noteBody.setPadding(dp(c, 14), dp(c, 12), dp(c, 14), dp(c, 12));
  noteBody.setBackground(rounded(Color.rgb(245, 249, 250), Color.rgb(217, 231, 235), dp(c, 10)));
  add(content, noteBody, dp(c, 8));

  String hint = launcher
    ? "Mở phần cập nhật launcher để kiểm tra và cài phiên bản mới."
    : "Mở phần cài đặt để kiểm tra khả năng cập nhật.";
  TextView help = text(c, hint, 13, MUTED, false);
  help.setLineSpacing(dp(c, 2), 1f);
  add(content, help, dp(c, 16));
  return new AlertDialog.Builder(c).setView(scroll);
 }
}
