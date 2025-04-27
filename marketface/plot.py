#!/usr/bin/env python3
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from marketface import database

import matplotlib.pyplot as plt


def plot_difference_distribution(plot):
    differences = [record.difference for record in database.get_all()]
    # filter difference if abs is lower than 10 because most difference
    # between real price and predicted price fall close to 0, because
    # the model is train to predict the real price therefore the difference
    # will be close to 0 we want to plot the distribution of the difference
    differences = [x for x in differences if abs(x) > 15]

    # Create histogram
    plot.hist(differences, bins=2*100+1, edgecolor='black')

    plot.set_xlabel('Difference')
    plot.set_ylabel('Frequency')
    plot.set_title('Difference Histogram')


def plot_price_distribution(plot):
    prices = [record.price_usd for record in database.get_all()]
    prices = [price for price in prices if 600 < price < 4000]

    # Create histogram
    plot.hist(prices, bins=2*10+1, edgecolor='black')

    plot.set_xlabel('Price')
    plot.set_ylabel('Frequency')
    plot.set_title('Price Histogram')


if __name__ == "__main__":
    # Create figure with two subplots, one above the other
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8))

    plot_difference_distribution(ax1)
    plot_price_distribution(ax2)

    # Adjust layout to prevent overlap
    plt.tight_layout()

    # Display plot
    plt.show()