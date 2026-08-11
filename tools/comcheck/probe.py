from pathlib import Path
from playwright.sync_api import sync_playwright
import json
OUT=Path('tools/comcheck/out'); OUT.mkdir(parents=True,exist_ok=True)
reqs=[]; responses=[]; console=[]
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    page=b.new_page(viewport={'width':1440,'height':1000})
    page.on('request', lambda r: reqs.append((r.method,r.url,r.resource_type)))
    page.on('response', lambda r: responses.append((r.status,r.url)))
    page.on('console', lambda m: console.append(f'{m.type}: {m.text}'))
    resp=page.goto('https://comcheck.energycode.pnl.gov',wait_until='networkidle',timeout=120000)
    page.wait_for_timeout(3000)
    print('FINAL_URL=',page.url)
    print('STATUS=',resp.status if resp else None)
    print('TITLE=',page.title())
    print('BODY=\n'+page.locator('body').inner_text()[:12000])
    inputs=[]
    for e in page.locator('input').all():
        inputs.append({k:e.get_attribute(k) for k in ('type','name','id','placeholder','autocomplete','aria-label')})
    buttons=[{'text':e.inner_text(),'type':e.get_attribute('type'),'id':e.get_attribute('id')} for e in page.locator('button').all()]
    links=[{'text':e.inner_text(),'href':e.get_attribute('href')} for e in page.locator('a').all()]
    print('INPUTS='+json.dumps(inputs,indent=2))
    print('BUTTONS='+json.dumps(buttons,indent=2))
    print('LINKS='+json.dumps(links[:100],indent=2))
    (OUT/'page.html').write_text(page.content(),encoding='utf-8')
    (OUT/'requests.txt').write_text('\n'.join(f'{m}\t{t}\t{u}' for m,u,t in reqs),encoding='utf-8')
    (OUT/'responses.txt').write_text('\n'.join(f'{s}\t{u}' for s,u in responses),encoding='utf-8')
    (OUT/'console.txt').write_text('\n'.join(console),encoding='utf-8')
    (OUT/'ui.json').write_text(json.dumps({'url':page.url,'inputs':inputs,'buttons':buttons,'links':links},indent=2),encoding='utf-8')
    page.screenshot(path=str(OUT/'page.png'),full_page=True)
    b.close()
