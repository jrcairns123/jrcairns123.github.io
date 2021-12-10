import pandas as pd
import numpy as np
from collections import defaultdict
from itertools import combinations
import csv
import networkx as nx
from networkx.algorithms.community.modularity_max import greedy_modularity_communities

def processData(file, options = ['korea','other']):

    if options == 'korea':
        df = pd.read_csv(file, header=None, index_col=0, low_memory=False)
    else:
        df = pd.read_csv(file, header=None, index_col=0)
        
    df_filtered = df[(df[7]==400) | (df[7]==420) | (df[7]==430) | (df[7]==440)].iloc[:,7:]
    x = df_filtered[df_filtered.columns[1::3]].columns.union([22,37])
    toStack = [df_filtered[x].iloc[:,:6],df_filtered[x].iloc[:,6:]]
    
    columnNames = ["Top","Jungle","Middle","Bot","Support","Win"]
    for i in toStack:
        i.columns=columnNames

    df = pd.concat(toStack).reset_index(drop=True)
    
    if options == 'korea':
        df['Win'] = df['Win'].replace("TRUE",1)
        df['Win'] = df['Win'].replace("True",1)
        df['Win'] = df['Win'].replace("FALSE",1)
        df['Win'] = df['Win'].replace("False",1)
    
    df['Win'] = df['Win'].astype(int)
    
    return df

def update_champ_counts(champ_counts, teams):
    for a in teams:
        champ_counts[a] += 1

def update_champ_pair_counts (champ_pair_counts, teams):
    for (a, b) in combinations (teams, 2):
        champ_pair_counts[(a, b)] += 1
        champ_pair_counts[(b, a)] += 1

def update_champ_pair_wins(champ_pair_wins, teams):
    for (a, b) in combinations (teams, 2):
        if teams[5] == 1:
            champ_pair_wins[(a, b)] += 1
            champ_pair_wins[(b, a)] += 1

def filter_rules(champ_pair_counts, champ_counts, conf_threshold, size):
    rules = {}
    lifts = {}
    for (a, b) in champ_pair_counts:
        conf_ab = champ_pair_counts[(a, b)] / champ_counts[a] * 100
        conf_ba = champ_pair_counts[(a, b)] / champ_counts[b] * 100
        lift_ab = (champ_pair_counts[(a, b)]/size) / (champ_counts[a]/size *champ_counts[b]/size)
        if conf_ab >= conf_threshold:
            rules[(a, b)] = conf_ab
            rules[(b, a)] = conf_ba
            if lift_ab > 1:
                lifts[(a,b)] = lift_ab
                lifts[(b,a)] = lift_ab
    return rules, lifts

def filter_supports(champ_pair_counts, allTeams, sup_threshold):
    supports = {}
    for k,v in champ_pair_counts.items():
        #toKey = tuple(sorted(list(k)))
        supp_ab = v/len(allTeams)*100
        if supp_ab >= sup_threshold:
            supports[k] = supp_ab
    return supports

def mine_rules(allTeams, withWins, sup_threshold, conf_threshold):
    champ_pair_counts = defaultdict(int)
    champ_counts = defaultdict(int)
    champ_pair_wins = defaultdict(int)
    size = len(allTeams)

    for teams in allTeams:
        update_champ_pair_counts(champ_pair_counts, teams)
        update_champ_counts(champ_counts, teams)
    
    for teams in withWins:
        update_champ_pair_wins(champ_pair_wins, teams)
    
    rules, lifts = filter_rules(champ_pair_counts, champ_counts, conf_threshold,size)
    supports = filter_supports(champ_pair_counts, allTeams, sup_threshold)
    
    return supports, rules, lifts,champ_pair_counts, champ_pair_wins

def filterGraph(z1,z2,z3,z4,z5, winRates):
    champ_win_rates = dict(((key, z5[key]/z4[key]) for key in z4.keys()))
    filtered_win_rates = dict(((k,v) for k,v in champ_win_rates.items() if v > winRates))
    
    filter_conf_by_supp = dict((k,v) for k,v in z1.items() if k in z2.keys())
    filter_conf_supp_by_lift = dict((k,v) for k,v in filter_conf_by_supp.items() if k in z3.keys())
    
    filtered_supps = dict(((k,v) for k,v in filter_conf_supp_by_lift.items() if k in filtered_win_rates.keys()))
    
    finalDict = {}
    for k,v in filtered_supps.items():
        toKey = tuple(sorted(list(k)))
        if toKey not in finalDict:
            finalDict[toKey]=v
    return finalDict

def createEdges(finalDict):
    finalList = []
    for item, values in finalDict.items():
        finalList.append([item[0],item[1],values])
    return finalList

def createNodes(finalDict, finalList):
    nodesData = defaultdict(int)
    for item, values in finalDict.items():
        if (item[0] not in nodesData.keys()) or (item[1] not in nodesData.keys()):
            nodesData[item[0]]
            nodesData[item[1]]
    
    finalNodes = []
    for item, values in nodesData.items():
        finalNodes.append([item,values])
     
    G = nx.Graph()
    for a in finalList:
        G.add_edge(a[0],a[1],weight = a[2])
    
    communities= sorted(greedy_modularity_communities(G))
    
    for i in range(len(finalNodes)):
        for j in range(len(communities)):
            if finalNodes[i][0] in communities[j]:
                if len(communities[j]) == 1:
                    finalNodes[i][1] = 0
                else:    
                    finalNodes[i][1] = j+1
    return finalNodes

def runAlgos(file, winRate, supp_T):
    x = file
    x_1 = x.drop(columns=['Win']).to_numpy()
    x_2 = x.to_numpy() 
    
    z1, z2, z3, z4, z5 = mine_rules(x_1,x_2,supp_T,5)
    
    finalDict = filterGraph(z1,z2,z3,z4,z5,winRate) 
    finalEdges = createEdges(finalDict)
    finalNodes = createNodes(finalDict, finalEdges)

    
    return finalNodes, finalEdges

kr = processData('data/matchdata_kr.csv', 'korea')
eun = processData('data/matchdata_eun1.csv', 'other')
euw = processData('data/matchdata_euw1.csv','other')
jp = processData('data/matchdata_jp1.csv','other')
na = processData('data/matchdata_na1.csv','other')
pdList = [kr, eun, euw, jp, na]
allDf = pd.concat(pdList)

## unhash to run:
## for kr, supp_T = 0.5
## for rest (inclusive of allDf), supp_T = 0.1

## finalNodes, finalEdges = runAlgos(kr, 0.55, 0.5)
## be sure to create file in format: edges_{region}.csv

## headers = ['source', 'target', 'value']
## with open("edges_kr.csv", "w", newline="") as e:
##    writer = csv.writer(e)
##    writer.writerow(headers)
##    writer.writerows(finalEdges)

## headers = ['id','group']
## with open('nodes_kr.csv','w',newline='') as n:
##    writer = csv.writer(n)
##    writer.writerow(headers)
##    writer.writerows(finalNodes)