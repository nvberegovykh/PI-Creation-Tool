from pathlib import Path
from playwright.sync_api import sync_playwright
import json, re

OUT=Path('tools/comcheck/legacy_discover'); OUT.mkdir(parents=True,exist_ok=True)
for p in OUT.glob('*'):
    try: p.unlink()
    except: pass

def snap(page,label):
    page.wait_for_timeout(500)
    data={'url':page.url,'body':page.locator('body').inner_text()[:50000],'elements':[]}
    for i,e in enumerate(page.locator('a,button,input,img,[role=button],span,div').all()):
        try:
            d={k:e.get_attribute(k) for k in ('id','name','type','title','alt','href','src','onclick','class','role')}
            txt=(e.inner_text() if e.evaluate('(n)=>n instanceof HTMLElement') else '')
            if txt or any(d.values()):
                d['tag']=e.evaluate('(n)=>n.tagName')
                d['text']=txt[:500]
                d['visible']=e.is_visible()
                data['elements'].append(d)
        except: pass
    (OUT/f'{label}.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
    (OUT/f'{label}.html').write_text(page.content(),encoding='utf-8')
    (OUT/f'{label}.txt').write_text(data['body'],encoding='utf-8')
    page.screenshot(path=str(OUT/f'{label}.png'),full_page=True)
    print(label,'elements',len(data['elements']),flush=True)
    for d in data['elements']:
        hay=' '.join(str(d.get(k) or '') for k in ('text','id','name','title','alt','href','src','onclick')).lower()
        if any(x in hay for x in ('load','open','upload','cxl','project','save a copy','download')):
            print('CAND',json.dumps(d)[:1200],flush=True)
    return data

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    page=b.new_page(viewport={'width':1600,'height':1000},accept_downloads=True)
    page.on('console',lambda m: print('CONSOLE',m.type,m.text,flush=True) if m.type in ('error','warning') else None)
    page.on('dialog',lambda d:(print('DIALOG',d.type,repr(d.message),flush=True),d.dismiss()))
    req=[]
    page.on('request',lambda r:req.append((r.method,r.url,r.resource_type)))
    page.goto('https://legacy-comcheck.energycode.pnl.gov/CheckWeb/index.html',wait_until='domcontentloaded',timeout=120000)
    page.wait_for_timeout(6000)
    snap(page,'00_initial')

    # New Project is the most likely entry point for a load/open action.
    try:
        page.locator('#new').click(timeout=5000)
        page.wait_for_timeout(1200)
        snap(page,'01_after_new_project')
    except Exception as e:
        print('NEW_PROJECT_CLICK_ERROR',repr(e),flush=True)

    # Click visible candidates one at a time and detect a file chooser without committing changes.
    selectors=[
        'text=Load Project','text=Open Project','text=Load','text=Open','text=Upload',
        '[title*="load" i]','[title*="open" i]','[title*="upload" i]','[alt*="load" i]','[alt*="open" i]',
        '[onclick*="load" i]','[onclick*="open" i]','[onclick*="upload" i]'
    ]
    for si,sel in enumerate(selectors):
        loc=page.locator(sel)
        for j in range(min(loc.count(),5)):
            e=loc.nth(j)
            if not e.is_visible(): continue
            try:
                print('TRY',sel,j,(e.inner_text() or '')[:200],flush=True)
                got=False
                try:
                    with page.expect_file_chooser(timeout=1500) as fc:
                        e.click()
                    chooser=fc.value
                    print('FILE_CHOOSER',sel,j,flush=True)
                    got=True
                except Exception as ex:
                    print('NO_CHOOSER',sel,j,type(ex).__name__,flush=True)
                snap(page,f'cand_{si}_{j}')
                if got: raise SystemExit(0)
            except SystemExit: raise
            except Exception as e2: print('CAND_ERR',sel,j,repr(e2),flush=True)

    # Report all file inputs after interactions, including hidden/detached patterns.
    print('FILE_INPUTS',page.locator('input[type=file]').count(),flush=True)
    for i,e in enumerate(page.locator('input[type=file]').all()):
        try: print('FILE_INPUT',i,e.evaluate('(n)=>n.outerHTML'),flush=True)
        except: pass
    (OUT/'requests.txt').write_text('\n'.join(f'{m}\t{t}\t{u}' for m,u,t in req),encoding='utf-8')
    b.close()
