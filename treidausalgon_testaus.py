import requests
from datetime import date, timedelta, datetime
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
import yfinance as yf

API_KEY = config.API_KEY
SEC_KEY = config.SEC_KEY

class Trade:
    def __init__(self, osake, hinta, maara, long):
        self.osake = osake
        self.avaushinta = hinta
        self.maara = maara
        self.long = long
    
    def __str__(self):
        if self.long:
            long = "long"
        else:
            long = "short"
        return f"{self.osake}, {self.maara}, {long} "
        
class Salkku:
    def __init__(self, paaoma):
        self.paaoma = paaoma
        self.positiot = []
        self.alkupaaoma = paaoma
        self.kateinen = paaoma
        self.voitto = 0
    
    def osta(self, trade):
        if trade.long:
            self.kateinen -= trade.maara * trade.avaushinta
        self.positiot.append(trade)

    def sulje_positio(self, osake, hinta):
        for positio in self.positiot:
            if positio.osake == osake and positio.long:
                self.kateinen += positio.maara * hinta
                self.positiot.remove(positio)
            else:
                self.kateinen += positio.maara * positio.avaushinta - positio.maara * hinta
                self.positiot.remove(positio)

    def paivita_tiedot(self, hinta):
        self.paaoma = self.kateinen

        for positio in self.positiot:
            if positio.long:
                self.paaoma += positio.maara * hinta
            else:
                self.paaoma += positio.maara * positio.avaushinta - positio.maara * hinta

        self.voitto = self.paaoma - self.alkupaaoma



class Algoritmi:
    def __init__(self, osake):
        
        self.osta = 0
        self.myy = 0
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
    
    def data_analyysi(self, data):
        self.df = data
        
        self.df["SMA 20"] = self.df.ta.sma(20)
        self.df["SMA 50"] = self.df.ta.sma(50)
        self.df["SMA 200"] = self.df.ta.sma(200)
        #print(self.df.iloc[-1]["SMA 200"] > self.df.iloc[-2]["SMA 200"])
        self.osakkeen_hinta = self.df["Close"].iloc[-1]
        #print(self.osakkeen_hinta)
        #print(self.df)
        self.rsi = self.df.ta.rsi().iloc[-1]     
        #print(self.rsi) 
    
        
    def onko_liukuvat_nousevia(self):
        self.liukuva_200_nousee = self.df.iloc[-1]["SMA 200"] > self.df.iloc[-2]["SMA 200"]
        self.liukuva_50_nousee = self.df.iloc[-1]["SMA 50"] > self.df.iloc[-2]["SMA 50"]
        self.liukuva_20_nousee = self.df.iloc[-1]["SMA 20"] > self.df.iloc[-2]["SMA 20"]
   

        
    def ostetaanko(self):
        self.osta = 0
        # liukuvien analysointi
        if self.liukuva_200_nousee:
            self.osta += 0.2
        else:
            self.osta -= 0.2
        if self.liukuva_50_nousee:
            self.osta += 0.2
        else:
            self.osta -= 0.2
        if self.liukuva_20_nousee:
            self.osta += 0.1
        else:
            self.osta -= 1
        if self.osakkeen_hinta > self.liukuva_200:
            self.osta += 0.2
        else:
            self.osta -= 0.2
        if self.osakkeen_hinta > self.liukuva_50:
            self.osta += 0.2
        else:
            self.osta -= 0.2
        # RSI analyysi
        if self.liukuva_200_nousee:
            rsi = self.rsi
            rsi = rsi - 60
            rsi = rsi / 100
            self.osta -= rsi
        else: # laskutrendi
            rsi = self.rsi
            rsi = rsi - 40
            rsi = rsi / 100
            self.osta -= rsi
        
        print("x")
        #print(self.rsi)
        
        print(self.osta)
        return 

    


def testaa_algoritmia():
    aloitus_paiva = datetime(2022, 1, 1)
    lopetus_paiva = datetime(2023, 1, 1)
    paiva = timedelta(days=1)
    salkku = Salkku(10000)
    
    
    
    while True:
        if lopetus_paiva == datetime.now():
            return
        data = yf.download("SPY", start=aloitus_paiva.strftime("%Y-%m-%d"), end=lopetus_paiva.strftime("%Y-%m-%d"))
        df = pd.DataFrame(data)
        hinta = data["Close"].iloc[-1]
        algo = Algoritmi("SPY")
        algo.data_analyysi(data)
        algo.onko_liukuvat_nousevia()
        algo.ostetaanko()

        if algo.osta > 0.6:
            maara = salkku.kateinen // algo.osakkeen_hinta
            if maara == 0:
                continue
            osto = Trade("SPY", hinta, maara, True)
            salkku.osta(osto)
        
        elif abs(algo.osta) < 0.3:
            salkku.sulje_positio("SPY", hinta)
        
        elif algo.osta < -0.7:
            maara = salkku.kateinen // (hinta * 2)
            if maara == 0:
                continue
            osto = Trade("SPY", algo.osakkeen_hinta, maara, False)
            salkku.osta(osto)
        salkku.paivita_tiedot(hinta)
        aloitus_paiva += paiva
        lopetus_paiva += paiva
        for positio in salkku.positiot:
            print(positio)
        print(salkku.kateinen)
        print(salkku.paaoma)
        print(hinta)
        input1 = input()
        if input1 == "q":
            break
testaa_algoritmia()