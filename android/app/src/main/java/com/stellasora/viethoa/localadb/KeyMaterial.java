package com.stellasora.viethoa.localadb;
import android.content.Context;
import java.io.*;
import java.math.BigInteger;
import java.nio.channels.FileLock;
import java.security.*;
import java.security.cert.*;
import java.security.interfaces.RSAPublicKey;
import java.security.spec.PKCS8EncodedKeySpec;
import java.util.Date;
import javax.security.auth.x500.X500Principal;
import org.bouncycastle.jce.provider.BouncyCastleProvider;
import org.bouncycastle.x509.X509V3CertificateGenerator;
final class KeyMaterial {
 final PrivateKey privateKey;final X509Certificate certificate;
 private KeyMaterial(PrivateKey p,X509Certificate c){privateKey=p;certificate=c;}
 static KeyMaterial load(Context context)throws Exception{
  File dir=Store.internal(context,"local_adb_identity");if(!dir.isDirectory()&&!dir.mkdirs())throw new IOException("Không tạo được vùng khóa ADB riêng.");
  try(RandomAccessFile lock=new RandomAccessFile(new File(dir,"identity.lock"),"rw");FileLock ignored=lock.getChannel().lock()){
   File key=new File(dir,"private.pk8"),cert=new File(dir,"certificate.der");
   if(key.isFile()&&cert.isFile()){
    PrivateKey p=KeyFactory.getInstance("RSA").generatePrivate(new PKCS8EncodedKeySpec(java.nio.file.Files.readAllBytes(key.toPath())));
    X509Certificate c=(X509Certificate)CertificateFactory.getInstance("X.509",new BouncyCastleProvider()).generateCertificate(new FileInputStream(cert));c.checkValidity();
    if(!(((RSAPublicKey)c.getPublicKey()).getModulus().bitLength()>=2048))throw new IOException("Khóa ADB không đạt yêu cầu.");
    Signature s=Signature.getInstance("SHA256withRSA");byte[] challenge="stella-local-adb-key-check".getBytes(java.nio.charset.StandardCharsets.UTF_8);s.initSign(p);s.update(challenge);byte[] sig=s.sign();s.initVerify(c.getPublicKey());s.update(challenge);if(!s.verify(sig))throw new IOException("Khóa và chứng thư ADB không khớp.");return new KeyMaterial(p,c);
   }
   if(key.exists()||cert.exists())throw new IOException("Khóa ADB riêng đang thiếu một phần. Không tự thay khóa đã ghép nối.");
   KeyPairGenerator generator=KeyPairGenerator.getInstance("RSA");generator.initialize(2048);KeyPair pair=generator.generateKeyPair();long now=System.currentTimeMillis();
   X509V3CertificateGenerator g=new X509V3CertificateGenerator();X500Principal principal=new X500Principal("CN=StellaSora_LocalADB");g.setIssuerDN(principal);g.setSubjectDN(principal);g.setSerialNumber(new BigInteger(128,new SecureRandom()).abs().add(BigInteger.ONE));g.setNotBefore(new Date(now-86400000L));g.setNotAfter(new Date(now+3650L*86400000L));g.setPublicKey(pair.getPublic());g.setSignatureAlgorithm("SHA256withRSA");X509Certificate c=g.generate(pair.getPrivate());
   try(FileOutputStream o=new FileOutputStream(key)){o.write(pair.getPrivate().getEncoded());o.getFD().sync();}key.setReadable(false,false);key.setWritable(false,false);key.setReadable(true,true);key.setWritable(true,true);
   try(FileOutputStream o=new FileOutputStream(cert)){o.write(c.getEncoded());o.getFD().sync();}return new KeyMaterial(pair.getPrivate(),c);
  }
 }
}
