#!/bin/bash

echo "VERSION: $WAVES_VERSION"

/usr/bin/python3 "/waves-node/hocon-parser.py"
echo "Downloading jar file ..."
FILENAME="waves-all-$WAVES_VERSION.jar"
if [ ! -f "/waves-node/${FILENAME}" ]; then
    /usr/bin/curl -sLo "/waves-node/${FILENAME}" "https://github.com/wavesplatform/Waves/releases/download/v${WAVES_VERSION}/${FILENAME}"
fi


echo "Node is starting..."
mkdir -p /waves/data
/usr/bin/java -Dlogback.stdout.level="${WAVES_LOG_LEVEL}" "-Xmx${WAVES_HEAP_SIZE}" -jar "/waves-node/${FILENAME}" /waves/configs/waves-config.conf