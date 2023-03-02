import ccxt
from datetime import datetime, timedelta
import time
import configparser
import requests
from colorit import *
from pprint import pprint

init_colorit()

def line_notify(token, msg):
    if token != "":
        url = 'https://notify-api.line.me/api/notify'
        line_headers = {'content-type': 'application/x-www-form-urlencoded', 'Authorization': 'Bearer ' + token}
        try:
            response = requests.post(url, headers=line_headers, data={'message': msg, 'Authorization': 'Bearer ' + token}, timeout = 10)
        except requests.ConnectionError as e :
            logfile = open('log_future.txt', 'a')
            logfile.write("OOPS!! Connection Error. Make sure you are connected to Internet. Technical Details given below.\n" +str(e) + '\n'  )
            logfile.close()  
            pass
        except requests.exceptions.ReadTimeout as e :
            logfile = open('log_future.txt', 'a')
            logfile.write("Line Notify timeout.\n" +str(e) + '\n'  )
            logfile.close()  
            pass

def format_cunumber(info, zero) :
    item = ""
    if zero == 1 :
        item = str("{:,.1f}".format(info))
    if zero == 2 :
        item = str("{:,.2f}".format(info))
    if zero == 3 :
        item = str("{:,.3f}".format(info))
    if zero == 4 :
        item = str("{:,.4f}".format(info))
    if zero == 5 :
        item = str("{:,.5f}".format(info))
    if zero == 6 :
        item = str("{:,.6f}".format(info))
    return item

def format_cunumber2(info) :
    item = str("{:,.2f}".format(info))
    return item

config = configparser.ConfigParser()
config.sections()
config.read('config.ini')

api_key = config['BINANCE']['api_key']
secret_key = config['BINANCE']['api_secret']
line_token = config['BINANCE']['line_token']
margin_type = str(config['BINANCE']['margin_type'])
ticket = config['BINANCE']['ticker']
amounts = config['BINANCE']['amount']
myLeverage = config['BINANCE']['leverage']
time_frame = "1h"
ema_fast =  int(10)
ema_slow = int(21)

exchange = ccxt.binance({
    'enableRateLimit': True,
    'apiKey' : api_key,
    'secret' : secret_key,
    'options': {
        'defaultType': 'future',  # ←-------------- 'spot' and 'future'
    },
})

hour_date_time = datetime.now()
time_next_line = hour_date_time.strftime('%H')  

is_next_ema = "Y"

