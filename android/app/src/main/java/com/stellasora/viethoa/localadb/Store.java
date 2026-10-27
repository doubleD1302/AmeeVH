package com.stellasora.viethoa.localadb;
import android.content.Context;
import android.util.AtomicFile;
import org.json.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;
final class Store {
 static final String GAME="com.YoStarEN.StellaSora", APP="com.stellasora.viethoa.localadb", REPO="doubleD1302/AmeeVH";
 static JSONObject obj(Object... a) { JSONObject j=new JSONObject();try{for(int i=0;i<a.length;i+=2)j.put((String)a[i],a[i+1]);}catch(JSONException e){throw new IllegalStateException(e);}return j; }
 static byte[] readAll(InputStream in,int limit)throws IOException{ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] b=new byte[32768];int n;while((n=in.read(b))!=-1){out.write(b,0,n);if(out.size()>limit)throw new IOException("Dữ liệu quá lớn.");}return out.toByteArray();}
 static String text(File f) throws IOException {try(InputStream i=new FileInputStream(f)){return new String(readAll(i,16777216),StandardCharsets.UTF_8);}}
 static JSONObject read(File f) throws Exception {return new JSONObject(text(f));}
 static void write(File f,JSONObject j) throws IOException {File p=f.getParentFile();if(!p.isDirectory()&&!p.mkdirs())throw new IOException("Không tạo được thư mục trạng thái.");AtomicFile a=new AtomicFile(f);FileOutputStream o=null;try{o=a.startWrite();o.write(j.toString().getBytes(StandardCharsets.UTF_8));a.finishWrite(o);}catch(IOException e){if(o!=null)a.failWrite(o);throw e;}}
 static String hash(File f) throws Exception {MessageDigest d=MessageDigest.getInstance("SHA-256");try(InputStream i=new FileInputStream(f)){byte[] b=new byte[131072];int n;while((n=i.read(b))!=-1)d.update(b,0,n);}return hex(d.digest());}
 static String digest(String s) throws Exception {return hex(MessageDigest.getInstance("SHA-256").digest(s.getBytes(StandardCharsets.UTF_8)));}
 static String hex(byte[] b){StringBuilder s=new StringBuilder();for(byte x:b)s.append(String.format(Locale.ROOT,"%02x",x));return s.toString();}
 static File internal(Context c,String name){return new File(c.getFilesDir(),name);}
 static File external(Context c,String name) throws IOException {File b=c.getExternalFilesDir(null);if(b==null)throw new IOException("Chưa truy cập được bộ nhớ ngoài của ứng dụng.");File f=new File(b,name);if(!f.isDirectory()&&!f.mkdirs())throw new IOException("Không tạo được vùng tải và sao lưu.");if(!f.getCanonicalPath().startsWith(b.getCanonicalPath()+"/"))throw new IOException("Vùng lưu vượt phạm vi ứng dụng.");return f;}
 static JSONObject defaults(){return obj("repo",REPO,"branch","main","host","127.0.0.1","connection_port",0);}
 static JSONObject config(Context c)throws Exception{File f=internal(c,"config.json");return f.isFile()?read(f):defaults();}
 static void validateConfig(JSONObject j)throws Exception {String repo=j.optString("repo"),branch=j.optString("branch");if(!repo.matches("[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")||repo.contains(".."))throw new IOException("Kho GitHub cần có dạng tài-khoản/tên-kho.");if(branch.trim().isEmpty()||branch.length()>150||branch.contains("..")||branch.matches(".*[\\x00-\\x20~^:?*\\\\].*"))throw new IOException("Nhánh GitHub không hợp lệ.");}
 static JSONObject asset(Context c,String name)throws Exception{try(InputStream i=c.getAssets().open("ui/"+name)){return new JSONObject(new String(readAll(i,4194304),StandardCharsets.UTF_8));}}
 static String cleanError(Throwable e){String s=e.getMessage();return s==null?e.getClass().getSimpleName():s.substring(0,Math.min(700,s.length()));}
 static String q(String s){if(s.indexOf('\0')>=0||s.indexOf('\n')>=0||s.indexOf('\r')>=0)throw new IllegalArgumentException("Đường dẫn chứa ký tự điều khiển.");return "'"+s.replace("'","'\\''")+"'";}
}
