from datetime import date
import pandas as pd
import sys
import numpy as np
import warnings
from tqdm import tqdm
import os
import glob

cointResults = pd.read_csv("cointResults/networkCointResults.csv")
uniqueProducts = cointResults['Product'].unique()
speedOfAdjustmentResults = pd.DataFrame()
for uniqueProduct in uniqueProducts:
    productCointResults= cointResults.loc[cointResults['Product'] == uniqueProduct]
    productCointResults['issues']=0
    productCointResults['Helper']=None
    for index, row in productCointResults.iterrows():
        #sort og and dest so that we have something to aggregate pairs
        l =list([row['Origin'],row['Destination']])
        l = sorted(l)
        productCointResults.at[index, 'sortedOgDest'] = ''.join(l)
        productCointResults.at[index, 'Helper'] = uniqueProduct+row['Origin']+row['Destination']

        #identify VECMEligible
        if(row['vecmEligible']=="TRUE"):
            productCointResults.at[index, 'vecmEligibleBool'] = 1
        else:
            productCointResults.at[index, 'vecmEligibleBool'] = 0

        #identify cointegrated
        if(row['EngleGranger_results']=="Cointegrated"):
            productCointResults.at[index, 'cointBool'] = 1
        else:
            productCointResults.at[index, 'cointBool'] = 0
    
    ##calculate if they are truly cointegrated. Sometimes when done individually one directed pair is not and the other is. If any are cointegrated, say they both are.
    for index, row in productCointResults.iterrows():
        pair = row['sortedOgDest']
        pairDf = productCointResults.loc[productCointResults['sortedOgDest'] == pair]
        pairDf = pairDf.replace({'(None,)': None}, regex=True)
        pairDf.vecm_alphaOrigin_pvalue = pairDf.vecm_alphaOrigin_pvalue.astype(float)
        pairDf.vecm_A_rSquared = pairDf.vecm_A_rSquared.astype(float)
        pairDf.vecm_alphaOrigin = pairDf.vecm_alphaOrigin.astype(float)

        if(pairDf['cointBool'].sum()>0):
            productCointResults.at[index, 'pairCoint'] = 1
        else:
            productCointResults.at[index, 'pairCoint'] = 0

        if(pairDf['vecmEligible'].sum()==2):
            productCointResults.at[index, 'pairIntegrated'] = 1
        else:
            productCointResults.at[index, 'pairIntegrated'] = 0

        pairSAD = 0
        for index2, row2 in pairDf.iterrows():
            if(row2['vecm_alphaOrigin_pvalue']<0.10 and row2['vecm_A_rSquared']>0.10):
                pairSAD = pairSAD + abs(row2['vecm_alphaOrigin'])
            else:
                productCointResults.at[index, 'issues'] = 1
        productCointResults.at[index, 'pairSAD'] = pairSAD

    productCointResults = productCointResults.drop_duplicates('sortedOgDest', keep='last') 
    
    results = productCointResults[['Product','Origin','Destination','Helper','pairLength','pairCoint','pairIntegrated','pairSAD','issues']]
    speedOfAdjustmentResults = pd.concat([speedOfAdjustmentResults, results])
print(speedOfAdjustmentResults)
print("=====OUTPUT TO ./pairwiseResults/pairwiseResults.csv")
speedOfAdjustmentResults.to_csv("./pairwiseResults/pairwiseResults.csv")