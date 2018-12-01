#!/usr/bin/env bash

# ############ ############ ############ NOTES ############ ############ ############
# This script takes care of running each test as a separate python test.
# It is easy to run each test as an isolated python process as it interacts with
# internal python logging system and the atexit() triggers at the system-level are
# tough to mess with.
# ############ ############ ############ ############ ############ ############ #####

# Current test coverage for TestSCALogger0 - TestSCALogger8
for (( n=0; n<=8; n++ ))
do
    echo "********** Executing TestClass: TestSCALogger$n **********"
    nosetests tests/test_sca_logger.py:TestSCALogger"$n" --nologcapture
    # sleep to make sure the kinesis resources are cleaned up correctly
    sleep 0.5
    echo ""
done

for (( m=0; m<=0; m++ ))
do
    echo "********** Executing TestClass: TestSCALogDecorator$m **********"
    nosetests tests/test_sca_log_decorator.py:TestSCALogDecorator"$m" --nologcapture
    # sleep to make sure the kinesis resources are cleaned up correctly
    sleep 0.5
    echo ""
done