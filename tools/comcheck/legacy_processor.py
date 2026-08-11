from pathlib import Path
from playwright.sync_api import sync_playwright
import base64, zlib, json, re, time

OUT=Path('tools/comcheck/legacy_out'); OUT.mkdir(parents=True,exist_ok=True)
for p in OUT.glob('*'):
    try: p.unlink()
    except: pass

# Exact known-loadable 250 Midwood Backstop CXL, SHA256
# 84ca06da590837664b94734bb82c1906054dd269d3939a6efb2cc60b229a799d
CXL_Z64='''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'''
TARGET=OUT/'250_Midwood_BACKSTOP_known_loadable.cxl'
TARGET.write_bytes(zlib.decompress(base64.b64decode(CXL_Z64)))

log=[]; dialogs=[]
def emit(*a):
    s=' '.join(str(x) for x in a); print(s,flush=True); log.append(s)

def dump_controls(page,label):
    data={'url':page.url,'body':page.locator('body').inner_text()[:30000],'inputs':[],'buttons':[],'selects':[]}
    for e in page.locator('input').all():
        try: data['inputs'].append({k:e.get_attribute(k) for k in ('type','name','id','value','title','aria-label')})
        except: pass
    for e in page.locator('button').all():
        try: data['buttons'].append({'text':e.inner_text(),'id':e.get_attribute('id'),'title':e.get_attribute('title')})
        except: pass
    for idx,e in enumerate(page.locator('select').all()):
        try:
            data['selects'].append({'idx':idx,'name':e.get_attribute('name'),'id':e.get_attribute('id'),'value':e.input_value(),'options':e.locator('option').all_text_contents()})
        except: pass
    (OUT/f'{label}.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
    (OUT/f'{label}.txt').write_text(data['body'],encoding='utf-8')
    try: page.screenshot(path=str(OUT/f'{label}.png'),full_page=True)
    except: pass
    emit(label,'inputs',len(data['inputs']),'buttons',len(data['buttons']),'selects',len(data['selects']))
    return data

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page(viewport={'width':1600,'height':1000},accept_downloads=True)
    def on_dialog(d):
        dialogs.append({'type':d.type,'message':d.message})
        emit('DIALOG',d.type,repr(d.message))
        d.accept()
    page.on('dialog',on_dialog)
    page.on('console',lambda m: emit('CONSOLE',m.type,m.text) if m.type in ('error','warning') else None)
    page.goto('https://legacy-comcheck.energycode.pnl.gov/CheckWeb/index.html',wait_until='domcontentloaded',timeout=120000)
    page.wait_for_timeout(8000)
    dump_controls(page,'00_initial')

    files=page.locator('input[type=file]')
    emit('FILE_INPUT_COUNT',files.count())
    if files.count()==0:
        # Some GWT builds create the input only after the load icon/button is pressed.
        for label in ('Load','Open','Upload','Load Project'):
            try:
                page.get_by_text(label,exact=True).first.click(timeout=1500)
                page.wait_for_timeout(500)
                if page.locator('input[type=file]').count(): break
            except: pass
        files=page.locator('input[type=file]')
    if files.count()==0:
        emit('FATAL no file input found')
        dump_controls(page,'00_no_file_input')
        raise SystemExit(2)

    files.first.set_input_files(str(TARGET.resolve()))
    page.wait_for_timeout(15000)
    loaded=dump_controls(page,'01_loaded')
    emit('DIALOGS_AFTER_LOAD',json.dumps(dialogs))
    if any('Unable to load' in d['message'] for d in dialogs):
        raise SystemExit(3)

    body=loaded['body']
    emit('HAS_SIM_FAIL', 'Envelope simulations failed' in body)
    emit('HAS_TBD', 'Envelope TBD' in body)

    # Open Envelope tab.
    clicked=False
    for sel in ["text=ENVELOPE","text=Envelope"]:
        try:
            page.locator(sel).first.click(timeout=3000); clicked=True; break
        except: pass
    page.wait_for_timeout(2000)
    env=dump_controls(page,'02_envelope')

    # Select the roof row by its visible assembly/description, then Edit.
    roof_clicked=False
    for needle in ('R1_Roof','Attic Roof, Steel Joists','R1'):
        loc=page.get_by_text(needle,exact=False)
        if loc.count():
            try:
                loc.first.click(timeout=3000); roof_clicked=True; emit('ROOF_ROW_CLICKED',needle); break
            except Exception as e: emit('ROOF_CLICK_ERR',needle,repr(e))
    if not roof_clicked:
        # The first body table row is roof in this project; find a row containing the description.
        for i,row in enumerate(page.locator('tr').all()):
            try:
                txt=row.inner_text()
                if 'Attic Roof' in txt:
                    row.click(); roof_clicked=True; emit('ROOF_TR_CLICKED',i,txt[:500]); break
            except: pass
    page.wait_for_timeout(500)

    edit_clicked=False
    for q in [page.get_by_text('Edit',exact=True),page.get_by_role('button',name='Edit')]:
        if q.count():
            try: q.first.click(timeout=3000); edit_clicked=True; break
            except: pass
    page.wait_for_timeout(1500)
    dump_controls(page,'03_roof_edit')
    emit('ROOF_EDIT_OPENED',edit_clicked)

    (OUT/'dialogs.json').write_text(json.dumps(dialogs,indent=2),encoding='utf-8')
    browser.close()

(OUT/'processor.log').write_text('\n'.join(log),encoding='utf-8')
