#!/bin/bash

# psql test_template -U esko -c "DROP DATABASE test_eskodb;"
# psql test_template -U esko -c "CREATE DATABASE test_eskodb;"
# psql test_eskodb -U esko -f eskodb2.sql

#export PYTHONPATH=$(pwd)/tests/:$(pwd)

python tornado_serveri.py tests/test_config.json &
SERVER_PID=$!

robot --outputdir=tests/functional/results \
      --pythonpath .:tests \
      -e selenium \
      tests/functional/

TEST_RESULT=$?
echo ${TEST_RESULT}

kill $SERVER_PID

#
python3 /Users/tommioinonen/git/TestArchiver/test_archiver/output_parser.py \
        --database eskodb_tests --dbengine postgres --user esko \
        --series "Test development" \
        tests/functional/results/output.xml


exit ${TEST_RESULT}
