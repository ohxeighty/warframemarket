import requests
import argparse
import json
import sys
import datetime 
 
parser = argparse.ArgumentParser(description="Warframe Trading Assistant")
parser.add_argument("-v", "--verbose", action="store_true") 

args = parser.parse_args() 

n = 10 
# we want to grab median price over x weeks 
# of item from either full name or initials 
# maybe a warning if there has been an x change in x weeks, i.e. significant change in the price 


class bcolors: 
    WARNING = "\033[93m"
    BOLD = "\033[1m"
    GREEN = "\033[92m" 
    BLUE = "\033[94m"
    CLEAR = "\033[0m"
    RED = "\033[91m"
    
def eprint(text):
    print(bcolors.RED + "[!] " + text + bcolors.CLEAR)

def iprint(text):
    if args.verbose:
        print(bcolors.BOLD + "[*] " + text + bcolors.CLEAR)
    
def bprint(text):
    print(bcolors.BOLD + text + bcolors.CLEAR) 

def gprint(text):
    print(bcolors.GREEN + text + bcolors.CLEAR) 
    
def market_request(path):
    url="https://api.warframe.market/v1/" + path 
    iprint("Requesting: " + url) 
    r = requests.get(url) 
    return r.json()
    
def rwloop(cache): 
    global n # n datapoints 
    
    while 1:
        i = input(": ").lower()
        matches = []
        # handle initials 
        if len(i.split()) == sum([len(j) for j in i.split()]):
            initials = i.split()
            matches = [item for item in cache if initials == [j[0] for j in item["item_name"].lower().split() if j[0] != "("]]
        else:
            # query cache 
            #matches = next(item for item in cache if i in item["item_name"]) 
            matches = [item for item in cache if i in item["item_name"].lower()]
        
        match = None
        
        # handle multiple matches
        if len(matches) > 1:
            bprint("Multiple Items Matched - Type Index of Desired Item") 
            for index,m in enumerate(matches):
                gprint("["+str(index)+"] " + m["item_name"]) 
            while match == None:
                try:
                    i = input(": ")
                    i = int(i) 
                    match = matches[i] 
                except KeyboardInterrupt:
                    sys.exit()
                except:
                    eprint("Invalid index")
                
        elif len(matches) == 1:
            match = matches[0] 
        else: 
            continue  
        # query market 
        item_info = market_request("items/"+match["url_name"])
        item_stats = market_request("items/"+match["url_name"]+"/statistics")
        # process dict 
        trading_tax = item_info["payload"]["item"]["items_in_set"][0]["trading_tax"] 
        try:
            ducats = item_info["payload"]["item"]["items_in_set"][0]["ducats"]
        except:
            ducats = 0
        days = item_stats["payload"]["statistics_live"]["90days"]
        days.sort(key=lambda item:datetime.datetime.strptime(item["datetime"],"%Y-%m-%dT%H:00:00.000+00:00"))
        
        # take n last data points, then take their average median 
        if not len(days) <= n: 
            days = days[-n:]
        median = sum([day["median"] for day in days]) / len(days)
        mean = sum([day["avg_price"] for day in days]) / len(days)
        
        bprint("===Statistics===")
        gprint("Median value over past " + str(n) + " datapoints: " + "\033[94m" + str(median))
        gprint("Median value from " + str(days[-1]["datetime"]).split(":")[0] + ": " + "\033[94m" +str(days[-1]["median"]))
        gprint("Mean value over past " + str(n) + " datapoints: " + "\033[94m" + str(mean)) 
        gprint("Mean value from " + str(days[-1]["datetime"]).split(":")[0] + ": " + "\033[94m" +str(days[-1]["avg_price"]))
        if ducats != 0:
            gprint("Ducat Value: " + "\033[94m" + str(ducats)) 
        gprint("Trading Tax: " + "\033[94m" + str(trading_tax))    
# Build item cache 
iprint("Building item cache...")
    
item_cache = market_request("items")["payload"]["items"]
iprint("Built item cache")
# Main loop 
rwloop(item_cache) 

iprint("Leaving...") 


