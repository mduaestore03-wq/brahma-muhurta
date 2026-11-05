import csv, math
from datetime import datetime, date, time, timedelta, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent; path=ROOT/'Brahma_Podolsk_2026_COMPLETE/Brahma_Podolsk_2026_Calendar.csv'; rows=list(csv.DictReader(path.open(encoding='utf-8-sig')))
r=math.pi/180; lat=55.42419; lon=37.55472

def apparent_sunrise(day):
 dt=datetime.combine(day,time.min,tzinfo=timezone.utc); mins=360
 for _ in range(8):
  ts=dt+timedelta(minutes=mins); jul=ts.timestamp()/86400+2440587.5; t=(jul-2451545)/36525
  l=(280.46646+t*(36000.76983+t*.0003032))%360; m=357.52911+t*(35999.05029-.0001537*t); e=.016708634-t*(.000042037+.0000001267*t)
  c=math.sin(m*r)*(1.914602-t*(.004817+.000014*t))+math.sin(2*m*r)*(.019993-.000101*t)+math.sin(3*m*r)*.000289; om=125.04-1934.136*t; lam=l+c-.00569-.00478*math.sin(om*r); obl=23+(26+(21.448-t*(46.815+t*(.00059-t*.001813)))/60)/60+.00256*math.cos(om*r); dec=math.asin(math.sin(obl*r)*math.sin(lam*r)); y=math.tan(obl*r/2)**2; eq=4*(y*math.sin(2*l*r)-2*e*math.sin(m*r)+4*e*y*math.sin(m*r)*math.cos(2*l*r)-.5*y*y*math.sin(4*l*r)-1.25*e*e*math.sin(2*m*r))/r
  ch=math.cos(90.833*r)/(math.cos(lat*r)*math.cos(dec))-math.tan(lat*r)*math.tan(dec); mins=720-4*(lon+math.degrees(math.acos(ch)))-eq
 return (dt+timedelta(minutes=mins+180)).replace(second=0,microsecond=0)
for row in rows:
 s=apparent_sunrise(date.fromisoformat(row['date'])); row['sunrise']=s.strftime('%H:%M'); row['window']=f'{(s-timedelta(minutes=96)).strftime("%H:%M")}–{(s-timedelta(minutes=48)).strftime("%H:%M")}'; row['window_fixed']=row['window']; row['explanation']=row['explanation'].replace('Восход '+row['sunrise'], 'Восход '+row['sunrise'])
fields=list(rows[0]); path.open('w').close()
with path.open('w',encoding='utf-8-sig',newline='') as f: w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
print('updated',len(rows))
for d in ['2026-10-22','2026-10-29','2026-10-31','2026-11-10','2026-12-21','2026-12-31']:
 x=next(q for q in rows if q['date']==d); print(d,x['sunrise'],x['window'])
