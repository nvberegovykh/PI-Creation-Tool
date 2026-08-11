from playwright.sync_api import sync_playwright
import json,re
with sync_playwright() as p:
 b=p.chromium.launch(headless=True); page=b.new_page(viewport={'width':1600,'height':1000})
 page.goto('https://legacy-comcheck.energycode.pnl.gov/CheckWeb/index.html',wait_until='domcontentloaded',timeout=120000); page.wait_for_timeout(5000)
 print('INITIAL_URL',page.url)
 print('INITIAL_NEW_OUTER',page.locator('#new').evaluate('(n)=>n.outerHTML'))
 page.locator('#new').click(); page.wait_for_timeout(1500)
 print('AFTER_URL',page.url)
 print('BODY',page.locator('body').inner_text()[:12000].replace('\n',' | '))
 print('FILES',page.locator('input[type=file]').count())
 for sel in ['input','button','a','img','[onclick]','[title]','[alt]']:
  for e in page.locator(sel).all():
   try:
    h=e.evaluate('(n)=>n.outerHTML')
    if any(x in h.lower() for x in ('load','open','upload','cxl','project')):
     print('EL',h[:2000])
   except: pass
 html=page.content()
 for term in ('load','open','upload','cxl','projectaction'):
  print('TERM',term)
  for m in list(re.finditer(term,html,re.I))[:30]: print(html[max(0,m.start()-500):m.end()+700].replace('\n',' ')[:1400])
 b.close()
