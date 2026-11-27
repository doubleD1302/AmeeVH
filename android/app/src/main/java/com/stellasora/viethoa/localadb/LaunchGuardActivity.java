package com.stellasora.viethoa.localadb;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;
import org.json.JSONObject;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Layer B (Zero-Permission Guarded Launcher Trampoline):
 * Entry point for pinned Home Screen shortcut "Stella Sora Việt Hóa" and in-app "Mở game".
 * - Vanilla game (no Vietnamese receipt) -> opens Stella Sora immediately (<5ms).
 * - Vietnamese installed -> queries 432-byte serverlist.html (~0.2s, falls back to cache if offline):
 *   - Update detected -> hard-blocks into GameUpdateGuardActivity (authentic game-asset warning).
 *   - Up to date -> launches com.YoStarEN.StellaSora cleanly.
 */
public final class LaunchGuardActivity extends Activity {
 private final ExecutorService executor = Executors.newSingleThreadExecutor();
 private volatile boolean finished;

 @Override protected void onCreate(Bundle savedInstanceState) {
  super.onCreate(savedInstanceState);

  Intent gameIntent = getPackageManager().getLaunchIntentForPackage(Store.GAME);
  if (gameIntent == null) {
   Toast.makeText(this, "Chưa tìm thấy ứng dụng Stella Sora Android trên máy.", Toast.LENGTH_LONG).show();
   finish();
   return;
  }

  JSONObject local = OfficialAndroidClient.readInstalledLocalState(this);
  if (!local.optBoolean("vhModified", false)) {
   launchGameAndFinish(gameIntent);
   return;
  }

  // Show compact authentic Stella Sora checking pill while verifying serverlist.html (~0.2s)
  setContentView(buildCheckingView());

  executor.execute(() -> {
   JSONObject state;
   try {
    state = OfficialAndroidClient.checkAndSave(this, 5000);
   } catch (Exception offline) {
    state = OfficialAndroidClient.readCachedGuardState(this);
   }
   final JSONObject finalState = state;
   runOnUiThread(() -> {
    if (finished || isFinishing()) return;
    if (finalState != null && finalState.optBoolean("needsRestore", false)) {
     OfficialUpdateNotice.notifyIfNeeded(this, finalState);
     Intent guard = new Intent(this, GameUpdateGuardActivity.class)
       .putExtra(GameUpdateGuardActivity.EXTRA_SOURCE, "Lối tắt bảo vệ cập nhật");
     startActivity(guard);
     finished = true;
     finish();
    } else {
     launchGameAndFinish(gameIntent);
    }
   });
  });
 }

 private FrameLayout buildCheckingView() {
  FrameLayout root = new FrameLayout(this);
  root.setBackgroundColor(Color.argb(150, 12, 22, 42));

  LinearLayout pill = new LinearLayout(this);
  pill.setOrientation(LinearLayout.HORIZONTAL);
  pill.setGravity(Gravity.CENTER_VERTICAL);
  int padH = GameAlertViewBuilder.dp(this, 18);
  int padV = GameAlertViewBuilder.dp(this, 14);
  pill.setPadding(padH, padV, padH, padV);

  GradientDrawable bg = new GradientDrawable(
    GradientDrawable.Orientation.TL_BR,
    new int[]{Color.rgb(38, 66, 120), Color.rgb(27, 50, 96)}
  );
  bg.setCornerRadius(GameAlertViewBuilder.dp(this, 12));
  bg.setStroke(GameAlertViewBuilder.dp(this, 1), Color.rgb(18, 184, 196));
  pill.setBackground(bg);
  pill.setElevation(GameAlertViewBuilder.dp(this, 8));

  ImageView star = new ImageView(this);
  star.setImageResource(R.drawable.game_star_gold);
  LinearLayout.LayoutParams sLp = new LinearLayout.LayoutParams(
    GameAlertViewBuilder.dp(this, 22), GameAlertViewBuilder.dp(this, 22));
  sLp.rightMargin = GameAlertViewBuilder.dp(this, 10);
  pill.addView(star, sLp);

  TextView tv = new TextView(this);
  tv.setText("Đang kiểm tra bản cập nhật Yostar…");
  tv.setTextColor(Color.WHITE);
  tv.setTextSize(14f);
  tv.setTypeface(Typeface.DEFAULT_BOLD);
  pill.addView(tv);

  ProgressBar pb = new ProgressBar(this);
  pb.setIndeterminate(true);
  LinearLayout.LayoutParams pbLp = new LinearLayout.LayoutParams(
    GameAlertViewBuilder.dp(this, 20), GameAlertViewBuilder.dp(this, 20));
  pbLp.leftMargin = GameAlertViewBuilder.dp(this, 12);
  pill.addView(pb, pbLp);

  root.addView(pill, new FrameLayout.LayoutParams(
    ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.CENTER));
  return root;
 }

 private void launchGameAndFinish(Intent gameIntent) {
  finished = true;
  try {
   gameIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
   startActivity(gameIntent);
  } catch (Exception e) {
   Toast.makeText(this, "Không mở được Stella Sora: " + Store.cleanError(e), Toast.LENGTH_LONG).show();
  }
  finish();
 }

 @Override protected void onDestroy() {
  finished = true;
  executor.shutdownNow();
  super.onDestroy();
 }
}
