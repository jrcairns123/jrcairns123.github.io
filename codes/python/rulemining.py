import pandas as pd
import numpy as np
from collections import defaultdict
from itertools import combinations

def processData(file):
    df = pd.read_csv(file, header=None, index_col=0)
    df_filtered = df[(df[7]==400) | (df[7]==420) | (df[7]==430) | (df[7]==440)].iloc[:,7:]
    x = df_filtered[df_filtered.columns[1::3]].columns.union([22,37])
    toStack = [df_filtered[x].iloc[:,:6],df_filtered[x].iloc[:,6:]]
    columnNames = ["Top","Jungle","Middle","Bot","Support","Win"]
    for i in toStack:
        i.columns=columnNames  
    df = pd.concat(toStack).reset_index(drop=True)
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
        conf_ba = champ_pair_counts[(b, a)] / champ_counts[b] * 100
        lift_ab = (champ_pair_counts[(a, b)]/size) / (champ_counts[a]/size *champ_counts[b]/size)
        if conf_ab >= conf_threshold:
            rules[(a, b)] = conf_ab
            rules[(b,a)] = conf_ba
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
