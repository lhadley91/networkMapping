import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.vector_ar.vecm import coint_johansen
import statsmodels.tsa.stattools as ts 
from matplotlib import pyplot
def get_johansen(y, p):
##check out https://nbviewer.jupyter.org/github/mapsa/seminario-doc-2014/blob/master/cointegration-example.ipynb
        """
        Get the cointegration vectors at 95% level of significance
        given by the trace statistic test. 
        y is data columns. 
        p is det_order (int) –
            -1 - no deterministic terms
            0 - constant term
            1 - linear trend
        """

        N, l = y.shape
        jres = coint_johansen(y, 0, p)
        trstat = jres.lr1                       # trace statistic
        tsignf = jres.cvt                       # critical values

        for i in range(l):
            if trstat[i] > tsignf[i, 1]:     # 0: 90%  1:95% 2: 99%
                r = i + 1
        jres.r = r
        jres.evecr = jres.evec[:, :r]

        return jres

productCol = "Product"
dateCol = "Date"
dataCountThreshold=15
srcDataFilePath = "./formattedSrc/formattedSrc-deflated.csv"
srcPrices = pd.read_csv(srcDataFilePath, thousands=',')


##get unique products and loop through each
uniqueProducts = srcPrices[productCol].unique()
for uniqueProduct in uniqueProducts:
    productName = uniqueProduct
    productDf = srcPrices.loc[srcPrices[productCol] == productName]
    print("===="+productName+"====")
    cointPair = productDf[["Arusha","Dar es salaam"]]
    cointPair = cointPair.dropna()
    print(cointPair)
    ##johansen test
    p=1
    jres=get_johansen(cointPair,p)
    print("There are "+ str(jres.r)+ "cointegration vectors")

    ##engle Granger bivariate test
    
    EGresult=ts.coint(cointPair["Arusha"], cointPair["Dar es salaam"], autolag="AIC",maxlag=12)
    EGtstat = EGresult[0]
    EGpvalue = EGresult[1]
    EGcritValues = EGresult[2]
    print(EGpvalue)
    cointPair.plot()
    pyplot.show()
    exit()