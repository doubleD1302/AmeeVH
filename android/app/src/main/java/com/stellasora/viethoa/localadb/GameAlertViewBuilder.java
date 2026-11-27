package com.stellasora.viethoa.localadb;

import android.content.Context;
import android.graphics.Color;
import android.graphics.PorterDuff;
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
import org.json.JSONObject;

/**
 * Shared native Android UI builder styled with authentic Stella Sora game assets:
 * - Navy gradient header (#264278 -> #1B3260) + mirrored game_pop_halftone + 5dp Coral bar
 * - game_tyrant_head + game_warning_icon + game_star_gold hero composition
 * - game_line_divider luminous game divider
 * - game_btn_coral & game_btn_ice faceted CTA buttons (HARD-BLOCK: zero bypass button)
 */
final class GameAlertViewBuilder {
 private static final int NAVY_TL = Color.rgb(38, 66, 120);
 private static final int NAVY_BR = Color.rgb(27, 50, 96);
 private static final int CORAL = Color.rgb(225, 29, 72);
 private static final int CORAL_DARK = Color.rgb(159, 18, 57);
 private static final int PORCELAIN = Color.rgb(246, 249, 253);
 private static final int ICE_BG = Color.rgb(238, 244, 250);
 private static final int HAIRLINE = Color.rgb(213, 224, 238);
 private static final int NAVY_INK = Color.rgb(30, 46, 74);
 private static final int SLATE_BODY = Color.rgb(55, 76, 107);
 private static final int SLATE_MUTED = Color.rgb(96, 118, 148);
 private static final int WARN_BG = Color.rgb(255, 241, 244);
 private static final int WARN_BORDER = Color.rgb(245, 188, 200);

 private GameAlertViewBuilder() {}

 static int dp(Context c, float v) {
  return Math.round(v * c.getResources().getDisplayMetrics().density);
 }

 static View buildMandatoryUpdateAlert(
   Context c,
   JSONObject state,
   String sourceLabel,
   String exitLabel,
   Runnable onRestore,
   Runnable onExit
 ) {
  String localGame = state != null ? state.optString("localGameVersion", "") : "";
  String localRes = state != null ? state.optString("localResourceVersion", "") : "";
  String latestGame = state != null ? state.optString("latestGameVersion", "") : "";
  String latestRes = state != null ? state.optString("latestResourceVersion", "") : "";

  // Full-screen translucent navy scrim blocking all taps underneath
  FrameLayout root = new FrameLayout(c);
  root.setBackgroundColor(Color.argb(214, 10, 20, 38));
  root.setClickable(true);
  root.setFocusable(true);
  int padOuter = dp(c, 16);
  root.setPadding(padOuter, dp(c, 32), padOuter, dp(c, 32));

  // Center Light Porcelain Card
  LinearLayout card = new LinearLayout(c);
  card.setOrientation(LinearLayout.VERTICAL);
  card.setClipToOutline(true);
  GradientDrawable cardBg = new GradientDrawable();
  cardBg.setColor(PORCELAIN);
  cardBg.setCornerRadius(dp(c, 12));
  cardBg.setStroke(dp(c, 1), HAIRLINE);
  card.setBackground(cardBg);
  card.setElevation(dp(c, 14));

  int maxCardW = Math.min(c.getResources().getDisplayMetrics().widthPixels - padOuter * 2, dp(c, 430));
  FrameLayout.LayoutParams cardLp = new FrameLayout.LayoutParams(maxCardW, ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.CENTER);
  root.addView(card, cardLp);

  // 1. Navy Gradient Header + mirrored game_pop_halftone + 5dp Coral left bar
  FrameLayout header = new FrameLayout(c);
  GradientDrawable headGrad = new GradientDrawable(GradientDrawable.Orientation.TL_BR, new int[]{NAVY_TL, NAVY_BR});
  header.setBackground(headGrad);

  ImageView halftone = new ImageView(c);
  halftone.setImageResource(R.drawable.game_pop_halftone);
  halftone.setScaleType(ImageView.ScaleType.CENTER_CROP);
  halftone.setScaleX(-1f);
  halftone.setAlpha(0.14f);
  header.addView(halftone, new FrameLayout.LayoutParams(dp(c, 160), ViewGroup.LayoutParams.MATCH_PARENT, Gravity.END));

  View leftCoral = new View(c);
  leftCoral.setBackgroundColor(CORAL);
  header.addView(leftCoral, new FrameLayout.LayoutParams(dp(c, 5), ViewGroup.LayoutParams.MATCH_PARENT, Gravity.START));

  View bottomCoral = new View(c);
  bottomCoral.setBackgroundColor(CORAL);
  header.addView(bottomCoral, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(c, 2), Gravity.BOTTOM));

