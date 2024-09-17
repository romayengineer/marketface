# Description

This is a simple project made in python playwright and is for pulling
facebook marketplace items into a database for analysis like e.g. to
know if a product has a fair price or if it is cheep

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
