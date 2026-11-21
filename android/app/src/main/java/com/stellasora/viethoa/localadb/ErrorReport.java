package com.stellasora.viethoa.localadb;
import android.content.Context;
import android.net.ConnectivityManager;
import android.net.LinkProperties;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.os.Build;
import android.os.Looper;
import android.os.StatFs;
import android.os.SystemClock;
import android.provider.Settings;
import org.json.*;
import java.io.File;
import java.net.*;
import java.text.SimpleDateFormat;
import java.util.*;

/**
 * Builds the plain-language, copy-ready error report shown with every error dialog.
 * Privacy: never includes ADB host/ports, pairing codes, device identifiers, bindings or URL query strings.
 */
final class ErrorReport {
 private static volatile String lastId="",lastText="";
 private static volatile JSONObject lastReport=null;
 private ErrorReport(){}

 static String safeUrl(String address){
  try{URL u=new URL(address);return u.getProtocol()+"://"+u.getHost()+u.getPath();}catch(Exception e){return "(url không hợp lệ)";}
 }

 /** Stable machine-readable code. Prefers an explicit StellaException code anywhere in the cause chain. */
 static String classify(Throwable e){return ErrorCatalog.classify(e);}
 static String classifyText(String text){return ErrorCatalog.classifyText(text);}

