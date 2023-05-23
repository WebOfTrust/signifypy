#!/bin/bash

#
# Run this script from the base SignifyPy directory, like
# signifypy% ./integration/app/delegate.sh
#

#print commands
#set -x

#save this current directory, this is where the integration_clienting file also is
ORIG_CUR_DIR=$( pwd )

#run a clean witness network
echo "Launching a clean witness network"
KERI_PRIMARY_STORAGE="/usr/local/var/keri"
KERI_FALLBACK_STORAGE="~/.keri"

# Check if the environment variable is set
if [ -z "$KERIPY_DIR" ]; then
    default_value="../keripy"
    # Prompt the user for input with a default value
    read -p "Keripy dir not set, [$default_value]: " input
    # Set the value to the user input or the default value
    KERIPY_DIR=${input:-$default_value}
fi
# Use the value of the environment variable
echo "KERIPY_DIR is set to: $KERIPY_DIR"

witPid=-1
if [ -d "${KERIPY_DIR}" ]; then
    cd ${KERIPY_DIR}
    rm -rf ${KERI_PRIMARY_STORAGE}/*;rm -Rf ${KERI_FALLBACK_STORAGE}/*;kli witness demo &
    witPid=$!
    sleep 5
    echo "Clean witness network launched"
else
    echo "KERIPY dir missing ${KERIPY_DIR}"
    exit 1
fi

#create the delegator from keripy
echo "Creating delegator"
KERIPY_SCRIPTS_DIR="${KERIPY_DIR}/scripts"
if [ -d "${KERIPY_SCRIPTS_DIR}" ]; then
    kli init --name delegator --nopasscode --config-dir ${KERIPY_SCRIPTS_DIR} --config-file demo-witness-oobis --salt 0ACDEyMzQ1Njc4OWdoaWpsaw
    # kli init --name delegator --nopasscode --config-dir /Users/meenyleeny/VSCode/keripy/scripts --config-file demo-witness-oobis --salt 0ACDEyMzQ1Njc4OWdoaWpsaw
    KERIPY_DELEGATOR_CONF="${KERIPY_SCRIPTS_DIR}/demo/data/delegator.json"
    if [ -f "${KERIPY_DELEGATOR_CONF}" ]; then
        kli incept --name delegator --alias delegator --file ${KERIPY_DELEGATOR_CONF}
        # kli incept --name delegator --alias delegator --file /Users/meenyleeny/VSCode/keripy/scripts/demo/data/delegator.json
        echo "Delegator created"
        # delgator auto-accepts the delegation request
        kli delegate confirm --name delegator --alias delegator -Y &
        echo "Delegator waiting to auto-accept delegation request"
    else
        echo "Delegator configuration missing ${KERIPY_DELEGATOR_CONF}"
    fi
else
    echo "KERIPY Directory ${KERIPY_SCRIPTS_DIR} does not exist."
fi

# Check if the environment variable is set
if [ -z "$KERIA_DIR" ]; then
    default_value="../keria"
    # Prompt the user for input with a default value
    read -p "Keria dir not set, [$default_value]: " input
    # Set the value to the user input or the default value
    KERIA_DIR=${input:-$default_value}
fi
# Use the value of the environment variable
echo "KERIA_DIR is set to: $KERIA_DIR"

# run keria cloud agent
echo "Running keria cloud agent"
keriaPid=-1
if [ -d "${KERIA_DIR}" ]; then
    keria start --config-file demo-witness-oobis.json --config-dir $KERIA_DIR/scripts &
    keriaPid=$!
    sleep 5
    echo "Keria cloud agent running"
else
    echo "Keria dir missing ${KERIA_DIR}"
fi

# echo "Running signify test delegation"
# Assumes you are running from the base signify dir (see hint at the top)
echo "Launching Signifypy test delegation"
signifyPid=-1
cd ${ORIG_CUR_DIR}
iClient="./integration/app/integration_clienting.py"
if [ -f "${iClient}" ]; then
    python -c 'from integration.app.integration_clienting import test_delegation; test_delegation()' &
    signifyPid=$!
    sleep 10
    echo "Completed signify test delegation"
else
    echo "integration_clienting.py module missing ${iClient}"
    exit 1
fi

echo "Tearing down any leftover processes"
#tear down the signify client
kill $signifyPid >/dev/null 2>&1
# tear down the keria cloud agent
kill $keriaPid >/dev/null 2>&1
# tear down the witness network
kill $witPid >/dev/null 2>&1