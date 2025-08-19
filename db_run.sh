#!/usr/bin/bash

cd ./data/base/

pocketbase serve --http 0.0.0.0:8090 $@

