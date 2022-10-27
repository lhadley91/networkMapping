from datetime import date
import pandas as pd
from prepareCPIData import prepareCPIData
from applyCPI import applyCPI
from tqdm import tqdm

srcDataFilePath = "./srcData/RATIN20211014.csv"
srcCPIFilePath = "./CPIData/FAOSTAT_data_10-13-2021.csv"
dateCol = "Date"
pricesCol = "Wholesale"
marketCol = "Market"
productCol = "Product"
dataFreq = "SMS" ##semi-month start frequency (1st and 15th) https://stackoverflow.com/a/53662178/1263330
outlierLimit = 3
startDate = "2016-01-01"
endDate = "2020-03-01"
lowerAbsoluteThreshold = 100
higherAbsoluteThreshold = 10000
diffIter = 2
thresholdDiff2Drop = 0.25
srcPrices = pd.read_csv(srcDataFilePath, thousands=',')
#Drop zeros
srcPrices= srcPrices[srcPrices[pricesCol] >= 0]

#Aggregate the date and markets by averages
srcPrices = srcPrices.groupby([dateCol, productCol, marketCol], as_index=False)[pricesCol].mean()

#Prepare CPI data
CPIDf = prepareCPIData(srcCPIFilePath = srcCPIFilePath, dataFreq = dataFreq)

#rename some pesky markets
srcPrices[marketCol]= srcPrices[marketCol].replace(['Kobero market'], 'Kobero')

#Pivot the data
pivotPrices = (srcPrices.set_index([dateCol, productCol, marketCol])[pricesCol]
    .unstack()
    .reset_index()
    .rename_axis(None, axis=1))

#Add in dates with no data, which were not present in the datafile
pivotPrices[dateCol] = pd.to_datetime(pivotPrices[dateCol], infer_datetime_format=True)


maxDate = max(pivotPrices[dateCol])
minDate = min(pivotPrices[dateCol]).replace(day=1)
workArray = pd.DataFrame()
workArray[dateCol] = pd.bdate_range(start=minDate, end=maxDate)

workArray2 = pd.DataFrame()

workArray = pd.merge(workArray,pivotPrices,how='left',on=dateCol)
#Set Min Date
mask = (workArray[dateCol] > startDate)
workArray = workArray.loc[mask]
#Set Max Date
mask = (workArray[dateCol] < endDate)
workArray = workArray.loc[mask]



uniqueProducts = workArray[productCol].unique()

for uniqueProduct in tqdm(uniqueProducts):
    productName = uniqueProduct
    productDf = workArray.loc[workArray[productCol] == productName]
    productDf.to_csv("tests/test.csv")
    ##remove low values
    for (columnName, columnData) in productDf.iteritems():
        if columnName == dateCol or columnName == productCol:
            continue
        for index, value in columnData.items():
            if(value<=lowerAbsoluteThreshold or value>=higherAbsoluteThreshold):
                productDf.at[index, columnName]=None

    ##remove heartbeats
    for (columnName, columnData) in productDf.iteritems():
        if columnName == dateCol or columnName == productCol:
            continue
        diffCol = "percdiff_"+columnName
        productDf[diffCol] = columnData.pct_change()
        forwardDiffCol = "forwardpercdiff_"+columnName
        productDf[forwardDiffCol] = columnData.pct_change(2)
        productDf[forwardDiffCol] = productDf[forwardDiffCol].shift(-1)
        forwardCol = "forward_"+columnName
        productDf[forwardCol] = columnData.shift(-1)
        lagCol = "lag_"+columnName
        productDf[lagCol] = columnData.shift(1)
        burpCol = "burp_"+columnName
        productDf[burpCol] = None
        for index, value in productDf[diffCol].items():
            cellValue = productDf.at[index, columnName]
            percDiffValue = value
            forwardValue = productDf.at[index, forwardCol]
            forwardpercdiffValue = productDf.at[index, forwardDiffCol]
            lagValue = productDf.at[index, lagCol]
            if(cellValue>0 and
                forwardValue >0 and
                abs(percDiffValue)>.25 and
                lagValue>0 and
                abs(forwardpercdiffValue)<.10):
                productDf.at[index, columnName]=None
        productDf = productDf.drop(columns=[diffCol,forwardDiffCol,forwardCol,lagCol,burpCol])

    
    ##remove sudden shifts
    for (columnName, columnData) in productDf.iteritems():
        if columnName == dateCol or columnName == productCol:
            continue
        
        diffCol = "diff_"+columnName
        productDf[diffCol] = columnData.ffill().diff()
        for n in range(0,diffIter):
            for index, value in productDf[diffCol].items():
                percDiff = abs(value)/productDf.at[index, columnName]
                if percDiff>=thresholdDiff2Drop:
                    productDf.at[index, columnName]=None
            
        productDf = productDf.drop(columns=diffCol)

        productDf[columnName] = productDf[columnName].replace(',', '').astype(float)

    #remove outliers
    for (columnName, columnData) in productDf.iteritems():
        if columnName != dateCol and columnName != productCol:
            
            zCol = "z_"+str(columnName)
            productDf[zCol] = (columnData - columnData.mean())/columnData.std(ddof=0)

            for index, value in productDf[zCol].items():
                if value>=outlierLimit:
                    ##workArray.set_value(index, columnName, None)
                    productDf.at[index, columnName]=None
            productDf = productDf.drop(columns=zCol)
    
    productDf.to_csv("tests/testAfter.csv")
    ##print(productDf['Date'])
    productDf.set_index(dateCol,inplace=True, drop=True)
    productDf = productDf.resample(dataFreq).median()
    productDf.loc[:,productCol] = productName
    workArray2 = pd.concat([workArray2, productDf])


workArray2.to_csv("./formattedSrc/formattedSrc.csv")

#apply CPI transforms
workArray2 = applyCPI(dateCol, workArray2,CPIDf)
workArray2['Kampala'] = workArray2[['Kampala', 'Owino']].mean(axis=1)
workArray2 = workArray2.drop(columns=['Owino'])
workArray2['Kigali'] = workArray2[['Kigali', 'Kimironko']].mean(axis=1)
workArray2 = workArray2.drop(columns=['Kimironko'])
print(workArray2)
workArray2.to_csv("./formattedSrc/formattedSrc-deflated.csv")