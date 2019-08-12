CONFIGFILE=jitenshop/config.ini
USER=$(awk -F " = " '/user/ {print $2}' $CONFIGFILE)
DBNAME=$(awk -F " = " '/dbname/ {print $2}' $CONFIGFILE)
HOST=$(awk -F " = " '/host/ {print $2}' $CONFIGFILE)
PORT=$(awk -F " = " '/port/ {print $2}' $CONFIGFILE)
echo "user:$USER dbname:$DBNAME host:$HOST port:$PORT"

SCHEMA=$(awk -F " = " '/schema/ {print $2}' $CONFIGFILE)
DATADIR=data/$SCHEMA/

if [ -d "$DATADIR" ]; then
    echo "Remove $DATADIR folder..."
    rm -r $DATADIR
fi

psql -v ON_ERROR_STOP=1 "host=$HOST port=$PORT user=$USER dbname=postgres" -c "drop database if exists $DBNAME" || exit
psql -v ON_ERROR_STOP=1 "host=$HOST port=$PORT user=$USER dbname=postgres" -c "create database $DBNAME" || exit

psql -v ON_ERROR_STOP=1 "host=$HOST port=$PORT user=$USER dbname=$DBNAME" -c "CREATE EXTENSION postgis" || exit