while True :
    hour_date_time = datetime.now()
    time_nows_line = hour_date_time.strftime('%H') 
    try :      
        walletbalance = 0
        pnl = 0
        marginbalance = 0
        root_balance = exchange.fetch_balance()
        for x in root_balance['info']['assets'] :
            if x['asset'] == margin_type :   
                walletbalance = float(x['walletBalance'])
                pnl = float(x['unrealizedProfit'])
                marginbalance = float(x['marginBalance'])        
        print("-----------------------------------------")
        print(color("Future Binance V1.6 By iSUDJAB", colorit.Colors.yellow)) 
        print("-----------------------------------------")    
        print("Balance : " + format_cunumber2(walletbalance))
        print("Unrealized PNL : " + format_cunumber2(pnl))
        print("Margin Balance : " + format_cunumber2(marginbalance))        
        print("-----------------------------------------")    
        msg = "\nFutures USD@-M \U0001F973\U0001F389\U0001F38A"
        msg += "\nBalance : " + format_cunumber2(walletbalance)
        msg += "\nUnrealized PNL : " + format_cunumber2(pnl)
        msg += "\nMargin Balance : " + format_cunumber2(marginbalance)

        info_ticket = ticket.strip()
        info_amount = amounts.strip()         
        info_leverage = myLeverage.strip()       
        root_entryprice = 0
        root_unrealizedprofit = 0
        root_size = 0
        root_leverage = 0
        root_symbols = info_ticket.replace("/", "")           
        for x in root_balance['info']['positions'] :
            if x['symbol'] == root_symbols :           
                root_entryprice = float(x['entryPrice'])
                root_unrealizedprofit = float(x['unrealizedProfit'])
                root_size = float(x['positionAmt'])
                root_leverage = float(x['leverage'])            
        root_tickets =  exchange.fetch_ticker(info_ticket)            
        root_pricelast = root_tickets['last']
        dotzero = len(str(root_pricelast).split(".")[1])
        sum_fast = 0 
        sum_slow = 0 
        bar_fast = exchange.fetch_ohlcv(info_ticket, time_frame, limit = ema_fast) 
        bar_slow = exchange.fetch_ohlcv(info_ticket, time_frame, limit = ema_slow)     
        i = 1
        for x in bar_fast :  
            if i <= ema_fast :
                sum_fast += float(x[1])
                i += 1
        x_fast = sum_fast / ema_fast
        i = 1
        for x in bar_slow :  
            if i <= ema_slow :
                sum_slow += float(x[1])
                i += 1
        x_slow = sum_slow / ema_slow   

        print(color("Coin : "  + str(info_ticket), colorit.Colors.blue))   
        print("Last Print : " + str(format_cunumber(root_pricelast, int(dotzero))))
        print("Entry Price : " + str(format_cunumber(root_entryprice, int(dotzero))))   
        print("Size : " + str(root_size))   
        print("Leverage : " + str(int(root_leverage)))
        print("Profit : " + str(format_cunumber2(root_unrealizedprofit)))                        
        print("EMA Fast : " + str(format_cunumber(x_fast, int(dotzero))))
        print("EMA Slow : " + str(format_cunumber(x_slow, int(dotzero))))               
        msg += "\n-----------------------------------"  
        msg += "\nCoin : " + str(info_ticket)   
        msg += "\nLast Print : " + str(format_cunumber(root_pricelast, int(dotzero)))        
        msg += "\nProfit : " + str(format_cunumber2(root_unrealizedprofit))  

        if  is_next_ema != "" :
            if float(x_fast) > float(x_slow) :
                is_next_ema = "Y"
            if float(x_fast) < float(x_slow) :
                is_next_ema = "N"

        # ===== POSITION BUY
        if float(x_fast) > float(x_slow) :    
            print(color("Status : EMA CROSS UP", colorit.Colors.green))
            print("-----------------------------------------")    
            msg += "\nStatus : EMA CROSS UP \U0001F7E2"            
            if root_size < 0 :
                try :
                    close_position = exchange.create_order(symbol = info_ticket, type = "market", side = "buy", amount = abs(root_size), price = None, params = {'reduceOnly': 'true'}) 
                    root_size = 0
                except :
                    pass        
            if  is_next_ema != "Y" :
                if float(root_size) == float(0) :
                    try :
                        set_leverage = exchange.set_leverage(leverage = int(info_leverage), symbol = root_symbols) # Set Leverage
                    except :
                        pass
                    symbol = info_ticket # BTC/BUSD
                    type = 'market'  # or 'limit'
                    side = 'buy'  # or 'sell'
                    amount = float(info_amount)
                    price = None
                    params = {
                        'position_side': 'LONG',
                    }
                    order = exchange.create_order(symbol, type, side, amount, price, params)
                    is_next_ema = ""
            elif is_next_ema == "" :
                if float(root_size) == float(0) :
                    try :
                        set_leverage = exchange.set_leverage(leverage = int(info_leverage), symbol = root_symbols) # Set Leverage
                    except :
                        pass
                    symbol = info_ticket # BTC/BUSD
                    type = 'market'  # or 'limit'
                    side = 'buy'  # or 'sell'
                    amount = float(info_amount)
                    price = None
                    params = {
                        'position_side': 'LONG',
                    }
                    order = exchange.create_order(symbol, type, side, amount, price, params)
                    is_next_ema = ""
        # ===== POSITION SELL
        if float(x_fast) < float(x_slow) :    
            print(color("Status : EMA CROSS DOWN", colorit.Colors.red))
            print("-----------------------------------------")               
            msg += "\nStatus : EMA CROSS DOWN \U0001F534"               
            if root_size > 0 :
                try :
                    close_position = exchange.create_order(symbol = info_ticket, type = "market", side = "sell", amount = root_size, price = None, params = {'reduceOnly': 'true'})
                    root_size = 0
                except :
                    pass
            if is_next_ema != "N" : 
                if float(root_size) == float(0) :
                    try :
                        set_leverage = exchange.set_leverage(leverage = int(info_leverage), symbol = root_symbols) # Set Leverage
                    except :
                        pass               
                    symbol = info_ticket # BTC/BUSD
                    type = 'market'  # or 'limit'
                    side = 'sell'  # or 'buy'
                    amount = float(info_amount)
                    price = None
                    params = {
                        'position_side': 'SHORT',
                    }
                    order = exchange.create_order(symbol, type, side, amount, price, params)  
                    is_next_ema = ""
            elif is_next_ema == "" :
                if float(root_size) == float(0) :                    
                    try :
                        set_leverage = exchange.set_leverage(leverage = int(info_leverage), symbol = root_symbols) # Set Leverage
                    except :
                        pass               
                    symbol = info_ticket # BTC/BUSD
                    type = 'market'  # or 'limit'
                    side = 'sell'  # or 'buy'
                    amount = float(info_amount)
                    price = None
                    params = {
                        'position_side': 'SHORT',
                    }
                    order = exchange.create_order(symbol, type, side, amount, price, params)  
                    is_next_ema = ""
        if time_nows_line == time_next_line :
            next_hour_date_time = datetime.now() + timedelta(hours = 1)    
            time_next_line = next_hour_date_time.strftime('%H')
            line_notify(line_token, msg)  
        print("\n")
        time.sleep(20)
    except Exception as ex:
        pass

