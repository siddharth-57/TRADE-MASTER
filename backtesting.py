#importing libraries
import requests
from alpha_vantage.timeseries import TimeSeries
import numpy as np
import pandas as pd
import talib
import yfinance as yf
import copy

#displaying the output completely
pd.set_option("display.max_rows",None)
pd.set_option("display.max_columns",None)   
pd.set_option("display.width",None)

def stock_backtest(symbol_list):
    all_trades_taken=[]             #main list to store all the trades taken
    for symbol in symbol_list:
        df = yf.Ticker(f"{symbol}.NS").history(period="1y",interval="1d")

        #MA CROSSOVER STRATEGY WITH RSI 
        #THE CURRENT STRATEGY IS ONLY FOR ONE WAY TRADES THAT IS IF THE FIRST POSITION TAKEN IS LONG THEN SUBSEUENTLY ALL POSITIONS TAKEN WILL BE LONG SAME APPLIES TO SHORT TRADES AS WELL
        #MAKE CHANGES LATER TO ACCOMODATE SUCH THAT BOTH LONG AND SHORT TRADES MAY BE TAKEN.
        #A SIMPLE APPROACH IS THAT ONCE A TRADE CLOSES CLOSE IT SUCH A MANNER THAT YOU BUY/SELL 2 TIMES THE AMOUNT OF STOCKS YOU HAD IN THAT POSITION.

        df["MA_10"] = talib.MA(df["Close"],timeperiod=10)
        df["MA_50"] = talib.MA(df["Close"],timeperiod=50)
        df["RSI_14"] = talib.RSI(df["Close"],timeperiod=14)

        #to store the details of our current trade taken
        trade ={"Symbol":None,"Buy/Sell":None,"Entry":None,"Entry Date":None,"Exit":None,"Exit Date":None,} #other parameters like volume and all can also be added later   
        position = None

        for a in df.index[49:]:

            if df["MA_10"][a]>df["MA_50"][a] and df["RSI_14"][a]>70 and position!="Buy":    #for making long entry(buying a stock)
                if trade["Symbol"] is not None: #if the trade is already taken then exit the position 
                    trade["Exit"] = df["Close"][a]
                    trade["Exit Date"] = a  
                    all_trades_taken.append(copy.deepcopy(trade)) #once the trade is completed add it to the  list of taken trades
                if position is not None:    #if the position is not None(ignoring the first trade which solves the double sided trade problem)
                    trade["Symbol"] = symbol
                    trade["Buy/Sell"] = "Buy"
                    trade["Entry"] = df["Close"][a]
                    trade["Entry Date"] = a
                position = "Buy"

            if df["MA_10"][a]<df["MA_50"][a] and df["RSI_14"][a]<70 and position!="Sell":   #for making short entry(short selling a stock)
                if trade["Symbol"] is not None:  
                    trade["Exit"] = df["Close"][a]
                    trade["Exit Date"] = a  
                    all_trades_taken.append(copy.deepcopy(trade)) 
                if position is not None:
                    trade["Symbol"] = symbol
                    trade["Buy/Sell"] = "Sell"
                    trade["Entry"] = df["Close"][a]
                    trade["Entry Date"] = a
                position="Sell"

    return all_trades_taken

symbol_list=["Reliance","TATAMOTORS","Upl"]

trades_data = stock_backtest(symbol_list)

if trades_data: 
    df = pd.DataFrame(trades_data)
    df["P&L"]= np.where(df["Buy/Sell"] == "Buy",100*(df["Exit"]-df["Entry"])/df["Entry"],100*(df["Exit"]-df["Entry"])/df["Entry"])
    df["Probability"] = 100*(np.where(df["P&L"]>0,1,0).cumsum())/(np.where(df["P&L"]!=np.NaN,1,0).cumsum()) #probability of successfull trade
    df["Return"] = df["P&L"].cumsum() 
    df["Drawdown"] = df["Return"] - (df["Return"].cummax().apply(lambda x:x if x>0 else 0))
    print(df)
else:
    print("NO TRADES TAKEN")