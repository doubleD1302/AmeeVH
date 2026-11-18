package com.stellasora.viethoa.localadb;
import android.content.Context;
import android.os.Build;
import android.os.StatFs;
import org.json.*;
import java.io.File;
import java.net.*;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.regex.*;
import javax.net.ssl.SSLException;

/**
 * Builds the copy-ready error report shown next to every error dialog.
 * Privacy: never includes ADB host/ports, pairing codes, device identifiers, bindings or URL query strings.
 */
final class ErrorReport {
 private static volatile String lastId="",lastText="";
 private ErrorReport(){}

 static String safeUrl(String address){
  try{URL u=new URL(address);return u.getProtocol()+"://"+u.getHost()+u.getPath();}catch(Exception e){return "(url không hợp lệ)";}
 }

 /** Stable machine-readable code. Prefers an explicit StellaException code anywhere in the cause chain. */
 static String classify(Throwable e){
  int depth=0;
  for(Throwable t=e;t!=null&&depth<8;t=t.getCause(),depth++)if(t instanceof StellaException)return ((StellaException)t).code;
  StringBuilder all=new StringBuilder();depth=0;Throwable root=e;
  for(Throwable t=e;t!=null&&depth<8;t=t.getCause(),depth++){if(t.getMessage()!=null)all.append(t.getMessage()).append('\n');root=t;}
  if(root instanceof UnknownHostException||root instanceof ConnectException||root instanceof SocketTimeoutException||root instanceof SSLException||root instanceof SocketException)return "E-NET";
  return classifyText(all.toString());
 }

 static String classifyText(String text){
  if(text==null)return "E-UNKNOWN";
  Matcher http=Pattern.compile("HTTP ([0-9]{3})").matcher(text);if(http.find())return "E-HTTP-"+http.group(1);
  if(text.contains("Phiên bản game đã khác"))return "E-VER-CHANGED";
  if(text.contains("Game đã cập nhật"))return "E-VER-CHANGED";
  if(text.contains("Hãy thoát Stella Sora"))return "E-GAME-RUNNING";
  if(text.contains("Không đủ bộ nhớ")||text.contains("Không đủ dung lượng")||text.contains("Bộ nhớ vùng game"))return "E-STORAGE";
  if(text.contains("SHA256")||text.contains("kích thước"))return "E-VERIFY";
  if(text.contains("quá thời hạn")||text.contains("vượt thời hạn"))return "E-TIMEOUT";
  if(text.contains("không khớp phiên bản")||text.contains("Gói Android không khớp"))return "E-PKG-MISMATCH";
  if(text.contains("Chưa có gói")||text.contains("gói bản dịch Android"))return "E-NO-PACKAGE";
  if(text.contains("Chưa kết nối Local ADB")||text.contains("Kết nối chưa được xác nhận")||text.contains("ADB"))return "E-ADB";
  if(text.contains("Tệp đã đổi")||text.contains("Tệp game đổi")||text.contains("Tệp đã thay đổi")||text.contains("đổi ngoài thao tác")||text.contains("Tệp đổi"))return "E-FILE-CHANGED";
  if(text.contains("Backup"))return "E-BACKUP";
  if(text.contains("nhật ký")||text.contains("Nhật ký"))return "E-JOURNAL";
  if(text.contains("Yêu cầu bị chặn")||text.contains("Tải bị chặn")||text.contains("không thuộc giao diện"))return "E-UI-BLOCKED";
  return "E-UNKNOWN";
 }

