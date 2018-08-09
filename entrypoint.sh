#!/bin/bash

echo "VERSION: $WAVES_VERSION"

/usr/bin/python3 "/waves-node/starter.py"
echo "Node is starting..."
mkdir -p /waves/data
/usr/bin/java -Dlogback.stdout.level="${WAVES_LOG_LEVEL}" "-Xmx${WAVES_HEAP_SIZE}" -jar "/waves-node/waves-all-${WAVES_VERSION}.jar" $WAVES_CONFIG_FILE