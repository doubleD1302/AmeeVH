"""Build-only Android candidate; never invokes adb, emulator, app, install or tests."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,shutil,time
root=Path(__file__).resolve().parent;project=root.parent
work=project/'work/build_android_launcher_r02';report=project/'reports/android_launcher_layout_20261027_r02/implementer';dist=project/'dist/android_launcher_candidate_r02'
gradle=Path(r'C:\Users\chann\.gradle\wrapper\dists\gradle-9.3.1-all\9ot9r568e8zfvvd4mn8rbu1j0\gradle-9.3.1\bin\gradle.bat')
jbr=Path(r'C:\Program Files\Android\Android Studio\jbr');sdk=Path(r'C:\Users\chann\AppData\Local\Android\Sdk');shared=Path(r'C:\Users\chann\.gradle\caches')
for folder in (work,report,dist,work/'tmp',work/'gradle-home',work/'android-user'):folder.mkdir(parents=True,exist_ok=True)
output=dist/'StellaSora_LocalADB_0.1.1_candidate.apk'
if output.exists():raise SystemExit('Delivered candidate exists; choose a new revision instead of overwriting.')
env=dict(os.environ);env.update({'JAVA_HOME':str(jbr),'ANDROID_HOME':str(sdk),'ANDROID_SDK_ROOT':str(sdk),'ANDROID_USER_HOME':str(work/'android-user'),'GRADLE_USER_HOME':str(work/'gradle-home'),'GRADLE_RO_DEP_CACHE':str(shared),'TMP':str(work/'tmp'),'TEMP':str(work/'tmp')})
command=[str(gradle),'--offline','--no-daemon','--max-workers=2','--gradle-user-home',str(work/'gradle-home'),'--project-cache-dir',str(work/'project-cache'),'assembleDebug']
(report/'BUILD_ENVIRONMENT.json').write_text(json.dumps({'java_home':str(jbr),'sdk_read_only':str(sdk),'gradle':str(gradle),'shared_dependency_cache_read_only':str(shared),'isolated_gradle_home':str(work/'gradle-home'),'tests':'not_run_by_builder_root_device_tests_pending','devices_or_apps_executed':False},indent=2),encoding='utf8')
started=time.time()
with (report/'build.log').open('w',encoding='utf8') as log:
 result=subprocess.run(['cmd.exe','/d','/c',subprocess.list2cmdline(command)],cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
if result.returncode:raise SystemExit(result.returncode)
assembled=work/'gradle-output/app/outputs/apk/debug/app-debug.apk'
if not assembled.is_file():raise SystemExit('Gradle returned without expected APK.')
shutil.copy2(assembled,output)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
# Static APK/signature accounting is packaging evidence, not device testing.
verify=[str(sdk/'build-tools/36.0.0/apksigner.bat'),'verify','--verbose','--print-certs',str(output)]
verified=subprocess.run(['cmd.exe','/d','/c',subprocess.list2cmdline(verify)],env=env,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf8',errors='replace')
(report/'APK_SIGNATURE.txt').write_text(verified.stdout,encoding='utf8')
badging=subprocess.run([str(sdk/'build-tools/36.0.0/aapt2.exe'),'dump','badging',str(output)],env=env,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf8',errors='replace')
(report/'APK_METADATA.txt').write_text(badging.stdout,encoding='utf8')
receipt={'command':command,'working_directory':str(root),'build_exit_code':result.returncode,'duration_seconds':round(time.time()-started,2),'apk':str(output),'bytes':output.stat().st_size,'sha256':sha(output),'signature_read_exit_code':verified.returncode,'metadata_read_exit_code':badging.returncode,'keystore':str(root/'signing/candidate-debug.keystore'),'keystore_sha256':sha(root/'signing/candidate-debug.keystore'),'runtime_adb_keys':'created privately per app only at runtime; no host copy','tests':'not_run_by_builder_root_device_tests_pending','app_apk_emulator_or_device_executed':False,'installed':False,'published':False}
(report/'BUILD_RECEIPT.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8');(dist/'SHA256SUMS.txt').write_text(receipt['sha256']+' *'+output.name+'\n',encoding='utf8');print(json.dumps(receipt,ensure_ascii=False,indent=2))
if verified.returncode or badging.returncode:raise SystemExit('Packaging metadata/signature read failed; keep candidate and inspect reports.')
