#!/usr/bin/env python3
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from marketface import database

import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import mean_absolute_error
from sklearn.base import BaseEstimator


def load_data() -> pd.DataFrame:

    # Load data from database
    model_col = []
    cpu_col = []
    memory_col = []
    disk_col = []
    screen_col = []
    price_col = []
    all_records = database.get_all()
    for record in all_records:
        if record.title == "" or record.reviewed == False:
            continue
        if record.model not in ("air", "pro", ""):
            continue
        if record.cpu not in ("i3", "i5", "i7", "i9", "m1", "m2", "m3", "m4", ""):
            continue
        model_col.append(record.model)
        cpu_col.append(record.cpu)
        memory_col.append(record.memory)
        disk_col.append(record.disk)
        screen_col.append(record.screen)
        price_col.append(record.price_usd)

    print("model:  ", model_col[:10])
    print("cpu:    ", cpu_col[:10])
    print("memory: ", memory_col[:10])
    print("disk:   ", disk_col[:10])
    print("screen: ", screen_col[:10])
    print("price:  ", price_col[:10])
    print("count:  ", len(all_records))

    # Create the dataset
    data = pd.DataFrame({
        'model': model_col,
        'cpu': cpu_col,
        'ram': memory_col,
        'disk': disk_col,
        'screen': screen_col,
        'price': price_col,
    })

    # Preprocess: Replace missing values ("" for model/cpu, 0 for ram/disk/screen) with NaN
    data['model'] = data['model'].replace('', pd.NA)
    data['cpu'] = data['cpu'].replace('', pd.NA)
    data['ram'] = data['ram'].replace(0, pd.NA)
    data['disk'] = data['disk'].replace(0, pd.NA)
    data['screen'] = data['screen'].replace(0, pd.NA)

    # Convert to appropriate types
    data['model'] = data['model'].astype('category')
    data['cpu'] = data['cpu'].astype('category')
    data['ram'] = data['ram'].astype('Int64')
    data['disk'] = data['disk'].astype('Int64')
    data['screen'] = data['screen'].astype('Int64')
    data['price'] = data['price'].astype('float')

    return data


def get_best_model(X_train: pd.DataFrame, y_train: pd.DataFrame, n_iter: int = 1000) -> BaseEstimator:

    # Define XGBoost model
    model = xgb.XGBRegressor(
        objective='reg:squarederror',
        enable_categorical=True,
        random_state=42
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
        n_jobs=-1  # Use all available cores
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

    # Predict on test set with best model
    y_pred = best_model.predict(X_test)

    # Evaluate model
    mae = mean_absolute_error(y_test, y_pred)
    print(f"Mean Absolute Error on test set: {mae:.2f}")

    return best_model


def predict_for_new_data(model: BaseEstimator):

    # Example: Predict for a new sample
    new_data = pd.DataFrame({
        'model': [pd.NA],
        'cpu': ['m2'],
        'ram': [16],
        'disk': [pd.NA],
        'screen': [13]
    }).astype({
        'model': 'category',
        'cpu': 'category',
        'ram': 'Int64',
        'disk': 'Int64',
        'screen': 'Int64',
    })
    prediction = model.predict(new_data)
    print(f"Predicted price for new sample: {prediction[0]:.2f}")


def print_feature_importance(X: pd.DataFrame, model: BaseEstimator) -> None:

    # Feature importance
    feature_importance = model.feature_importances_
    for feature, importance in zip(X.columns, feature_importance):
        print(f"Feature: {feature}, Importance: {importance:.6f}")


def main(train: bool):

    data = load_data()

    # Define features and target
    X = data[['model', 'cpu', 'ram', 'disk', 'screen']]
    y = data['price']

    if train:

        best_model = split_and_train(X, y, n_iter=1000)

        # save best_model into file
        best_model.save_model('best_xgboost_model.json')

    else:

        best_model = xgb.XGBRegressor()
        best_model.load_model('best_xgboost_model.json')


    predict_for_new_data(best_model)

    print_feature_importance(X, best_model)


if __name__ == "__main__":

    train = False

    main(train)