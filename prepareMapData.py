import pandas as pd
import numpy as np

def removeUnnaturalPairs(uniqueProduct, edgeDf, unnaturalPairDf):
    for index, row in edgeDf.iterrows():
        marketA = row['Origin']
        marketB = row['Destination']
        if((
            (unnaturalPairDf['Product'] == uniqueProduct) & 
            (unnaturalPairDf['MarketplaceA'] == marketA) & 
            (unnaturalPairDf['MarketplaceB'] == marketB)).any()==True):
            edgeDf.drop(index, inplace=True)
    return edgeDf

        


marketCoords = pd.read_csv("./mapData/marketplaceCoords.csv")
pairwiseResults = pd.read_csv("./pairwiseResults/pairwiseResults.csv")
uniqueProducts = pairwiseResults['Product'].unique()
for uniqueProduct in uniqueProducts:
    productPairWiseResults= pairwiseResults.loc[pairwiseResults['Product'] == uniqueProduct]
    nodesList = productPairWiseResults['Origin'].tolist()+productPairWiseResults['Destination'].tolist()
    nodesList = list(set(nodesList))
    nodesDf = pd.DataFrame(nodesList, columns=['market'])

    nodesDf = nodesDf.merge(marketCoords, on='market', how='left')
    nodesDf = nodesDf[['market','country','Latitude','Longitude']]
    nodesDf = nodesDf.rename(columns={"market": "name", "Latitude": "lat", "Longitude": "long"})
    
    nodesDf.to_csv("./mapData/"+uniqueProduct+"-marketplaces.csv")

    ##now EDGES
    edgeDf = productPairWiseResults[['Origin','Destination','pairSAD']]
    edgeDf = productPairWiseResults.loc[(productPairWiseResults['pairCoint']==1)] ##comment out this line to get a undirected map statistics for each product
    
    edgeDf = edgeDf[['Origin','Destination','pairSAD']]
    edgeDf = removeUnnaturalPairs(uniqueProduct, edgeDf, pd.read_csv("./dataNetworks/unnaturalPairs.csv"))
    edgeDf['lineSize'] = edgeDf['pairSAD']
    edgeDf = edgeDf.merge(marketCoords, left_on="Origin", right_on="market", how='left')
    edgeDf = edgeDf.rename(columns={"Latitude": "start_lat", "Longitude": "start_long"})
    edgeDf = edgeDf.merge(marketCoords, left_on="Destination", right_on="market", how='left')
    edgeDf = edgeDf.rename(columns={"Latitude": "end_lat", "Longitude": "end_long"})
    edgeDf = edgeDf[['Origin','Destination','lineSize','start_lat','start_long','end_lat','end_long']]
    
    edgeDf.to_csv("./mapData/"+uniqueProduct+"-lines.csv")
