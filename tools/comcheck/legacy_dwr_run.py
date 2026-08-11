from pathlib import Path
from playwright.sync_api import sync_playwright
import base64, zlib, re, json, time
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'legacy_dwr_out'; OUT.mkdir(exist_ok=True)
for p in OUT.glob('*'):
    try:p.unlink()
    except:pass
src=(ROOT/'legacy_processor.py').read_text(encoding='utf-8')
m=re.search(r"CXL_Z64='''(.*?)'''",src,re.S); assert m
cxl=zlib.decompress(base64.b64decode(m.group(1)))
target=OUT/'250_Midwood_BACKSTOP_known_loadable.cxl'; target.write_bytes(cxl)

def dump(page,label):
    txt=page.locator('body').inner_text()
    (OUT/f'{label}.txt').write_text(txt,encoding='utf-8')
    (OUT/f'{label}.html').write_text(page.content(),encoding='utf-8')
    page.screenshot(path=str(OUT/f'{label}.png'),full_page=True)
    print(label,txt[:2500].replace('\n',' | '),flush=True); return txt

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    page=b.new_page(viewport={'width':1600,'height':1000},accept_downloads=True)
    dialogs=[]; net=[]
    page.on('dialog',lambda d:(dialogs.append(d.message),print('DIALOG',repr(d.message),flush=True),d.accept()))
    page.on('console',lambda m: print('CONSOLE',m.type,m.text,flush=True) if m.type in ('error','warning') else None)
    page.on('request',lambda r: net.append(('REQ',r.method,r.url,r.post_data or '')) if ('dwr' in r.url.lower() or 'upload' in r.url.lower()) else None)
    page.on('response',lambda r: net.append(('RES',str(r.status),r.url,'')) if ('dwr' in r.url.lower() or 'upload' in r.url.lower()) else None)
    page.goto('https://legacy-comcheck.energycode.pnl.gov/CheckWeb/index.html',wait_until='domcontentloaded',timeout=120000)
    page.wait_for_timeout(6000)
    print('FUNCS',page.evaluate('({uploadProject:typeof uploadProject,ProjectService:typeof ProjectService,dwr:typeof dwr,handler:typeof handleFullProjectResponse})'),flush=True)
    page.evaluate("""() => { const old=document.getElementById('fileToUpload'); if(old) old.remove(); const i=document.createElement('input'); i.type='file'; i.id='fileToUpload'; i.name='fileToUpload'; document.body.appendChild(i); window.__dwrResult=null; window.__dwrError=null; if(window.dwr?.engine?.setErrorHandler) dwr.engine.setErrorHandler(function(msg,ex){ window.__dwrError={msg:String(msg),ex:String(ex||'')}; console.error('DWRERR',msg,ex); }); }""")
    page.locator('#fileToUpload').set_input_files(str(target.resolve()))
    print('FILE_VALUE',page.locator('#fileToUpload').input_value(),flush=True)
    print('DWR_VALUE',page.evaluate("""() => { const v=dwr.util.getValue('fileToUpload'); return {type:typeof v, ctor:v&&v.constructor&&v.constructor.name, text:String(v), isFile:typeof File!=='undefined'&&v instanceof File, isList:typeof FileList!=='undefined'&&v instanceof FileList}; }"""),flush=True)
    try:
        page.evaluate("""() => { const f=dwr.util.getValue('fileToUpload'); ProjectService.uploadProject('250_Midwood_BACKSTOP_known_loadable.cxl', f, function(r){ window.__dwrResult=r; try{handleFullProjectResponse(r);}catch(e){console.error('HANDLEERR',e);} }); }""")
    except Exception as e: print('CALLERR',repr(e),flush=True)
    for i in range(20):
        page.wait_for_timeout(1000)
        result=page.evaluate('({r:window.__dwrResult,e:window.__dwrError})')
        if result['r'] is not None or result['e'] is not None:
            print('DWR_CALLBACK',json.dumps(result,default=str)[:20000],flush=True); break
    else: print('DWR_CALLBACK_TIMEOUT',flush=True)
    page.wait_for_timeout(3000)
    body=dump(page,'01_after_dwr')
    (OUT/'net.json').write_text(json.dumps(net,indent=2),encoding='utf-8')
    (OUT/'dialogs.json').write_text(json.dumps(dialogs,indent=2),encoding='utf-8')
    print('NET',json.dumps(net)[:30000],flush=True)
    print('LOADED',('250 Midwood' in body),flush=True)
    if '250 Midwood' in body and page.locator('#compliance').count():
        page.locator('#compliance').click(); print('COMPLIANCE_CLICKED',flush=True)
        page.wait_for_timeout(25000); dump(page,'02_compliance_25s')
    b.close()
