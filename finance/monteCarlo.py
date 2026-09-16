import random
import math
import sys
import statistics
from dataclasses import dataclass
from scipy.stats import norm
import numpy as np
import pandas as pd
from .impliedVolatility import ImpliedVolatilitySolver, surfaceParameters
from .blackscholes import BlackScholesModel as bsm
from datetime import date, datetime
import yfinance as yf
import matplotlib.pyplot as plt

class MonteCarlo:
    def __init__(self, initial, mew, sigma, days, strike, ticker, isPut, marketPrice):
        self.initial = initial
        self.mew = mew
        self.sigma = sigma
        self.days = days
        self.strike = strike
        self.ticker = ticker
        self.isPut = isPut
        self.marketPrice = marketPrice

        self.delta = 1/252
        self.payoffs = []
        self.finals = []

    def investment(self):

        # Commented to reduce console output, uncomment to see details for each period

        # Prints information for the initial period
        #print("Period 1: ")
        #print("Investment: " +str(initial))

        investments = [self.initial]

        final = self.initial
        for i in range(1, self.days):
            r = 1 + self.mew*self.delta + self.sigma*math.sqrt(self.delta)*random.gauss(0,1)

            final = final*(r)

            if final <= 0:
                final = 0.01

            investments.append(final)
            
        return investments, final

    def simulation(self, iterations):  
        for i in range(iterations):
            invests, f = self.investment()
            plt.plot(invests)
            self.finals.append(f)

        if self.isPut:
            self.payoffs = [max(self.strike - final, 0) for final in self.finals]
        else:
            self.payoffs = [max(final - self.strike, 0) for final in self.finals]

        self.meanPayoff = statistics.mean(self.payoffs)
        self.stdevPayoff = statistics.stdev(self.payoffs)
        self.medianPayoff = round(statistics.median(self.payoffs), 3)
        self.nowPayoff = self.meanPayoff*math.exp(-self.mew*(self.days/252))

    
    def propProfit(self):
        count = 0
        for final in self.finals:
            if final > self.strike:
                count += 1

        prop = count/(len(self.finals))
        return prop

    def profitability(self):
        count = 0
        for prf in self.profit:
            if prf > 0:
                count += 1

        prop = count/(len(self.finals))
        return prop

    @staticmethod
    def calculateRates(df, expiration, stock, ticker, isPut):
        expiration = pd.Timestamp(expiration)
        today = pd.Timestamp.today().normalize()
        T = (expiration - today).days / 365.0

        if T <= 0:
            raise ValueError("Expiration must be in the future.")

        yahoo = yf.Ticker(ticker)

        option_chain = yahoo.option_chain(
            expiration.strftime("%Y-%m-%d")
        )

        calls = option_chain.calls.copy()
        puts = option_chain.puts.copy()

        if "marketPrice" in df.columns:
            price_col = "marketPrice"
        else:
            df = df.copy()
            df["marketPrice"] = (
                pd.to_numeric(df["bid"], errors="coerce")
                + pd.to_numeric(df["ask"], errors="coerce")
            ) / 2
            price_col = "marketPrice"

        calls["marketPrice"] = (
            pd.to_numeric(calls["bid"], errors="coerce")
            + pd.to_numeric(calls["ask"], errors="coerce")
        ) / 2

        puts["marketPrice"] = (
            pd.to_numeric(puts["bid"], errors="coerce")
            + pd.to_numeric(puts["ask"], errors="coerce")
        ) / 2

        rates = []

        for _, row in df.iterrows():
            K = float(row["strike"])
            price = float(row[price_col])

            if not math.isfinite(price) or price <= 0:
                continue

            if isPut:
                match = calls[calls["strike"] == K]

                if match.empty:
                    continue

                C = float(match.iloc[0]["marketPrice"])
                P = price

            else:
                match = puts[puts["strike"] == K]

                if match.empty:
                    continue

                C = price
                P = float(match.iloc[0]["marketPrice"])

            if not math.isfinite(C) or not math.isfinite(P):
                continue

            if C <= 0 or P <= 0:
                continue

            discount_factor = (stock - C + P) / K

            if discount_factor <= 0:
                continue

            r = -math.log(discount_factor) / T

            if math.isfinite(r):
                rates.append(r)

        if not rates:
            raise ValueError("Could not calculate any valid risk-free rates.")

        return rates

    @staticmethod
    def calculateRiskFreeRate(df, expiration, stock, ticker, isPut):
        rates = MonteCarlo.calculateRates(
            df,
            expiration,
            stock,
            ticker,
            isPut
        )

        return float(np.median(rates))

    def skewness(self):
        if self.stdevPayoff == 0:
            return 0

        skewness = (3*(self.meanPayoff - self.medianPayoff))/self.stdevPayoff
        return round(skewness, 4)

    def kurtosis(self):
        sum4th = 0
        for payoff in self.payoffs:
            sum4th += (payoff - self.meanPayoff)**4

        n = len(self.payoffs)
        if n == 0 or self.stdevPayoff == 0:
            return 0

        kurtosis = (sum4th/n)/(self.stdevPayoff**4)
        return round(kurtosis, 4)

    def riskMeasurements(self, confidence_level=0.95):
        sortedProfits = sorted(self.profit)

        index = int((1-confidence_level)*len(sortedProfits))
        VaR = sortedProfits[index]

        CVaR = 0
        for i in range(index):
            CVaR += sortedProfits[i]/(index)

        return round(VaR, 3), round(CVaR, 3)

    def profitCalculator(self):
        self.profit = [payoff - self.marketPrice for payoff in self.payoffs]
        self.meanProfit = statistics.mean(self.profit)
        self.stDevProfit = statistics.stdev(self.profit)


        
