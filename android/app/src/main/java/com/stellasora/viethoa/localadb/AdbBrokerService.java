package com.stellasora.viethoa.localadb;
import android.app.*;import android.content.*;import android.os.*;import org.json.*;import org.conscrypt.Conscrypt;import io.github.muntashirakon.adb.*;import java.io.*;import java.security.*;import java.security.cert.Certificate;import java.util.concurrent.*;import java.util.concurrent.atomic.AtomicBoolean;
/** App-private broker; its main handler enforces an absolute process deadline. */
public final class AdbBrokerService extends Service {
 private final ExecutorService worker=Executors.newSingleThreadExecutor();private final Handler main=new Handler(Looper.getMainLooper());private final AtomicBoolean busy=new AtomicBoolean();private long active;private Session session;
 private final Messenger messenger=new Messenger(new Handler(Looper.getMainLooper()){@Override public void handleMessage(Message m){accept(m);}});
 private static final class Session extends AbsAdbConnectionManager {final KeyMaterial keys;Session(KeyMaterial k){keys=k;setApi(Build.VERSION.SDK_INT);setTimeout(18,TimeUnit.SECONDS);setThrowOnUnauthorised(true);}@Override protected PrivateKey getPrivateKey(){return keys.privateKey;}@Override protected Certificate getCertificate(){return keys.certificate;}@Override protected String getDeviceName(){return "StellaSora_LocalADB";}}
 @Override public IBinder onBind(Intent i){return messenger.getBinder();}
 private void accept(Message message){
  if(message.sendingUid!=android.os.Process.myUid())return;Bundle b=message.getData();long id=b.getLong("request_id");String action=b.getString("action","");Messenger reply=message.replyTo;
  if(!busy.compareAndSet(false,true)){respond(reply,id,false,"ADB đang có thao tác.");return;}active=id;long duration=Math.max(1000,Math.min(125000,b.getLong("timeout_ms",25000)));
  Runnable deadline=()->{if(busy.get()&&active==id){respond(reply,id,false,"ADB quá thời hạn. Hãy kết nối lại.");killOwnBroker();}};main.postDelayed(deadline,duration);
  worker.execute(()->{boolean ok=false;String value;try{
   if(session==null){Security.insertProviderAt(Conscrypt.newProvider(),1);session=new Session(KeyMaterial.load(this));}JSONObject args=new JSONObject(b.getString("args","{}"));
   switch(action){
    case "pair":{String host=AdbClient.ownHost(args.getString("host"));int port=AdbClient.port(args.getInt("port"));String code=args.getString("code");if(!code.matches("[0-9]{6}"))throw new IOException("Mã cần 6 số.");if(!session.pair(host,port,code))throw new IOException("Ghép nối chưa thành công.");value="Đã ghép nối; chưa kết nối.";break;}
    case "connect":{String host=AdbClient.ownHost(args.getString("host"));int port=AdbClient.port(args.getInt("port"));if(session.isConnected())session.disconnect();if(!session.connect(host,port))throw new IOException("Chưa kết nối được ADB.");value="transport_connected";break;}
    case "exec":{if(!session.isConnected())throw new IOException("Chưa kết nối ADB.");String command=args.getString("command");if(command.length()>64000||command.indexOf(0)>=0)throw new IOException("Lệnh nội bộ vượt giới hạn.");value=readCommand(command,duration-800,args.getString("marker"));break;}
    case "disconnect":session.disconnect();value="Đã ngắt ADB.";break;
    default:throw new IOException("Thao tác ADB không hợp lệ.");
   }ok=true;
  }catch(Throwable e){value=action.equals("pair")?"Ghép nối thất bại. Kiểm tra cổng và mã 6 số mới trong Gỡ lỗi không dây.":Store.cleanError(e);}
  boolean result=ok;String output=value;main.post(()->{if(active!=id)return;main.removeCallbacks(deadline);busy.set(false);respond(reply,id,result,output);});});
 }
 private String readCommand(String command,long timeout,String marker)throws Exception {
  if(!marker.matches("STELLA_EXIT_[0-9a-f]{32}"))throw new IOException("Marker nội bộ không hợp lệ.");
  java.util.regex.Pattern complete=java.util.regex.Pattern.compile("(?:\\r?\\n)"+marker+"[0-9]+\\r?\\n");long end=SystemClock.elapsedRealtime()+Math.max(500,timeout);
  try(AdbStream stream=session.openStream("shell:"+command)){
   ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] buffer=new byte[8192];
   while(true){int n=stream.read(buffer,0,buffer.length);if(n<0)throw new IOException("ADB đóng trước phản hồi kết thúc.");if(n>0)out.write(buffer,0,n);if(out.size()>131072)throw new IOException("Đầu ra ADB vượt giới hạn 128 KiB của kênh nội bộ.");String data=out.toString("UTF-8");if(complete.matcher(data).find())return data;if(SystemClock.elapsedRealtime()>end)throw new IOException("Lệnh ADB quá thời hạn.");}
  }
 }
 private static void respond(Messenger to,long id,boolean ok,String value){if(to==null)return;try{Message m=Message.obtain();Bundle b=new Bundle();b.putLong("request_id",id);b.putBoolean("ok",ok);b.putString("value",value);m.setData(b);to.send(m);}catch(RemoteException ignored){}}
 private void killOwnBroker(){if(Application.getProcessName().equals(getPackageName()+":adb"))android.os.Process.killProcess(android.os.Process.myPid());}
 @Override public void onDestroy(){worker.shutdownNow();killOwnBroker();super.onDestroy();}
}
