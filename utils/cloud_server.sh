#!/usr/bin/env bash

if [ -z "$VCD_SERVER" ];
then
    echo "Requires environment variables: VCD_SERVER VCD_ORG VCD_VDC VCD_CATALOG LICENSE"
    exit 1
fi

python --version
pip install --upgrade pip
pip install vcd_cli

vcd login $VCD_SERVER $VCD_ORG testrunner --vdc $VCD_VDC -V "27.0"

if [ -z "$TRAVIS_JOB_NUMBER" ]
then
    export MACHINE="$(date "+test-%Y-%m-%d-%H-%M-%S")"
else
    export MACHINE="travis-$TRAVIS_EVENT_TYPE-$TRAVIS_JOB_NUMBER-$TRAVIS_COMMIT"
fi

vcd --debug vapp create $VCD_CATALOG li45template "$MACHINE"
python utils/cloud_server.py vm publiclyaccessible "$MACHINE"
python utils/cloud_server.py vm bootstrap_li "$MACHINE"

eval $(python utils/cloud_server.py  vm externalip --env "$MACHINE")
pytest -v --server "$IP" --license "$LICENSE"

vcd vapp delete "$MACHINE" --yes --force
