#!/bin/bash

psql test_template -U esko -c "DROP DATABASE test_eskodb;"
psql test_template -U esko -c "CREATE DATABASE test_eskodb;"
psql test_eskodb -U esko -f eskodb2.sql

pwd=$(pwd)
export PYTHONPATH=${pwd}/tests/:${pwd}

python tornado_serveri.py tests/test_config.json &
SERVER_PID=$!

robot tests/functional/main.robot

kill $SERVER_PID

mv output.xml tests/functional/
mv log.html tests/functional/
mv report.html tests/functional/