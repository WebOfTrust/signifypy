#!/bin/bash

# To run this script you need to run the following command in a separate terminals:
#   > kli witness demo
# and from the vLEI repo run:
#   > vLEI-server -s ./schema/acdc -c ./samples/acdc/ -o ./samples/oobis/
#

# EHOuGiHMxJShXHgSb6k_9pqxmRb8H-LT0R2hQouHp8pW
kli init --name external --salt 0ACDEyMzQ1Njc4OWxtbm9GhI --nopasscode --config-dir "${KERI_SCRIPT_DIR}" --config-file demo-witness-oobis-schema
kli incept --name external --alias external --file "${KERI_DEMO_SCRIPT_DIR}"/data/gleif-sample.json

# EHMnCf8_nIemuPx-cUHaDQq8zSnQIFAurdEpwHpNbnvX
kli init --name qvi --salt 0ACDEyMzQ1Njc4OWxtbm9aBc --nopasscode --config-dir "${KERI_SCRIPT_DIR}" --config-file demo-witness-oobis-schema
kli incept --name qvi --alias qvi --file "${KERI_DEMO_SCRIPT_DIR}"/data/gleif-sample.json

# EIitNxxiNFXC1HDcPygyfyv3KUlBfS_Zf-ZYOvwjpTuz
kli init --name legal-entity --salt 0ACDEyMzQ1Njc4OWxtbm9AbC --nopasscode --config-dir "${KERI_SCRIPT_DIR}" --config-file demo-witness-oobis-schema
kli incept --name legal-entity --alias legal-entity --file "${KERI_DEMO_SCRIPT_DIR}"/data/gleif-sample.json

# EBcIURLpxmVwahksgrsGW6_dUw0zBhyEHYFk17eWrZfk
python "${KERI_SCRIPT_DIR}"/create_agent.py
python "${KERI_SCRIPT_DIR}"/create_person_aid.py

echo 'resolving external'
kli oobi resolve --name qvi --oobi-alias external --oobi http://127.0.0.1:5642/oobi/EHOuGiHMxJShXHgSb6k_9pqxmRb8H-LT0R2hQouHp8pW/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha
kli oobi resolve --name legal-entity --oobi-alias external --oobi http://127.0.0.1:5642/oobi/EHOuGiHMxJShXHgSb6k_9pqxmRb8H-LT0R2hQouHp8pW/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha
echo 'resolving qvi'
kli oobi resolve --name external --oobi-alias qvi --oobi http://127.0.0.1:5642/oobi/EHMnCf8_nIemuPx-cUHaDQq8zSnQIFAurdEpwHpNbnvX/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha
kli oobi resolve --name legal-entity --oobi-alias qvi --oobi http://127.0.0.1:5642/oobi/EHMnCf8_nIemuPx-cUHaDQq8zSnQIFAurdEpwHpNbnvX/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha
echo 'resolving legal-entity'
kli oobi resolve --name external --oobi-alias legal-entity --oobi http://127.0.0.1:5642/oobi/EIitNxxiNFXC1HDcPygyfyv3KUlBfS_Zf-ZYOvwjpTuz/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha
kli oobi resolve --name qvi --oobi-alias legal-entity --oobi http://127.0.0.1:5642/oobi/EIitNxxiNFXC1HDcPygyfyv3KUlBfS_Zf-ZYOvwjpTuz/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha
echo 'resolving person'
kli oobi resolve --name external --oobi-alias person --oobi http://127.0.0.1:3902/oobi/EBcIURLpxmVwahksgrsGW6_dUw0zBhyEHYFk17eWrZfk/agent/EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei
kli oobi resolve --name qvi --oobi-alias person --oobi http://127.0.0.1:3902/oobi/EBcIURLpxmVwahksgrsGW6_dUw0zBhyEHYFk17eWrZfk/agent/EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei
kli oobi resolve --name legal-entity --oobi-alias person --oobi http://127.0.0.1:3902/oobi/EBcIURLpxmVwahksgrsGW6_dUw0zBhyEHYFk17eWrZfk/agent/EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei

