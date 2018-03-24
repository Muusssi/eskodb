#!/bin/bash

psql test_template -U esko -c "DROP DATABASE test_eskodb;"
psql test_template -U esko -c "CREATE DATABASE test_eskodb;"
psql test_eskodb -U esko -f eskodb2.sql

pwd=$(pwd)
export PYTHONPATH=${pwd}/tests/:${pwd}

python tornado_serveri.py tests/test_config.json &
SERVER_PID=$!

robot --outputdir=tests/functional/results tests/functional/main.robot
TEST_RESULT=$?
echo ${TEST_RESULT}

kill $SERVER_PID

exit ${TEST_RESULT}
