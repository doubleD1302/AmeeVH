package com.stellasora.viethoa.localadb;
import org.json.*;
import java.io.IOException;

/** IOException that carries a stable error code and structured details for the copyable error report. */
final class StellaException extends IOException implements ErrorCatalog.Coded {
 final String code;
 @Override public String code(){return code;}
 final JSONObject details=new JSONObject();
 StellaException(String code,String message,Throwable cause,Object... keyValues){
  super(message,cause);
  this.code=code;
  try{for(int i=0;i+1<keyValues.length;i+=2)details.put((String)keyValues[i],keyValues[i+1]);}catch(JSONException ignored){}
 }
}
