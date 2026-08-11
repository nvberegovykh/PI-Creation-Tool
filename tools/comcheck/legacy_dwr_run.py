from pathlib import Path
from playwright.sync_api import sync_playwright
import base64, zlib, re, json, time

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'legacy_dwr_out'; OUT.mkdir(exist_ok=True)
for p in OUT.glob('*'):
    try:p.unlink()
    except:pass
src=(ROOT/'legacy_processor.py').read_text(encoding='utf-8')
m=re.search(r"CXL_Z64='''(.*?)'''",src,re.S)
assert m,'embedded baseline CXL not found'
cxl=zlib.decompress(base64.b64decode(m.group(1)))
target=OUT/'250_Midwood_BACKSTOP_known_loadable.cxl'; target.write_bytes(cxl)
print('CXL_BYTES',len(cxl),flush=True)

def dump(page,label):
    txt=page.locator('body').inner_text()
    (OUT/f'{label}.txt').write_text(txt,encoding='utf-8')
    (OUT/f'{label}.html').write_text(page.content(),encoding='utf-8')
    page.screenshot(path=str(OUT/f'{label}.png'),full_page=True)
    print(label,txt[:5000].replace('\n',' | '),flush=True)
    return txt

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    page=b.new_page(viewport={'width':1600,'height':1000},accept_downloads=True)
    dialogs=[]
    def dlg(d):
        dialogs.append(d.message); print('DIALOG',repr(d.message),flush=True); d.accept()
    page.on('dialog',dlg)
    page.on('console',lambda m: print('CONSOLE',m.type,m.text,flush=True) if m.type in ('error','warning') else None)
    page.goto('https://legacy-comcheck.energycode.pnl.gov/CheckWeb/index.html',wait_until='domcontentloaded',timeout=120000)
    page.wait_for_timeout(6000)
    print('HAS_UPLOAD_FN',page.evaluate('typeof uploadProject'),flush=True)
    print('HAS_PS',page.evaluate('typeof ProjectService'),flush=True)
    print('PS_UPLOAD',page.evaluate('typeof ProjectService!=="undefined" && typeof ProjectService.uploadProject'),flush=True)
    dump(page,'00_initial')
    # Inject the exact control shape expected by includes/load_save.js.
    page.evaluate("""() => { const old=document.getElementById('fileToUpload'); if(old) old.remove(); const i=document.createElement('input'); i.type='file'; i.id='fileToUpload'; i.name='fileToUpload'; i.style.position='fixed'; i.style.left='10px'; i.style.top='10px'; i.style.zIndex='999999'; document.body.appendChild(i); }""")
    page.locator('#fileToUpload').set_input_files(str(target.resolve()))
    print('FILE_VALUE',page.locator('#fileToUpload').input_value(),flush=True)
    try:
        page.evaluate('uploadProject()')
    except Exception as e:
        print('UPLOAD_CALL_ERROR',repr(e),flush=True)
    page.wait_for_timeout(20000)
    body=dump(page,'01_after_upload')
    print('DIALOGS',json.dumps(dialogs),flush=True)
    print('TITLE_VALUE',page.locator('#projectTitle').input_value() if page.locator('#projectTitle').count() else 'NONE',flush=True)
    print('CODE_TEXT',page.locator('#energyCode').input_value() if page.locator('#energyCode').count() else 'NONE',flush=True)
    loaded=('250 Midwood' in body and not any('Unable to load' in x for x in dialogs))
    print('LOADED',loaded,flush=True)
    if loaded:
        if page.locator('#compliance').count():
            print('CLICK_COMPLIANCE',flush=True)
            page.locator('#compliance').click()
            for sec in (5,15,30,60):
                page.wait_for_timeout((sec-(0 if sec==5 else {15:5,30:15,60:30}[sec]))*1000)
                txt=dump(page,f'compliance_{sec}s')
                print('COMP_STATUS',sec,'TBD' if 'Envelope TBD' in txt else 'NO_TBD','FAIL' if 'Envelope simulations failed' in txt else 'NO_FAIL',flush=True)
                if 'Envelope simulations failed' not in txt and 'Envelope TBD' not in txt: break
        else:
            print('NO_COMPLIANCE_BUTTON',flush=True)
    (OUT/'dialogs.json').write_text(json.dumps(dialogs,indent=2),encoding='utf-8')
    b.close()
