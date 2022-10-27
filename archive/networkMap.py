import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

'''
data = pd.read_csv('mapData/Maize-lines.csv')
G = nx.from_pandas_edgelist(df=data, source='origin', target='dest', edge_attr='lineSize',create_using = nx.DiGraph())
nx.draw(G)
plt.show()
'''
G=nx.Graph()
nodes = pd.read_csv('./mapData/Maize-marketplaces.csv')
edges = pd.read_csv('./mapData/Maize-lines.csv')
for index, row in nodes.iterrows():
    name = row['name']
    nodeLat = row['lat']
    nodeLong = row['long']
    G.add_node(name,pos=(nodeLong,nodeLat))

for index, row in edges.iterrows():
    origin = row['Origin']
    dest = row['Destination']
    weight = round(row['lineSize'])
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
labels = nx.get_edge_attributes(G,'weight')
nx.draw_networkx_edge_labels(G,pos,edge_labels=labels)
#nx.draw_networkx(G,pos)
plt.show()