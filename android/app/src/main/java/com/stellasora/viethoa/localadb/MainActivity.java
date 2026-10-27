package com.stellasora.viethoa.localadb;
import android.widget.FrameLayout;import android.Manifest;import android.app.*;import android.content.*;import android.content.pm.PackageManager;import android.graphics.Color;import android.net.*;import android.os.*;import android.provider.Settings;import android.view.*;import android.webkit.*;import org.json.*;import java.io.*;import java.util.*;
/** Trusted local HTTPS asset origin and a narrow explicit-action native bridge. */
public final class MainActivity extends Activity implements LauncherService.Listener {
 private static final String HOST="stella.local.invalid",HOME="https://stella.local.invalid/index.html";private WebView web;private boolean loaded,autoSynced,resumed;private String afterPermission;private boolean updateDialogShowing;
 private final Set<String> allowed=new HashSet<>(Arrays.asList("state","sync","saveSettings","pair","connect","disconnect","startPairingNotification","cancelPairing","detect","install","verify","restore","recover","checkUpdate","installUpdate","openWirelessSettings","launchGame","copyDiagnostics","copyAccount","openIssues","openDeviceInfo","openDevSettings"));
 @Override public void onCreate(Bundle saved){super.onCreate(saved);getWindow().setStatusBarColor(Color.rgb(243,248,250));getWindow().setNavigationBarColor(Color.rgb(243,248,250));getWindow().setDecorFitsSystemWindows(false);web=new WebView(this);web.setBackgroundColor(Color.rgb(243,248,250));FrameLayout container=new FrameLayout(this);container.setBackgroundColor(Color.rgb(243,248,250));container.addView(web,new FrameLayout.LayoutParams(-1,-1));setContentView(container);container.setOnApplyWindowInsetsListener((v,insets)->{android.graphics.Insets bars=insets.getInsets(WindowInsets.Type.systemBars()),ime=insets.getInsets(WindowInsets.Type.ime());v.setPadding(bars.left,bars.top,bars.right,Math.max(bars.bottom,ime.bottom));return WindowInsets.CONSUMED;});container.requestApplyInsets();WindowInsetsController barAppearance=getWindow().getInsetsController();if(barAppearance!=null)barAppearance.setSystemBarsAppearance(WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS|WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS,WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS|WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS);
  WebView.setWebContentsDebuggingEnabled(false);WebSettings settings=web.getSettings();settings.setJavaScriptEnabled(true);settings.setDomStorageEnabled(false);settings.setAllowFileAccess(false);settings.setAllowContentAccess(false);settings.setAllowFileAccessFromFileURLs(false);settings.setAllowUniversalAccessFromFileURLs(false);settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);settings.setSupportMultipleWindows(false);settings.setJavaScriptCanOpenWindowsAutomatically(false);settings.setMediaPlaybackRequiresUserGesture(true);web.addJavascriptInterface(new NativeBridge(),"StellaNative");
  web.setWebViewClient(new WebViewClient(){
   @Override public boolean shouldOverrideUrlLoading(WebView v,WebResourceRequest r){return !trusted(r.getUrl());}
   @Override public WebResourceResponse shouldInterceptRequest(WebView v,WebResourceRequest request){try{Uri uri=request.getUrl();if(!trusted(uri))return denied();String path=uri.getPath();if(path==null||path.equals("/"))path="/index.html";if(path.contains("..")||path.contains("\\")||!path.matches("/[A-Za-z0-9_./\\[\\]-]+"))return denied();String file=path.substring(1);String mime=file.endsWith(".html")?"text/html":file.endsWith(".css")?"text/css":file.endsWith(".js")?"text/javascript":file.endsWith(".png")?"image/png":file.endsWith(".svg")?"image/svg+xml":file.endsWith(".ttf")?"font/ttf":file.endsWith(".json")?"application/json":"text/plain";WebResourceResponse out=new WebResourceResponse(mime,mime.startsWith("image/")||mime.startsWith("font/")?null:"UTF-8",getAssets().open("ui/"+file));out.setResponseHeaders(Collections.singletonMap("X-Content-Type-Options","nosniff"));return out;}catch(Exception e){return denied();}}
   @Override public void onReceivedSslError(WebView v,android.webkit.SslErrorHandler handler,android.net.http.SslError error){handler.cancel();}
   @Override public void onPageFinished(WebView v,String url){if(url.equals(HOME)){loaded=true;emitState();maybeAutoSync();}}
  });web.setWebChromeClient(new WebChromeClient());web.setDownloadListener((url,userAgent,disposition,mime,length)->showMessage("Tải bị chặn","Chỉ tải gói qua chức năng có xác minh của launcher.",true));LauncherService.listen(this);try{UpdateNotice.schedule(this);}catch(RuntimeException ignored){}web.loadUrl(HOME);
 }
 private static boolean trusted(Uri uri){return "https".equals(uri.getScheme())&&HOST.equals(uri.getHost())&&(uri.getPort()==-1||uri.getPort()==443);}
 private static WebResourceResponse denied(){return new WebResourceResponse("text/plain","UTF-8",403,"Blocked",Collections.emptyMap(),new ByteArrayInputStream(new byte[0]));}
 private final class NativeBridge {@JavascriptInterface public void request(String action,String payload){if(action==null||!allowed.contains(action)||payload==null||payload.length()>65536){runOnUiThread(()->showMessage("Yêu cầu bị chặn","Thao tác không thuộc giao diện tin cậy.",true));return;}try{JSONObject args=new JSONObject(payload);runOnUiThread(()->handle(action,args));}catch(JSONException e){runOnUiThread(()->showMessage("Dữ liệu chưa hợp lệ","Không đọc được yêu cầu từ giao diện.",true));}}}
 private void handle(String action,JSONObject args){try{
  switch(action){
   case "state":emitState();break;
   case "openDeviceInfo":openDeviceInfo();break;
    case "openDevSettings":openDevSettings();break;
    case "openWirelessSettings":openWireless();break;
   case "startPairingNotification":if(!LauncherService.isDevOptions(this)){showDevModeGuideDialog();break;}if(Build.VERSION.SDK_INT>=33&&checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED){afterPermission=action;requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},71);}else {LauncherService.dispatch(this,action,args);openWireless();}break;
   case "openIssues":{JSONObject cfg=Store.config(this);Store.validateConfig(cfg);external("https://github.com/"+cfg.getString("repo")+"/issues");break;}
   case "copyAccount":{String method=args.optString("method");JSONArray methods=Store.asset(this,"support/payment_methods.json").getJSONArray("methods");String account=null;for(int i=0;i<methods.length();i++){JSONObject m=methods.getJSONObject(i);if(m.getString("id").equals(method)&&!m.isNull("account_number"))account=m.getString("account_number");}if(account==null)throw new IOException("Nguồn chỉ có số ví được che. Hãy quét mã MoMo, không đoán số điện thoại.");clipboard("Tài khoản ủng hộ",account);showMessage("Đã sao chép","Đã sao chép số tài khoản từ thông tin được cung cấp.",false);break;}
   case "copyDiagnostics":{JSONObject s=LauncherService.snapshot(this);JSONObject report=Store.obj("app",s.opt("app"),"adb_connected",s.getJSONObject("adb").optBoolean("connected"),"adb_status",s.getJSONObject("adb").optString("status"),"game",s.opt("game"),"github",s.opt("github"),"message",s.optString("message"),"recovery",s.opt("recovery"));clipboard("Chẩn đoán Stella Sora",report.toString(2));showMessage("Đã sao chép báo cáo","Báo cáo chỉ được sao chép trên máy. Hãy xem lại trước khi tự gửi lên trang báo lỗi.",false);break;}
   case "launchGame":if(LauncherService.snapshot(this).optBoolean("busy"))throw new IOException("Hãy chờ thao tác đang chạy hoàn tất trước khi mở game.");Intent launch=getPackageManager().getLaunchIntentForPackage(Store.GAME);if(launch==null)throw new IOException("Chưa tìm thấy ứng dụng Stella Sora Android.");startActivity(launch);break;
   case "install":case "restore":case "recover":{JSONObject state=LauncherService.snapshot(this);if(state.optBoolean("busy"))throw new IOException("Đang có thao tác. Hãy chờ hoàn tất.");String root=state.getJSONObject("game").optString("root","Chưa xác định");String text=action.equals("install")?"Chỉ cài các tệp Android khớp phiên bản và SHA256. Gói Windows sẽ bị từ chối.":action.equals("restore")?"Khôi phục từ backup của đúng thiết bị và thư mục. Tệp đã đổi sau cài sẽ được giữ lại và báo xung đột.":"Đọc nhật ký và phục hồi thao tác bị ngắt. Không dùng backup của thiết bị khác.";new AlertDialog.Builder(this).setTitle(action.equals("install")?"Cài Việt hoá Android":action.equals("restore")?"Khôi phục bản trước cài":"Phục hồi thao tác").setMessage(root+"\n\n"+text+"\n\nHãy thoát game và chờ thao tác hoàn tất.").setNegativeButton("Để sau",null).setPositiveButton("Tiếp tục",(d,w)->LauncherService.dispatch(this,action,args)).show();break;}
   case "installUpdate":installUpdate();break;
   default:LauncherService.dispatch(this,action,args);
  }
 }catch(Exception e){showMessage("Chưa thực hiện được",Store.cleanError(e),true);}}
 private void installUpdate()throws Exception {JSONObject state=LauncherService.snapshot(this);if(state.optBoolean("busy"))throw new IOException("Hãy chờ thao tác đang chạy.");File apk=new File(getCacheDir(),"updates/update.apk"),metadata=Store.internal(this,"pending_update.json");if(!apk.isFile()||!metadata.isFile()){LauncherService.dispatch(this,"prepareUpdate",new JSONObject());return;}ChannelClient.verifyApk(this,apk,Store.read(metadata));if(!getPackageManager().canRequestPackageInstalls()){new AlertDialog.Builder(this).setTitle("Cho phép cài APK từ launcher").setMessage("Android cần bạn cho phép nguồn này trước. Sau khi cấp quyền, quay lại và bấm mở trình cài đặt lần nữa.").setNegativeButton("Để sau",null).setPositiveButton("Mở cài đặt",(d,w)->startActivity(new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,Uri.parse("package:"+getPackageName())))).show();return;}new AlertDialog.Builder(this).setTitle("Mở trình cài đặt Android").setMessage("APK đã đúng ứng dụng Local ADB, là bản mới hơn và có cùng chữ ký. Android vẫn yêu cầu bạn tự xác nhận cài đặt.").setNegativeButton("Để sau",null).setPositiveButton("Mở trình cài đặt",(d,w)->{Uri uri=Uri.parse("content://"+Store.APP+".updates/update.apk");Intent install=new Intent(Intent.ACTION_VIEW).setDataAndType(uri,"application/vnd.android.package-archive").addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);startActivity(install);}).show();}
 private void openWireless(){
  try{
   Intent tileIntent=new Intent("android.service.quicksettings.action.QS_TILE_PREFERENCES");
   tileIntent.putExtra(Intent.EXTRA_COMPONENT_NAME,new ComponentName("com.android.settings","com.android.settings.development.qstile.DevelopmentTiles$WirelessDebugging"));
   tileIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
   startActivity(tileIntent);
   return;
  }catch(Exception ignored){}
  try{
   Intent subSettings=new Intent();
   subSettings.setClassName("com.android.settings","com.android.settings.SubSettings");
   subSettings.putExtra(":android:show_fragment","com.android.settings.development.WirelessDebuggingFragment");
   subSettings.putExtra(":android:no_headers",true);
   subSettings.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
   startActivity(subSettings);
   return;
  }catch(Exception ignored){}
  for(String action:new String[]{"android.settings.WIRELESS_DEBUGGING_SETTINGS",Settings.ACTION_APPLICATION_DEVELOPMENT_SETTINGS,Settings.ACTION_SETTINGS}){
   Intent i=new Intent(action);
   i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
   if(i.resolveActivity(getPackageManager())!=null){startActivity(i);return;}
  }
  showMessage("Mở Gỡ lỗi không dây","Hãy tự mở Cài đặt → Tuỳ chọn nhà phát triển → Gỡ lỗi không dây.",false);
 }
 private void external(String url)throws Exception {Uri uri=Uri.parse(url);if(!"https".equals(uri.getScheme())||uri.getHost()==null)throw new IOException("Liên kết không hợp lệ.");startActivity(new Intent(Intent.ACTION_VIEW,uri));}
 private void clipboard(String label,String text){((ClipboardManager)getSystemService(CLIPBOARD_SERVICE)).setPrimaryClip(ClipData.newPlainText(label,text));}
 private void maybeAutoSync(){if(!loaded||!resumed||autoSynced)return;try{JSONObject snapshot=LauncherService.snapshot(this);if(!snapshot.optBoolean("busy")){LauncherService.dispatch(this,"sync",new JSONObject());autoSynced=true;}}catch(RuntimeException error){showMessage("Chưa đồng bộ tự động","Hãy mở ứng dụng và bấm Đồng bộ GitHub để thử lại.",true);}}
 private void emitState(){event(Store.obj("type","state","data",LauncherService.snapshot(this)));}
 private void showMessage(String title,String message,boolean error){event(Store.obj("type","message","data",Store.obj("title",title,"message",message,"error",error)));}
 @Override public void event(JSONObject e){runOnUiThread(()->{if(web!=null&&loaded)web.evaluateJavascript("window.Stella&&window.Stella.onEvent(JSON.parse("+JSONObject.quote(e.toString())+"))",null);if("state".equals(e.optString("type"))){JSONObject s=e.optJSONObject("data");if(s!=null){JSONObject g=s.optJSONObject("github"),r=s.optJSONObject("receipt");if(g!=null&&"online".equals(g.optString("releaseStatus"))&&"none".equals(g.optString("launcherStatus")))LauncherUpdateNotice.clearIfCurrent(this,g.optString("repo")+"/"+g.optString("branch"));if(g!=null&&"online".equals(g.optString("releaseStatus"))&&g.optJSONObject("launcherUpdate")!=null)LauncherUpdateNotice.observe(this,g.optString("repo")+"/"+g.optString("branch"),g.optJSONObject("launcherUpdate"),g.optString("releaseNotes"),false);if(g!=null&&"online".equals(g.optString("releaseStatus"))&&"none".equals(g.optString("manifestStatus")))UpdateNotice.clearIfCurrent(this,g.optString("repo")+"/"+g.optString("branch"));if(g!=null&&"online".equals(g.optString("releaseStatus"))&&"available".equals(g.optString("manifestStatus")))UpdateNotice.observe(this,g.optString("repo")+"/"+g.optString("branch"),g.optString("translationVersion"),g.optString("releaseNotes"),r!=null&&r.optBoolean("present")?r.optString("version"):UpdateNotice.installed(this),false);}showUpdateNotice();}});}
 private void showUpdateNotice(){if(!resumed||!loaded||updateDialogShowing)return;String[] notice=UpdateNotice.pending(this);if(notice==null){showLauncherUpdateNotice();return;}updateDialogShowing=true;new AlertDialog.Builder(this).setTitle("Có bản Việt hoá "+notice[0]).setMessage(notice[1]+"\n\nMở phần cài đặt để kiểm tra khả năng cập nhật.").setNegativeButton("Đóng",(d,w)->UpdateNotice.dismiss(this,notice[0])).setNeutralButton("Tắt trong 24 giờ",(d,w)->UpdateNotice.snooze(this)).setOnCancelListener(d->UpdateNotice.dismiss(this,notice[0])).setOnDismissListener(d->{updateDialogShowing=false;showLauncherUpdateNotice();}).show();}
 private void showLauncherUpdateNotice(){if(!resumed||!loaded||updateDialogShowing)return;String[] notice=LauncherUpdateNotice.pending(this);if(notice==null)return;long code=Long.parseLong(notice[2]);updateDialogShowing=true;new AlertDialog.Builder(this).setTitle("Có launcher mới "+notice[0]).setMessage(notice[1]+"\n\nMở phần cập nhật launcher để kiểm tra và cài phiên bản mới.").setNegativeButton("Đóng",(d,w)->LauncherUpdateNotice.dismiss(this,code)).setNeutralButton("Tắt trong 24 giờ",(d,w)->LauncherUpdateNotice.snooze(this)).setOnCancelListener(d->LauncherUpdateNotice.dismiss(this,code)).setOnDismissListener(d->updateDialogShowing=false).show();}
 private void offerUpdateNotifications(){if(Build.VERSION.SDK_INT<33||checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)==PackageManager.PERMISSION_GRANTED)return;android.content.SharedPreferences p=getSharedPreferences("translation_notice",MODE_PRIVATE);if(p.getBoolean("permission_offered",false))return;p.edit().putBoolean("permission_offered",true).apply();new AlertDialog.Builder(this).setTitle("Thông báo bản Việt hoá mới").setMessage("Cho phép thông báo để nhận tin khi có bản Việt hoá mới, kể cả khi bạn không mở launcher.").setNegativeButton("Để sau",null).setPositiveButton("Cho phép",(d,w)->requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},72)).show();}
 @Override protected void onResume(){super.onResume();resumed=true;LauncherService.listen(this);if(loaded){emitState();maybeAutoSync();showUpdateNotice();}new Handler(Looper.getMainLooper()).postDelayed(()->{if(resumed&&!updateDialogShowing)offerUpdateNotifications();},1200);}
 @Override protected void onPause(){resumed=false;super.onPause();}
 @Override public void onRequestPermissionsResult(int request,String[] permissions,int[] grants){super.onRequestPermissionsResult(request,permissions,grants);if(request==71){String action=afterPermission;afterPermission=null;if(grants.length>0&&grants[0]==PackageManager.PERMISSION_GRANTED&&action!=null){LauncherService.dispatch(this,action,new JSONObject());if("startPairingNotification".equals(action))openWireless();}else showMessage("Chưa được phép hiện thông báo","Ghép đôi nhanh từ thông báo chưa dùng được. Bạn vẫn có thể nhập cổng và mã thủ công trong launcher hoặc cấp quyền thông báo trong Cài đặt ứng dụng.",true);}}
 @Override public void onBackPressed(){if(web==null||!loaded){super.onBackPressed();return;}web.evaluateJavascript("window.Stella?window.Stella.goBack():false",result->{if(!"true".equals(result))finish();});}
 @Override protected void onDestroy(){LauncherService.unlisten(this);if(web!=null){web.removeJavascriptInterface("StellaNative");web.destroy();web=null;}super.onDestroy();}

 private void openDeviceInfo(){
  for(String action:new String[]{Settings.ACTION_DEVICE_INFO_SETTINGS,"android.settings.DEVICE_INFO_SETTINGS",Settings.ACTION_SETTINGS}){
   try{
    Intent i=new Intent(action);
    i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
    if(i.resolveActivity(getPackageManager())!=null){startActivity(i);return;}
   }catch(Exception ignored){}
  }
  showMessage("Mở Cài đặt","Hãy mở Cài đặt hệ thống ➔ Thông tin điện thoại để chạm 7 lần bật Chế độ nhà phát triển.",false);
 }
 private void openDevSettings(){
  for(String action:new String[]{Settings.ACTION_APPLICATION_DEVELOPMENT_SETTINGS,"android.settings.APPLICATION_DEVELOPMENT_SETTINGS",Settings.ACTION_SETTINGS}){
   try{
    Intent i=new Intent(action);
    i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
    if(i.resolveActivity(getPackageManager())!=null){startActivity(i);return;}
   }catch(Exception ignored){}
  }
  showMessage("Mở Tuỳ chọn nhà phát triển","Hãy mở Cài đặt ➔ Tuỳ chọn nhà phát triển.",false);
 }
 private void showDevModeGuideDialog(){
  new AlertDialog.Builder(this)
   .setTitle("Chưa bật Tuỳ chọn nhà phát triển")
   .setMessage("Để sử dụng Gỡ lỗi không dây, bạn cần kích hoạt Chế độ nhà phát triển trước:\n\n1. Bấm nút 'Mở Thông tin điện thoại' bên dưới.\n2. Tìm dòng 'Số bản dựng' (Build Number) hoặc 'Phiên bản OS / HyperOS / MIUI'.\n3. Chạm liên tiếp 7 lần vào dòng đó cho đến khi máy báo 'Bạn đã là nhà phát triển!'.\n\nSau khi kích hoạt xong, quay lại ứng dụng để bắt đầu kết nối.")
   .setPositiveButton("Mở Thông tin điện thoại",(d,w)->openDeviceInfo())
   .setNeutralButton("Mở Cài đặt",(d,w)->{
    try{Intent i=new Intent(Settings.ACTION_SETTINGS);i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);startActivity(i);}catch(Exception ignored){}
   })
   .setNegativeButton("Đóng",null)
   .show();
 }
}
