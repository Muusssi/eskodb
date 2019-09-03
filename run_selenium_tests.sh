#!/bin/bash

psql -U esko -c "DROP DATABASE test_eskodb;"
psql -U esko -c "CREATE DATABASE test_eskodb;"
psql test_eskodb -U esko -f eskodb2.sql

PYTHONPATH=./ python3 tornado_serveri.py tests/test_config.json &
SERVER_PID=$!

robot --outputdir=tests/functional/results/selenium \
      --pythonpath .:tests \
      -i selenium \
      tests/functional/
      #-e done \

TEST_RESULT=$?
echo ${TEST_RESULT}

kill $SERVER_PID

exit ${TEST_RESULT}
