import pandas as pd
from .impliedVolatility import ImpliedVolatilitySolver, surfaceParameters
from .blackscholes import BlackScholesModel as bsm
from datetime import date, datetime
import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np

#Cleaner is a class that "cleans" pandas data frame of options chain
class Cleaner:
    def __init__(self, dataframe, ticker, exp):
        self.dataframe = dataframe.copy()
        self.ticker = ticker
        self.exp = exp

        today = date.today()
        exp_date = datetime.strptime(self.exp, "%Y-%m-%d").date()
        self.T = max((exp_date - today).days/365, 1/365)

        ticker = yf.Ticker(self.ticker)
        self.price = ticker.history(period = "1d")["Close"].iloc[-1]

        self.r = 0.04

    def spread(self):
        spread = self.dataframe['ask'] - self.dataframe['bid']
        return round(spread, 2)

    def marketPrice(self):
        marketPrice = self.spread() / 2 + self.dataframe['bid']
        return round(marketPrice, 2)


    def cleanChain(self, truths, minVolume=None, minMP=None, maxSpread=None):
        self.dataframe['spread'] = self.spread()
        self.dataframe['marketPrice'] = self.marketPrice()

        if truths.showVolume:
            if minVolume is not None:
                self.dataframe = self.dataframe[self.dataframe['volume'] > minVolume]
            else:
                self.dataframe = self.dataframe[self.dataframe['volume'] >= 0]
        else:
            self.dataframe = self.dataframe.drop('volume', axis=1, errors='ignore')

        if truths.showITM is False:
            self.dataframe = self.dataframe.drop('inTheMoney', axis=1, errors='ignore')

        if truths.showContrSize is False:
            self.dataframe = self.dataframe.drop('contractSize', axis=1, errors='ignore')

        if truths.showCurrency is False:
            self.dataframe = self.dataframe.drop('currency', axis=1, errors='ignore')

        if truths.showLastTrd is False:
            self.dataframe = self.dataframe.drop('lastTradeDate', axis=1, errors='ignore')

        if minMP is not None:
            self.dataframe = self.dataframe[self.dataframe['marketPrice'] >= minMP]

        if maxSpread is not None:
            self.dataframe = self.dataframe[self.dataframe['spread'] < maxSpread]

        if truths.showImpVol or truths.showGreeks:
            self.addImpVolatility(truths.put)

        if truths.showGreeks:
            greeks = self.greeksDF(truths.put)
            self.dataframe = self.dataframe.merge(greeks, on='contractSymbol', how='left')
        else:
            self.dataframe = self.dataframe.drop(['delta', 'gamma', 'theta', 'vega', 'rho'], axis=1, errors='ignore')

        if truths.showSpread is False:
            self.dataframe = self.dataframe.drop('spread', axis=1, errors='ignore')

        if truths.showMP is False:
            self.dataframe = self.dataframe.drop('marketPrice', axis=1, errors='ignore')

        if truths.showImpVol is False:
            self.dataframe = self.dataframe.drop('impliedVolatility', axis=1, errors='ignore')

        self.dataframe = self.dataframe.drop(
            ['expiration'],
            axis=1,
            errors='ignore'
        )

        return self.dataframe

    def addImpVolatility(self, isPut):

        for index, row in self.dataframe.iterrows():
            K = row['strike']

            marketPrice = row['marketPrice']
            impVol = ImpliedVolatilitySolver(self.price, K, self.T, self.r, 1, marketPrice, isPut)
            volatility = impVol.implied_volatility()

            if np.isnan(volatility):
                continue

            self.dataframe.at[index, 'impliedVolatility'] = volatility

    def is_price_valid(self, isPut):
        discount = np.exp(-self.r * self.T)

        for index, row in self.dataframe.iterrows():
            K = row['strike']

            if isPut:
                min_price = max(0.0, K * discount - self.price)
            else:
                min_price = max(0.0, self.price - K * discount)

            if self.dataframe.at[index, 'marketPrice'] < min_price:
                self.dataframe = self.dataframe.drop(index)

    def volatiltiyStrikePlot(self, name, volumeBool):
        fig, ax1 = plt.subplots()

        x = []
        y = []
        for index, row in self.dataframe.iterrows():
            x.append(self.dataframe.at[index, 'strike'])
            y.append(self.dataframe.at[index, 'impliedVolatility'])

        ax1.scatter(x, y, color = "blue", label = "Implied Volayility")

        coefficients = np.polyfit(x, y, deg = 2)
        quadratic = np.poly1d(coefficients)

        x_curve = np.linspace(min(x), max(x), 100)
        y_curve = quadratic(x_curve)

        ax1.plot(x_curve, y_curve, color = "red", linewidth = 2, label = "Regression of Implied Volatility")
        equation = "Fitted Equation: V = {coefficients[0]}K² + {coefficients[1]}K + {coefficients[2]}"

        ax1.set_xlabel("Strike Price")
        ax1.set_ylabel("Implied Volatility")

        ax2 = ax1.twinx()

        y2 = []

        if volumeBool:
            for index, row in self.dataframe.iterrows():
                y.append(self.dataframe.at[index, 'volume'])

        else:
            for index, row in self.dataframe.iterrows():
                y.append(self.dataframe.at[index, 'openInterest'])

        ax2.bar(x, y2, color = '#713f96', alpha = 0.3)

        plt.show()


    def greeksDF(self, isPut):
        delta = []
        gamma = []
        theta = []
        vega = []
        rho = []
        greeks = self.dataframe[['contractSymbol']].copy()

        for index, row in self.dataframe.iterrows():
            K = row['strike']
            sigma = row['impliedVolatility']

            option = bsm(self.price, K, self.T, self.r, sigma)
            if isPut:
                dictionary = option.greeks(True)
                gamma.append(dictionary["gamma"])
                delta.append(dictionary["delta"])
                theta.append(dictionary["theta"])
                vega.append(dictionary["vega"])
                rho.append(dictionary["rho"])
                

            else:
                dictionary = option.greeks()
                gamma.append(dictionary["gamma"])
                delta.append(dictionary["delta"])
                theta.append(dictionary["theta"])
                vega.append(dictionary["vega"])
                rho.append(dictionary["rho"])

        greeks['delta'] = delta
        greeks['gamma'] = gamma
        greeks['theta'] = theta
        greeks['vega'] = vega
        greeks['rho'] = rho

        return greeks

    def fairPrice(self, isPut):
        fairPrices = []
        for index, row in self.dataframe.iterrows():
            K = row['strike']
            sigma = row['impliedVolatility']
            option = bsm(self.price, K, self.T, self.r, sigma)

            if isPut: fairPrices.append(option.put_price())
            else: fairPrices.append(option.call_price())

        fairPrices = self.dataframe[['contractSymbol']].copy()
        fairPrices['fairPrice'] = fairPrices

class Truths:
    def __init__(self, 
                 showMP, 
                 showSpread, 
                 showVolume, 
                 showImpVol, 
                 showITM, 
                 showContrSize,
                 showCurrency,
                 showLastTrd,
                 showGreeks,
                 put):
        self.showMP = showMP
        self.showSpread = showSpread
        self.showVolume = showVolume
        self.showImpVol = showImpVol
        self.showITM = showITM
        self.showContrSize = showContrSize
        self.showCurrency = showCurrency
        self.showLastTrd = showLastTrd
        self.showGreeks = showGreeks
        self.put = put