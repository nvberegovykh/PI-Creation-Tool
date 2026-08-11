import requests,re
base='https://legacy-comcheck.energycode.pnl.gov/CheckWeb/'
for path in ['includes/load_save.js','includes/login.js','dwr/interface/ProjectView.js']:
 r=requests.get(base+path,timeout=60); print('\n###',path,r.status_code,len(r.text)); t=r.text
 for term in ['uploadProjectFile','uploadForm','loadProject','load','projectAction','cxl','File','saveProject','getProjects']:
  print('\nTERM',term)
  for m in list(re.finditer(term,t,re.I))[:20]: print(t[max(0,m.start()-800):m.end()+1400])
