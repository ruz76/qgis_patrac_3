#!/usr/bin/env bash

# Be carefull it may change also color of the label

sed -i 's/<prop k="color" v="136,150,238,255"\/>/<prop k="color" v="255,254,159,255"\/>/g' $1
sed -i 's/<prop v="136,150,238,255" k="color"\/>/<prop k="color" v="255,254,159,255"\/>/g' $1