kli vc registry incept --name external --alias external --registry-name vLEI-external
kli vc registry incept --name qvi --alias qvi --registry-name vLEI-qvi
kli vc registry incept --name legal-entity --alias legal-entity --registry-name vLEI-legal-entity

# Issue QVI credential vLEI from GLEIF External to QVI
kli vc issue --name external --alias external --registry-name vLEI-external --schema EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao --recipient EHMnCf8_nIemuPx-cUHaDQq8zSnQIFAurdEpwHpNbnvX --data @"${KERI_DEMO_SCRIPT_DIR}"/data/qvi-data.json
kli vc accept --name qvi --alias qvi --poll --auto
kli vc list --name qvi --alias qvi

# Issue LE credential from QVI to Legal Entity - have to create the edges first
QVI_SAID=$(kli vc list --name qvi --alias qvi --said --schema EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao)
echo \"$QVI_SAID\" | jq -f "${KERI_DEMO_SCRIPT_DIR}"/data/legal-entity-edges-filter.jq  > /tmp/legal-entity-edges.json
kli saidify --file /tmp/legal-entity-edges.json
kli vc issue --name qvi --alias qvi --registry-name vLEI-qvi --schema ENPXp1vQzRF6JwIuS-mp2U8Uf1MoADoP_GqQ62VsDZWY --recipient EIitNxxiNFXC1HDcPygyfyv3KUlBfS_Zf-ZYOvwjpTuz --data @"${KERI_DEMO_SCRIPT_DIR}"/data/legal-entity-data.json --edges @/tmp/legal-entity-edges.json --rules @"${KERI_DEMO_SCRIPT_DIR}"/data/rules.json
kli vc accept --name legal-entity --alias legal-entity --poll --auto
kli vc list --name legal-entity --alias legal-entity

# Issue ECR Authorization credential from Legal Entity to QVI - have to create the edges first
LE_SAID=$(kli vc list --name legal-entity --alias legal-entity --said)
echo \"$LE_SAID\" | jq -f "${KERI_DEMO_SCRIPT_DIR}"/data/ecr-auth-edges-filter.jq > /tmp/ecr-auth-edges.json
kli saidify --file /tmp/ecr-auth-edges.json
kli vc issue --name legal-entity --alias legal-entity --registry-name vLEI-legal-entity --schema EH6ekLjSr8V32WyFbGe1zXjTzFs9PkTYmupJ9H65O14g --recipient EHMnCf8_nIemuPx-cUHaDQq8zSnQIFAurdEpwHpNbnvX --data @"${KERI_DEMO_SCRIPT_DIR}"/data/ecr-auth-data.json --edges @/tmp/ecr-auth-edges.json --rules @"${KERI_DEMO_SCRIPT_DIR}"/data/ecr-auth-rules.json
kli vc accept --name qvi --alias qvi --poll --auto
kli vc list --name qvi --alias qvi

# Issue ECR credential from QVI to Person
AUTH_SAID=$(kli vc list --name qvi --alias qvi --said --schema EH6ekLjSr8V32WyFbGe1zXjTzFs9PkTYmupJ9H65O14g)
echo "[\"$QVI_SAID\", \"$AUTH_SAID\"]" | jq -f "${KERI_DEMO_SCRIPT_DIR}"/data/ecr-edges-filter.jq > /tmp/ecr-edges.json
kli saidify --file /tmp/ecr-edges.json
kli vc issue --name qvi --alias qvi --private --registry-name vLEI-qvi --schema EEy9PkikFcANV1l7EHukCeXqrzT1hNZjGlUk7wuMO5jw --recipient EBcIURLpxmVwahksgrsGW6_dUw0zBhyEHYFk17eWrZfk --data @"${KERI_DEMO_SCRIPT_DIR}"/data/ecr-data.json --edges @/tmp/ecr-edges.json --rules @"${KERI_DEMO_SCRIPT_DIR}"/data/ecr-rules.json
python "${KERI_SCRIPT_DIR}"/list_person_credentials.py
