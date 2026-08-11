import requests, json
BASE='https://comcheck.energycode.pnl.gov/api/v2.0'
s=requests.Session()
r=s.get(BASE+'/projects/new',timeout=60)
print('new',r.status_code,r.headers.get('content-type'))
j=r.json()
for name,payload in [('wrapper',j),('project',j.get('project'))]:
    for ep in ['/compliance/start-run-simulation','/compliance/audit-payload-state','/compliance/create-report']:
        try:
            rr=s.post(BASE+ep,json=payload,timeout=60)
            print(name,ep,rr.status_code,rr.text[:1200].replace('\n',' '))
        except Exception as e: print(name,ep,'ERR',repr(e))
