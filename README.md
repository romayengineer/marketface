# Description

This is a simple project made in python playwright and is for pulling
facebook marketplace items into a database for analysis like e.g. to
know if a product has a fair price or if it is cheep

## Prerequisites

Python 3.10.0
pocketbase (python package) 0.12.3
pocketbase (binary) 0.22.34

It can also work with 

pocketbase (python package) 0.15.0
pocketbase (binary) 0.27.2

- pyenv install 3.10.0
- pyenv global 3.10.0
- pip install pipenv
- pipenv install --verbose
- pipenv shell
- playwright install chromium

## How to run

python marketface/scrap_marketface.py

then run the database from

cd marketface/data/base

and query the items table with

title != "" && reviewed = false

## Table Items

- url: string
- title: string
- description: string
- img_path: string
- priceArs: float
- priceUsd: float
- usdArsRate: float
- usd: bool
- deleted: bool
- cpu: string
- memory: int
- disk: int
- screen: float
- yearBought: int
- yeahModel: int

## Example of output on training

### Trained with 5 attributes

```
records len:  457
powerset len:  11029
replication factor:  24.133479212253828
replication log2:  4.592964012116638
Fitting 5 folds for each of 2000 candidates, totalling 10000 fits
Best parameters: {'subsample': 0.8, 'reg_lambda': 0.1, 'reg_alpha': 1.0, 'n_estimators': 500, 'min_child_weight': 3, 'max_depth': 8, 'learning_rate': 0.05, 'gamma': 0.2, 'colsample_bytree': 1.0}
Best cross-validation MAE: 358.17216904602344
Mean Absolute Error on test set: 329.99
Predicted price for new sample: 1157.42
Feature: model, Importance: 0.053688
Feature: cpu, Importance: 0.320316
Feature: ram, Importance: 0.357489
Feature: disk, Importance: 0.130250
Feature: screen, Importance: 0.138257
```

### Trained with 6 attributes (including year bought)

```
records len:  457
powerset len:  16796
replication factor:  36.7527352297593
replication log2:  5.199779717776948
Mean Absolute Error on test set: 285.16
Predicted price for new sample: 839.73
Feature: model, Importance: 0.045730
Feature: cpu, Importance: 0.318961
Feature: ram, Importance: 0.321874
Feature: disk, Importance: 0.096231
Feature: screen, Importance: 0.101094
Feature: year_bought, Importance: 0.116111
```

============================================================

```
records len:  457
powerset len:  17382
replication factor:  38.03501094091904
replication log2:  5.24925611493349
Fitting 5 folds for each of 2000 candidates, totalling 10000 fits
Best parameters: {'subsample': 1.0, 'reg_lambda': 0, 'reg_alpha': 0, 'n_estimators': 500, 'min_child_weight': 3, 'max_depth': 8, 'learning_rate': 0.1, 'gamma': 0.1, 'colsample_bytree': 1.0}
Best cross-validation MAE: 309.8714793548702
Mean Absolute Error on test set: 283.81
Predicted price for new sample: 815.18
Feature: model, Importance: 0.040261
Feature: cpu, Importance: 0.303444
Feature: ram, Importance: 0.304731
Feature: disk, Importance: 0.098179
Feature: screen, Importance: 0.114299
Feature: year_bought, Importance: 0.139085
```


## Plan for the project:

1. [DONE] create database to insert the url and image path
2. [DONE] open each of the urls and pull title, description, price and other data
3. [DONE] (there is a jupyter notebook that does this) query the data and analyse it for decision making
4. #TODO add dynamic programing AKA caching for the function that loops over each link to speed up the process if there are hundreds of items to process it can take a few seconds when it can be done in a fraction of a second if I cache the return of the function that cheks if the item already exists on the database

## play_dynamic.py script

this is for quick development cycle as I reload this module
dynamically and I update the code to see the changing without
reloading the interpreter or the browser

once the functions in here are well developed and tested
I'll move them to the main script



