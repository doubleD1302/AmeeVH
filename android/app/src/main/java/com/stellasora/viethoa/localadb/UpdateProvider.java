package com.stellasora.viethoa.localadb;
import android.content.*;import android.database.*;import android.net.Uri;import android.os.*;import android.provider.OpenableColumns;import java.io.*;
/** A single read-only, grant-scoped APK URI. No arbitrary file paths. */
public final class UpdateProvider extends ContentProvider {
 @Override public boolean onCreate(){return true;}
 private File file(Uri uri)throws FileNotFoundException{if(!"content".equals(uri.getScheme())||!(Store.APP+".updates").equals(uri.getAuthority())||!"/update.apk".equals(uri.getPath()))throw new FileNotFoundException("URI không hợp lệ.");File f=new File(getContext().getCacheDir(),"updates/update.apk");if(!f.isFile())throw new FileNotFoundException("APK chưa sẵn sàng.");return f;}
 @Override public ParcelFileDescriptor openFile(Uri u,String mode)throws FileNotFoundException{if(!"r".equals(mode))throw new FileNotFoundException("Chỉ đọc APK.");return ParcelFileDescriptor.open(file(u),ParcelFileDescriptor.MODE_READ_ONLY);}
 @Override public String getType(Uri u){return "application/vnd.android.package-archive";}
 @Override public Cursor query(Uri u,String[] projection,String selection,String[] args,String sort){try{File f=file(u);MatrixCursor cursor=new MatrixCursor(new String[]{OpenableColumns.DISPLAY_NAME,OpenableColumns.SIZE});cursor.addRow(new Object[]{"StellaSora_LocalADB_Update.apk",f.length()});return cursor;}catch(FileNotFoundException e){return null;}}
 @Override public Uri insert(Uri u,ContentValues v){throw new UnsupportedOperationException();}@Override public int update(Uri u,ContentValues v,String s,String[] a){throw new UnsupportedOperationException();}@Override public int delete(Uri u,String s,String[] a){throw new UnsupportedOperationException();}
}
