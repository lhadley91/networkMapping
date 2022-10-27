import numpy as np
from numpy.lib.arraysetops import unique
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import itertools
from tqdm import tqdm

def all_possible_paths(G):
    roots = []
    leaves = []
    all_possible_paths_list = []
    for node in G.nodes :
        roots.append(node)
        leaves.append(node)

    for root in tqdm(roots) :
        print("Root:",root)
        for leaf in tqdm(leaves) :
            print("Leaf:",leaf)
            for path in tqdm(nx.all_simple_edge_paths(G, root, leaf,7)) :
                all_possible_paths_list.append(path)

    return all_possible_paths_list

pairwiseResults = pd.read_csv("./pairwiseResults/pairwiseResults.csv")
uniqueProducts = pairwiseResults['Product'].unique()
for uniqueProduct in uniqueProducts:
    print(uniqueProduct)
    G=nx.Graph()
    nodes = pd.read_csv('./mapData/'+uniqueProduct+'-marketplaces.csv')
    edges = pd.read_csv('./mapData/'+uniqueProduct+'-lines.csv')
    for index, row in nodes.iterrows():
        name = row['name']
        nodeLat = row['lat']
        nodeLong = row['long']
        G.add_node(name,pos=(nodeLong,nodeLat))

    for index, row in edges.iterrows():
        origin = row['Origin']
        dest = row['Destination']
        weight = row['lineSize']
        G.add_edge(origin,dest, weight=weight)

    widths = nx.get_edge_attributes(G, 'weight')
    nodelist = G.nodes()
    pos=nx.get_node_attributes(G,'pos')


    nx.draw_networkx_nodes(G,pos,
                        nodelist=nodelist,
                        node_size=300,
                        node_color='black',
                        alpha=0.8)   
    nx.draw_networkx_edges(G,pos,
                        edgelist = widths.keys(),
                        width=list(widths.values()),
                        min_source_margin =0,
                        min_target_margin = 0,
                        edge_color='blue', 
                        alpha=1)
    #labels = nx.get_edge_attributes(G,'weight')
    #nx.draw_networkx_edge_labels(G,pos,edge_labels=labels)
    eigenvector_centrality = nx.eigenvector_centrality(G,max_iter=1000,weight="weight")
    eigDF = pd.DataFrame(data=eigenvector_centrality, index=["EigCentralityValue"]).transpose().sort_values(by=['EigCentralityValue'])
    eigDF.to_csv("./networkAnalysis/eigenvector/"+uniqueProduct+"-eigvector.csv")


    chainDf = pd.DataFrame({'Chain':all_possible_paths(G), "Length":0})
    for index, row in tqdm(chainDf.T.iteritems()):
        chainSum = 0
        oneLevelDownEdgeWeight=0
        chainLength = len(row['Chain'])
        startingChain = row['Chain'][0]
        startingEdgeWeight = G.get_edge_data(*startingChain)['weight']
        oneLevelDownChain = row['Chain'][:-1]
        if(len(oneLevelDownChain)>0):
            for chainEdge in oneLevelDownChain:
                oneLevelDownChainEdgeWeight = G.get_edge_data(*chainEdge)['weight']
                oneLevelDownEdgeWeight = oneLevelDownEdgeWeight+oneLevelDownChainEdgeWeight
            oneLevelDownEdgeWeight = oneLevelDownEdgeWeight/len(oneLevelDownChain)

        for chainEdge in row['Chain']:
            chainEdgeWeight = G.get_edge_data(*chainEdge)['weight']
            chainSum = chainSum+chainEdgeWeight 
        
        chainDf.at[index, 'Length'] = chainLength
        chainDf.at[index, 'ChainAverage'] = chainSum/chainLength
        chainDf.at[index, 'startingChain'] = str(startingChain)
        chainDf.at[index, 'startingEdgeWeight'] = startingEdgeWeight
        chainDf.at[index, 'oneLevelDown'] = str(oneLevelDownChain)
        chainDf.at[index, 'oneLevelDownEdgeWeight'] = oneLevelDownEdgeWeight
        chainDf.at[index, 'marginalAvgIncrease'] = (chainSum/chainLength)-oneLevelDownEdgeWeight
    chainDf.to_csv("./networkAnalysis/chains/"+uniqueProduct+"-chainAnalysis.csv")
    exit()
#nx.draw_networkx(G,pos)
#plt.show()