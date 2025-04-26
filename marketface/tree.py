
#!/usr/bin/env python3
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from marketface import database

import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error


model_col = []
cpu_col = []
memory_col = []
disk_col = []
price_col = []
all_records = database.get_all()
for record in all_records:
    model_col.append(record.model)
    cpu_col.append(record.cpu)
    memory_col.append(record.memory)
    disk_col.append(record.disk)
    price_col.append(record.price_usd)

print("model:  ", model_col[:10])
print("cpu:    ", cpu_col[:10])
print("memory: ", memory_col[:10])
print("disk:   ", disk_col[:10])
print("price:  ", price_col[:10])
print("count:  ", len(all_records))

# Create the dataset from your example
data = pd.DataFrame({
    'model': model_col,
    'cpu': cpu_col,
    'ram': memory_col,
    'disk': disk_col,
    'price': price_col,
})

# Preprocess: Replace missing values ("" for model/cpu, 0 for disk) with NaN
data['model'] = data['model'].replace('', pd.NA)
data['cpu'] = data['cpu'].replace('', pd.NA)
data['ram'] = data['ram'].replace(0, pd.NA)
data['disk'] = data['disk'].replace(0, pd.NA)

# Convert model and cpu to categorical type for XGBoost
data['model'] = data['model'].astype('category')
data['cpu'] = data['cpu'].astype('category')
data['ram'] = data['ram'].astype('Int64')
data['disk'] = data['disk'].astype('Int64')

# Define features and target
X = data[['model', 'cpu', 'ram', 'disk']]
# X = data[['model', 'cpu']]
y = data['price']

# Split data into training and test sets (use a small test size due to tiny dataset)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=42)

# Initialize and train XGBoost model
model = xgb.XGBRegressor(
    objective='reg:squarederror',  # For regression
    enable_categorical=True,       # Handle categorical features
    n_estimators=50,               # Number of trees
    learning_rate=0.1,             # Step size
    max_depth=3,                   # Max depth of trees
    random_state=42
)
model.fit(X_train, y_train)

# Predict on test set
y_pred = model.predict(X_train)

# Evaluate model
mae = mean_absolute_error(y_train, y_pred)
print(f"Mean Absolute Error on train set: {mae:.2f}")

# Predict on test set
y_pred = model.predict(X_test)

# Evaluate model
mae = mean_absolute_error(y_test, y_pred)
print(f"Mean Absolute Error on test set: {mae:.2f}")

# Example: Predict for a new sample with some missing values
new_data = pd.DataFrame({
    'model': [pd.NA],
    'cpu': ['m2'],
    'ram': [16],
    'disk': [pd.NA]
}).astype({
    'model': 'category',
    'cpu': 'category',
    'ram': 'Int64',
    'disk': 'Int64',
})
prediction = model.predict(new_data)
print(f"Predicted price for new sample: {prediction[0]:.2f}")

# Optional: Feature importance
feature_importance = model.feature_importances_
for feature, importance in zip(X.columns, feature_importance):
    print(f"Feature: {feature}, Importance: {importance:.6f}")