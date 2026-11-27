package com.stellasora.viethoa.localadb;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import org.json.JSONObject;

/**
 * Hard-blocking translucent modal Activity displaying the authentic Stella Sora game-asset
 * update warning. Used by LaunchGuardActivity (Layer B), Notification taps (Layer C),
 * and Accessibility overlay fallback (Layer A). Never offers a bypass to launch the game.
 */
public final class GameUpdateGuardActivity extends Activity {
 static final String EXTRA_SOURCE = "guard_source";

 @Override protected void onCreate(Bundle savedInstanceState) {
  super.onCreate(savedInstanceState);
  JSONObject state = OfficialAndroidClient.readCachedGuardState(this);
  String source = getIntent() != null ? getIntent().getStringExtra(EXTRA_SOURCE) : null;
  if (source == null || source.isEmpty()) source = "Bảo vệ cập nhật Stella Sora";

  View root = GameAlertViewBuilder.buildMandatoryUpdateAlert(
    this,
    state,
    source,
    "Đóng (Không mở game)",
    () -> {
     Intent i = new Intent(this, MainActivity.class)
       .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP)
       .putExtra(MainActivity.EXTRA_GUARD_RESTORE, true);
     startActivity(i);
     finish();
    },
    this::finish
  );
  setContentView(root);
 }

 @Override public void onBackPressed() {
  // Closing simply aborts launch; never bypasses into Stella Sora
  finish();
 }
}
