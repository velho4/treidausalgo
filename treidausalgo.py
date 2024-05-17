import requests
from datetime import date, timedelta
import numpy as np
import time
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
    def __init__(self, api_key, sec_key, osake):
        self.api_key = api_key
        self.sec_key = sec_key
        self.osake = osake 
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
    
    def viimeisin_hinta(self):
        payload = {}
        url = 'https://data.alpaca.markets/v2/stocks/' + self.osake + '/trades/latest'
        response = requests.request("GET", url, headers=self.headers, data=payload)
        response = response.json()
        return response["trade"]["p"]


    def toimeksianto(self, market_order_data):
        
        self.asiakas.submit_order(order_data=market_order_data)

    def tilin_data(self):
        payload = {}
        palautus = requests.request("GET", "https://paper-api.alpaca.markets/v2/account", headers=self.headers, data=payload)   
        palautus = palautus.json()
        return palautus

    def kaikki_positiot(self):
        payload = {}
        response = requests.request("GET", url="https://paper-api.alpaca.markets/v2/positions", headers=self.headers, data= payload)
        response = response.json()
        return pd.DataFrame(response)

    def sulje_kaikki(self):
        self.asiakas.close_all_positions(cancel_orders=True)




class Algoritmi:
    def __init__(self, osake):
        
        self.api_key = API_KEY
        self.sec_key = SEC_KEY
        self.api = API_liikenne(API_KEY, SEC_KEY, osake)
        self.osta = False
        self.myy = False
        self.kateinen = 0
        self.osakkeen_hinta = 0
        self.rsi = 0
        self.liukuva_200 = 0
        self.liukuva_50 = 0
        self.liukuva_20 = 0
        self.liukuva_200_nousee = False
        self.liukuva_50_nousee = False
        self.liukuva_20_nousee = False
        self.salkun_arvo = 0
        self.position_koon_raja = 0
        self.df = pd.DataFrame()
    
    def data_analyysi(self):
        self.df = self.api.data_palvelimelta()
        self.df["SMA 20"] = self.df.ta.sma(20)
        self.df["SMA 50"] = self.df.ta.sma(50)
        self.df["SMA 200"] = self.df.ta.sma(200)
        print(self.df.iloc[-1]["SMA 200"] > self.df.iloc[-2]["SMA 200"])
        self.osakkeen_hinta = self.api.viimeisin_hinta()
        self.rsi = self.df.rsi()        
    
    def tilin_tiedot(self):
        tiedot = self.api.tilin_data()
        self.kateinen = float(tiedot['non_marginable_buying_power'])
        self.salkun_arvo = tiedot["portfolio_value"]
        self.position_koon_raja = float(self.salkun_arvo) * 0.2
        if self.kateinen < self.position_koon_raja:
            self.position_koon_raja = self.kateinen
        
        
    def onko_liukuvat_nousevia(self):
        self.liukuva_200_nousee = self.df.iloc[-1]["SMA 200"] > self.df.iloc[-2]["SMA 200"]
        self.liukuva_50_nousee = self.df.iloc[-1]["SMA 50"] > self.df.iloc[-2]["SMA 50"]
        self.liukuva_20_nousee = self.df.iloc[-1]["SMA 20"] > self.df.iloc[-2]["SMA 20"]
   

        
    def ostetaanko(self):
        if self.liukuva_200_nousee and self.liukuva_50_nousee and self.liukuva_20_nousee:
            if self.osakkeen_hinta > self.liukuva_50 and self.osakkeen_hinta > self.liukuva_200:
                if self.osakkeen_hinta <= self.liukuva_20 * 1.01:
                    self.osta = True
    
    def myydäänkö(self):
        if se

    
    def shortataaanko(self):


    
    def osto(self):
        if self.kateinen == 0:
            return
        positiot = self.api.kaikki_positiot()
        for indeksi, positio in positiot.iterrows():
            if positio["symbol"] == self.api.osake:                
                if float(positio["market_value"]) < self.position_koon_raja - self.osakkeen_hinta:
                    osakkeiden_maara = (self.position_koon_raja - float(positio["market_value"])) // self.osakkeen_hinta
                    order_data = MarketOrderRequest(symbol=self.api.osake, qty=osakkeiden_maara, side=OrderSide.BUY, time_in_force=TimeInForce.DAY)
                    self.api.toimeksianto(order_data)
                    return
                else:
                    return
            
        osakkeiden_maara = self.position_koon_raja // float(self.osakkeen_hinta)
        print(self.position_koon_raja)
        print(self.osakkeen_hinta)
        print(osakkeiden_maara)
        order_data = MarketOrderRequest(symbol=self.api.osake, qty=osakkeiden_maara, side=OrderSide.BUY, time_in_force=TimeInForce.DAY)
        self.api.toimeksianto(order_data)        
                

        
    
    
def silmukka():
    while True:
        for osake in config.osakkeet:
            algo = Algoritmi(osake)
            algo.data_analyysi()
            algo.tilin_tiedot()
            algo.onko_liukuvat_nousevia()
            algo.ostetaanko()
            algo.osto()
            
        
        time.sleep(10)



silmukka()