  LinearLayout headRow = new LinearLayout(c);
  headRow.setOrientation(LinearLayout.HORIZONTAL);
  headRow.setGravity(Gravity.CENTER_VERTICAL);
  headRow.setPadding(dp(c, 16), dp(c, 12), dp(c, 14), dp(c, 14));

  ImageView headIcon = new ImageView(c);
  headIcon.setImageResource(R.drawable.game_warning_sm);
  LinearLayout.LayoutParams hiLp = new LinearLayout.LayoutParams(dp(c, 24), dp(c, 20));
  hiLp.rightMargin = dp(c, 10);
  headRow.addView(headIcon, hiLp);

  LinearLayout titleCol = new LinearLayout(c);
  titleCol.setOrientation(LinearLayout.VERTICAL);
  TextView titleTv = new TextView(c);
  titleTv.setText("CẢNH BÁO CẬP NHẬT STELLA SORA");
  titleTv.setTextColor(Color.WHITE);
  titleTv.setTextSize(14.5f);
  titleTv.setTypeface(Typeface.DEFAULT_BOLD);
  titleCol.addView(titleTv);

  TextView badgeTv = new TextView(c);
  badgeTv.setText("BẮT BUỘC KHÔI PHỤC DỮ LIỆU GỐC");
  badgeTv.setTextColor(Color.WHITE);
  badgeTv.setTextSize(10.5f);
  badgeTv.setTypeface(Typeface.DEFAULT_BOLD);
  badgeTv.setPadding(dp(c, 7), dp(c, 2), dp(c, 7), dp(c, 2));
  GradientDrawable pill = new GradientDrawable();
  pill.setColor(CORAL);
  pill.setCornerRadius(dp(c, 4));
  badgeTv.setBackground(pill);
  LinearLayout.LayoutParams badgeLp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
  badgeLp.topMargin = dp(c, 4);
  titleCol.addView(badgeTv, badgeLp);

