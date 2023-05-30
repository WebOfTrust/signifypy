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
KERI_FALLBACK_STORAGE="${HOME}/.keri"

function getKeripyDir() {
    # Check if the environment variable is set
    if [ -z "$KERIPY_DIR" ]; then
        default_value="../keripy"
        # Prompt the user for input with a default value
        read -p "Set keripy dir [${default_value}]: " input
        # Set the value to the user input or the default value
        KERIPY_DIR=${input:-$default_value}
    fi
    # Use the value of the environment variable
    echo "$KERIPY_DIR"
}

function getKeriaDir() {
    # Check if the environment variable is set
    if [ -z "$KERIA_DIR" ]; then
        default_value="../keria"
        # Prompt the user for input with a default value
        read -p "Set keria dir [${default_value}]: " input
        # Set the value to the user input or the default value
        KERIA_DIR=${input:-$default_value}
    fi
    # Use the value of the environment variable
    echo "$KERIA_DIR"
}

function runDelegator() {
    #create the delegator from keripy
    keriDir=$1
    echo "Creating delegator"
    KERIPY_SCRIPTS_DIR="${keriDir}/scripts"
    delPid=-1
    if [ -d "${KERIPY_SCRIPTS_DIR}" ]; then
        kli init --name delegator --nopasscode --config-dir "${KERIPY_SCRIPTS_DIR}" --config-file demo-witness-oobis --salt 0ACDEyMzQ1Njc4OWdoaWpsaw
        KERIPY_DELEGATOR_CONF="${KERIPY_SCRIPTS_DIR}/demo/data/delegator.json"
        if [ -f "${KERIPY_DELEGATOR_CONF}" ]; then
            kli incept --name delegator --alias delegator --file "${KERIPY_DELEGATOR_CONF}"
            # kli incept --name delegator --alias delegator --file /Users/meenyleeny/VSCode/keripy/scripts/demo/data/delegator.json
            echo "Delegator created"
            # delgator auto-accepts the delegation request
            kli delegate confirm --name delegator --alias delegator -Y &
            delPid=$!
            echo "Delegator waiting to auto-accept delegation request"
        else
            echo "Delegator configuration missing ${KERIPY_DELEGATOR_CONF}"
        fi
    else
        echo "KERIPY directory ${KERIPY_SCRIPTS_DIR} does not exist."
    fi
}

echo "Welcome to the integration test setup/run/teardown script"

runSignify="test_salty"
while [ "${runSignify}" != "n" ]
do
    echo "Setting up..."
    witPid=-1
    keriDir=$(getKeripyDir)
    echo "Keripy dir set to: ${keriDir}"
    read -p "Run witness network (y/n)? [y]: " input
    runWit=${input:-"y"}
    if [ "${runWit}" == "y" ]; then
        if [ -d  "${keriDir}" ]; then
            cd "${keriDir}" || exit
            rm -rf ${KERI_PRIMARY_STORAGE}/*;rm -Rf ${KERI_FALLBACK_STORAGE}/*;kli witness demo &
            witPid=$!
            sleep 5
            echo "Clean witness network launched"
        else
            echo "KERIPY dir missing ${keriDir}"
            exit 1
        fi
    else
        echo "Skipping witness network"
    fi
    echo ""

    # run keria cloud agent
    keriaPid=-1
    read -p "Run Keria (y/n)? [y]: " input
    runKeria=${input:-"y"}
    if [ "${runKeria}" == "y" ]; then
        echo "Running keria cloud agent"
        keriaDir=$(getKeriaDir)
        if [ -d "${keriaDir}" ]; then
            keria start --config-file demo-witness-oobis.json --config-dir ${keriaDir}/scripts &
            keriaPid=$!
            sleep 5
            echo "Keria cloud agent running"
        else
            echo "Keria dir missing ${keriaDir}"
        fi
    fi
    echo ""

    # Assumes you are running from the base signify dir (see hints at the top)
    cd "${ORIG_CUR_DIR}" || exit
    integrationTestModule="integration.app.integration_clienting"
    echo "Available functions in ${integrationTestModule}"
    python -c "import ${integrationTestModule}; print('\n'.join(x for x in dir(${integrationTestModule}) if x.startswith('test_')))"

    read -p "What signify test to run (n to skip)?, [${runSignify}]: " input
    runSignify=${input:-$runSignify}
    if [ "${runSignify}" == "n" ]; then
        echo "Skipping signify test"
    else
        echo "Launching Signifypy test ${runSignify}"
        signifyPid=-1
        iClient="./integration/app/integration_clienting.py"
        if [ -f "${iClient}" ]; then
            if [ "${runSignify}" == "test_delegation" ]; then
                runDelegator ${keriDir}
            fi
            python -c "from ${integrationTestModule} import ${runSignify}; ${runSignify}()" &
            signifyPid=$!
            sleep 10
            echo "Completed signify ${runSignify}"
        else
            echo "${iClient} module missing"
            exit 1
        fi
    fi
    echo ""

    read -p "Your witness network and KERIA are still running, hit enter to tear down: " input
    echo "Tearing down any leftover processes"
    #tear down the signify client
    kill "$signifyPid" >/dev/null 2>&1
    # tear down the keria cloud agent
    kill $keriaPid >/dev/null 2>&1
    # tear down the delegator
    kill "$delPid" >/dev/null 2>&1
    # tear down the witness network
    kill $witPid >/dev/null 2>&1

    read -p "Run another test (n to quit, hit enter to run another test)?: " input
    runSignify=${input:-$runSignify}
done

echo "Done"