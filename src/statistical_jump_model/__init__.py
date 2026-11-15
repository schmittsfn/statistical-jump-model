"""Research implementation; see README.md for source conventions and limits."""
import math
import numpy as np
import pandas as pd

VERSION = "source-contracts/1"

JUMP_FEATURES=['downside_10','sortino_20','sortino_60']
JUMP_CONVENTIONS={
    'source':'Shu, Yu and Mulvey arxiv:2402.05272v3 sections 3.4.1–3.4.3',
    'features':'excess returns; DD10, Sortino20, Sortino60; no log or clipping',
    'downside':'sqrt weighted negative-return second moment; printed equation omits sqrt, author code and annualization support sqrt',
    'ewm':'normalized geometric weights (adjust=True); all available past observations',
    'standardization':'training population mean/std, ddof=0',
    'labels':'author sort_by=cumret; state0 bull, state1 bear; missing states sorted last and unreachable',
    'initial_fit':'first January/July session with at least3000 complete prior feature observations',
    'training':3000,'inference':3000,'refit':'first session of January/July, fit through preceding session',
    'validation':'eight calendar years of online strategy returns; monthly selection',
    'penalty_grid':[0.,1.,3.,10.,30.,100.,300.,1000.],
    'execution':'signal t affects return t+2; 10bp per exposure change',
    'unresolved':'paper omits grid, EWM initialization, cash conversion, exact refit dates and normalization convention',
}


def jump_features(excess):
    if not isinstance(excess,pd.Series) or excess.index.has_duplicates or not excess.index.is_monotonic_increasing:
        raise ValueError('ordered unique excess returns required')
    if not np.isfinite(excess).all():raise ValueError('missing or nonfinite excess returns')
    squared=excess.clip(upper=0).pow(2)
    out=pd.DataFrame(index=excess.index)
    for h in (10,20,60):
        downside=np.sqrt(squared.ewm(halflife=h,adjust=True).mean())
        if h==10:out['downside_10']=downside
        else:out['sortino_'+str(h)]=excess.ewm(halflife=h,adjust=True).mean()/downside.where(downside>0)
    return out


def jump_terminal(features,centers,penalty):
    from jumpmodels.jump import dp
    x=np.asarray(features,float);c=np.asarray(centers,float)
    if x.ndim!=2 or c.shape!=(2,x.shape[1]) or not len(x) or not np.isfinite(x).all() or (np.isinf(c).any() or not np.isfinite(c).all(axis=1).any()) or not np.isfinite(penalty) or penalty<0:
        raise ValueError('invalid jump inference inputs')
    losses=.5*np.square(x[:,None,:]-c[None,:,:]).sum(axis=2)
    value=dp(losses,np.array([[0.,penalty],[penalty,0.]]),return_value_mx=True)
    return int(np.argmin(value[-1]))


def jump_strategy_returns(asset,cash,bull,cost=.001):
    if not asset.index.equals(cash.index) or not asset.index.equals(bull.index):raise ValueError('strategy inputs must align')
    exposure=bull.astype(float).shift(2)
    turnover=exposure.diff().abs()
    first=exposure.first_valid_index()
    if first is not None:turnover.loc[first]=abs(exposure.loc[first])
    return cash+exposure*(asset-cash)-cost*turnover


def fit_jump_features(features,excess,penalty,seed=137):
    from jumpmodels.jump import JumpModel
    from threadpoolctl import threadpool_limits
    if len(features)!=3000 or not features.index.equals(excess.index) or not np.isfinite(features).all().all():
        raise ValueError('jump calibration requires 3000 aligned complete feature observations')
    mean=features.mean().to_numpy();scale=features.std(ddof=0).to_numpy()
    if (scale<=1e-12).any():raise ValueError('degenerate jump features')
    model=JumpModel(n_components=2,jump_penalty=float(penalty),cont=False,n_init=10,random_state=seed,max_iter=1000,tol=1e-8)
    with threadpool_limits(limits=1):model.fit((features-mean)/scale,ret_ser=excess,sort_by='cumret')
    centers=[[None if np.isnan(value) else float(value) for value in row] for row in model.centers_]
    return {'version':VERSION,'centers':centers,'mean':mean.tolist(),'scale':scale.tolist(),
            'adverse_state':1,'penalty':float(penalty),'seed':seed,
            'train_start':str(features.index[0].date()),'train_end':str(features.index[-1].date())}


