#!/usr/bin/env bash

zip -r marketface_data.zip data

new_file=marketface_data_`date +%Y%m%d%H%M%S`.zip
new_location=~/Project/backups/marketface/$new_file

mv marketface_data.zip $new_location

echo backup saved into $new_location