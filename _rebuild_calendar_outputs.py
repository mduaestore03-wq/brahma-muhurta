import csv, json, re
from pathlib import Path
root=Path(__file__).resolve().parent
folder=root/'Brahma_Podolsk_2026_COMPLETE'
csv_path=folder/'Brahma_Podolsk_2026_Calendar.csv'
rows=list(csv.DictReader(csv_path.open(encoding='utf-8-sig')))
for r in rows:
    r['window']=r['window_fixed']
    r.pop('window_night15',None)
    r['explanation']=re.sub(r'[^.]*\(ночь/15\), альтернативно ([^.]*)\. ', lambda m: f"{r['window']} (фиксированные 96–48 минут до восхода). ", r['explanation'], count=1)
    r['explanation']=r['explanation'].replace(f"{r['window_fixed']} (48 минут)", f"{r['window_fixed']} (фиксированные 96–48 минут до восхода)")
fields=list(rows[0])
with csv_path.open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
# JS is a canonical browser payload, with one method and no legacy aliases.
js_path=folder/'podolsk-calendar.js'
js_rows=[]
for r in rows:
    js_rows.append(r)
js='\'use strict\';\nwindow.PODOLSK_DAILY = '+json.dumps({r['date']:r for r in js_rows},ensure_ascii=False,indent=2)+';\n'
js_path.write_text(js,encoding='utf-8')

# Generated markdown: make fixed 96–48 the only displayed window.
for name in ['Brahma_Podolsk_2026_Explanations.md','Brahma_Podolsk_2026_Practices.md']:
    p=folder/name
    text=p.read_text(encoding='utf-8')
    text=text.replace('оба представлены, ни один не объявлен единственно каноническим', 'в приложении выбран единый фиксированный метод')
    text=text.replace('Время определяется двумя разными методами (оба представлены, ни один не объявлен единственно каноническим): 14-я из 15 частей ночи и интервал 96–48 минут до восхода.', 'В приложении используется единый фиксированный метод: интервал 96–48 минут до местного восхода.')
    text=re.sub(r'\d{2}:\d{2}–\d{2}:\d{2} \(ночь/15\), альтернативно (\d{2}:\d{2}–\d{2}:\d{2}) \(48 минут\)', r'\1 (фиксированные 96–48 минут до восхода)', text)
    text=re.sub(r' · (\d{2}:\d{2}–\d{2}:\d{2})$', r' · \1', text)
    p.write_text(text,encoding='utf-8')
