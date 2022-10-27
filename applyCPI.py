import pandas as pd
import numpy as np
import math
from tqdm import tqdm

def applyCPI(dateCol, workArray2,CPIDf):
    CPIDf =CPIDf.reset_index()
    workArray2 =workArray2.reset_index()
    marketplaceCountries = pd.read_csv("formattedSrc/marketplaceCoords.csv")
    
    maxDate = max(CPIDf['period'])
    minDate = min(CPIDf['period'])
    mask = (workArray2[dateCol] > minDate) & (workArray2[dateCol] <= maxDate)
    workArray2 = workArray2.loc[mask]
    failedMarketSearches = list()
    for market in workArray2:
        #skip non market columns
        if(market == "Product" or market == "Date"):
            continue

        #get country
        try:
            country = marketplaceCountries.loc[marketplaceCountries['Marketplace'] == market].Country.item()
        except:
            workArray2.drop(columns=[market],inplace=True)
            failedMarketSearches.append(market)
            continue
        
        for index, value in workArray2[market].items():
            if math.isnan(value):
                continue
            #get date
            refDate = workArray2.at[index, dateCol]
            #get CPI value
            CPIvalue = CPIDf.loc[(CPIDf['period'] == refDate) & (CPIDf['Area'] == country)].Value.item()
            #calculate deflatedValue
            deflatedValue = value*(100/CPIvalue)
            #apply deflatedValue to cell
            if(deflatedValue==0):
                workArray2.at[index, market] = None
            else:
                workArray2.at[index, market] = deflatedValue
            

    workArray2.set_index([dateCol], inplace=True)
    print("Failed Market Searches (and therefore dropped!): "+str(failedMarketSearches))
    return workArray2