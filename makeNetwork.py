import pandas as pd
import numpy as np
import ast

srcDataFilePath = "./networks/initialmapping.csv"
networkInit = pd.read_csv(srcDataFilePath)
networkAvailabilityResultsFilePath = "./dataNetworks/networkAvailabilityResults.csv"
networkAvailabilityResults = pd.read_csv(networkAvailabilityResultsFilePath)
maxIteration = 1 ##I'm not sure if this works for >1
marketsCountThreshold =10

def findNetwork(og_market, availableMarkets): 
    #Get Original network
    origin_network = networkInit.loc[networkInit["Origin"] == og_market]
    print(origin_network)
    origin_dests = origin_network["Destination"].unique()
    
    ##find a list of those not available to start our search
    missingDests = list(set(origin_dests)-set(availableMarkets))
    
    outputNetwork = list()
    if len(missingDests)==0:
        print("All Available")
        outputNetwork = origin_dests.tolist()
        print(outputNetwork)
    else:
        outputNetwork = list(set(origin_dests)-set(missingDests))
        print("Missing and need to follow: "+str(missingDests) )

    iteration = 0
    '''DEBUG
    if(og_market=="Nairobi"):
        print(og_market)
        print(outputNetwork)
        print(str(missingDests))
        input()
    '''
    while len(missingDests)>0 and iteration < maxIteration:
        print("Iteration:"+str(iteration))
        print("Current network is: " + str(outputNetwork))
        print("Current Missing and need to follow: "+str(missingDests))
        if(len(missingDests)==0 or "nextIterMissingDests" not in locals()):
            nextIterMissingDests = list()
        for new_og_market in missingDests:
            print("  We are finding the continuing network for missing market :"+new_og_market)
            
            missingDests.remove(new_og_market) ##remove current start

            newOriginData = networkInit.loc[networkInit["Origin"] == new_og_market]
            
            for index, row in newOriginData.iterrows():
                if(row["Destination"] in availableMarkets and row["Destination"] != og_market and row["Destination"] not in outputNetwork):
                    print("    Adding "+row["Destination"]+" to Network")
                    outputNetwork.append(row["Destination"])
                elif(row["Destination"] not in nextIterMissingDests and row["Destination"] not in outputNetwork and row["Destination"] != og_market):
                    print("    Missing and To Follow: "+row["Destination"])
                    nextIterMissingDests.append(row["Destination"])
                    print("   Next Iteration includes: ", str(nextIterMissingDests))
        if(len(missingDests)==0 and iteration < maxIteration):
            iteration = iteration+1
            missingDests = nextIterMissingDests
    '''DEBUG
    if(og_market=="Nairobi"):
        print(outputNetwork)
        print(missingDests)
        input()
    '''
    return list(set(outputNetwork))


networkMapResults = pd.DataFrame()
for index, row in networkAvailabilityResults.iterrows():
    product = row['Product']
    marketsCount = row['marketsCount']
    availableMarkets = row['markets']
    availableMarkets = ast.literal_eval(availableMarkets)

    print(availableMarkets)
    if marketsCount>marketsCountThreshold:
        for ogmarket in availableMarkets:
            print("Product: ", product)
            marketNetwork = findNetwork(ogmarket,availableMarkets)
            for destmarket in marketNetwork:
                results = { "Product":product,
                    "Origin":ogmarket,
                    "Destination":destmarket
                }   
                results = pd.DataFrame.from_dict([results])
                networkMapResults = pd.concat([networkMapResults, results])
print("---OUTPUT TO /dataNetworks/networkMapResults.csv---")
networkMapResults.to_csv("./dataNetworks/networkMapResults.csv")
