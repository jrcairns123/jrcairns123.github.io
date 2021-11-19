<b>For match data extraction:</b>

each py file creates the input file for the next one

download the initial canisback matchlist json and put in the same folder as these py files

0) take canisback matchlist and extract unique puuid's
1) take unique puuid's and extract 10 matchid's from each puuid
2) take unique matchid's and extract match data

update api key, region (eun1, euw1, etc.) and platform (asia, americas, europe)

finetune delay (lowest delay without bombing will be different for each file; test for at least 100 api calls)

adjust start index if restarting run

refresh api key from riot website before long session - each key only lasts for 24 hours

backup match data file periodically - will take a couple of days to collect 100k+ rows of data!