 private static String hint(String code){
  switch(code){
   case "E-DL-VERIFY":return "Tệp tải về khác kích thước/SHA256 so với bảng kê (manifest). Thường do URL trong manifest trỏ tới tệp của bản phát hành khác, hoặc tệp bị thay sau khi tạo manifest. So sánh contentLength/receivedBytes với expectedSize.";
   case "E-DL-OVERSIZE":return "Tệp trên máy chủ lớn hơn kích thước công bố. Kiểm tra contentLength và URL trong manifest.";
   case "E-DL-RANGE":return "Máy chủ trả dải byte nối tiếp không khớp yêu cầu. Hãy thử tải lại.";
   case "E-DL-TIMEOUT":return "Quá thời hạn tải tệp nhưng phần đã tải hợp lệ vẫn được giữ lại. Bấm thử lại để nối tiếp.";
   case "E-HTTP-403":case "E-HTTP-429":return "GitHub đang tạm giới hạn lượt gọi API theo IP mạng (thường gặp trên 4G CGNAT hoặc Wi-Fi chung). Chờ vài phút hoặc đổi mạng rồi thử lại.";
   case "E-VER-CHANGED":return "Game đã cập nhật sau lần cài trước nên bản sao lưu cũ không dùng để khôi phục. Cài lại bản dịch cho phiên bản game hiện tại.";
   case "E-GAME-RUNNING":return "Cần thoát hẳn Stella Sora rồi thử lại.";
   case "E-STORAGE":return "Thiếu dung lượng. Xem storage.* trong báo cáo.";
   case "E-NET":return "Lỗi mạng hoặc chứng chỉ. Kiểm tra Wi-Fi/VPN rồi thử lại.";
   case "E-PKG-MISMATCH":return "Gói trên GitHub không khai báo phiên bản game/tài nguyên đang cài trên máy.";
   case "E-FILE-CHANGED":return "Tệp game bị thay đổi ngoài thao tác của launcher (game vừa tự cập nhật?).";
   default:return "";
  }
 }

 private static JSONObject pick(JSONObject from,String... keys){
  JSONObject out=new JSONObject();if(from==null)return out;
  try{for(String k:keys)if(from.has(k))out.put(k,from.get(k));}catch(JSONException ignored){}
  return out;
 }

 private static JSONArray chain(Throwable e){
  JSONArray list=new JSONArray();int depth=0;
  for(Throwable t=e;t!=null&&depth<6;t=t.getCause(),depth++){
   try{
    JSONObject item=new JSONObject();item.put("class",t.getClass().getName());
    String m=t.getMessage();if(m!=null)item.put("message",m.length()>600?m.substring(0,600)+"…":m);
    if(t instanceof StellaException){item.put("code",((StellaException)t).code);item.put("details",((StellaException)t).details);}
    JSONArray frames=new JSONArray();StackTraceElement[] st=t.getStackTrace();
    for(StackTraceElement f:st){if(frames.length()>=8)break;if(f.getClassName().startsWith("com.stellasora"))frames.put(f.getClassName().replace("com.stellasora.viethoa.localadb.","")+"."+f.getMethodName()+":"+f.getLineNumber());}
    if(frames.length()==0)for(StackTraceElement f:st){if(frames.length()>=5)break;frames.put(f.getClassName()+"."+f.getMethodName()+":"+f.getLineNumber());}
    item.put("stack",frames);list.put(item);
   }catch(JSONException ignored){}
  }
  return list;
 }

 private static long free(File f){try{return f==null?-1:new StatFs(f.getAbsolutePath()).getAvailableBytes();}catch(Exception e){return -1;}}

