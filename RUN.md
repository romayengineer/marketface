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

============================================================

```
records len:  483
powerset len:  23862
replication factor:  49.40372670807454
replication log2:  5.626547968690595
Fitting 5 folds for each of 2000 candidates, totalling 10000 fits
Best parameters: {'subsample': 1.0, 'reg_lambda': 0.1, 'reg_alpha': 1.0, 'n_estimators': 500, 'min_child_weight': 1, 'max_depth': 8, 'learning_rate': 0.1, 'gamma': 0, 'colsample_bytree': 1.0}
Best cross-validation MAE: 296.2995853187791
Mean Absolute Error on test set: 273.74
Predicted price for new sample: 768.38
Feature: model, Importance: 0.049784
Feature: cpu, Importance: 0.206038
Feature: ram, Importance: 0.303823
Feature: disk, Importance: 0.095869
Feature: screen, Importance: 0.104545
Feature: year_bought, Importance: 0.239941
```

============================================================

```
records len:  507
powerset len:  25214
replication factor:  49.73175542406312
replication log2:  5.636095450960539
Fitting 5 folds for each of 2000 candidates, totalling 10000 fits
Best parameters: {'subsample': 1.0, 'reg_lambda': 1.0, 'reg_alpha': 1.0, 'n_estimators': 500, 'min_child_weight': 3, 'max_depth': 8, 'learning_rate': 0.05, 'gamma': 0, 'colsample_bytree': 1.0}
Best cross-validation MAE: 314.5160953457254
Mean Absolute Error on test set: 292.81
Predicted price for new sample: 783.32
Feature: model, Importance: 0.057885
Feature: cpu, Importance: 0.186108
Feature: ram, Importance: 0.330775
Feature: disk, Importance: 0.101617
Feature: screen, Importance: 0.110928
Feature: year_bought, Importance: 0.212686

real    22m19.996s
user    259m47.935s
sys     5m17.627s
```