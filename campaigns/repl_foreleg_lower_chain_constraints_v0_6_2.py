"""Pure-stdlib, moved-one-level lower forelimb IK. All angles in degrees.
Hinge labels track physical control locations, not guessed anatomy:
upper bending witness Bone_014/020 projects forward (+Z),
lower bending witness Bone_013/019 folds backward (-Z).
The previous constraints were one level too high in the skeleton. Existing hindlimb motions are never changed.
"""
from __future__ import annotations
import math

LOW=(-47.,-12.,-80.,-45.)
HIGH=(47.,75.,14.,45.)

def clamp(x,lo,hi):return max(lo,min(hi,x))

def fk(links,angles):
    pos=[tuple(links[0])]
    theta=0.
    for i in range(4):
        theta+=math.radians(angles[i]);co=math.cos(theta);si=math.sin(theta)
        # links=[start, dy/dz link entries] so there are 5 positions in total.
        x,y,z=pos[-1];dx,dy,dz=links[i+1]
        pos.append((x+dx,y+co*dy-si*dz,z+si*dy+co*dz))
    return pos

def chord(a,b,c):
    # Signed z protrusion of b relative to the a-c line at b's y.
    den=c[1]-a[1]
    if abs(den)<1e-4:
        # Not a valid planar, downward link -> anatomically impossible pose.
        return float('nan')
    return b[2]-(a[2]+(b[1]-a[1])/den*(c[2]-a[2]))

def poles(pos):
    return chord(*pos[:3]),chord(*pos[1:4])

def bell(s):return max(0.,math.sin(math.pi*clamp(s,0.,1.)))

def residual(links,q,target,s):
    pos=fk(links,q);e,k=poles(pos)
    if not math.isfinite(e+k):return [1e4]*8
    # Relative demands taper to neutral at the contact boundaries.
    lift=bell(s)
    upper_goal=-.064+.125*lift
    lower_goal=.004-.082*lift
    # first 2 equations enforce real hoof placement; next two
    # enforce *opposite* anatomical hinge/pole directions.
    # The final 4 softly regularize joint angles for continuity.
    return [200*(pos[-1][1]-target[1]),200*(pos[-1][2]-target[2]),
            85*max(0.,upper_goal-e),85*max(0.,k-lower_goal),
            .025*q[0],.030*q[1],.030*q[2],.045*q[3]]

def solve_linear(a,b):
    m=[list(row)+[v] for row,v in zip(a,b)]
    for i in range(4):
        row=max(range(i,4),key=lambda k:abs(m[k][i]))
        if abs(m[row][i])<1e-12:return None
        m[i],m[row]=m[row],m[i]
        p=m[i][i]
        for j in range(i,5):m[i][j]/=p
        for k in range(4):
            if k==i:continue
            factor=m[k][i]
            for j in range(i,5):m[k][j]-=factor*m[i][j]
    return [row[4] for row in m]

def optimize(links,target,s,old):
    seeds=[old,[-1,41,-60,-12],[-8,52,-65,-15],[-2,18,-35,-7]]
    best=None
    for seed in seeds:
        q=[clamp(v,LOW[i]+1e-6,HIGH[i]-1e-6) for i,v in enumerate(seed)]
        lam=.05
        r=residual(links,q,target,s);loss=sum(z*z for z in r)
        for iteration in range(80):
            jac=[]
            for i in range(4):
                h=.035
                plus=q[:];minus=q[:];plus[i]+=h;minus[i]-=h
                rp=residual(links,plus,target,s);rm=residual(links,minus,target,s)
                jac.append([(a-b)/(2*h) for a,b in zip(rp,rm)])
            jtj=[[sum(jac[i][k]*jac[j][k] for k in range(8)) for j in range(4)] for i in range(4)]
            rhs=[-sum(jac[i][k]*r[k] for k in range(8)) for i in range(4)]
            changed=False
            for trial in range(10):
                matrix=[[jtj[i][j]+(lam if i==j else 0) for j in range(4)] for i in range(4)]
                dx=solve_linear(matrix,rhs)
                if dx is None:break
                candidate=[clamp(q[i]+dx[i],LOW[i],HIGH[i]) for i in range(4)]
                test=residual(links,candidate,target,s)
                new_loss=sum(z*z for z in test)
                if new_loss <loss-1e-12:
                    q=candidate;r=test;loss=new_loss
                    lam=max(1e-6,lam*.43);changed=True;break
                lam=min(1e10,lam*4)
            if not changed:break
        if best is None or loss<best[0]:best=(loss,q)
    return best[1],best[0]
