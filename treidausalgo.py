import requests
from datetime import date, timedelta
import numpy as np
import pandas as pd
import pandas_ta as ta
import alpaca_trade_api as tradeapi
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus
from alpaca.data.live import StockDataStream
from alpaca.trading.stream import TradingStream
import config
API_KEY = config.API_KEY
SEC_KEY = config.SEC_KEY

class API_liikenne:
    def __init__(self, api_key, sec_key):
        self.api_key = api_key
        self.sec_key = sec_key
        self.osake = config.osakkeet 
        self.asiakas = TradingClient(self.api_key, self.sec_key, paper=True)
        self.headers = headers = {'Accept': 'application/json','APCA-API-KEY-ID' : self.api_key,'APCA-API-SECRET-KEY' : self.sec_key,'Content-Type': 'application/json'}
    
    def data_palvelimelta(self):
        osake = self.osake
        timeframe = config.timeframe 
        aloitus_paivamaara = (date.today() - timedelta(days=310)).strftime("%Y-%m-%d")
        #aloitus_paivamaara = "2021-01-01"
        url =  "https://data.alpaca.markets/v2/stocks/bars?symbols=" + osake + "&timeframe=" + timeframe + "&start=" + aloitus_paivamaara + "&limit=1000"
        payload = {}
        response = requests.request("GET", url, headers=self.headers, data=payload)

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
        
        return pd.DataFrame({'Symbol': symbolit, 'Day': paivat, 'Close':sulkuhinnat})


    def Toimeksianto(self, market_order_data):
        
        self.asiakas.submit_order(order_data=market_order_data)

    def tilin_data(self):
        payload = {}
        response = requests.request("GET", "https://paper-api.alpaca.markets/v2/account", headers=self.headers, data=payload )   
        response = response.json()
        print(response)
    

    def kaikki_positiot(self):
        payload = {}
        response = requests.request("GET", url="https://paper-api.alpaca.markets/v2/positions", headers=self.headers, data= payload)
        response = response.json()
        return pd.DataFrame(response)

    def sulje_kaikki(self):
        self.asiakas.close_all_positions(cancel_orders=True)




class Algoritmi:
    def __init__(self):
        
        self.api_key = API_KEY
        self.sec_key = SEC_KEY
        self.api = API_liikenne(API_KEY, SEC_KEY)
        self.osta = False
        self.myy = False
        self.kateinen = 0
        self.hinta = 0
        self.liukuva_200 = 0
        self.liukuva_50 = 0
        self.liukuva_20 = 0
        self.liukuva_200_nousee = False
        self.liukuva_50_nousee = False
        self.liukuva_20_nousee = False
        
        self.hinnat = []
        self.df = pd.DataFrame
    
    def data_analyysi(self):
        self.df = self.api.data_palvelimelta()
        self.df["SMA 20"] = self.df.ta.sma(20)
        self.df["SMA 50"] = self.df.ta.sma(50)
        self.df["SMA 200"] = self.df.ta.sma(200)
        print(self.df)
        for hinta in self.df["Close"]:
            self.hinnat.append(hinta)
            
        print(self.hinnat)    
        self.hinta = self.hinnat[-1]
        self.laske_liukuva(200)
        self.laske_liukuva(50)
        self.laske_liukuva(20)
        print(self.liukuva_200, self.liukuva_50, self.liukuva_20)
    
    def tilin_tiedot(self):
        tiedot = self.api.tilin_data()
        self.kateinen = tiedot['non_marginable_buying_power']
        
        


    def laske_liukuva(self, aika):
        pituus = len(self.hinnat)
        summa = 0
        maara = 0
        for hinta in self.hinnat[pituus - (aika) : pituus]:
            summa += hinta
            maara += 1
        
        if aika == 200:
            self.liukuva_200 = summa/maara
            return
        elif aika == 50:
            self.liukuva_50 = summa/maara
            return
        self.liukuva_20 = summa/maara
        return
    
    def palauta_liukuva(self, aika):
        pituus = len(self.hinnat)
        summa = 0
        maara = 0
        for hinta in self.hinnat[pituus - (aika + 1) : pituus - 1]:
            summa += hinta
            maara += 1
        
        return summa/maara
    
    def onko_liukuvat_nousevia(self):
        self.liukuva_200_nousee = self.palauta_liukuva(200) < self.liukuva_200
        self.liukuva_50_nousee = self.palauta_liukuva(50) < self.liukuva_50
        self.liukuva_20_nousee = self.palauta_liukuva(20) < self.liukuva_20
        print(self.liukuva_20_nousee, self.liukuva_50_nousee, self.liukuva_200_nousee)
        print(self.palauta_liukuva(50), self.liukuva_50)

        
    def ostetaanko(self):
        if self.liukuva_200_nousee and self.liukuva_50_nousee and self.liukuva_20_nousee:
            if self.hinta > self.liukuva_50 and self.hinta > self.liukuva_200:
                if self.hinta <= self.liukuva_20:
                    self.osta = True
        
    
    def osta(self):
        positiot = self.api.kaikki_positiot()
        for positio in positiot["symbol"]:
            if positio == self.api.osake:
                pass

        
    
    
    def silmukka(self):
        algo = Algoritmi()
        algo.data_analyysi()
        algo.onko_liukuvat_nousevia()
        algo.ostetaanko()












algo = Algoritmi()
algo.data_analyysi()
algo.onko_liukuvat_nousevia()
algo.ostetaanko()
market_order_data = MarketOrderRequest(
                    symbol="SPY",
                    qty=1,
                    side=OrderSide.SELL,
                    time_in_force=TimeInForce.DAY
                    )

# Market order
algo.api.asiakas.submit_order(order_data=market_order_data)
algo.api.kaikki_positiot()
algo.api.tilin_data()