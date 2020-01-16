PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games"
export PATH
unset PYTHONPATH
unset GISBASE
unset LD_LIBRARY_PATH
#printenv
echo "1: " + $1
echo "2: " + $2
echo "3: " + $3
echo "4: " + $4
echo "5: " + $5
echo "6: " + $6
python $2/grass/gpx.py $1 $2 $3 $4 $5 $6
