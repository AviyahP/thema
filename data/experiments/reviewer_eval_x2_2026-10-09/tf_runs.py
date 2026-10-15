import sys,glob,time; sys.path.insert(0,'.')
from tf_common import *
X=ROOT+'data/ontology/v0.4-leaves-x2/'
K=open(X+'embedding_keys.txt').read().split(); ix={k:i for i,k in enumerate(K)}; n=len(K)
files=sorted(glob.glob(X+'trees/*/row*.npz'))[:200]
SC=[8,16,32,64,128,256,512,1024,2048]
t=time.time()
if os.path.exists('/tmp/labels.npy'):
    L=np.load('/tmp/labels.npy'); P=np.load('/tmp/pres.npy')
else:
    L=np.full((len(files),len(SC),n),-1,np.int32); P=np.zeros((len(files),n),bool)
    for r,f in enumerate(files):
        z=np.load(f); sz=z['sizes']; ip=z['chain_indptr']; ci=z['chain_idx']
        P[r]=np.unpackbits(z['present'].view(np.uint8),bitorder='little')[:n].astype(bool)
        csz=sz[ci]
        for si,s in enumerate(SC):
            cs=np.concatenate([[0],np.cumsum(csz<=s)])
            cnt=cs[ip[1:]]-cs[ip[:-1]]
            lab=np.where(cnt>0, ci[np.maximum(ip[:-1]+cnt-1,0)], -(np.arange(n)+2))
            L[r,si]=lab
    np.save('/tmp/labels.npy',L); np.save('/tmp/pres.npy',P)
print('labels',time.time()-t,flush=True)
def rate(Lr,Pr,i1,i2,same):
    # pooled over runs: fraction of present pairs sharing a label
    A=Lr[:,i1];B=Lr[:,i2];pa=Pr[:,i1];pb=Pr[:,i2]
    eq=(A[:,:,None]==B[:,None,:])&pa[:,:,None]&pb[:,None,:]
    tot=(pa[:,:,None]&pb[:,None,:])
    if same:
        k=len(i1); d=np.arange(k); eq[:,d,d]=False; tot[:,d,d]=False
    T=tot.sum()
    return eq.sum()/T if T else np.nan
rows=[]
for q,p in enumerate(PAIRS):
    pid=p['id']; lab=LAB.get(pid)
    if lab not in ('twin','facet'): continue
    a,b=pid.split('|'); A,B=M[a],M[b]
    ia=np.array([ix[k] for k in A-B if k in ix]); ib=np.array([ix[k] for k in B-A if k in ix])
    ic=np.array([ix[k] for k in A&B if k in ix]); iu=np.concatenate([ia,ib,ic]).astype(int)
    ia=ia.astype(int); ib=ib.astype(int)
    u=len(A|B); si=next(i for i,s in enumerate(SC) if s>=u); si2=min(si+1,len(SC)-1)
    Lr=L[:,si]; Lr2=L[:,si2]
    f=dict(id=pid)
    f['F1']=rate(Lr,P,ia,ib,False)
    wa=rate(Lr,P,ia,ia,True) if len(ia)>1 else np.nan; wb=rate(Lr,P,ib,ib,True) if len(ib)>1 else np.nan
    f['F2']=np.nanmean([wa,wb])-f['F1'] if not (np.isnan(wa) and np.isnan(wb)) else np.nan
    f['F3']=rate(Lr,P,iu,iu,True)
    f['F4']=rate(Lr2,P,ia,ib,False)
    iA=np.array([ix[k] for k in A if k in ix]); iB=np.array([ix[k] for k in B if k in ix])
    same=0;cnt=0
    for r in range(L.shape[0]):
        la=Lr[r,iA][P[r,iA]]; lb=Lr[r,iB][P[r,iB]]
        if len(la)==0 or len(lb)==0: continue
        va,ca=np.unique(la,return_counts=True); vb,cb=np.unique(lb,return_counts=True)
        same+=int(va[ca.argmax()]==vb[cb.argmax()]); cnt+=1
    f['F5']=same/cnt if cnt else np.nan
    f['scale']=SC[si]
    rows.append(f)
    if q%500==0: print(q,time.time()-t,flush=True)
json.dump(rows,open('/tmp/tf_runs.json','w'),default=float)
print('done',len(rows),time.time()-t)
