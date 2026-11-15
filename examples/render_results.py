"""Render published aggregate results; does not execute the historical study."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'docs/results'
d = json.loads((DATA / 'summary.json').read_text())
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False,'axes.edgecolor':'#d0d7de','text.color':'#172b4d','axes.labelcolor':'#172b4d','xtick.color':'#536477','ytick.color':'#172b4d','savefig.facecolor':'#f7f9fc','figure.facecolor':'#f7f9fc','axes.facecolor':'#f7f9fc'})
colors = {'NVDA':'#157f83','SMH':'#536ac6'}
fig, ax = plt.subplots(figsize=(12,6.8))
fig.subplots_adjust(left=.31,right=.91,top=.77,bottom=.18)
fig.text(.055,.94,d['title'],fontsize=23,weight='bold')
fig.text(.055,.885,'How sensitive are the warnings?',fontsize=16)
fig.text(.055,.837,'Changed warning days versus baseline · one convention changed at a time',fontsize=10,color='#536477')
variants=d['variants']; tickers=list(d['baseline']); y=np.arange(len(variants)); width=.32
for i,t in enumerate(tickers):
 values=[]
 for v in variants:
  a=v['instruments'][t];assert 0<=a['warning_disagreements']<=a['common_observations']
  value=100*a['warning_disagreements']/a['common_observations'];assert abs(value-100*a['warning_disagreement_fraction'])<1e-9
  values.append(value)
 pos=y+(i-(len(tickers)-1)/2)*width
 ax.barh(pos,values,height=width*.85,color=colors[t],label=t,zorder=3)
 for yy,val in zip(pos,values):ax.text(val+.12,yy,f'{val:.2f}%',va='center',fontsize=9)
ax.set_yticks(y,[v['name'] for v in variants]);ax.invert_yaxis();ax.set_xlim(0,max(8,max(100*a['warning_disagreement_fraction'] for v in variants for a in v['instruments'].values() if a['warning_disagreement_fraction'] is not None)*1.22));ax.axvline(5,color='#a6adb7',linestyle='--',linewidth=1);ax.grid(axis='x',alpha=.15);ax.set_xlabel('Common valid dates with a different warning (%)');ax.legend(loc='lower right',frameon=False)
fig.text(.055,.08,'Historical development study · 5% reference is descriptive, not statistical significance.',fontsize=10)
fig.text(.055,.045,'Coverage: '+ ' · '.join(f"{t} {d['baseline'][t]['first']} to {d['baseline'][t]['last']}" for t in tickers),fontsize=9,color='#536477')
fig.savefig(DATA/'sensitivity.png',dpi=160);plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(12,6.8));fig.subplots_adjust(left=.24,right=.94,top=.74,bottom=.22,wspace=.32)
fig.text(.055,.94,d['title'],fontsize=23,weight='bold');fig.text(.055,.885,'Does the baseline entry filter help?',fontsize=16);fig.text(.055,.835,'Fixed-policy simulation · same-calendar controls within each instrument',fontsize=10,color='#536477')
rows=[]
for t,b in d['baseline'].items():
 for k,label,col in [('tuned','Model baseline','#157f83'),('trend','Trend control','#536ac6'),('immediate','Immediate entry','#bd7352')]:rows.append((f'{t} / {label}',b['policies'][k],col))
y=np.arange(len(rows))
for ax,key,title in zip(axes,['annualized_return','max_drawdown'],['Annualized return (%)','Maximum drawdown (%)']):
 values=[100*r[1][key] for r in rows];ax.barh(y,values,color=[r[2] for r in rows],height=.6,zorder=3);ax.set_yticks(y,[r[0] for r in rows] if ax is axes[0] else []);ax.invert_yaxis();ax.set_title(title,fontsize=12,pad=20);ax.grid(axis='x',alpha=.15)
 span=max(abs(x) for x in values);ax.set_xlim((0,span*1.3) if key=='annualized_return' else (-span*1.3,0))
 for yy,val in zip(y,values):ax.text(val+(span*.025 if val>=0 else -span*.025),yy,f'{val:.1f}',va='center',ha='left' if val>=0 else 'right',fontsize=10)
fig.text(.055,.145,'Periods: '+' · '.join(f"{t} {b['entry_first']} to {b['last']}" for t,b in d['baseline'].items()),fontsize=9)
fig.text(.055,.10,'Mean stock exposure: '+' · '.join(f"{t}: model {b['policies']['tuned']['mean_exposure']:.0%}, trend {b['policies']['trend']['mean_exposure']:.0%}, immediate {b['policies']['immediate']['mean_exposure']:.0%}" for t,b in d['baseline'].items()),fontsize=9)
fig.text(.055,.055,'Development evidence, not validated prediction. Immediate entry is not buy and hold. See README for costs and rules.',fontsize=9,color='#536477')
fig.savefig(DATA/'outcomes.png',dpi=160);plt.close(fig)
print('Rendered and checked',d['title'])
