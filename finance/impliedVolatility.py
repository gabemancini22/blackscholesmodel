import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from .blackscholes import BlackScholesModel
import numpy as np
import pandas as pd
from typing import cast
from scipy.stats import norm
from scipy.optimize import brentq
import math

class surfaceParameters:
    def __init__(self, typeX, typeY, startX, startY, endX, endY, numX, numY):
        self.typeX = typeX
        self.typeY = typeY
        self.startX = startX
        self.startY = startY
        self.endX = endX
        self.endY = endY
        self.xStep = numX
        self.yStep = numY

# ImpliedVolatilitySolver calculates implied volatility using the Newton-Raphson method.
# This class uses BlackScholesModel for caluclations
#S: Stock Price
#K: Strike Price
#T: Time to expiration
#r: risk free interest rate (assumed 0.04)

class ImpliedVolatilitySolver:
    def __init__(self, S, K, T, r, init_guess, marketPrice, isPut):
        self.S = S
        self.K = K
        self.T = T
        self.r = r
        self.init_guess = init_guess
        self.marketPrice = marketPrice
        self.isPut = isPut

        self.count = 0
        self.errorX = []
        self.errorY = []

    def vega(self, volatility):
        model = BlackScholesModel(self.S, self.K, self.T, self.r, volatility)
        d1 = model.d1(volatility)
        return self.S * norm.pdf(d1) * np.sqrt(self.T)

    #Calculates implied volatility using both newton raphson and brents method
    def implied_volatility(self):
        impVolatility = self.init_guess

        model = BlackScholesModel(
            self.S, 
            self.K, 
            self.T, 
            self.r, 
            impVolatility)
        
        if self.isPut == True:
            VPrice = model.put_price()
        else:
            VPrice = model.call_price()

        count = 0
        while abs(VPrice - self.marketPrice) > 0.00001: 

            vega = self.vega(impVolatility)
            if abs(vega) < 1e-8:
                self.count +=1
                iv = self.run_brent()
                return iv

            impVolatility = impVolatility - (VPrice - self.marketPrice)/vega
            impVolatility = max(impVolatility, 0.00001)  # Ensure volatility is non-negative

            model2 = BlackScholesModel(
                self.S, 
                self.K, 
                self.T, 
                self.r, 
                impVolatility)

            if self.isPut:
                VPrice = model2.put_price()
            else:
                VPrice = model2.call_price()

            if count >= 1000:
                return self.run_brent()

            count += 1
    
        return round(impVolatility, 4)

    # Functions for brents method and implied volatiltiy calculation
    def objective_function(self, sigma):
        model = BlackScholesModel(self.S, self.K, self.T, self.r, sigma)
        price = model.put_price() if self.isPut else model.call_price()
        return price - self.marketPrice

    def run_brent(self):
        low_vol, high_vol = 1e-5, 5.0  # 0.001% to 500% volatility range
        try:
            if self.objective_function(low_vol) * self.objective_function(high_vol) <= 0:
                v = brentq(self.objective_function, low_vol, high_vol)
                return float(v) #type: ignore
            return float(np.nan)
        except Exception:
            return float(np.nan)

    #Validation for implied volatility surface
    def impVolatilitySurface_VALIDATION(self, params):
        sigma = self.init_guess

        if params.typeX == params.typeY:
            print("Error: Choose 2 different Parameters.")
            return

        xVals = np.linspace(params.startX, params.endX, num = params.xStep)
        yVals = np.linspace(params.startY, params.endY, num = params.yStep)
        X, Y = np.meshgrid(xVals, yVals)
        volatilities = [[]]

        for i in range(0, len(xVals)):
            x = xVals[i]
            setattr(self, params.typeX, x)
            for j in range(0, len(yVals)):
                y = yVals[j]
                setattr(self, params.typeY, y)
                    
                impVolatility = self.implied_volatility()
                volatilities[i].append((sigma))

            volatilities.append([])

        if volatilities[-1] == []:
            volatilities.pop()

        (X2, Y2) = np.meshgrid(self.errorX, self.errorY)
        volatilities = np.array(volatilities).T

        fig = plt.figure()
        ax = cast(Axes3D, fig.add_subplot(111, projection = "3d"))

        surf = ax.plot_surface(X, Y, volatilities, cmap = "winter", alpha = 1)

        ax.set_zlabel("Implied Volatility")
        plt.show()

    # Calculates implied volatility surface using implied volatility method. 
    # Plots it along with plotting input values that lead to divergence Due to vega near 0
    # Uses real data, if real data is not used, the surface will not be very accurate
    def impVolatilitySurface(self, params):
        self.count = 0
        self.errorX = []
        self.errorY = []

        parameter_names = {
        "S": "Stock Price",
        "K": "Strike Price",
        "r": "Risk-Free Interest Rate",
        "T": "Time to Maturity (Years)",
        "sigma" : "volatility",
        "marketPrice": "Market Price"
        }
    
        if params.typeX == params.typeY:
            print("Error: Choose 2 different Parameters.")
            return
    
        xVals = np.linspace(params.startX, params.endX, num = params.xStep)
        yVals = np.linspace(params.startY, params.endY, num = params.yStep)
        X, Y = np.meshgrid(xVals, yVals)
        volatilities = [[]]
    
        for i in range(0, len(xVals)):
            x = xVals[i]
            setattr(self, params.typeX, x)
            for j in range(0, len(yVals)):
                y = yVals[j]
                setattr(self, params.typeY, y)

                impVolatility = self.implied_volatility()
                volatilities[i].append((impVolatility))

                if np.isnan(volatilities[i][j]):
                    self.errorX.append(x)
                    self.errorY.append(y)
    
            volatilities.append([])
    
        if volatilities[-1] == []:
            volatilities.pop()
    
        (X2, Y2) = np.meshgrid(self.errorX, self.errorY)
        volatilities = np.array(volatilities).T
    
        fig = plt.figure()
        ax = cast(Axes3D, fig.add_subplot(111, projection = "3d"))
    
        surf = ax.plot_surface(X, Y, volatilities, cmap = "winter", alpha = 1)
        ax.scatter(self.errorX, self.errorY, [0]*len(self.errorX), color = "red", marker = ".",s = 40,alpha = 0.2, label = "No Convergence")  #type: ignore
    
        ax.set_xlabel(parameter_names[params.typeX])
        ax.set_ylabel(parameter_names[params.typeY])
        ax.set_zlabel("Implied Volatility")
    
        plt.show()
        print(f"Number of Unplotted Error Volatilities: {self.count}")

    # prints some options contract numbers
    def Options(self):
        print("")
        if self.isPut: print("Options Contract: Put") 
        else: print("Options Contract: Call")
        print("")
        print(f"Stock Price: {self.S}")
        print(f"Strike Price: {self.K}")
        print(f"Contract Length: {self.T} Years")
        print(f"Risk Free Interest Rate: {self.r}")
        print(f"Market Price: {self.marketPrice}")

