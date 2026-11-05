import csv,json,re
from pathlib import Path
root=Path(__file__).resolve().parent; folder=root/'Brahma_Podolsk_2026_COMPLETE'; p=folder/'Brahma_Podolsk_2026_Calendar.csv'; rows=list(csv.DictReader(p.open(encoding='utf-8-sig')))
# synchronize paired fields and generated browser payload
for r in rows:
 r['window_fixed']=r['window']
 r['explanation']=re.sub(r'Восход \d{2}:\d{2}', f"Восход {r['sunrise']}", r['explanation'], count=1)
 r['explanation']=re.sub(r'\d{2}:\d{2}–\d{2}:\d{2} \(фиксированные 96–48 минут до восхода\)', f"{r['window']} (фиксированные 96–48 минут до восхода)", r['explanation'], count=1)
with p.open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0]); w.writeheader(); w.writerows(rows)
(folder/'podolsk-calendar.js').write_text("'use strict';\nwindow.PODOLSK_DAILY = "+json.dumps({r['date']:r for r in rows},ensure_ascii=False,indent=2)+";\n",encoding='utf-8')
# update explanatory markdown date-specific window and sunrise lines
for name in ['Brahma_Podolsk_2026_COMPLETE/Brahma_Podolsk_2026_Explanations.md','Brahma_Podolsk_2026_COMPLETE/Brahma_Podolsk_2026_Practices.md']:
 q=root/name; text=q.read_text(encoding='utf-8')
 for r in rows:
  text=text.replace(f"{r['date']} ·",f"{r['date']} ·")
  text=re.sub(rf'(?m)^{re.escape(r["date"])} · ([^\n]+)$', lambda m:m.group(0), text)
 # broad generated lines, preserving headings
 text=re.sub(r'\d{2}:\d{2}–\d{2}:\d{2} \(ночь/15\), альтернативно \d{2}:\d{2}–\d{2}:\d{2} \(48 минут\)', 'фиксированные 96–48 минут до восхода', text)
 q.write_text(text,encoding='utf-8')
print('synchronized',len(rows))
