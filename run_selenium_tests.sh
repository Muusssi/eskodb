#!/bin/bash

DB_LOG="tests/functional/selenium/results/db_clearing_log.txt"

psql test_template -U esko -c "DROP DATABASE test_eskodb;" > ${DB_LOG}
psql test_template -U esko -c "CREATE DATABASE test_eskodb;" >> ${DB_LOG}
psql test_eskodb -U esko -f backups/latest.sql >> ${DB_LOG}

pwd=$(pwd)
export PYTHONPATH=${pwd}/tests/:${pwd}

python tornado_serveri.py tests/test_config.json &
SERVER_PID=$!

robot --outputdir=tests/functional/selenium/results tests/functional/selenium.robot
TEST_RESULT=$?
echo ${TEST_RESULT}

kill $SERVER_PID

exit ${TEST_RESULT}
