#!/bin/bash

#
# Run this script from the base SignifyPy directory, like
# signifypy% ./integration/app/delegate.sh
#

#print commands
#set -x

#save this current directory, this is where the integration_clienting file also is
ORIG_CUR_DIR=$( pwd )

KERI_PRIMARY_STORAGE="/usr/local/var/keri"
KERI_FALLBACK_STORAGE="${HOME}/.keri"

KERI_DEV_BRANCH="development"
KERI_DEV_TAG="c3a6fc455b5fac194aa9c264e48ea2c52328d4c5"
VLEI_DEV_BRANCH="dev"
VLEI_DEV_TAG="ed982313dab86bfada3825857601a10d71ce9631"
KERIA_DEV_BRANCH="main"
KERIA_DEV_TAG="65bebb4912557067ca290f4765e85aafa657c46f"
SIGNIFY_DEV_BRANCH="main"

prompt="y"
function intro() {
    echo "Welcome to the integration test setup/run/teardown script"
    read -p "Enable prompts?, [y]: " enablePrompts
    prompt=${enablePrompts:-"y"}
    if [ "${prompt}" != "n" ]; then
        echo "Prompts enabled"
    else
        echo "Skipping prompts, using defaults"
    fi
}

function getKeripyDir() {
    # Check if the environment variable is set
    if [ -z "$KERIPY_DIR" ]; then
        default_value="../keripy"
        # Prompt the user for input with a default value
        if [ "${prompt}" == "y" ]; then
            read -p "Set keripy dir [${default_value}]: " keriDirInput
        fi
        # Set the value to the user input or the default value
        KERIPY_DIR=${keriDirInput:-$default_value}
    fi
    # Use the value of the environment variable
    echo "$KERIPY_DIR"
}

function getVleiDir() {
    # Check if the environment variable is set
    if [ -z "$VLEI_DIR" ]; then
        default_value="../vLEI"
        # Prompt the user for input with a default value
        if [ "${prompt}" == "y" ]; then
            read -p "Set vlei dir [${default_value}]: " vleiDirInput
        fi
        # Set the value to the user input or the default value
        VLEI_DIR=${vleiDirInput:-$default_value}
    fi
    # Use the value of the environment variable
    echo "$VLEI_DIR"
}

