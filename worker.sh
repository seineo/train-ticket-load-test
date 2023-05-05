#!/bin/bash

echo "${MASTER_HOST}"-"${MASTER_PORT}"
locust -f locust_file.py --worker --master-host "${MASTER_HOST}" --master-port "${MASTER_PORT}"
