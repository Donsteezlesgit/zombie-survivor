#!/usr/bin/env python3
"""2D PARITY TEST - run before every push that touches 3D code.
Paints every map with 3D switched OFF and hashes the 2D ground picture.
  python3 tests/parity2d.py            -> compare against tests/2d-baseline.json
  python3 tests/parity2d.py --save     -> (re)write the baseline (only when 2D art is meant to change)
Also checks that turning 3D ON then OFF again gives the identical 2D picture."""
import json, sys, os, hashlib, subprocess, threading, http.server, socketserver, functools
from playwright.sync_api import sync_playwright
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
base = os.path.join(root, 'tests', '2d-baseline.json')
tmp = '/tmp/parity2d'; os.makedirs(tmp, exist_ok=True)
src = open(os.path.join(root, 'index.html'), encoding='utf-8').read()
if len(sys.argv) > 2 and sys.argv[1] == '--from':      # test an older commit's file
    src = subprocess.check_output(['git', '-C', root, 'show', sys.argv[2] + ':index.html']).decode('utf-8')
i = src.rindex("\n})();")
src = src[:i] + "\n  window.__ev = function (c) { return eval(c); };" + src[i:]
open(os.path.join(tmp, 'index.html'), 'w', encoding='utf-8').write(src)
for f in ('three.min.js', 'peerjs.min.js', 'sw.js', 'manifest.webmanifest'):
    if os.path.exists(os.path.join(root, f)): open(os.path.join(tmp, f), 'wb').write(open(os.path.join(root, f), 'rb').read())
h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=tmp)
class Q(h.func):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Q, directory=tmp)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
JS = "(function(m){ setMap(m); var c=groundL.c, x=groundL.x, d=x.getImageData(0,0,c.width,c.height).data, h=2166136261; for(var i=0;i<d.length;i+=7){ h^=d[i]; h=Math.imul(h,16777619); } return c.width+':'+(h>>>0); })"
NONDET = ['haunted']   # paints with Math.random, so its hash changes every run (also in the original)
res = {}; errs = []
with sync_playwright() as p:
    b = p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = b.new_page(viewport={"width": 844, "height": 390})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.add_init_script("try{localStorage.setItem('zs-v3d','0')}catch(e){}")
    pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(1500)
    ev = lambda c: pg.evaluate("__ev(%s)" % json.dumps(c))
    ids = ev("MAPS.map(function(m){return m.id})")
    for m in ids:
        if m in NONDET: continue
        res[m] = ev("(%s)('%s')" % (JS, m)); ev("mapId=''; 0")
    # 3D on then off must give the identical 2D picture
    if 'dummytown' in ids and ev("typeof repaintArt") == 'function':
        ev("v3off=false; setMap('dummytown'); v3off=true; repaintArt(); 0")
        res['dummytown-after-toggle'] = ev("(function(){var c=groundL.c,x=groundL.x,d=x.getImageData(0,0,c.width,c.height).data,h=2166136261;for(var i=0;i<d.length;i+=7){h^=d[i];h=Math.imul(h,16777619);}return c.width+':'+(h>>>0);})()")
    b.close()
if errs: print("PAGE ERRORS:", errs[:3])
print(json.dumps(res, indent=1))
if '--save' in sys.argv: json.dump(res, open(base, 'w'), indent=1); print('baseline saved'); sys.exit(0)
exp = json.load(open(base)); bad = [k for k in exp if res.get(k) != exp[k] and k != 'dummytown-after-toggle']
if res.get('dummytown-after-toggle') and res['dummytown-after-toggle'] != exp.get('dummytown'): bad.append('dummytown-after-toggle')
print('FAIL 2D changed: ' + ', '.join(bad) if bad else 'OK - 2D art identical to baseline'); sys.exit(1 if bad else 0)