function getKeriaDir() {
    # Check if the environment variable is set
    if [ -z "$KERIA_DIR" ]; then
        default_value="../keria"
        # Prompt the user for input with a default value
        if [ "${prompt}" == "y" ]; then
            read -p "Set keria dir [${default_value}]: " keriaDirInput
        fi
        # Set the value to the user input or the default value
        KERIA_DIR=${keriaDirInput:-$default_value}
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

function runMultisig() {
    #create the delegator from keripy
    keriDir=$1
    echo "Creating multisig"
    KERIPY_SCRIPTS_DIR="${keriDir}/scripts"
    delPid=-1
    if [ -d "${KERIPY_SCRIPTS_DIR}" ]; then

        # Follow commands run in parallel
        kli multisig incept --name multisig1 --alias multisig1 --group multisig --file ${KERI_DEMO_SCRIPT_DIR}/data/multisig-triple-sample.json &
        pid=$!
        PID_LIST+=" $pid"
        kli multisig incept --name multisig2 --alias multisig2 --group multisig --file ${KERI_SCRIPTS_DIR}/data/multisig-triple-sample.json &
        pid=$!
        PID_LIST+=" $pid"


        kli init --name multisig1 --salt 0ACDEyMzQ1Njc4OWxtbm9aBc --nopasscode --config-dir "${KERIPY_SCRIPTS_DIR}" --config-file demo-witness-oobis
        kli init --name multisig2 --salt 0ACDEyMzQ1Njc4OWdoaWpsaw --nopasscode --config-dir "${KERIPY_SCRIPTS_DIR}" --config-file demo-witness-oobis
        KERIPY_MULTISIG_CONF_1="${KERIPY_SCRIPTS_DIR}/demo/data/multisig-1-sample.json"
        KERIPY_MULTISIG_CONF_2="${KERIPY_SCRIPTS_DIR}/demo/data/multisig-2-sample.json"
        if [ -f "${KERIPY_MULTISIG_CONF_2}" ]; then
            kli incept --name multisig1 --alias multisig1 --file "${KERIPY_MULTISIG_CONF_1}"
            kli incept --name multisig2 --alias multisig2 --file "${KERIPY_MULTISIG_CONF_2}"

            echo "Multisig 1 and 2 created"
            kli oobi resolve --name multisig1 --oobi-alias multisig2 --oobi http://127.0.0.1:5642/oobi/EJccSRTfXYF6wrUVuenAIHzwcx3hJugeiJsEKmndi5q1/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha &
            kli oobi resolve --name multisig1 --oobi-alias multisig3 --oobi http://127.0.0.1:5642/oobi/EKzS2BGQ7qkmEfsjGdx2w5KwmpWKf7lEXAMfB4AKqvUe/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha &
            kli oobi resolve --name multisig2 --oobi-alias multisig1 --oobi http://127.0.0.1:5642/oobi/EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha &
            kli oobi resolve --name multisig2 --oobi-alias multisig3 --oobi http://127.0.0.1:5642/oobi/EKzS2BGQ7qkmEfsjGdx2w5KwmpWKf7lEXAMfB4AKqvUe/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha &
            echo "All participants of multisig looking for each other"
        else
            echo "Multisig configuration missing ${KERIPY_MULTISIG_CONF_2}"
        fi
    else
        echo "KERIPY directory ${KERIPY_SCRIPTS_DIR} does not exist."
    fi
}

function runIssueEcr() {
    cd "${ORIG_CUR_DIR}" || exit
    if [ "${prompt}" == "y" ]; then
        read -p "Run vLEI issue ECR script (n to skip)?, [n]: " runEcr
    fi
    runIssueEcr=${runEcr:-"n"}
    if [ "${runIssueEcr}" == "n" ]; then
        echo "Skipping Issue ECR script"
    else
        echo "Running issue ECR script"
        scriptsDir="scripts"
        if [ -d "${scriptsDir}" ]; then
            echo "Launching Issue ECR script"
            cd ${scriptsDir} || exit
            source env.sh
            source issue-ecr.sh
            echo "Completed issue ECR script"
            python list_person_credentials.py
            echo "Listed person credentials"
        fi
    fi
    cd "${ORIG_CUR_DIR}" || exit
}

function runKeri() {
    cd ${ORIG_CUR_DIR} || exit
    witPid=-1
    keriDir=$(getKeripyDir)
    echo "Keripy dir set to: ${keriDir}"
    if [ "${prompt}" == "y" ]; then
        read -p "Run witness network (y/n)? [y]: " runWitNet
    fi
    runWit=${runWitNet:-"y"}
    if [ "${runWit}" == "y" ]; then
        if [ -d  "${keriDir}" ]; then
            #run a clean witness network
            echo "Launching a clean witness network"
            cd "${keriDir}" || exit
            updateFromGit ${KERI_DEV_BRANCH}
            installPythonUpdates "keri"
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
}

function runKeria() {
        # run keria cloud agent
    keriaPid=-1

    if [ "${prompt}" == "y" ]; then
        read -p "Run Keria (y/n)? [y]: " runKeriaInput
    fi
    runKeria=${runKeriaInput:-"y"}
    if [ "${runKeria}" == "y" ]; then
        echo "Running keria cloud agent"
        keriaDir=$(getKeriaDir)
        if [ -d "${keriaDir}" ]; then
            cd "${keriaDir}" || exit
            updateFromGit ${KERIA_DEV_BRANCH}
            installPythonUpdates "keria"
            export KERI_AGENT_CORS=true
            keria start --config-file demo-witness-oobis.json --config-dir "${keriaDir}/scripts" &
            keriaPid=$!
            sleep 5
            echo "Keria cloud agent running"
        else
            echo "Keria dir missing ${keriaDir}"
        fi
    fi
    echo ""
}

function runSignifyIntegrationTests() {
    # Assumes you are running from the base signify dir (see hints at the top)
    cd "${ORIG_CUR_DIR}" || exit
    integrationTestModule="integration.app.integration_clienting"
    echo "Available functions in ${integrationTestModule}"
    testList=$(python -c "import ${integrationTestModule}; print('\n'.join(x for x in dir(${integrationTestModule}) if x.startswith('test_')))")
    echo "${testList}"
    # echo "all"

    read -p "What signify test to run (n to skip integration tests)?, [${runSignify}]: " runSigInput
    runSignify=${runSigInput:-"n"}
    if [ "${runSignify}" == "n" ]; then
        echo "Skipping signify test"
    else
        runIntegrationTest "${runSignify}"
    fi
}

function runIntegrationTest() {
    testName=$1
    echo "Launching Signifypy integration test ${testName}"
    signifyPid=-1
    updateFromGit ${SIGNIFY_DEV_BRANCH}
    installPythonUpdates "signify"
    iClient="./integration/app/integration_clienting.py"
    if [ -f "${iClient}" ]; then
        if [ "${testName}" == "test_delegation" ]; then
            runDelegator "${keriDir}"
        fi
        if [ "${testName}" == "test_multisig" ]; then
            runMultisig "${keriDir}"
        fi
        python -c "from ${integrationTestModule} import ${testName}; ${testName}()" &
        signifyPid=$!
        sleep 10
        echo "Completed signify ${testName}"
    else
        echo "${iClient} module missing"
        exit 1
    fi
}

function runVlei() {
    # run vLEI cloud agent
    cd ${ORIG_CUR_DIR} || exit
    vleiPid=-1
    if [ "${prompt}" == "y" ]; then
        read -p "Run vLEI (y/n)? [y]: " runVleiInput
    fi
    runVlei=${runVleiInput:-"y"}
    if [ "${runVlei}" == "y" ]; then
        echo "Running vLEI server"
        vleiDir=$(getVleiDir)
        if [ -d "${vleiDir}" ]; then
            cd "${vleiDir}" || exit
            updateFromGit ${VLEI_DEV_BRANCH}
            installPythonUpdates "vlei"
            vLEI-server -s ./schema/acdc -c ./samples/acdc/ -o ./samples/oobis/ &
            vleiPid=$!
            sleep 5
            echo "vLEI server is running"
        else
            echo "vLEI dir missing ${vleiDir}"
        fi
    fi
    echo ""
}

function installPythonUpdates() {
    name=$1
    if [ "${prompt}" == "y" ]; then
        read -p "Install $name?, [n]: " installInput
    fi
    install=${installInput:-"n"}
    if [ "${install}" == "n" ]; then
        echo "Skipping install of $name"
    else
        echo "Installing python module updates..."
        python -m pip install -e .
    fi
}

function updateFromGit() {
    branch=$1
    commit=$2

    if [ "${prompt}" == "y" ]; then
        read -p "Update git repo ${branch} ${commit}?, [n]: " upGitInput
    fi
    update=${upGitInput:-"n"}
    if [ "${update}" == "y" ]; then
        echo "Updating git branch ${branch} ${commit}"
        fetch=$(git fetch)
        echo "git fetch status ${fetch}"
        if [ -z "${commit}" ]; then
            switch=$(git switch "${branch}")
            echo "git switch status ${switch}"
            pull=$(git pull)
            echo "git pull status ${pull}"
        else
            switch=$(git checkout "${commit}")
            echo "git checkout commit status ${switch}"
        fi
    else
        echo "Skipping git update ${branch}"
    fi
}

runInt="test_salty"
while [ "${runInt}" != "n" ]
do
    intro

    echo "Setting up..."

    runKeri

    sleep 3

    runVlei

    sleep 3

    runKeria

    sleep 3

    runSignifyIntegrationTests

    sleep 3

    runIssueEcr

    echo ""

    if [ "${prompt}" == "y" ]; then
        read -p "Your servers still running, hit enter to tear down: " teardown
    fi
    
    echo "Tearing down any leftover processes"
    #tear down the signify client
    kill "$signifyPid" >/dev/null 2>&1
    # tear down the keria cloud agent
    kill $keriaPid >/dev/null 2>&1
    # tear down the delegator
    kill "$delPid" >/dev/null 2>&1
    # tear down the vLEI server
    kill $vleiPid >/dev/null 2>&1
    # tear down the witness network
    kill $witPid >/dev/null 2>&1

    read -p "Run another test [n]?: " runAgain
    runInt=${runAgain:-"n"}
done

echo "Done"