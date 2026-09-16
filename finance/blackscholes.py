import random
import math
import statistics
from dataclasses import dataclass
from scipy.stats import norm
import numpy as np

# Black Scholes Model Calculation class
# Calculates greeks

class BlackScholesModel:
    def __init__(self, S, K, T, r, sigma):
        self.S = S  # Current stock price
        self.K = K  # Strike price
        self.T = T  # Time to expiration in years
        self.r = r  # Risk-free interest rate
        self.sigma = sigma  # Volatility of the underlying stock

# Methods d1, d2 call and put price calculate fair prices,
    def d1(self, volatility = None):
        if volatility is None:
            volatility = self.sigma
        numerator = np.log(self.S/self.K) + self.T*(self.r + 0.5 * volatility**2)
        return numerator / (volatility * np.sqrt(self.T))
    
    def d2(self, volatility = None):
        if volatility is None:
            volatility = self.sigma
        return self.d1(volatility) - volatility * np.sqrt(self.T)

    def call_price(self, volatility = None):
        if volatility is None:
            d1 = self.d1()
            d2 = self.d2()

        else:
            d1 = self.d1(volatility)
            d2 = self.d2(volatility)

        term1 = self.S * norm.cdf(d1)
        term2 = self.K * np.exp(-self.r * self.T) * norm.cdf(d2)
        return term1 - term2


    def put_price(self, volatility = None):
        if volatility is None:
            d1 = self.d1()
            d2 = self.d2()
        else:
            d1 = self.d1(volatility)
            d2 = self.d2(volatility)

        term1 = self.K * np.exp(-self.r * self.T) * norm.cdf(-d2)
        term2 = self.S * norm.cdf(-d1)

        return term1 - term2

# Calculates the greeks for the object  
    def greeks(self, isPut = False):
        d1 = self.d1()
        d2 = self.d2()
        if isPut:
            delta = norm.cdf(d1) - 1
            t2 = self.r*self.K*np.exp(-self.r*self.T)*norm.cdf(-d2)
            t1 = self.S*norm.pdf(d1)*self.sigma/(2*np.sqrt(self.T))
            theta = -t1 + t2
            rho = -self.K*self.T*np.exp((-self.r)*self.T)*norm.cdf(-d2)

        else:
            delta = norm.cdf(d1)
            t2 = self.r*self.K*np.exp(-self.r*self.T)*norm.cdf(d2)
            t1 = self.S*norm.pdf(d1)*self.sigma/(2*np.sqrt(self.T))
            theta = -t1 - t2
            rho = self.K*self.T*np.exp((-self.r)*self.T)*norm.cdf(d2)

        denom = self.S*self.sigma*np.sqrt(self.T)
        if denom <= 1e-5:
            gamma = 0
        else:
            gamma = norm.pdf(d1)/(self.S*self.sigma*np.sqrt(self.T))
        vega = self.S*norm.pdf(d1)*np.sqrt(self.T)

        return {
            "delta": np.round(delta, 3),
            "gamma": np.round(gamma, 3),
            "vega": np.round(vega, 3),
            "theta": np.round(theta, 3),
            "rho": np.round(rho, 3)
        }

    # blackScholesCall and Put prints calculated fair price and greeks for the object
    def blackScholesCall(self):
        print(f"Fair Call Price: {np.round(self.call_price(), 4)}")

        greeks = self.greeks() 
        for name, value in greeks.items():
            print(f"{name}: {value}")

    def blackScholesPut(self):
        print(f"Fair Put Price: {np.round(self.put_price(), 4)}")

        greeks = self.greeks(True) 
        for name, value in greeks.items():
            print(f"{name}: {value}")