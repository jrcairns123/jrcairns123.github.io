import pandas as pd
import numpy as np
from collections import defaultdict
from itertools import combinations
import csv

# pick from eun1,euw1,jp1,kr,na1,all
region = "all"

file = "matchdata/matchdata_"+region+".csv"

# support % = % of occurence of a champion pair from all teams played in all matches
sup_threshold = 0.1

# confidence % = % occurence of A-B pair from all teams with champion A
conf_threshold = 5

edges_file_out = "edges_"+region+"_"+str(sup_threshold)+"_"+str(conf_threshold)+".csv"
nodes_file_out = "nodes_"+region+"_"+str(sup_threshold)+"_"+str(conf_threshold)+".csv"

def processData(file):
    # read csv file
    df = pd.read_csv(file, header=None, index_col=0)
    
    # filter based on queueid and subset columns from the 7th index to the last. 
    # index 0-6 includes matchId, gameCreation, gameMode, gameType, gameVersion, mapId, queueId
    #"queueId": 400,
    #"map": "Summoner's Rift",
    #"description": "5v5 Draft Pick games",
    
    #"queueId": 420,
    #"map": "Summoner's Rift",
    #"description": "5v5 Ranked Solo games",
    
    #"queueId": 430,
    #"map": "Summoner's Rift",
    #"description": "5v5 Blind Pick games",
    
    #"queueId": 440,
    #"map": "Summoner's Rift",
    #"description": "5v5 Ranked Flex games",
    df_filtered = df[(df[7]==400) | (df[7]==420) | (df[7]==430) | (df[7]==440)].iloc[:,7:]
    
    ## take every third column starting from the first index, referring to the champ names at the respective lane
    ## so column at index 1 is top lane champion, column at index 3 is jungle lane champion, and so on...
    ## .columns after filtering (df_filtered[df_filtered.columns[1::3]]) 
    ## is to take all column indices for the respective lanes and retrieve an Int64Index list
    ## .union([22,37]) is to add column indices 22 and 37 to this index list in its appropriate element position
    ## the way that the raw data is structured is as followed:
    ## puuid, champName, win (bool true or false) for each player
    ## since all players have a respective win column 
    ## and players 1 - 5 are on the same team whereas players 6-10 are on the other team
    ## column indice 22 refers to the 5th player's win column whereas
    ## indice 37 refers to the 10th player's win column
    ## i took column 22 to be the win column for team 1
    ## and column 37 to be the win column for team 2
    x = df_filtered[df_filtered.columns[1::3]].columns.union([22,37])
    
    # create list of dataframes the first dataframe is team 1 and the second dataframe is team 2
    toStack = [df_filtered[x].iloc[:,:6],df_filtered[x].iloc[:,6:]]
    
    # create list of columns since concat function requires same column names
    columnNames = ["Top","Jungle","Middle","Bot","Support","Win"]
    for i in toStack:
        i.columns=columnNames
        
    # concat stacks the dataframes on top of each other    
    df = pd.concat(toStack).reset_index(drop=True)
    
    # change boolean datatype to int
    
    # kr file has a mix of TRUE/True/FALSE/False which trips up the int conversion
    df['Win'] = df['Win'].replace("TRUE",1)
    df['Win'] = df['Win'].replace("True",1)
    df['Win'] = df['Win'].replace("FALSE",0)
    df['Win'] = df['Win'].replace("False",0)
    
    
    df['Win'] = df['Win'].astype(int)
    return df



# update dictionary that counts the instances of champions
def update_champ_counts(champ_counts, teams):
    for a in teams:
        champ_counts[a] += 1


# update dictionary that counts the instances of champion pairs
def update_champ_pair_counts (champ_pair_counts, teams):
    for (a, b) in combinations (teams, 2):
        champ_pair_counts[(a, b)] += 1
        champ_pair_counts[(b, a)] += 1
        
def update_champ_pair_wins(champ_pair_wins, teams):
    for (a, b) in combinations (teams, 2):
        if teams[5] == 1:
            champ_pair_wins[(a, b)] += 1
            champ_pair_wins[(b, a)] += 1
            


## calculate confidence levels of champ pairs and filter based on threshold 
## measures how likely item B is selected when A is selected (conditional probability)
## important to know logically that a => b != b => a
## a => b and b => a are two distinct logical pairs
## for example:
## the confidence level of if a player n picks Rakan, then player n+C picks Xayah (a => b)
## is not the same as if player n picks Xayah, then player n+C picks Rakan (b => a)
## also note:
## a => b == Pr(B|A) = Pr(A and B)/ Pr(A); notation is different