 /** Developer-only notes appended to the report (the user-facing explanation comes from ErrorCatalog). */
 private static String hint(String code){
  switch(code){
   case "E-DL-VERIFY":return "Tệp tải về khác kích thước/SHA256 so với bảng kê (manifest). Thường do URL trong manifest trỏ tới tệp của bản phát hành khác, hoặc tệp bị thay sau khi tạo manifest. So sánh contentLength/receivedBytes với expectedSize.";
   case "E-DL-OVERSIZE":return "Tệp trên máy chủ lớn hơn kích thước công bố. Kiểm tra contentLength và URL trong manifest.";
   case "E-DL-RANGE":return "Máy chủ trả dải byte nối tiếp không khớp yêu cầu.";
   case "E-HTTP-403":case "E-HTTP-429":return "GitHub giới hạn lượt gọi API theo IP mạng (thường gặp trên 4G CGNAT hoặc Wi-Fi chung).";
   case "E-PKG-MISMATCH":return "Gói trên GitHub không khai báo phiên bản game/tài nguyên đang cài trên máy. So sánh payload.* với game.* trong báo cáo.";
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

 // ------------------------------------------------------------------ network diagnosis
 /** How the phone is connected (type, validated, private DNS). No addresses or identifiers. */
 static JSONObject networkInfo(Context c){
  JSONObject o=new JSONObject();
  try{
   o.put("airplane",Settings.Global.getInt(c.getContentResolver(),Settings.Global.AIRPLANE_MODE_ON,0)==1);
   ConnectivityManager cm=(ConnectivityManager)c.getSystemService(Context.CONNECTIVITY_SERVICE);
   Network n=cm==null?null:cm.getActiveNetwork();
   if(n==null){o.put("active",false);return o;}
   o.put("active",true);
   NetworkCapabilities nc=cm.getNetworkCapabilities(n);
   if(nc!=null){
    JSONArray transports=new JSONArray();
    if(nc.hasTransport(NetworkCapabilities.TRANSPORT_WIFI))transports.put("wifi");
    if(nc.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR))transports.put("cellular");
    if(nc.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET))transports.put("ethernet");
    if(nc.hasTransport(NetworkCapabilities.TRANSPORT_VPN))transports.put("vpn");
    o.put("transports",transports);
    o.put("internet",nc.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET));
    o.put("validated",nc.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED));
    o.put("captivePortal",nc.hasCapability(NetworkCapabilities.NET_CAPABILITY_CAPTIVE_PORTAL));
    o.put("metered",!nc.hasCapability(NetworkCapabilities.NET_CAPABILITY_NOT_METERED));
   }
   LinkProperties lp=cm.getLinkProperties(n);
   if(lp!=null){
    o.put("privateDns",lp.isPrivateDnsActive());
    String name=lp.getPrivateDnsServerName();if(name!=null&&!name.isEmpty())o.put("privateDnsHost",name);
   }
   o.put("dataSaver",cm.getRestrictBackgroundStatus()==ConnectivityManager.RESTRICT_BACKGROUND_STATUS_ENABLED);
  }catch(Throwable t){try{o.put("error",t.getClass().getSimpleName());}catch(JSONException ignored){}}
  return o;
 }

 private static final class HostResult{volatile String dns="pending",ip="",tcp="pending",detail="";volatile long ms=-1;}

 private static String reason(Throwable t){String m=t.getMessage();return t.getClass().getSimpleName()+(m==null||m.isEmpty()?"":" ("+(m.length()>80?m.substring(0,80):m)+")");}

 /** DNS + TCP:443 for GitHub's hosts and a neutral control, bounded to ~8 s. Never call on the main thread. */
 static JSONObject probe(){
  final String[] hosts={"api.github.com","raw.githubusercontent.com","github.com"};
  final long start=SystemClock.elapsedRealtime(),end=start+8000;
  final Map<String,HostResult> results=new LinkedHashMap<>();
  final List<Thread> threads=new ArrayList<>();
  for(final String host:hosts){
   final HostResult r=new HostResult();results.put(host,r);
   Thread th=new Thread(()->{
    try{r.ip=InetAddress.getByName(host).getHostAddress();r.dns="ok";}catch(Throwable t){r.dns="fail";r.tcp="skip";r.detail=reason(t);return;}
    long t1=SystemClock.elapsedRealtime();
    try(Socket s=new Socket()){s.connect(new InetSocketAddress(r.ip,443),3500);r.tcp="ok";r.ms=SystemClock.elapsedRealtime()-t1;}
    catch(Throwable t){r.tcp="fail";r.detail=reason(t);r.ms=SystemClock.elapsedRealtime()-t1;}
   },"probe-"+host);
   th.setDaemon(true);th.start();threads.add(th);
  }
  final String[] control={"pending","pending"};   // [dns, tcp]
  Thread cd=new Thread(()->{try{InetAddress.getByName("www.microsoft.com");control[0]="ok";}catch(Throwable t){control[0]="fail";}},"probe-ctl-dns");
  Thread ct=new Thread(()->{try(Socket s=new Socket()){s.connect(new InetSocketAddress("1.1.1.1",443),3500);control[1]="ok";}catch(Throwable t){control[1]="fail";}},"probe-ctl-tcp");
  cd.setDaemon(true);ct.setDaemon(true);cd.start();ct.start();threads.add(cd);threads.add(ct);
  for(Thread th:threads){long left=end-SystemClock.elapsedRealtime();if(left>0){try{th.join(left);}catch(InterruptedException ie){Thread.currentThread().interrupt();break;}}}
  JSONObject out=new JSONObject();
  try{
   JSONObject hostJson=new JSONObject();boolean allOk=true,dnsFail=false;StringBuilder failed=new StringBuilder();
   for(Map.Entry<String,HostResult> e:results.entrySet()){
    HostResult r=e.getValue();
    if("pending".equals(r.dns)){r.dns="fail";r.tcp="skip";r.detail="không trả lời kịp (quá thời gian chờ DNS)";}
    else if("pending".equals(r.tcp)){r.tcp="fail";r.detail="không kết nối kịp (quá thời gian chờ)";}
    hostJson.put(e.getKey(),Store.obj("dns",r.dns,"ip",r.ip,"tcp",r.tcp,"ms",r.ms,"detail",r.detail));
    if(!"ok".equals(r.tcp)){allOk=false;if(failed.length()>0)failed.append(", ");failed.append(e.getKey());}
    if(!"ok".equals(r.dns))dnsFail=true;
   }
   if("pending".equals(control[0]))control[0]="fail";
   if("pending".equals(control[1]))control[1]="fail";
   boolean cDns="ok".equals(control[0]),cTcp="ok".equals(control[1]);
   String verdict,text;
   if(allOk){verdict="ok";text="Lúc kiểm tra, điện thoại kết nối tới GitHub bình thường. Lỗi có thể chỉ xảy ra thoáng qua; hãy thử lại.";}
   else if(!cDns&&!cTcp){verdict="offline";text="Điện thoại đang không có Internet: ngay cả điểm kiểm tra chung cũng không kết nối được. Hãy kiểm tra Wi-Fi/dữ liệu di động.";}
   else if(dnsFail&&cDns){verdict="dns_blocked";text="Internet vẫn hoạt động nhưng không tra được địa chỉ ("+failed+"). GitHub có thể bị chặn ở DNS của mạng bạn; thử đổi mạng, đổi DNS riêng tư hoặc dùng VPN.";}
   else if(dnsFail){verdict="dns_broken";text="Điện thoại vẫn ra được Internet qua địa chỉ IP nhưng DNS đang hỏng, nên không tìm ra GitHub. Hãy đổi mạng hoặc đổi DNS riêng tư.";}
   else{verdict="blocked";text="Internet vẫn hoạt động nhưng kết nối tới GitHub ("+failed+") bị chặn hoặc quá chậm. Hãy kiểm tra VPN/tường lửa hoặc đổi mạng.";}
   out.put("hosts",hostJson);out.put("control",Store.obj("dns",control[0],"tcp1111",control[1]));
   out.put("verdict",verdict);out.put("verdictText",text);out.put("durationMs",SystemClock.elapsedRealtime()-start);
  }catch(JSONException ignored){}
  return out;
 }

 /** Sentence summarising the connectivity checks, or empty when there is nothing useful to add. */
 private static String networkVerdict(JSONObject net,JSONObject probe){
  if(net!=null&&net.optBoolean("airplane"))return "Đang bật chế độ máy bay. Hãy tắt chế độ máy bay rồi thử lại.";
  if(net!=null&&net.has("active")&&!net.optBoolean("active"))return "Điện thoại chưa kết nối mạng nào (tắt Wi-Fi/dữ liệu di động hoặc mất sóng).";
  if(net!=null&&net.optBoolean("captivePortal"))return "Wi-Fi đang yêu cầu đăng nhập (trang đăng nhập Wi-Fi công cộng). Hãy mở trình duyệt và đăng nhập.";
  if(net!=null&&net.has("validated")&&!net.optBoolean("validated"))return "Đã nối mạng nhưng Android báo mạng chưa ra được Internet. Hãy kiểm tra Wi-Fi/dữ liệu di động hoặc đổi mạng.";
  return probe==null?"":probe.optString("verdictText");
 }

 // ------------------------------------------------------------------ report
 /** Never throws. {@code snapshot} is the launcher state at failure time (may be null). */
 static JSONObject build(Context c,String action,String title,String message,Throwable e,String forcedCode,JSONObject snapshot){
  JSONObject r=new JSONObject();
  try{
   String code=forcedCode!=null?forcedCode:e!=null?classify(e):classifyText(message);
   ErrorCatalog.Entry entry=ErrorCatalog.lookup(code);
   long now=System.currentTimeMillis();SimpleDateFormat iso=new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ssZ",Locale.ROOT);
   r.put("code",code);r.put("reportId",Long.toString(now,36).toUpperCase(Locale.ROOT));r.put("time",iso.format(new Date(now)));
   r.put("title",title);r.put("message",message);r.put("action",action==null?"":action);
   r.put("errorTitle",entry.title);r.put("level",entry.level);
   JSONArray steps=new JSONArray();for(String s:entry.steps)steps.put(s);r.put("steps",steps);
   String explain=entry.summary;
   if(entry.network){
    JSONObject net=networkInfo(c);r.put("network",net);
    JSONObject probe=Looper.myLooper()==Looper.getMainLooper()?null:probe();   // network on the main thread would crash
    if(probe!=null)r.put("probe",probe);
    String verdict=networkVerdict(net,probe);
    if(!verdict.isEmpty())explain+="\n\nKiểm tra tự động: "+verdict;
   }
   r.put("explain",explain);
   String hint=hint(code);if(!hint.isEmpty())r.put("hint",hint);
   JSONObject s=snapshot==null?new JSONObject():snapshot;
   r.put("lastStep",s.optJSONObject("progress")==null?"":s.getJSONObject("progress").optString("label"));
   r.put("phase",s.optString("phase"));
   r.put("app",pick(s.optJSONObject("app"),"versionName","versionCode","variant"));
   r.put("android",Store.obj("release",Build.VERSION.RELEASE,"sdk",Build.VERSION.SDK_INT,"model",Build.MANUFACTURER+" "+Build.MODEL));
   r.put("game",pick(s.optJSONObject("game"),"installed","package","versionsKnown","gameVersion","resourceVersion","root","reason"));
   r.put("github",pick(s.optJSONObject("github"),"repo","branch","releaseStatus","releaseVersion","manifestStatus","translationVersion","manifestSha256","announcementStatus","announcementError","errorCode","errorStage","errorRaw","message"));
   r.put("payload",pick(s.optJSONObject("payload"),"available","compatible","updateAvailable","version","fileCount","reason","reasonCode"));
   r.put("receipt",pick(s.optJSONObject("receipt"),"present","version","manifestSha256","files","stale","installedGameVersion","installedResourceVersion"));
   r.put("recovery",pick(s.optJSONObject("recovery"),"pending","message"));
   JSONObject adb=s.optJSONObject("adb");r.put("adb",Store.obj("connected",adb!=null&&adb.optBoolean("connected"),"hasIdentity",adb!=null&&adb.optBoolean("hasIdentity"),"status",adb==null?"":adb.optString("status")));
   JSONObject storage=Store.obj("internalFreeBytes",free(c.getFilesDir()),"externalFreeBytes",free(c.getExternalFilesDir(null)));r.put("storage",storage);
   try{File active=Store.internal(c,"state/active_journal.json");if(active.isFile()){JSONObject j=Store.read(active);r.put("journal",Store.obj("state",j.optString("state"),"id",j.optString("id"),"version",j.optString("version"),"gameVersion",j.optString("gameVersion"),"resourceVersion",j.optString("resourceVersion"),"files",j.optJSONArray("files")==null?0:j.getJSONArray("files").length(),"pendingFile",j.optString("pending")));}}catch(Exception ignored){}
   r.put("errorChain",e==null?new JSONArray():chain(e));
  }catch(Exception ignored){}
  return r;
 }

 /** Report for a known situation (no exception), e.g. "why is the install button blocked?". */
 static JSONObject explain(Context c,String code,String action,JSONObject snapshot){
  ErrorCatalog.Entry e=ErrorCatalog.lookup(code);
  return build(c,action,e.title,e.summary,null,e.code,snapshot);
 }

 /** Remembers the report (memory + disk) so the copy button can fetch it by id. Returns the same object. */
 static JSONObject record(Context c,JSONObject report){
  try{
   lastId=report.optString("reportId");
   lastReport=report;
   lastText=text(report);
   Store.write(Store.internal(c,"state/last_error.json"),report);
  }catch(Exception ignored){}
  return report;
 }

 private static String numbered(JSONArray steps){
  StringBuilder sb=new StringBuilder();
  for(int i=0;i<steps.length();i++)sb.append("  ").append(i+1).append(". ").append(steps.optString(i)).append('\n');
  return sb.toString();
 }

 /** Human-readable header followed by the full JSON, ready to paste to the developers. */
 static String text(JSONObject r){
  try{
   JSONObject android=r.optJSONObject("android"),app=r.optJSONObject("app");
   StringBuilder sb=new StringBuilder();
   sb.append("STELLA SORA VIỆT HOÁ — MÃ LỖI ").append(r.optString("code")).append(" (#").append(r.optString("reportId")).append(")\n");
   sb.append("Nền tảng: Android ").append(android==null?"?":android.optString("release")).append(" (SDK ").append(android==null?"?":android.optString("sdk")).append(") · ")
     .append(android==null?"?":android.optString("model")).append(" · Launcher ").append(app==null?"?":app.optString("versionName")).append(" (").append(app==null?"?":app.optString("versionCode")).append(")\n");
   sb.append("Thời gian: ").append(r.optString("time")).append('\n');
   sb.append("Đang làm: ").append(r.optString("action").isEmpty()?"(không rõ)":r.optString("action")).append('\n');
   sb.append("Bước cuối: ").append(r.optString("lastStep").isEmpty()?"(không có)":r.optString("lastStep")).append("\n\n");
   sb.append("Tiêu đề: ").append(r.optString("errorTitle")).append('\n');
   sb.append("Giải thích: ").append(r.optString("explain")).append('\n');
   JSONArray steps=r.optJSONArray("steps");
   if(steps!=null&&steps.length()>0)sb.append("Cách xử lý đã gợi ý:\n").append(numbered(steps));
   sb.append("Thông báo gốc: ").append(r.optString("message").isEmpty()?"(không có)":r.optString("message")).append('\n');
   JSONObject probe=r.optJSONObject("probe");
   if(probe!=null){
    sb.append("\n--- Đo kết nối lúc lỗi ---\n");
    JSONObject hosts=probe.optJSONObject("hosts");
    if(hosts!=null){Iterator<String> it=hosts.keys();while(it.hasNext()){String h=it.next();JSONObject v=hosts.optJSONObject(h);if(v==null)continue;
     sb.append("  ").append(h).append(": DNS ").append("ok".equals(v.optString("dns"))?"ok "+v.optString("ip"):"LỖI").append("; TCP:443 ").append(v.optString("tcp")).append(v.optString("detail").isEmpty()?"":" — "+v.optString("detail")).append('\n');}}
    JSONObject ctl=probe.optJSONObject("control");
    if(ctl!=null)sb.append("  Điểm đối chứng: DNS ").append(ctl.optString("dns")).append("; TCP 1.1.1.1:443 ").append(ctl.optString("tcp1111")).append('\n');
    sb.append("  Kết luận tự động (").append(probe.optString("verdict")).append("): ").append(probe.optString("verdictText")).append('\n');
   }
   sb.append("\n--- Chi tiết kỹ thuật (JSON) ---\n").append(r.toString(2));
   return sb.toString();
  }catch(JSONException e){return r.toString();}
 }

 /** Text of the report with the given id, or the latest one when id is empty or unknown. Null when none exists. */
 static String find(Context c,String id){
  if(!lastText.isEmpty()&&(id==null||id.isEmpty()||id.equals(lastId)))return lastText;
  try{File f=Store.internal(c,"state/last_error.json");if(f.isFile()){JSONObject r=Store.read(f);if(id==null||id.isEmpty()||id.equals(r.optString("reportId")))return text(r);}}catch(Exception ignored){}
  return lastText.isEmpty()?null:lastText;
 }

 /** The report object with the given id (memory first, then disk). Null when unknown. */
 static JSONObject findReport(Context c,String id){
  JSONObject m=lastReport;
  if(m!=null&&(id==null||id.isEmpty()||id.equals(m.optString("reportId"))))return m;
  try{File f=Store.internal(c,"state/last_error.json");if(f.isFile()){JSONObject r=Store.read(f);if(id==null||id.isEmpty()||id.equals(r.optString("reportId")))return r;}}catch(Exception ignored){}
  return null;
 }

 /** One-line summary of the last error for the diagnostics report. */
 static JSONObject lastSummary(Context c){
  try{File f=Store.internal(c,"state/last_error.json");if(f.isFile())return pick(Store.read(f),"code","reportId","time","action","message");}catch(Exception ignored){}
  return new JSONObject();
 }

 /** Adds the explanation and report identifiers to a message event payload. */
 static JSONObject attach(JSONObject data,JSONObject report){
  try{
   if(report!=null){
    data.put("code",report.optString("code"));data.put("reportId",report.optString("reportId"));
    data.put("errorTitle",report.optString("errorTitle"));data.put("explain",report.optString("explain"));
    data.put("level",report.optString("level"));
    if(report.optJSONArray("steps")!=null)data.put("steps",report.getJSONArray("steps"));
   }
  }catch(JSONException ignored){}
  return data;
 }
}
