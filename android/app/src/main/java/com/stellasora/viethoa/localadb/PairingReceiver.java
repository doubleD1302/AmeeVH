package com.stellasora.viethoa.localadb;
import android.app.RemoteInput;import android.content.*;import android.os.Bundle;
/** Explicit non-exported notification receiver; nonce is validated by live service. */
public final class PairingReceiver extends BroadcastReceiver {
 @Override public void onReceive(Context c,Intent i){String nonce=i.getData()==null?"":i.getData().getLastPathSegment();if("stella.PAIR_REPLY".equals(i.getAction())){Bundle values=RemoteInput.getResultsFromIntent(i);CharSequence code=values==null?null:values.getCharSequence("pair_code");LauncherService.notificationReply(nonce,code==null?"":code.toString());if(values!=null)values.clear();}else if("stella.PAIR_CANCEL".equals(i.getAction()))LauncherService.notificationCancel(nonce);}
}
