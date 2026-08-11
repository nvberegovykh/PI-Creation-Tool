from pathlib import Path
from playwright.sync_api import sync_playwright
import json, re, urllib.parse

OUT=Path('tools/comcheck/out'); OUT.mkdir(parents=True,exist_ok=True)
for p in OUT.glob('*'):
    try: p.unlink()
    except: pass
reqs=[]; responses=[]; console=[]

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    page=b.new_page(viewport={'width':1440,'height':1000})
    page.on('request', lambda r: reqs.append((r.method,r.url,r.resource_type)))
    page.on('response', lambda r: responses.append((r.status,r.url)))
    page.on('console', lambda m: console.append(f'{m.type}: {m.text}'))
    resp=page.goto('https://comcheck.energycode.pnl.gov',wait_until='networkidle',timeout=120000)
    page.wait_for_timeout(1500)

    print('FINAL_URL=',page.url)
    print('STATUS=',resp.status if resp else None)
    print('BODY=',page.locator('body').inner_text()[:5000].replace('\n',' | '))

    # Capture the unauthenticated fresh project JSON exactly as the app receives it.
    r=page.request.get('https://comcheck.energycode.pnl.gov/api/v2.0/projects/new', timeout=120000)
    print('NEW_PROJECT_STATUS=',r.status)
    print('NEW_PROJECT_CT=',r.headers.get('content-type'))
    new_txt=r.text()
    (OUT/'new_project.txt').write_text(new_txt,encoding='utf-8')
    try:
        new_json=r.json()
        (OUT/'new_project.json').write_text(json.dumps(new_json,indent=2),encoding='utf-8')
        print('NEW_PROJECT_JSON=',json.dumps(new_json)[:12000])
    except Exception as e:
        print('NEW_PROJECT_JSON_ERROR=',repr(e))

    # Capture registration UI without submitting anything.
    try:
        page.get_by_role('button', name='REGISTER').click()
        page.wait_for_timeout(1000)
        reg_body=page.locator('body').inner_text()
        print('REGISTER_BODY=',reg_body[:8000].replace('\n',' | '))
        inputs=[]
        for e in page.locator('input').all():
            inputs.append({k:e.get_attribute(k) for k in ('type','name','id','placeholder','autocomplete','aria-label')})
        buttons=[{'text':e.inner_text(),'type':e.get_attribute('type'),'id':e.get_attribute('id')} for e in page.locator('button').all()]
        print('REGISTER_INPUTS=',json.dumps(inputs))
        print('REGISTER_BUTTONS=',json.dumps(buttons))
        (OUT/'register.html').write_text(page.content(),encoding='utf-8')
        page.screenshot(path=str(OUT/'register.png'),full_page=True)
    except Exception as e:
        print('REGISTER_PROBE_ERROR=',repr(e))

    # Discover application JS and scrape internal API route strings.
    scripts=[]
    for e in page.locator('script[src]').all():
        src=e.get_attribute('src')
        if src:
            scripts.append(urllib.parse.urljoin(page.url,src))
    scripts=list(dict.fromkeys(scripts))
    print('SCRIPT_COUNT=',len(scripts))
    routes=set(); interesting=[]
    for i,u in enumerate(scripts):
        try:
            rr=page.request.get(u,timeout=120000)
            txt=rr.text()
            if any(k in txt.lower() for k in ('simulation','compliance','report','projects/new','register')):
                interesting.append(u)
                (OUT/f'bundle_{i}.js').write_text(txt,encoding='utf-8')
            for pat in [r'["\']([^"\']*/api/v2\.0/[^"\']+)["\']', r'["\']([^"\']*/api/[^"\']+)["\']']:
                for m in re.finditer(pat,txt):
                    val=m.group(1)
                    if len(val)<300: routes.add(val)
            # Catch path fragments around useful words.
            for m in re.finditer(r'.{0,180}(simulation|compliance|report|projects/new|register).{0,220}',txt,re.I):
                s=m.group(0)
                if len(s)<500: routes.add('SNIP:'+s)
        except Exception as e:
            print('BUNDLE_ERROR=',u,repr(e))
    (OUT/'scripts.txt').write_text('\n'.join(scripts),encoding='utf-8')
    (OUT/'interesting_scripts.txt').write_text('\n'.join(interesting),encoding='utf-8')
    (OUT/'routes.txt').write_text('\n'.join(sorted(routes)),encoding='utf-8')
    print('ROUTES_START')
    for x in sorted(routes)[:400]: print(x[:800])
    print('ROUTES_END')

    (OUT/'requests.txt').write_text('\n'.join(f'{m}\t{t}\t{u}' for m,u,t in reqs),encoding='utf-8')
    (OUT/'responses.txt').write_text('\n'.join(f'{s}\t{u}' for s,u in responses),encoding='utf-8')
    (OUT/'console.txt').write_text('\n'.join(console),encoding='utf-8')
    b.close()
