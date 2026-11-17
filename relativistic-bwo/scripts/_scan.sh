#!/usr/bin/env bash
# Runs the scripts named and prints each one's oscillating power, efficiency, spectral peak,
# the current back on the cathode's wall and the mean γ mid-way (scan helper, not part of run.sh).
cd "$(dirname "$0")"
for f in "$@"; do n=${f%.json}; ~/emcraft/target-engine/release/emcraft-cli run $f > ../results/$n.out 2> ../results/$n.err; python3 - "$n" <<'PY'
import sys, math, cmath, json
sys.path.insert(0,'.'); import figures as F
n=sys.argv[1]
t=open(f'../results/{n}.out').read()
num=lambda key: float(t[t.index(key):].split(':')[1].split(',')[0].split('}')[0])
osc, eff = num('"oscillating_w"'), num('"efficiency"')
dec=json.JSONDecoder(); i=0; back=mid=None
while (i:=t.find('{',i))>=0:
    try:
        o,j=dec.raw_decode(t,i); i=j
        if isinstance(o.get('walls'),dict) and 'z-' in o['walls']: back=o['walls']['z-']['current']; mid=o.get('mid_gamma')
    except ValueError: i+=1
_, d = F.rows(f"{n}-probes.csv")
half=d[len(d)//2:][::2]; tt=[r[0]*1e-9 for r in half]; ez=[r[3] for r in half]; m=sum(ez)/len(ez); ez=[e-m for e in ez]
N=len(ez); w=[0.5-0.5*math.cos(2*math.pi*k/(N-1)) for k in range(N)]
fs=[2.8+0.01*k for k in range(161)]
amp=[abs(sum(a*e*cmath.exp(-2j*math.pi*f*1e9*x) for a,e,x in zip(w,ez,tt))) for f in fs]
print(n, f'{osc/1e9:.3f} GW', f'eff {eff*100:.1f} %', f'f {fs[amp.index(max(amp))]:.2f} GHz', f'back {back:.0f} A', f'mid gamma {mid:.2f}', flush=True)
PY
done
