#!/usr/bin/env python3
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from marketface import database
from marketface.power import LaptopAttributes, power_set_of_known_attrs

from math import log2
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import mean_absolute_error
from sklearn.base import BaseEstimator
from pocketbase.models.utils.base_model import BaseModel
from typing import List



# Define ordinal mappings for categorical features
# This is to add monotonic constraints
MODEL_ORDER = {'air': 1, 'pro': 2}  # MacBook Air < MacBook Pro
CPU_ORDER = {'i3': 1, 'i5': 2, 'i7': 3, 'i9': 4, 'm1': 5, 'm2': 6, 'm3': 7, 'm4': 8}  # i3 < i5 < i7 < i9 < M1 < M2 < M3 < M4

def load_records() -> List[BaseModel]:

    filtered_records = []
    all_records = database.get_all()
    for record in all_records:
        # it must be reviewed
        if record.title == "" or record.reviewed == False:
            continue
        # price must be greater than 600
        if record.price_usd < 300:
            continue
        # price must be lower than 4000
        if record.price_usd > 4000:
            continue
        # it must be not deleted
        if record.deleted == True:
            continue
        # it must be not broken
        if record.broken == True:
            continue
        # it must be known model
        if record.model not in ("air", "pro", ""):
            continue
        # it must be known cpu
        if record.cpu not in ("i3", "i5", "i7", "i9", "m1", "m2", "m3", "m4", ""):
            continue
        filtered_records.append(record)

    return filtered_records

# def new_dataframe(model, cpu, memory, disk, screen)

def load_data() -> pd.DataFrame:

    # Load data from database
    filtered_records = load_records()

    records_len = len(filtered_records)

    # Create power set of products
    # as there are 5 attributes this multiplies the records by 32 == 2 ** 5
    # this gives the model more data to train on for cases were there are missing values
    # by creating syntetic new products were values that we know are set and the rest ommited
    power_set_of_products: List[LaptopAttributes] = []

    for record in filtered_records:
        product = LaptopAttributes(
            price_usd=record.price_usd,
            model=record.model,
            cpu=record.cpu,
            memory=record.memory,
            disk=record.disk,
            screen=record.screen,
            year_bought=record.year_bought,
        )
        power_set_of_products.extend(power_set_of_known_attrs(product))

    powerset_len = len(power_set_of_products)

    # Create DataFrame from power set of products
    model_col = []
    cpu_col = []
    memory_col = []
    disk_col = []
    screen_col = []
    year_bought_col = []
    price_col = []
    for record in power_set_of_products:
        model_col.append(record.model)
        cpu_col.append(record.cpu)
        memory_col.append(record.memory)
        disk_col.append(record.disk)
        screen_col.append(record.screen)
        year_bought_col.append(record.year_bought)
        price_col.append(record.price_usd)

    # Create the dataset
    data = pd.DataFrame({
        'model': model_col,
        'cpu': cpu_col,
        'ram': memory_col,
        'disk': disk_col,
        'screen': screen_col,
        'year_bought': year_bought_col,
        'price': price_col,
    })

    # Preprocess: Replace missing values ("" for model/cpu, 0 for ram/disk/screen) with NaN
    data['model'] = data['model'].replace('', np.nan)
    data['cpu'] = data['cpu'].replace('', np.nan)
    data['ram'] = data['ram'].replace(0, np.nan)
    data['disk'] = data['disk'].replace(0, np.nan)
    data['screen'] = data['screen'].replace(0, np.nan)
    data['year_bought'] = data['year_bought'].replace(0, np.nan)

    # Apply ordinal encoding for known categories, leaving np.nan as is
    data['model'] = data['model'].map(MODEL_ORDER)
    data['cpu'] = data['cpu'].map(CPU_ORDER)

    # Convert to appropriate types
    data['model'] = data['model'].astype('float')
    data['cpu'] = data['cpu'].astype('float')
    data['ram'] = data['ram'].astype('float')
    data['disk'] = data['disk'].astype('float')
    data['screen'] = data['screen'].astype('float')
    data['year_bought'] = data['year_bought'].astype('float')
    data['price'] = data['price'].astype('float')

    print(data.head(50).to_string(index=False))

    print("records len: ", records_len)
    print("powerset len: ", powerset_len)
    print("replication factor: ", powerset_len / records_len)
    print("replication log2: ", log2(powerset_len / records_len))

    # sys.exit(0)

    return data


def get_best_model(X_train: pd.DataFrame, y_train: pd.DataFrame, n_iter: int = 1000) -> BaseEstimator:

    # Define XGBoost model
    model = xgb.XGBRegressor(
        objective='reg:squarederror',
        random_state=42,
        monotone_constraints={
            'model': 1,
            'cpu': 1,
            'ram': 1,
            'disk': 1,
            'screen': 1,
            'year_bought': 1,
        },
        missing=np.nan  # Explicitly set missing value handling
    )

    # Define hyperparameter search space
    param_dist = {
        'n_estimators': [50, 100, 200, 500],      # 4
        'learning_rate': [0.01, 0.05, 0.1, 0.2],  # 4
        'max_depth': [3, 4, 5, 6, 8],             # 5
        'min_child_weight': [1, 3, 5, 7],         # 4
        'subsample': [0.6, 0.8, 1.0],             # 3
        'colsample_bytree': [0.6, 0.8, 1.0],      # 3
        'gamma': [0, 0.1, 0.2, 0.5],              # 4
        'reg_alpha': [0, 0.1, 1.0],               # 3
        'reg_lambda': [0, 0.1, 1.0]               # 3
    }
    # 4 * 4 * 5 * 4 * 3 * 3 * 4 * 3 * 3 = 103680

    # Perform RandomizedSearchCV
    random_search = RandomizedSearchCV(
        estimator=model,
        param_distributions=param_dist,
        n_iter=n_iter,  # Number of parameter combinations to try
        scoring='neg_mean_absolute_error',  # Optimize for MAE
        cv=5,  # 5-fold cross-validation
        verbose=1,
        random_state=42,
        n_jobs=-1,  # Use all available cores
        error_score="raise",
    )
    random_search.fit(X_train, y_train)

    # Best model
    best_model = random_search.best_estimator_
    print("Best parameters:", random_search.best_params_)
    print("Best cross-validation MAE:", -random_search.best_score_)

    return best_model


