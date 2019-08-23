#!/bin/bash

/usr/bin/python3 "/waves-node/starter.py"
echo "Node is starting..."
mkdir -p /waves/data
java --add-modules=java.xml.bind --add-exports java.base/jdk.internal.ref=ALL-UNNAMED -Dlogback.stdout.level="${WAVES_LOG_LEVEL}" "-XX:+ExitOnOutOfMemoryError" "-Xmx${WAVES_HEAP_SIZE}" -jar "/waves-node/waves-all-${WAVES_VERSION}.jar" $WAVES_CONFIG_FILE
