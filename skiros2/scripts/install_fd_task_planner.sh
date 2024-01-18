#!/bin/bash
echo "Installing planner..."

# Check if git is installed
if ! [ -x "$(command -v git)" ]; then
    echo "Error: git is not installed." >&2
    exit 1
fi

default="~/.skiros/planner"
# Check if an argument is provided
if [ $# -eq 0 ]; then
    echo "Select install folder or leave blank for default [default: $default]:"
    read folder
else
    folder=$1
fi

# Navigate to install folder
if [[ $folder == "" ]]; then
    folder=${default/"~"/$HOME}
else
    folder=${folder/"~"/$HOME}
fi

# Installing planner
if [ ! -d "$folder/tfd" ]; then
    echo "Installing planner."
    mkdir -p $folder
    cd $folder
    git clone https://github.com/neighthan/tfd
    cd tfd
    ./build
    cd -
else
    echo "Folder $folder/${tfd} already exists. Skipping installation."
    cd $folder
fi

echo "Add environment variable to bashrc"
string="export TFD_HOME=$(pwd)/tfd/downward"
temp=$(cat ~/.bashrc | grep "$string")
if [ -z "$temp" ]; then
    echo "# TDF Planner for SkiROS" >> ~/.bashrc
    echo $string >> ~/.bashrc
    echo "Printing string in .bashrc: $string"
else
    echo "No export string added to bashrc (it is already there)"
fi

source ~/.bashrc
