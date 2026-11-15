import math
import unittest
import numpy as np
import pandas as pd
import statistical_jump_model as models

class JumpReferenceTests(unittest.TestCase):
    def test_features_manual_geometric_weights(self):
        r=pd.Series([-.1,.2,-.3,.1])
        result=models.jump_features(r).iloc[-1]
        for h in (10,20,60):
            weights=np.array([2**(-j/h) for j in (3,2,1,0)])
            weights/=weights.sum()
            dd=math.sqrt(sum(weights*np.minimum(r,0)**2))
            expected=dd if h==10 else sum(weights*r)/dd
            self.assertAlmostEqual(result['downside_10' if h==10 else 'sortino_'+str(h)],expected)

    def test_terminal_dp_exhaustive(self):
        from importlib.util import find_spec
        if not find_spec('jumpmodels'):self.skipTest('optional gauge extra')
        from itertools import product
        x=np.array([[0.],[.8],[.9],[.1]])
        centers=np.array([[0.],[1.]])
        for penalty in (0.,.2,1.):
            for length in range(1,len(x)+1):
                candidates=[]
                for path in product(range(2),repeat=length):
                    loss=sum(.5*float((x[i]-centers[s])@(x[i]-centers[s])) for i,s in enumerate(path))
                    loss+=penalty*sum(path[i]!=path[i-1] for i in range(1,length))
                    candidates.append((loss,path[-1]))
                expected=min(candidates)[1]
                self.assertEqual(models.jump_terminal(x[:length],centers,penalty),expected)

    def test_cumulative_labels_not_mean(self):
        from importlib.util import find_spec
        if not find_spec('jumpmodels'):self.skipTest('optional gauge extra')
        from jumpmodels.base import sort_param_dict
        params={'ret_':np.array([.01,.02]),'proba_':np.array([[1,0],[1,0],[1,0],[0,1]]),'centers_':np.array([[10.],[20.]])}
        sort_param_dict(params,sort_by='cumret')
        self.assertEqual(params['centers_'].ravel().tolist(),[10.,20.])

    def test_empty_and_tied_states_follow_author_sort_and_inference(self):
        from importlib.util import find_spec
        if not find_spec('jumpmodels') or not find_spec('numba'):self.skipTest('optional gauge extra')
        from jumpmodels.base import sort_param_dict
        from jumpmodels.jump import do_E_step
        from unittest.mock import patch
        from types import SimpleNamespace
        import json
        for means in ([.01,np.nan],[.01,.01]):
            params={'ret_':np.array(means),'proba_':np.eye(2),'centers_':np.array([[10.],[20.]])}
            sort_param_dict(params,sort_by='cumret')
            self.assertEqual(params['centers_'].ravel().tolist(),[10.,20.])
        index=pd.bdate_range('2000-01-03',periods=3000)
        features=pd.DataFrame({'a':np.sin(np.arange(3000))},index=index)
        excess=pd.Series(.01,index=index)
        estimator=SimpleNamespace(centers_=np.array([[0.],[np.nan]]),fit=lambda *args,**kwargs:None)
        with patch('jumpmodels.jump.JumpModel',return_value=estimator):
            fit=models.fit_jump_features(features,excess,1000.)
        self.assertEqual(fit['centers'],[[0.],[None]])
        json.dumps(fit,allow_nan=False)
        positions=np.array([2998,2999])
        result=models.jump_rolling_states(features,fit,positions,window=4)
        normalized=(features-fit['mean'])/fit['scale']
        for position in positions:
            x=normalized.iloc[position-3:position+1].to_numpy()
            expected=do_E_step(x,estimator.centers_,np.array([[0.,1000.],[1000.,0.]]),return_value_mx=True)[-1].argmin()
            self.assertEqual(models.jump_terminal(x,fit['centers'],1000.),expected)
            self.assertEqual(result.loc[index[position]],expected==0)
        real_fit=models.fit_jump_features(features,excess,1e9)
        self.assertEqual(real_fit['centers'][1],[None])
        self.assertTrue(models.jump_rolling_states(features,real_fit,positions,window=4).all())

    def test_lag_and_transaction_cost(self):
        r=pd.Series([.1,.2,.3,.4,.5])
        cash=pd.Series([.01]*5)
        signal=pd.Series([True,False,False,True,True])
        result=models.jump_strategy_returns(r,cash,signal)
        self.assertTrue(result.iloc[:2].isna().all())
        self.assertAlmostEqual(result.iloc[2],.3-.001)
        self.assertAlmostEqual(result.iloc[3],.01-.001)
        self.assertAlmostEqual(result.iloc[4],.01)

    def test_rolling_inference_resets_window(self):
        from importlib.util import find_spec
        if not find_spec('jumpmodels') or not find_spec('numba'):self.skipTest('optional gauge extra')
        index=pd.bdate_range('2020-01-01',periods=8)
        features=pd.DataFrame({'a':[0.,.2,.9,.8,.4,.1,.9,.8]},index=index)
        fit={'mean':[0.],'scale':[1.],'centers':[[0.],[1.]],'penalty':.2,'adverse_state':1}
        positions=np.arange(3,8)
        result=models.jump_rolling_states(features,fit,positions,window=4)
        expected=[models.jump_terminal(features.iloc[i-3:i+1],fit['centers'],.2)==0 for i in positions]
        self.assertEqual(result.tolist(),expected)
        pd.testing.assert_series_equal(result.iloc[:3],models.jump_rolling_states(features.iloc[:6],fit,positions[:3],window=4))

    def test_policy_schedule_and_future_invariance(self):
        from unittest.mock import patch
        index=pd.bdate_range('1999-01-04',periods=5600)
        asset=pd.Series(.001+.02*np.sin(np.arange(len(index))*.7),index=index)
        cash=pd.Series(.0001,index=index)
        seen=[]
        def fit(features,excess,penalty,seed):
            self.assertEqual(len(features),3000)
            self.assertEqual(features.index[-1],excess.index[-1])
            seen.append(features.index[-1])
            return {'penalty':penalty,'train_end':str(features.index[-1].date())}
        def states(features,state,positions):
            self.assertLess(pd.Timestamp(state['train_end']),features.index[positions[0]])
            return pd.Series(np.arange(len(positions))%7!=0,index=features.index[positions])
        with patch.object(models,'fit_jump_features',side_effect=fit),patch.object(models,'jump_rolling_states',side_effect=states):
            first=models.jump_policy(asset.iloc[:5500],cash.iloc[:5500])
            later=models.jump_policy(asset,cash)
        pd.testing.assert_series_equal(first['bull'],later['bull'].reindex(first['bull'].index))
        self.assertTrue(first['selections'])
        for row in later['fits']:
            start=pd.Timestamp(row['signal_start'])
            self.assertIn(start.month,(1,7))
            previous=index[index.get_loc(start)-1]
            self.assertNotEqual(start.month,previous.month)
        for row in later['selections']:
            self.assertEqual(pd.Timestamp(row['at'])-pd.DateOffset(years=8),pd.Timestamp(row['validation_start']))
            self.assertGreaterEqual(pd.Timestamp(row['validation_start']),index[3002])
