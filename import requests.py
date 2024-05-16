import requests
import json
import pandas as pd
import config
pd.set_option("display.max_columns", None)
#pd.set_option("max_rows", None)
pd.set_option("min_rows", 100)
symbolit = config.osakkeet
timeframe = config.timeframe 
url =  "https://data.alpaca.markets/v2/stocks/bars?symbols=" + symbolit + "&timeframe=" + timeframe + "&start=2022-01-03T00:00:00Z&limit=1000"

payload = {}
headers = {
  'Accept': 'application/json',
  'APCA-API-KEY-ID' : 'PKOAR4N5ZWE8VQ1OHHC0',
  'APCA-API-SECRET-KEY' : "sN4zYRqHr59i3KBHEseudn4M9MFLFbnNCKl00SPO",

  'Content-Type': 'application/json'
}
response = requests.request("GET", url, headers=headers, data=payload)

response_data = response.json()

bars = response_data["bars"]
sulkuhinnat = []
symbolit = []
paivat = []

for symbol, details in bars.items():
    
    for data in details:
        symbolit.append(symbol)
        sulkuhinnat.append(data["c"])
        paivat.append(data['t'])

df = pd.DataFrame({'Symbol': symbolit, 'Day': paivat, 'Price':sulkuhinnat})
print(df) 
summa = 0
maara = 0
for hinta in df["Price"]:
    maara += 1
    summa += hinta
print(summa / maara)