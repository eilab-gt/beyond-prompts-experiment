#!/bin/bash

cd ../Application/Deployment/Models || exit

mkdir -p gedi

cd gedi || exit

wget https://storage.googleapis.com/sfr-gedi-data/gedi_topic.zip
unzip gedi_topic.zip
rm gedi_topic.zip

cd .. || exit

mkdir -p carp

cd carp || exit

wget https://the-eye.eu/public/AI/models/CARP/CARP_L.pt