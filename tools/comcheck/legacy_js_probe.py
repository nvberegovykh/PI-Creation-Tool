import requests,re
base='https://legacy-comcheck.energycode.pnl.gov/CheckWeb/'
for path in ['dwr/interface/ProjectService.js','includes/load_save.js']:
 r=requests.get(base+path,timeout=60); print('\n###',path,r.status_code,len(r.text)); t=r.text
 print(t[:20000])