 /** Never throws. {@code snapshot} is the launcher state at failure time (may be null). */
 static JSONObject build(Context c,String action,String title,String message,Throwable e,String forcedCode,JSONObject snapshot){
  JSONObject r=new JSONObject();
  try{
   String code=forcedCode!=null?forcedCode:e!=null?classify(e):classifyText(message);
   long now=System.currentTimeMillis();SimpleDateFormat iso=new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ssZ",Locale.ROOT);
   r.put("code",code);r.put("reportId",Long.toString(now,36).toUpperCase(Locale.ROOT));r.put("time",iso.format(new Date(now)));
   r.put("title",title);r.put("message",message);r.put("action",action==null?"":action);
   String hint=hint(code);if(!hint.isEmpty())r.put("hint",hint);
   JSONObject s=snapshot==null?new JSONObject():snapshot;
   r.put("lastStep",s.optJSONObject("progress")==null?"":s.getJSONObject("progress").optString("label"));
   r.put("phase",s.optString("phase"));
   r.put("app",pick(s.optJSONObject("app"),"versionName","versionCode","variant"));
   r.put("android",Store.obj("release",Build.VERSION.RELEASE,"sdk",Build.VERSION.SDK_INT,"model",Build.MANUFACTURER+" "+Build.MODEL));
   r.put("game",pick(s.optJSONObject("game"),"installed","package","versionsKnown","gameVersion","resourceVersion","root","reason"));
   r.put("github",pick(s.optJSONObject("github"),"repo","branch","releaseStatus","releaseVersion","manifestStatus","translationVersion","manifestSha256","announcementStatus","message"));
   r.put("payload",pick(s.optJSONObject("payload"),"available","compatible","updateAvailable","version","fileCount","reason"));
   r.put("receipt",pick(s.optJSONObject("receipt"),"present","version","manifestSha256","files","stale","installedGameVersion","installedResourceVersion"));
   r.put("recovery",pick(s.optJSONObject("recovery"),"pending","message"));
   JSONObject adb=s.optJSONObject("adb");r.put("adb",Store.obj("connected",adb!=null&&adb.optBoolean("connected"),"hasIdentity",adb!=null&&adb.optBoolean("hasIdentity"),"status",adb==null?"":adb.optString("status")));
   JSONObject storage=Store.obj("internalFreeBytes",free(c.getFilesDir()),"externalFreeBytes",free(c.getExternalFilesDir(null)));r.put("storage",storage);
   try{File active=Store.internal(c,"state/active_journal.json");if(active.isFile()){JSONObject j=Store.read(active);r.put("journal",Store.obj("state",j.optString("state"),"id",j.optString("id"),"version",j.optString("version"),"gameVersion",j.optString("gameVersion"),"resourceVersion",j.optString("resourceVersion"),"files",j.optJSONArray("files")==null?0:j.getJSONArray("files").length(),"pendingFile",j.optString("pending")));}}catch(Exception ignored){}
   r.put("errorChain",e==null?new JSONArray():chain(e));
  }catch(Exception ignored){}
  return r;
 }

 /** Remembers the report (memory + disk) so the copy button can fetch it by id. Returns the same object. */
 static JSONObject record(Context c,JSONObject report){
  try{
   lastId=report.optString("reportId");
   lastText=text(report);
   Store.write(Store.internal(c,"state/last_error.json"),report);
  }catch(Exception ignored){}
  return report;
 }

 static String text(JSONObject report){
  try{return "STELLA SORA VIỆT HOÁ — MÃ LỖI "+report.optString("code")+" (#"+report.optString("reportId")+")\n"+report.toString(2);}catch(JSONException e){return report.toString();}
 }

 /** Text of the report with the given id, or the latest one when id is empty or unknown. Null when none exists. */
 static String find(Context c,String id){
  if(!lastText.isEmpty()&&(id==null||id.isEmpty()||id.equals(lastId)))return lastText;
  try{File f=Store.internal(c,"state/last_error.json");if(f.isFile()){JSONObject r=Store.read(f);if(id==null||id.isEmpty()||id.equals(r.optString("reportId")))return text(r);}}catch(Exception ignored){}
  return lastText.isEmpty()?null:lastText;
 }

 /** One-line summary of the last error for the diagnostics report. */
 static JSONObject lastSummary(Context c){
  try{File f=Store.internal(c,"state/last_error.json");if(f.isFile())return pick(Store.read(f),"code","reportId","time","action","message");}catch(Exception ignored){}
  return new JSONObject();
 }

 /** Adds the report identifiers to a message event payload. */
 static JSONObject attach(JSONObject data,JSONObject report){
  try{if(report!=null){data.put("code",report.optString("code"));data.put("reportId",report.optString("reportId"));}}catch(JSONException ignored){}
  return data;
 }
}
