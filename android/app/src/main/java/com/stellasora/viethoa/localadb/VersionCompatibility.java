package com.stellasora.viethoa.localadb;

/** Only explicitly declared versions match. Empty, wildcard and unknown values do not authorize a patch. */
final class VersionCompatibility {
 private VersionCompatibility(){}
 static boolean matches(String declared,String observed){
  if(declared==null||observed==null)return false;
  String actual=observed.trim();if(!valid(actual))return false;
  for(String version:declared.split("[,;|]")){
   String candidate=version.trim();
   if(!valid(candidate))continue;
   if(candidate.equals(actual))return true;
  }
  return false;
 }
 private static boolean valid(String value){return value.matches("[0-9][0-9A-Za-z_.-]*");}
 static boolean matchesBoth(String declaredGame,String declaredResource,String game,String resource){return matches(declaredGame,game)&&matches(declaredResource,resource);}
}
