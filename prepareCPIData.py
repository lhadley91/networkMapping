import pandas as pd
import numpy as np

def prepareCPIData(srcCPIFilePath, dataFreq):
    CPIDf = pd.read_csv(srcCPIFilePath)
    CPIDf = CPIDf[['Area','Year','Months Code','Value']]
    CPIDf['Area']= CPIDf['Area'].replace(['United Republic of Tanzania'], 'Tanzania')
    CPIDf['Area']= CPIDf['Area'].replace(['Democratic Republic of the Congo'], 'DRC')

    CPIDf['Months Code'] = CPIDf['Months Code'] - 7000
    CPIDf['Months Code'] = CPIDf['Months Code'].astype(str).str.zfill(2)
    CPIDf["period"] = CPIDf["Year"].astype(str) + "-" + CPIDf["Months Code"]
    CPIDf["period"] = pd.to_datetime(CPIDf["period"])
    CPIDf.set_index(['period'], inplace=True)
    CPIDf = CPIDf.groupby('Area').resample(dataFreq).sum()
    CPIDf = CPIDf.replace(0,np.nan)
    CPIDf['Value'] = CPIDf['Value'].interpolate(limit_direction='backward')
    CPIDf.to_csv("./CPIData/CPIInterpolated.csv")
    return CPIDf