def split_and_train(X: pd.DataFrame, y: pd.DataFrame, n_iter: int = 1000) -> BaseEstimator:

    # Split data into training and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=42)

    best_model = get_best_model(X_train, y_train, n_iter=n_iter)

    return best_model


def get_error(model: BaseEstimator, X_test: pd.DataFrame, y_test: pd.DataFrame) -> None:

    # Predict on test set with best model
    y_pred = model.predict(X_test)

    # Evaluate model
    mae = mean_absolute_error(y_test, y_pred)
    print(f"Mean Absolute Error on test set: {mae:.2f}")


def predict(model: BaseEstimator, record: BaseModel) -> float:

    # Example: Predict for a new sample
    data = pd.DataFrame({
        'model': [record.model],
        'cpu': [record.cpu],
        'ram': [record.memory],
        'disk': [record.disk],
        'screen': [record.screen],
        'year_bought': [record.year_bought],
    })

    # Preprocess: Replace missing values ("" for model/cpu, 0 for ram/disk/screen) with NaN
    data['model'] = data['model'].replace('', np.nan)
    data['cpu'] = data['cpu'].replace('', np.nan)
    data['ram'] = data['ram'].replace(0, np.nan)
    data['disk'] = data['disk'].replace(0, np.nan)
    data['screen'] = data['screen'].replace(0, np.nan)
    data['year_bought'] = data['year_bought'].replace(0, np.nan)

    # Apply ordinal encoding for known categories, leaving np.nan as is
    data['model'] = data['model'].map(MODEL_ORDER)
    data['cpu'] = data['cpu'].map(CPU_ORDER)

    # Convert to appropriate types
    data['model'] = data['model'].astype('float')
    data['cpu'] = data['cpu'].astype('float')
    data['ram'] = data['ram'].astype('float')
    data['disk'] = data['disk'].astype('float')
    data['screen'] = data['screen'].astype('float')
    data['year_bought'] = data['year_bought'].astype('float')

    prediction = model.predict(data)

    # get first element as the output is a vector of 1 dimension
    return prediction[0]


def predict_all():

    best_model = xgb.XGBRegressor()
    best_model.load_model('best_xgboost_model.json')

    all_records = database.get_all()
    for i, record in enumerate(all_records):
        prediction = predict(best_model, record)
        database.update_item_by_id(record.id, {
            "predicted": float(prediction),
            "difference": float(record.price_usd - prediction),
        })
        print(i, record.price_usd, prediction, record.price_usd - prediction)


def predict_for_new_data(model: BaseEstimator):

    # Example: Predict for a new sample
    data = pd.DataFrame({
        'model': [np.nan],
        'cpu': ['m2'],
        'ram': [16],
        'disk': [np.nan],
        'screen': [13],
        'year_bought': [np.nan],
    })

    # Preprocess: Replace missing values ("" for model/cpu, 0 for ram/disk/screen) with NaN
    data['model'] = data['model'].replace('', np.nan)
    data['cpu'] = data['cpu'].replace('', np.nan)
    data['ram'] = data['ram'].replace(0, np.nan)
    data['disk'] = data['disk'].replace(0, np.nan)
    data['screen'] = data['screen'].replace(0, np.nan)
    data['year_bought'] = data['screen'].replace(0, np.nan)

    # Apply ordinal encoding for known categories, leaving np.nan as is
    data['model'] = data['model'].map(MODEL_ORDER)
    data['cpu'] = data['cpu'].map(CPU_ORDER)

    # Convert to appropriate types
    data['model'] = data['model'].astype('float')
    data['cpu'] = data['cpu'].astype('float')
    data['ram'] = data['ram'].astype('float')
    data['disk'] = data['disk'].astype('float')
    data['screen'] = data['screen'].astype('float')
    data['year_bought'] = data['year_bought'].astype('float')

    prediction = model.predict(data)
    print(f"Predicted price for new sample: {prediction[0]:.2f}")


def print_feature_importance(X: pd.DataFrame, model: BaseEstimator) -> None:

    # Feature importance
    feature_importance = model.feature_importances_
    for feature, importance in zip(X.columns, feature_importance):
        print(f"Feature: {feature}, Importance: {importance:.6f}")


def main(train: bool, split: bool, n_iter: int = 1000):

    data = load_data()

    # Define features and target
    X = data[['model', 'cpu', 'ram', 'disk', 'screen', 'year_bought']]
    y = data['price']

    if train:

        if split:

            best_model = split_and_train(X, y, n_iter=n_iter)

        else:

            best_model = get_best_model(X, y, n_iter=n_iter)

        # save best_model into file
        best_model.save_model('best_xgboost_model.json')

    else:

        best_model = xgb.XGBRegressor()
        best_model.load_model('best_xgboost_model.json')


    get_error(best_model, X, y)

    predict_for_new_data(best_model)

    print_feature_importance(X, best_model)


if __name__ == "__main__":

    train = True
    split = False
    n_iter = 2000

    main(train, split, n_iter)
    # predict_all()