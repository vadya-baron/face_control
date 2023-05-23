#! /bin/bash

# На случай, если будет падать
# python ./main.py &

while 1>0
do
ps -A | grep main.py > /dev/null
if [ $? = "1" ]
then python ./main.py &
fi
sleep 5
done
