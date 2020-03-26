import requests
import argparse
import json
import sys
import datetime 

# workaround for ansi codes
import ctypes
kernel32 = ctypes.windll.kernel32 
kernel32.SetConsoleMode(kernel32.GetStdHandle(-11),7)
 
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
    CYAN = "\033[96m"
    BLUE = "\033[94m"
    YELLOW = "\33[33m" 
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

def cprint(text):
    print(bcolors.CYAN + text + bcolors.CLEAR) 

def market_request(path):
    url="https://api.warframe.market/v1/" + path 
    iprint("Requesting: " + url) 
    r = requests.get(url) 
    return r.json()

def rwloop(cache): 
    global n # n datapoints 
    
    while 1:
        ui = input("Item: ").lower()
        if ui and ui[0] == "!":
            if ui[1:] == "help":
                bprint("!refresh - Rebuild the item cache")
                bprint("!quit - quit") 
            elif ui[1:] == "refresh":
                iprint("Building item cache...")
                cache = market_request("items")["payload"]["items"]
                iprint("Built item cache")
            elif ui[1:] == "quit":
                bprint("Bye")
                sys.exit()
        else:
            for i in [x.strip() for x in ui.split(",")]: 
                matches = []
                # handle initials 
                if len(i.split()) == sum([len(j) for j in i.split()]):
                    initials = i.split()
                    matches = [item for item in cache if initials == [j[0] for j in item["item_name"].lower().split() if j[0] != "("]]
                else:
                    # query cache 
                    #matches = next(item for item in cache if i in item["item_name"]) 
                    matches = [item for item in cache if i in item["item_name"].lower()]
                
                if len(matches) == 0:
                    eprint("No matches for " + i)
                    continue 
                match = None
                
                # handle multiple matches
                if len(matches) > 1:
                    bprint("Multiple Items Matched - Type Index of Desired Item") 
                    gprint("[-1] " + "Back") 
                    for index,m in enumerate(matches):
                        gprint("["+str(index)+"] " + m["item_name"]) 
                    while not match:
                        try:
                            i = input("Index: ")
                            i = int(i) 
                            if i == -1:
                                break
                            match = matches[i] 
                        except KeyboardInterrupt:
                            sys.exit()
                        except:
                            eprint("Invalid index")
                        
                elif len(matches) == 1:
                    match = matches[0] 
                else: 
                    continue  
                    
                if not match:
                    continue 
                # query market 
                item_info = market_request("items/"+match["url_name"])
                item_stats = market_request("items/"+match["url_name"]+"/statistics")
                
                #the actual item we want... any request for an item thats part of a set gets a response for that whole set...
                item_info_list = item_info["payload"]["item"]["items_in_set"]
                item_info = next(item for item in item_info_list if item["en"]["item_name"] == match["item_name"])
                
                # process dict 
                try:
                    trading_tax = item_info["trading_tax"]
                except:
                    trading_tax = 0
                try:
                    ducats = item_info["ducats"]
                except:
                    ducats = 0
                days = item_stats["payload"]["statistics_closed"]["90days"] # STATISTICS CLOSED OR LIVE??
                if "mod_rank" in days[0]:
                    days = [day for day in days if day["mod_rank"] == 0]
                days.sort(key=lambda item:datetime.datetime.strptime(item["datetime"],"%Y-%m-%dT%H:00:00.000+00:00"))
                
                # take n last data points, then take their average median 
                if not len(days) <= n: 
                    days = days[-n:]
                median = sum([day["median"] for day in days]) / len(days)
                mean = sum([day["avg_price"] for day in days]) / len(days)
                volume = sum([day["volume"] for day in days]) / len(days) 
               
                # color code volume based on sales 
                if volume < 5: 
                    volume_str = bcolors.RED + str(volume) 
                elif volume < 10: 
                    volume_str = bcolors.YELLOW + str(volume) 
                else:
                    volume_str = bcolors.GREEN + str(volume) 
                
                bprint("===" + match["item_name"] + "===")
                gprint("Median value over past " + str(n) + " datapoints: " + bcolors.CYAN + str(median))
                gprint("Median value from " + str(days[-1]["datetime"]).split(":")[0] + ": " + bcolors.CYAN +str(days[-1]["median"]))
                gprint("Mean value over past " + str(n) + " datapoints: " + bcolors.CYAN + str(mean)) 
                gprint("Mean value from " + str(days[-1]["datetime"]).split(":")[0] + ": " + bcolors.CYAN +str(days[-1]["avg_price"]))
                if ducats != 0:
                    gprint("Ducat Value: " + bcolors.CYAN + str(ducats)) 
                if trading_tax != 0:
                    gprint("Trading Tax: " + bcolors.CYAN + str(trading_tax))    

                cprint("Average volume sold over past " + str(n) + " datapoints: " + volume_str) 
                cprint("Volume sold on " + str(days[-1]["datetime"]).split(":")[0] + ": " + bcolors.YELLOW +str(days[-1]["volume"]))
# Build item cache 
iprint("Building item cache...")
    
item_cache = market_request("items")["payload"]["items"]
item_cache.sort(key=lambda i:(i["item_name"]))
iprint("Built item cache")
# Main loop 
rwloop(item_cache) 

iprint("Leaving...") 


