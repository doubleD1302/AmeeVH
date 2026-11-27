package com.stellasora.viethoa.localadb;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** Non-exported receiver triggered by Android ShortcutManager when the user confirms pinning "Chơi Stella VH". */
public final class ShortcutPinnedReceiver extends BroadcastReceiver {
 @Override public void onReceive(Context context, Intent intent) {
  if (intent == null || !ShortcutGuardHelper.ACTION_SHORTCUT_PINNED.equals(intent.getAction())) {
   return;
  }
  ShortcutGuardHelper.onPinCallbackReceived(context);
  LauncherService.notifyShortcutStateChanged(context, true);
 }
}
