

# Demostrating vLEI Credential Issuance to KERIA AID
This directory contains the scripts needed to create a vLEI hierarchy of credentials with the QVI, and Legal Entity
credentials being issued to AIDs created with the `kli` but the ECR credential is issued to an AID hosted in a KERIA
service.  To accomplish this, the script expects running witnesses and a running KERIA service and uses `python` scripts 
to create an Agent in the KERIA service, perform OOBI resolution and finally list the newly issued credential all using
the SignifyPy client library in the `python` scripts.

The script using `0123456789abcdefghijk` as the passcode for the Agent it creates.  This can be used in other Signify 
Clients to test credential list and export.

## Scripts
* issue-ecr.sh - main entry point that uses the kli and python with SignifyPy to create the scenario
* create_agent.py - `python` script for Booting an Agent in a running instance of KERIA
* create_person_aid.py - `python` script for performing AID inception and OOBI resolution (including data OOBIs for schema)
* list_person_credentials.py - `python` script for listing and exporting the credential received (this can be run any number of times after the main script completes)

## Directories
* data - This directory contains the AID inception files and data files for credential issuance
* keri - This directory contains a configuration file for the `kli` commands that create AIDs.

## Steps
There are three steps to running this demo.  Each of the steps listed must be run in the order list, in separate terminal
windows and be left running.

#### From the keripy repo 

In the root directory of the repo on the development branch:

```bash
$ rm -rf /usr/local/var/keri/*;kli witness demo
```

#### From the KERIA repo 

In the root directory of the repo on the main branch:

```bash
$ keria start --config-dir scripts --config-file demo-witness-oobis
```

#### From the signifypy repo

In the `scripts` directory on the main branch:

```bash
$ source ./env.sh;./issue-ecr.sh
```

After that is complete, the command 

```bash
$ python list_person_credentials.py
```

can be run repeatedly to see the exported credential.