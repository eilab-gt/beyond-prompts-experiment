#!/bin/bash

# This script runs the addon server.

# Running this server will give you an IP it runs on; You will need to put that address into configurations for other servers.

# Conda setup
eval "$(command conda 'shell.bash' 'hook' 2> /dev/null)"

echo "Setting source directory..."

#BASEDIR=$(dirname "$0")
BASEDIR="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
echo "$BASEDIR"
SOURCEDIR="$BASEDIR/../../" # The folder containing `StorytellingDomain`

echo "Adding the following source directory: [$SOURCEDIR]"

export PYTHONPATH="$PYTHONPATH:$SOURCEDIR"

echo "PYTHONPATH is [$PYTHONPATH]"

echo "Activating conda env 'storytelling-domain-for-creative-wand'..."

conda activate storytelling-domain-for-creative-wand

cd ../../StorytellingDomain/Application/Deployment/ || exit

echo "pwd:"
pwd

python StartAddonServer.py pnb-demo-release carp-demo-release

# Then you can do this: ssh -fNT -L 8765:localhost:8765 [username@hostname]