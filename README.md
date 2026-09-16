This is a project that creates a GUI using Qt through PySide6 to create a mini Options Terminal.
This is my code free for anyone to use, but I have done all of this on my own. 
I worked very hard on this, so thank you for looking at it!!

Along with the financial code and the gui, there is a project report that explains a lot of the mathematics and briefly details the gui, while going into depth about some financial topics and limitations of the black scholes model and dealing with realistic data when pricing options.

GUI

Opening Window
The GUI is run through engine.py. This opens up the initial window, which allows you to choose what you want the options chain to showm and some bounds for it too, for example, you can cap the maximum spread and filter out options with low volume. 
This also allows the user to pick whether the chain will display call or put options.

QStackedWidget
Once the user clicks show chain, the options terminal will open up, displaying all of the options for a specific ticker and expiration date. 
The user can also look at a volatility plot with respect to strike price overlayed onto either volume or open interest(Which the user can toggle on or off). Some statistics are shown on the volatility smile page, and a quadratic regression model is shown as well. The volatility smile was plotted using MatPlotLibrary.
The User can also look at a volatility surface for all of the expiration dates for the chosen ticker.
The Volatility surface was plotted using MatPlotLibrary.
On the options chain, the user has the ability to pick a certain option and run a monte carlo simulation using that option's implied volatility and risk-free interest rate. Statistics are calculated for this simulation, such as a histogram of profits, standard deviation and expected profits and more. The histogram was plotted using MatPlotLibrary.

Finance

All data was collected from yfinance, and pandas data frames were used for calculations and displaying the options chain. 
The finance folder has an implied volatility file, which calculates implied volatility and other related measurements using the Newton-Raphson method and Brent's Method for approximating implied volatility. In this file as well, there is an implied volatility surface validation, that uses theoretical implied volatilities instead of realistic ones to make sure the implied volatility surface is correct. This surface is much more linear than real implied volatility surfaces due to the fact that it is theoretical data.

The Monte Carlo class was designed specifically for the use in the monte carlo simulation on one of the QStackedWidget pages. This also calculates relevant statitics. The BlackScholes file calculates fair price, and uses the blackscholesmodel to calculate many other relevant statistics, such as the greeks.