## lifts measures dependency of variables
## if lift > 1, there is a positive correlation between the variable
## if lift = 1, no dependence
## if lift < 1, there is a negative correlation
## for our intents and purposes, we are only looking for lifts that are greater than 1
## lift{a => b} = conf(A => b) / Pr(B) = Pr(A and B) / (Pr(A) * Pr(B))
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

## Measures how frequently an champ pairs are selected 

# function calls all previous functions and inits empty dicts
def mine_rules(allTeams, withWins, sup_threshold, conf_threshold):
    champ_pair_counts = defaultdict(int)
    champ_counts = defaultdict(int)
    champ_pair_wins = defaultdict(int)
    size = len(allTeams)
    
    ## iterate through np arrays without win element to collect champ pair counts and individual counts
    ## and populate dictionary that holds the champ/pairs as keys whereas the counts are value
    for teams in allTeams:
        update_champ_pair_counts(champ_pair_counts, teams)
        update_champ_counts(champ_counts, teams)
    
    ## iterate throughout np arrays WITH win element present
    for teams in withWins:
        update_champ_pair_wins(champ_pair_wins, teams)
    
    rules, lifts = filter_rules(champ_pair_counts, champ_counts, conf_threshold,size)
    supports = filter_supports(champ_pair_counts, allTeams, sup_threshold)
    
    return supports, rules, lifts, champ_pair_counts, champ_pair_wins, champ_counts, size

def filter_supports(champ_pair_counts, allTeams, sup_threshold):
    supports = {}
    for k,v in champ_pair_counts.items():
        #toKey = tuple(sorted(list(k)))
        supp_ab = v/len(allTeams)*100
        if supp_ab >= sup_threshold:
            supports[k] = supp_ab
    return supports


def filterResults(z1,z2,z3,z4,z5):
    
    ## since we are using the confidence levels as edge values, we have to filter the confidence dictionary
    ## using results from the support and lift dictionaries
    
    # first, filter keys in confidence dictionary using support
    filter_conf_by_supp = dict((k,v) for k,v in z2.items() if k in z1.keys())
    
    # second, filter keys in confidence dictionary that was already filtered by supports using lifts
    filter_conf_supp_by_lift = dict((k,v) for k,v in filter_conf_by_supp.items() if k in z3.keys())
    
    # calculate pairwise win rates
    champ_win_rates = dict(((key, z5[key]/z4[key]) for key in z4.keys()))
    
    # filter pairwise win rates by threshold of 0.5
    ## for future implementation, i will set the win rates as an argument 
    #filtered_win_rates = dict(((k,v) for k,v in champ_win_rates.items() if v >0.5))
    
    # returns second order filtered dictionary using the filtered pairwise win rates
    #return dict(((k,v) for k,v in filter_conf_supp_by_lift.items() if k in filtered_win_rates.keys()))
    
    output_dict = {}
    for k in filter_conf_supp_by_lift.keys():
        output_dict[k] = (filter_conf_supp_by_lift[k],champ_win_rates[k])

    return output_dict

## put path file below
## IMPORTANT:
## Create two np arrays: one with without win column and one with.

print(f"running {region} with support {sup_threshold}% and confidence {conf_threshold}%")
x = processData(file)
x_1 = x.drop(columns=['Win']).to_numpy()
x_2 = x.to_numpy() 

# filter using support threshold of 0.3% and confidence level of 5%
z1,z2,z3,z4,z5,z6,z7 = mine_rules(x_1,x_2,sup_threshold,conf_threshold)

edgeDict = filterResults(z1,z2,z3,z4,z5)
print(f"number of edges: {len(edgeDict)}")

node_list = []
for s,t in edgeDict.keys():
    node_list.append(s)
    node_list.append(t)
node_list = list(set(node_list))
nodeList = []
for node in node_list:
    nodeList.append((node,z6[node]/z7))
print(f"number of nodes: {len(nodeList)}")
print(f"number of teams: {z7}")

edgeList = []
for item, values in edgeDict.items():
    edgeList.append([item[0],item[1],values[0],values[1]])
    
# output is a source-target pair with the associated confidence % and win rate
headers = ['source', 'target', 'conf','win_rate']
with open(edges_file_out, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    writer.writerows(edgeList)
    
headers = ['champion', 'popularity']
with open(nodes_file_out, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    writer.writerows(nodeList)