  headRow.addView(titleCol, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
  header.addView(headRow, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
  card.addView(header, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

  // Scrollable body
  ScrollView scroll = new ScrollView(c);
  scroll.setFillViewport(false);
  LinearLayout body = new LinearLayout(c);
  body.setOrientation(LinearLayout.VERTICAL);
  scroll.addView(body, new ScrollView.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

  // 2. Hero Band with Tyrant popup chibi + Warning icon + Star
  LinearLayout hero = new LinearLayout(c);
  hero.setOrientation(LinearLayout.HORIZONTAL);
  hero.setGravity(Gravity.CENTER_VERTICAL);
  GradientDrawable heroGrad = new GradientDrawable(GradientDrawable.Orientation.LEFT_RIGHT, new int[]{WARN_BG, Color.WHITE, ICE_BG});
  hero.setBackground(heroGrad);
  hero.setPadding(dp(c, 16), dp(c, 14), dp(c, 16), dp(c, 12));

  FrameLayout emblem = new FrameLayout(c);
  ImageView tyrant = new ImageView(c);
  tyrant.setImageResource(R.drawable.game_tyrant_head);
  tyrant.setScaleType(ImageView.ScaleType.FIT_CENTER);
  emblem.addView(tyrant, new FrameLayout.LayoutParams(dp(c, 72), dp(c, 72), Gravity.START | Gravity.TOP));

  ImageView warnBadge = new ImageView(c);
  warnBadge.setImageResource(R.drawable.game_warning_icon);
  warnBadge.setScaleType(ImageView.ScaleType.FIT_CENTER);
  emblem.addView(warnBadge, new FrameLayout.LayoutParams(dp(c, 34), dp(c, 32), Gravity.END | Gravity.BOTTOM));

  ImageView star = new ImageView(c);
  star.setImageResource(R.drawable.game_star_gold);
  emblem.addView(star, new FrameLayout.LayoutParams(dp(c, 15), dp(c, 15), Gravity.START | Gravity.TOP));

  LinearLayout.LayoutParams embLp = new LinearLayout.LayoutParams(dp(c, 84), dp(c, 84));
  embLp.rightMargin = dp(c, 12);
  hero.addView(emblem, embLp);

  LinearLayout heroText = new LinearLayout(c);
  heroText.setOrientation(LinearLayout.VERTICAL);
  TextView headline = new TextView(c);
  headline.setText("DỪNG LẠI — KHÔNG cập nhật khi còn bản Việt hoá!");
  headline.setTextColor(CORAL_DARK);
  headline.setTextSize(15f);
  headline.setTypeface(Typeface.DEFAULT_BOLD);
  heroText.addView(headline);

  TextView desc = new TextView(c);
  desc.setText("Máy chủ Yostar đã phát hành bản cập nhật mới. Nếu vào game tải bản vá ngay lúc này, tệp ngôn ngữ đã Việt hoá sẽ làm trình vá báo lỗi xác minh.");
  desc.setTextColor(SLATE_BODY);
  desc.setTextSize(13f);
  desc.setLineSpacing(dp(c, 2), 1f);
  LinearLayout.LayoutParams descLp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
  descLp.topMargin = dp(c, 5);
  heroText.addView(desc, descLp);

  hero.addView(heroText, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
  body.addView(hero, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

  // 3. Authentic luminous game divider (Common_Line_03.png)
  ImageView divider = new ImageView(c);
  divider.setImageResource(R.drawable.game_line_divider);
  divider.setScaleType(ImageView.ScaleType.FIT_XY);
  divider.setPadding(dp(c, 12), 0, dp(c, 12), 0);
  divider.setBackgroundColor(Color.WHITE);
  body.addView(divider, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(c, 8)));

  // 4. Version comparison box
  LinearLayout infoWrap = new LinearLayout(c);
  infoWrap.setOrientation(LinearLayout.VERTICAL);
  infoWrap.setBackgroundColor(Color.WHITE);
  infoWrap.setPadding(dp(c, 16), dp(c, 10), dp(c, 16), dp(c, 12));

  LinearLayout kvBox = new LinearLayout(c);
  kvBox.setOrientation(LinearLayout.VERTICAL);
  GradientDrawable kvBg = new GradientDrawable();
  kvBg.setColor(ICE_BG);
  kvBg.setCornerRadius(dp(c, 8));
  kvBg.setStroke(dp(c, 1), HAIRLINE);
  kvBox.setBackground(kvBg);
  kvBox.setPadding(dp(c, 12), dp(c, 10), dp(c, 12), dp(c, 10));

  addKvRow(c, kvBox, "Nguồn bảo vệ", sourceLabel, NAVY_INK, false);
  addKvRow(c, kvBox, "Bản đang cài Việt hoá", formatVer(localGame, localRes), SLATE_BODY, false);
  addKvRow(c, kvBox, "Bản mới từ Yostar", formatVer(latestGame, latestRes), CORAL, true);
  infoWrap.addView(kvBox, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

  // Safety strip
  LinearLayout strip = new LinearLayout(c);
  strip.setOrientation(LinearLayout.HORIZONTAL);
  strip.setGravity(Gravity.TOP);
  GradientDrawable stripBg = new GradientDrawable();
  stripBg.setColor(WARN_BG);
  stripBg.setCornerRadius(dp(c, 8));
  stripBg.setStroke(dp(c, 1), WARN_BORDER);
  strip.setBackground(stripBg);
  strip.setPadding(dp(c, 10), dp(c, 9), dp(c, 10), dp(c, 9));

  ImageView stripIcon = new ImageView(c);
  stripIcon.setImageResource(R.drawable.game_warning_sm);
  LinearLayout.LayoutParams siLp = new LinearLayout.LayoutParams(dp(c, 18), dp(c, 15));
  siLp.rightMargin = dp(c, 8);
  siLp.topMargin = dp(c, 2);
  strip.addView(stripIcon, siLp);

  TextView stripTv = new TextView(c);
  stripTv.setText("Quy trình an toàn: (1) Bấm nút đỏ bên dưới để khôi phục dữ liệu gốc → (2) Vào Stella Sora cập nhật xong → (3) Mở lại launcher cài Việt hoá mới.");
  stripTv.setTextColor(CORAL_DARK);
  stripTv.setTextSize(12.5f);
  stripTv.setLineSpacing(dp(c, 2), 1f);
  strip.addView(stripTv, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

  LinearLayout.LayoutParams stripLp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
  stripLp.topMargin = dp(c, 10);
  infoWrap.addView(strip, stripLp);

  body.addView(infoWrap, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

  card.addView(scroll, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));

  // 5. Footer with authentic Stella Sora 9-slice sprite CTAs (ZERO bypass option!)
  LinearLayout footer = new LinearLayout(c);
  footer.setOrientation(LinearLayout.VERTICAL);
  footer.setBackgroundColor(ICE_BG);
  footer.setPadding(dp(c, 16), dp(c, 12), dp(c, 16), dp(c, 14));

  View restoreBtn = makeGameSpriteButton(
    c,
    R.drawable.game_btn_coral,
    R.drawable.game_icon_restore,
    Color.WHITE,
    "Khôi phục dữ liệu gốc ngay",
    Color.WHITE,
    onRestore
  );
  footer.addView(restoreBtn, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(c, 48)));

  View exitBtn = makeGameSpriteButton(
    c,
    R.drawable.game_btn_ice,
    R.drawable.game_icon_stop,
    NAVY_INK,
    exitLabel != null && !exitLabel.isEmpty() ? exitLabel : "Thoát về màn hình chính",
    NAVY_INK,
    onExit
  );
  LinearLayout.LayoutParams exitLp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(c, 44));
  exitLp.topMargin = dp(c, 8);
  footer.addView(exitBtn, exitLp);

  TextView lockNote = new TextView(c);
  lockNote.setText("Đã khoá tạm vào game để tránh lỗi cập nhật dữ liệu.");
  lockNote.setTextColor(SLATE_MUTED);
  lockNote.setTextSize(11.5f);
  lockNote.setGravity(Gravity.CENTER_HORIZONTAL);
  LinearLayout.LayoutParams lnLp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
  lnLp.topMargin = dp(c, 7);
  footer.addView(lockNote, lnLp);

  card.addView(footer, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
  return root;
 }

 private static View makeGameSpriteButton(
   Context c,
   int bgRes,
   int iconRes,
   int iconTint,
   String label,
   int textColor,
   Runnable onClick
 ) {
  FrameLayout btn = new FrameLayout(c);
  btn.setClickable(true);
  btn.setFocusable(true);

  ImageView bg = new ImageView(c);
  bg.setImageResource(bgRes);
  bg.setScaleType(ImageView.ScaleType.FIT_XY);
  btn.addView(bg, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));

  LinearLayout row = new LinearLayout(c);
  row.setOrientation(LinearLayout.HORIZONTAL);
  row.setGravity(Gravity.CENTER);
  row.setPadding(dp(c, 14), 0, dp(c, 14), dp(c, 2));

  ImageView icon = new ImageView(c);
  icon.setImageResource(iconRes);
  icon.setColorFilter(iconTint, PorterDuff.Mode.SRC_IN);
  LinearLayout.LayoutParams icLp = new LinearLayout.LayoutParams(dp(c, 18), dp(c, 18));
  icLp.rightMargin = dp(c, 8);
  row.addView(icon, icLp);

  TextView tv = new TextView(c);
  tv.setText(label);
  tv.setTextColor(textColor);
  tv.setTextSize(14.5f);
  tv.setTypeface(Typeface.DEFAULT_BOLD);
  row.addView(tv);

  btn.addView(row, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
  btn.setOnClickListener(v -> {
   if (onClick != null) onClick.run();
  });
  return btn;
 }

 private static void addKvRow(Context c, LinearLayout parent, String label, String value, int valueColor, boolean boldVal) {
  LinearLayout row = new LinearLayout(c);
  row.setOrientation(LinearLayout.HORIZONTAL);
  row.setPadding(0, dp(c, 3), 0, dp(c, 3));

  TextView k = new TextView(c);
  k.setText(label);
  k.setTextColor(SLATE_MUTED);
  k.setTextSize(12.5f);
  row.addView(k, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

  TextView v = new TextView(c);
  v.setText(value);
  v.setTextColor(valueColor);
  v.setTextSize(12.5f);
  v.setGravity(Gravity.END);
  if (boldVal) v.setTypeface(Typeface.DEFAULT_BOLD);
  row.addView(v, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1.15f));

  parent.addView(row, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
 }

 private static String formatVer(String gameVer, String resVer) {
  boolean hasG = gameVer != null && !gameVer.isEmpty() && !"unknown".equalsIgnoreCase(gameVer);
  boolean hasR = resVer != null && !resVer.isEmpty() && !"unknown".equalsIgnoreCase(resVer);
  if (hasG && hasR) return "v" + gameVer + " · RES " + resVer;
  if (hasR) return "RES " + resVer;
  if (hasG) return "v" + gameVer;
  return "Chưa rõ";
 }
}
