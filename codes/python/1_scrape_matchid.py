#import http.client
import json
import csv
import urllib
import time

puuid_list = []

#update file name for puuid list
with open('puuid_eun1.csv', 'r') as read_obj:
    csv_reader = csv.reader(read_obj)
    for row in csv_reader:
        for i in range(1,11):
            puuid_list.append(row[i])

puuid_list = list(set(puuid_list))

#update api key,region,platform (asia, americas, europe)
api_key = "RGAPI-2acefa23-d2bb-454a-b024-0cf2e280b806"
region = "EUN1"
platform = "europe"

def scrape_matchid(j,puuid):
    
    #grab matches played after timestamp filter created - 6/17/2021
    #grab 10 matches per puuid
    URL = "https://"+platform+".api.riotgames.com/lol/match/v5/matches/by-puuid/"+puuid+"/ids?startTime=1623888000&start=0&count=10&api_key="+api_key
    request = urllib.request.urlopen(URL)
    data = json.loads(request.read())
    data.insert(0,j)
    
    return data

#reduce delay based on performance - start with 1.2 and go down to lowest without bombing after 100 records
delay = 0.8

#adjust start index if restarting; 0 for first run
start = 4546

with open('matchid_eun1.csv', 'a+', encoding='UTF8', newline='') as f:
    writer = csv.writer(f)

    # write the header
    #writer.writerow(header)

    # write the data
    for i in range(start,len(puuid_list)):
        print(f"\rprocessing {i} of {len(puuid_list)}",end="\r")
        try:    
            writer.writerow(scrape_matchid(i,puuid_list[i]))  
            time.sleep(delay)
        except:
            print("\rerror, retrying in 120s",end="\r")
            time.sleep(120)
            try: 
                writer.writerow(scrape_matchid(i,puuid_list[i]))  
                time.sleep(delay)
            except:
                pass
            
        
   
