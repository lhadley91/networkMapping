from datetime import date
import pandas as pd
from statsmodels.tsa.stattools import adfuller
from matplotlib import pyplot
import numpy as np
from arch.unitroot import PhillipsPerron
from arch.unitroot import ZivotAndrews
from tqdm import tqdm

def stationaryTest(marketData, threshold):
    #Note that we want our data to be stationary in order to work with it. See https://towardsdatascience.com/achieving-stationarity-with-time-series-data-abd59fd8d5a0
    ADFresult = adfuller(marketData, autolag='AIC')
    ADFStatistic = ADFresult[0]
    ADFp_value = ADFresult[1]
    ADFn_lags = ADFresult[2]
    if (ADFp_value>=threshold):
        ADFisStationary = 'Fail to reject the null hypothesis (H0), the data has a unit root and is non-stationary.'
    else:
        ADFisStationary = 'Reject the null hypothesis (H0), the data does not have a unit root and is stationary.'
    PPresult = PhillipsPerron(marketData)
    PPp_value = PPresult.pvalue
    PPp_lags = PPresult.lags
    if (PPp_value>=threshold):
        PPisStationary = "Fail to reject the null hypothesis (H0), which is " +PPresult.null_hypothesis
    else:
        PPisStationary = "Reject the null hypothesis and accept the alternative hypothesis, which is: " + PPresult.alternative_hypothesis
    
    
    results = {"ADFStatistic":ADFStatistic,
                "ADFp_value":ADFp_value,
                "ADFisStationary":ADFisStationary,
                "ADFn_lags":ADFn_lags,
                "PPp_value":PPp_value,
                "PPn_lags":PPp_lags,
                "PPisStationary":PPisStationary
                }
    return results


productCol = "Product"
dateCol = "Date"
dataCountThreshold=15
srcDataFilePath = "./formattedSrc/formattedSrc-deflated.csv"
srcPrices = pd.read_csv(srcDataFilePath, thousands=',')
allStationarityTestResults = pd.DataFrame()

uniqueProducts = srcPrices[productCol].unique()
##get unique products and loop through each
for uniqueProduct in tqdm(uniqueProducts):
    productName = uniqueProduct
    productDf = srcPrices.loc[srcPrices[productCol] == productName]
    print("===="+productName+"====")
    ##go through each marketplace
    for (columnName, columnData) in productDf.iteritems():
        if columnName != dateCol and columnName != productCol:
            marketName = columnName
            marketData = columnData.dropna()
            marketDataCount = marketData.count()
            print("   "+marketName+" - data: "+str(marketDataCount))

            if(marketDataCount<dataCountThreshold):     ##skip those with too few datapoints
                print("      Error: Too Few Datapoints")
                continue

            #ADF test at level
            stationaryTestResults = stationaryTest(marketData, 0.05)
            levelResults = pd.DataFrame.from_dict([stationaryTestResults]).add_prefix("levels_")
            
            #ADF test at log
            marketDataLog = np.log(marketData)
            stationaryTestResults = stationaryTest(marketDataLog, 0.05)
            logResults = pd.DataFrame.from_dict([stationaryTestResults]).add_prefix("log_")
            
            #ADF test with difference
            marketDataDiff = marketData.diff().dropna()
            stationaryTestResults = stationaryTest(marketDataDiff, 0.05)
            diffResults = pd.DataFrame.from_dict([stationaryTestResults]).add_prefix("diff_")

            concatResults = pd.concat([levelResults, logResults,diffResults], axis=1, join="inner")
            concatResults.loc[:,productCol] = productName
            concatResults.loc[:,"Marketplace"] = marketName
            concatResults.loc[:,"Obs"] = marketDataCount
            allStationarityTestResults = pd.concat([allStationarityTestResults, concatResults])
print(allStationarityTestResults)
allStationarityTestResults.to_csv("./stationaryTestResults/stationaryTestResults.csv")