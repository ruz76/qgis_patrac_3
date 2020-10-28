#!/usr/bin/env bash

sed -i 's/<prop v=\"0.26\"\ k=\"outline_width\"\/>/<prop v=\"2.0\"\ k=\"outline_width\"\/>/g' $1
sed -i 's/<prop k=\"outline_width\"\ v=\"0.26\"\/>/<prop v=\"2.0\"\ k=\"outline_width\"\/>/g' $1
sed -i 's/<prop k="outline_color" v="0,0,0,255"\/>/<prop k="outline_color" v="255,1,255,38"\/>/g' $1
sed -i 's/<prop v="0,0,0,255" k="outline_color"\/>/<prop k="outline_color" v="255,1,255,38"\/>/g' $1
