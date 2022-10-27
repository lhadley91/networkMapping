import numpy as np
import pandas as pd
from tqdm import tqdm


srcDataFilePath = "./formattedSrc/formattedSrc-deflated.csv"
srcMasterNetworkFilePath = "./networks/initialmapping.csv"
dataNetworkPath = "./dataNetworks/"
dateCol = "Date"
productCol= "Product"
densityThreshold = 30

srcPrices = pd.read_csv(srcDataFilePath, thousands=',', index_col=dateCol)
masterNetwork = pd.read_csv(srcMasterNetworkFilePath, thousands=',')

networkDensityResults = pd.DataFrame()

uniqueProducts = srcPrices[productCol].unique()
for uniqueProduct in tqdm(uniqueProducts):
    productPrices= srcPrices.loc[srcPrices[productCol] == uniqueProduct]

    for index, row in masterNetwork.iterrows():
        origin = row['Origin']
        destination = row['Destination']
        if(origin in ["Owino","Kimironko"] or destination in ["Owino","Kimironko"]):
            continue
        pairData = productPrices[[origin,destination]].diff().dropna()
        diffLength = len(pairData)
        
        results = { productCol:uniqueProduct,
                    "Origin":origin,
                    "Destination":destination,
                    "OriginStationarity":1,
                    "DestinationStationarity": 1,
                    "diffLength":diffLength
                    }
        results = pd.DataFrame.from_dict([results])
        networkDensityResults = pd.concat([networkDensityResults, results])
networkDensityResults.to_csv(dataNetworkPath+"networkDensityResults.csv")

##Estimate Network Availability
networkAvailabilityResults = pd.DataFrame()
for uniqueProduct in tqdm(uniqueProducts):
    productPrices= networkDensityResults.loc[networkDensityResults[productCol] == uniqueProduct]
    uniqueMarkets = productPrices['Origin'].unique()
    availableMarkets = list()
    for uniqueMarket in tqdm(uniqueMarkets):
        marketDensity = productPrices.loc[productPrices['Origin'] == uniqueMarket]
        medianDensity = marketDensity['diffLength'].mean()
        if(medianDensity>=densityThreshold):
            availableMarkets.append(uniqueMarket)
    results = { productCol:uniqueProduct,
                    "marketsCount":len(availableMarkets),
                    "markets":availableMarkets
                }   
    results = pd.DataFrame.from_dict([results])
    networkAvailabilityResults = pd.concat([networkAvailabilityResults, results])
networkAvailabilityResults.to_csv(dataNetworkPath+"networkAvailabilityResults.csv")