def jump_rolling_states(features,fit,positions,window=3000):
    from numba import njit
    # Two-state recurrence is identical to author DP; compilation avoids repeated Python loops.
    @njit
    def terminal_states(losses,positions,window,penalty):
        result=np.empty(len(positions),np.int64)
        for j in range(len(positions)):
            end=positions[j];start=end-window+1
            a=losses[start,0];b=losses[start,1]
            for i in range(start+1,end+1):
                a,b=losses[i,0]+min(a,b+penalty),losses[i,1]+min(b,a+penalty)
            result[j]=0 if a<=b else 1
        return result
    x=(features.to_numpy(float)-np.array(fit['mean']))/np.array(fit['scale'])
    positions=np.asarray(positions,dtype=np.int64)
    if not np.isfinite(x).all() or (positions<window-1).any() or (positions>=len(x)).any():raise ValueError('incomplete rolling inference window')
    centers=np.array(fit['centers'],dtype=float);losses=.5*np.square(x[:,None,:]-centers[None,:,:]).sum(axis=2)
    losses[np.isnan(losses)]=np.inf  # Author DP makes missing clusters unreachable.
    labels=terminal_states(losses,positions,window,float(fit['penalty']))
    return pd.Series(labels!=fit['adverse_state'],index=features.index[positions],name='bull')


def jump_policy(asset_returns,cash_returns,seed=137):
    """One chronological recipe for current readings and historical applications."""
    if not asset_returns.index.equals(cash_returns.index) or not isinstance(asset_returns.index,pd.DatetimeIndex):
        raise ValueError('dated aligned asset and cash returns required')
    if not np.isfinite(asset_returns).all() or not np.isfinite(cash_returns).all():raise ValueError('complete asset and cash returns required')
    excess=asset_returns-cash_returns;features=jump_features(excess)
    valid=np.isfinite(features).all(axis=1)
    if not valid.any():raise ValueError('no complete jump features')
    first=int(np.flatnonzero(valid)[0]);features=features.iloc[first:];excess=excess.reindex(features.index)
    if not np.isfinite(features).all().all():raise ValueError('interior missing jump features')
    index=features.index;n=len(index);window=3000
    if n<=window+2:raise ValueError('insufficient history for 3000-day jump calibration')
    starts=[i for i in range(window,n) if index[i].month in (1,7) and index[i].month!=index[i-1].month]
    if not starts or starts[0]+2>=n:raise ValueError('insufficient history after first eligible semester calibration')
    candidates={};fits=[];failures=[]
    for penalty in JUMP_CONVENTIONS['penalty_grid']:
        bull=pd.Series(np.nan,index=index)
        for start,stop in zip(starts,starts[1:]+[n]):
            try:
                fit=fit_jump_features(features.iloc[start-window:start],excess.iloc[start-window:start],penalty,seed)
                values=jump_rolling_states(features.iloc[:stop],fit,np.arange(start,stop))
                bull.iloc[start:stop]=values.to_numpy(float)
                fits.append({**fit,'signal_start':str(index[start].date()),'signal_end':str(index[stop-1].date())})
            except (ValueError,RuntimeError,AssertionError) as exc:
                failures.append({'penalty':penalty,'start':str(index[start].date()),'reason':str(exc)})
        candidates[penalty]=bull
    returns={p:jump_strategy_returns(asset_returns.reindex(index),cash_returns.reindex(index),v) for p,v in candidates.items()}
    selected=pd.Series(np.nan,index=index);penalties=selected.copy();selections=[]
    month_ends=[i for i in range(n-1) if index[i].month!=index[i+1].month]
    from ._calendar import calendar
    sessions=calendar(index[-1].year).schedule.index
    this_month=sessions[(sessions.year==index[-1].year)&(sessions.month==index[-1].month)]
    if len(this_month) and index[-1]==this_month[-1]:month_ends.append(n-1)
    for pos,end in enumerate(month_ends):
        cutoff=index[end];validation_start=cutoff-pd.DateOffset(years=8)
        if validation_start<index[starts[0]+2]:continue
        trials=[]
        for penalty,r in returns.items():
            sample=(r-cash_returns.reindex(index)).loc[validation_start:cutoff]
            if sample.empty or sample.isna().any() or sample.std(ddof=1)<=0:continue
            trials.append({'penalty':penalty,'sharpe':float(sample.mean()/sample.std(ddof=1)*np.sqrt(252))})
        if not trials:continue
        winner=max(trials,key=lambda r:r['sharpe'])['penalty']
        stop=month_ends[pos+1] if pos+1<len(month_ends) else n
        # Month-end selection governs that close's signal; it affects returns two sessions later.
        selected.iloc[end:stop]=candidates[winner].iloc[end:stop]
        penalties.iloc[end:stop]=winner
        selections.append({'at':str(cutoff.date()),'validation_start':str(validation_start.date()),'penalty':winner,'trials':trials})
    return {'bull':selected,'penalty':penalties,'fits':fits,'selections':selections,'failures':failures,
            'returns':jump_strategy_returns(asset_returns.reindex(index),cash_returns.reindex(index),selected),
            'conventions':JUMP_CONVENTIONS}
