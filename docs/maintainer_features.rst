Maintainer Feature Guide
========================

This page is the maintainer-facing map of the current SignifyPy request
surface.

The original tracking issue, `Documentation issue #18 <https://github.com/WebOfTrust/signifypy/issues/18>`_,
asked for request documentation for identifiers, agents, registries, schemas,
challenges, contacts, and credentials. That list is too small for the current
client. To keep the docs truthful, this guide also covers delegation plus the
other major maintained feature families that are already present in code and
tests.

Use this page when you need to answer four questions quickly:

- Which client accessor owns a feature?
- Which KERIA routes does that feature use?
- Which tests prove the behavior today?
- Where is the surface incomplete or intentionally narrow?

Documentation Plan
------------------

Closing the documentation gap for SignifyPy requires two layers of
documentation, not one:

- maintainer-facing feature docs in this guide, describing request families,
  route ownership, workflow semantics, and test coverage
- code-level docs in the implementation modules, especially class docstrings,
  method docstrings, and the autodoc-generated API reference pages

Verdict:

- updating only the narrative docs is insufficient because it leaves the code
  surface opaque to maintainers reading the implementation
- updating only docstrings is insufficient because it does not give maintainers
  one truthful map of the whole client surface

Plan rule:

- treat feature-guide updates and code-level documentation updates as one unit
  of maintenance work when documenting or expanding a major client surface
- when a resource family is added or materially changed, update both this guide
  and the relevant module docstrings in the same change where practical

Contract Sources
----------------

- ``signify-ts`` is the capability contract leader for modern Signify behavior.
- ``keripy`` and ``keria`` remain the behavior and interoperability references
  for KERI and KERIA workflow semantics.
- ``signifypy/tests/app``, ``tests/core``, and ``tests/peer`` are the fast
  request-shape guardrails.
- ``signifypy/tests/integration`` is the live workflow contract layer for the
  Python client.

Feature Inventory
-----------------

.. list-table::
   :header-rows: 1
   :widths: 18 20 24 38

   * - Family
     - Client surface
     - Primary modules
     - Status
   * - Agent requests
     - ``SignifyClient.boot()``, ``connect()``, ``states()``, ``approveDelegation()``, ``rotate()``
     - ``signify.app.clienting``
     - Maintained and unit-tested; owns controller-agent bootstrap and approval.
   * - Identifier requests
     - ``client.identifiers()``
     - ``signify.app.aiding``
     - Maintained and integration-tested across single-sig, witnessed, delegated, and multisig flows.
   * - Registry requests
     - ``client.registries()``
     - ``signify.app.credentialing``
     - Maintained for registry list/read plus canonical parity write APIs, with explicit compatibility aliases for older SignifyPy callers.
   * - Schema requests
     - ``client.schemas()``, ``client.oobis()``
     - ``signify.app.schemas``, ``signify.app.coring``
     - Maintained as both a dedicated schema read wrapper and an OOBI-backed schema resolution workflow.
   * - Challenge requests
     - ``client.challenges()``
     - ``signify.app.challenging``
     - Maintained for TS-style challenge generation, response, verification, and acceptance tracking.
   * - Contact requests
     - ``client.contacts()``
     - ``signify.app.contacting``
     - Maintained for TS-style contact list/get/add/update/delete, with one explicit legacy range-list path.
   * - Credential requests
     - ``client.credentials()``, ``client.ipex()``
     - ``signify.app.credentialing``
     - Maintained for credential query/read/delete plus canonical issue/revoke workflows, with IPEX still limited to grant/admit presentation paths.
   * - Delegation requests
     - ``client.delegations()``, ``client.identifiers().create(..., delpre=...)``
     - ``signify.app.delegating``, ``signify.app.aiding``
     - Maintained and covered in all four single-sig and multisig delegation permutations.
   * - Group requests
     - ``client.groups()``
     - ``signify.app.grouping``
     - Maintained for multisig request inspection, request fan-out, and join submission.
   * - Exchange requests
     - ``client.exchanges()``
     - ``signify.app.exchanging`` with ``signify.peer.exchanging`` as compatibility spine
     - Maintained for peer ``exn`` creation, send, fetch, and recipient-specific fan-out.
   * - OOBI and endpoint publication
     - ``client.oobis()``, ``client.endroles()``, ``client.identifiers().addEndRole()``, ``addLocScheme()``
     - ``signify.app.coring``, ``signify.app.ending``, ``signify.app.aiding``
     - Maintained and central to witnessed, schema, contact, and multisig discovery flows.
   * - Key state and key event requests
     - ``client.keyStates()``, ``client.keyEvents()``
     - ``signify.app.coring``
     - Maintained read/query surfaces used throughout the integration helper layer.
   * - Operations, notifications, and escrows
     - ``client.operations()``, ``client.notifications()``, ``client.escrows()``
     - ``signify.app.coring``, ``signify.app.notifying``, ``signify.app.escrowing``
     - Maintained support surfaces for polling long-running work and inspecting workflow side effects.

Agent Requests
--------------

Implementation:
``signify.app.clienting.SignifyClient``

Routes:

- ``POST /boot``
- ``GET /agent/{controller}``
- ``PUT /agent/{controller}?type=ixn``
- ``PUT /agent/{controller}``
- ``PUT /salt/{controller}``
- ``DELETE /salt/{controller}``

Responsibilities:

- Boot a cloud agent delegated to the local controller AID.
- Restore controller and agent state during ``connect()``.
- Approve the controller-to-agent delegation on first connect.
- Rotate the controller commitment for managed AIDs.
- Expose the resource accessors used by the rest of the client.

Primary tests:

- ``tests/app/test_clienting.py``
- ``tests/integration/test_provisioning_and_identifiers.py``

Identifier Requests
-------------------

Implementation:
``signify.app.aiding.Identifiers``

Routes:

- ``GET /identifiers``
- ``GET /identifiers/{name}``
- ``POST /identifiers``
- ``PUT /identifiers/{name}``
- ``DELETE /identifiers/{name}``
- ``POST /identifiers/{name}/events``
- ``POST /identifiers/{name}/endroles``
- ``POST /identifiers/{name}/locschemes``
- ``GET /identifiers/{name}/members``

Responsibilities:

- Create identifiers, including delegated and multisig inceptions.
- Rotate and interact with existing identifiers.
- Publish endpoint-role and location-scheme replies for OOBI-backed workflows.
- Return group member state for multisig coordination.
- Sign arbitrary KERI material with the identifier-local keeper.

Primary tests:

- ``tests/app/test_aiding.py``
- ``tests/integration/test_provisioning_and_identifiers.py``
- ``tests/integration/test_multisig.py``
- ``tests/integration/test_multisig_join.py``

Registry Requests
-----------------

Implementation:
``signify.app.credentialing.Registries``

Implemented surface today:

- ``client.registries().list(name)``
- ``client.registries().get(name, registryName)``
- ``client.registries().create(name, registryName, *, noBackers=True, baks=None, toad=0, nonce=None)``
- ``client.registries().createFromEvents(hab, name, registryName, vcp, ixn, sigs)``
- ``client.registries().rename(name, registryName, newName)``
- Compatibility aliases remain callable:

  - ``create(hab, registryName, ...)``
  - ``create_from_events(hab, registryName, vcp, ixn, sigs)``
  - ``rename(hab, registryName, newName)``

Routes:

- ``GET /identifiers/{name}/registries``
- ``GET /identifiers/{name}/registries/{registryName}``
- ``POST /identifiers/{name}/registries``
- ``PUT /identifiers/{name}/registries/{registryName}``

Responsibilities:

- Construct registry inception events and their anchoring interactions.
- Submit registry creation from locally built events.
- Keep SignifyTS workflow behavior while preferring the established
  KERIpy/KERIA/SignifyPy camelCase idiom for the maintained public write
  surface.
- Return ``RegistryResult`` from canonical registry creation paths, with
  synchronous ``op()`` unwrapping for the operation payload.
- Serialize issuance anchor attachments for downstream IPEX grant workflows.
- Rename and re-read registries as part of the maintained read-path contract.

Primary tests:

- ``tests/app/test_credentialing.py``
- ``tests/integration/test_credentials.py``
- ``tests/integration/test_multisig_credentials.py``
- ``tests/integration/test_provisioning_and_identifiers.py``

Schema Requests
---------------

Current reality:

- Schema support is still a maintained workflow because credential issuance and
  validation depend on resolving schema OOBIs into local state before issuing
  or admitting credentials.

Implemented surface today:

- ``client.schemas().get(said)``
- ``client.schemas().list()``
- ``client.oobis().resolve(schema_oobi, alias="schema")``

Routes:

- ``GET /schema``
- ``GET /schema/{said}``
- ``POST /oobis``

Primary tests:

- ``tests/app/test_schemas.py``
- ``tests/integration/test_provisioning_and_identifiers.py``
- ``tests/integration/test_credentials.py``
- ``tests/integration/test_multisig_credentials.py``

Maintainer note:

Document schema support in two layers: dedicated schema reads now exist, and
OOBI-backed schema resolution remains the workflow that makes those reads
useful in real credential flows.

Challenge Requests
------------------

Implementation:
``signify.app.challenging.Challenges``

Routes:

- ``GET /challenges?strength={n}``
- ``POST /challenges_verify/{source}``
- ``PUT /challenges_verify/{source}``
- ``POST /identifiers/{name}/exchanges``

Responsibilities:

- Generate random challenge phrases with explicit entropy strength.
- Send challenge responses through the peer exchange path.
- Ask KERIA to verify a signed response from a source AID.
- Mark accepted challenge responses as handled.

Primary tests:

- ``tests/app/test_challenging.py``
- ``tests/integration/test_challenges.py``

Contact Requests
----------------

Implementation:
``signify.app.contacting.Contacts``

Routes:

- ``GET /contacts``
- ``GET /contacts/{prefix}``
- ``POST /contacts/{prefix}``
- ``PUT /contacts/{prefix}``
- ``DELETE /contacts/{prefix}``

Responsibilities:

- Return resolved contact records already known to the agent.
- Support TS-style query/filter lookup through ``group``, ``filter_field``, and
  ``filter_value``.
- Support local metadata management for already-known remote contacts through
  ``get``, ``add``, ``update``, and ``delete``.
- Preserve one explicit legacy range-list path for older Python callers.

Primary tests:

- ``tests/app/test_contacting.py``
- ``tests/integration/test_provisioning_and_identifiers.py``

Credential Requests
-------------------

Implementation:
``signify.app.credentialing.Credentials`` and
``signify.app.credentialing.Ipex``

Routes:

- ``POST /credentials/query``
- ``GET /credentials/{said}``
- ``DELETE /credentials/{said}``
- ``POST /identifiers/{name}/credentials``
- ``DELETE /identifiers/{name}/credentials/{said}``
- ``POST /identifiers/{name}/ipex/grant``
- ``POST /identifiers/{name}/ipex/admit``

Responsibilities:

- Query locally held credentials.
- Read a credential through one maintained JSON/CESR contract:
  ``get(said, includeCESR=False)``, with ``export(said)`` kept as the CESR
  compatibility alias.
- Delete one locally stored credential copy through ``delete(said)``.
- Construct and submit credential issuance events through canonical
  ``issue(name, registryName, ...)`` while keeping the older
  ``create(hab, registry, ...)`` form as explicit compatibility surface.
- Construct and submit credential revocation events through
  ``revoke(name, said, *, timestamp=None)`` and expose the result through the
  dedicated write-result wrapper.
- Construct and submit IPEX grant and admit exchanges for presentation flows.

Maintainer note:

- Do not treat the credential write normalization as license to fold in
  broader IPEX conversation-surface expansion here.

Primary tests:

- ``tests/app/test_credentialing.py``
- ``tests/integration/test_credentials.py``
- ``tests/integration/test_multisig_credentials.py``
- ``tests/integration/test_provisioning_and_identifiers.py``

Delegation Requests
-------------------

Implementation:
``signify.app.delegating.Delegations`` plus delegated identifier inception in
``signify.app.aiding.Identifiers.create(..., delpre=...)``

Routes:

- ``POST /identifiers``
- ``POST /identifiers/{name}/delegation``

Responsibilities:

- Create delegated identifier inceptions through ``delpre`` on identifier
  creation.
- Approve delegated inception by anchoring the delegate event with a delegator
  interaction event.
- Return the long-running operation that KERIA uses for witness and anchor
  convergence.

Primary tests:

- ``tests/app/test_delegating.py``
- ``tests/integration/test_delegation.py``
- ``tests/app/test_aiding.py`` for delegated inception request shape

Group Requests
--------------

Implementation:
``signify.app.grouping.Groups``

Routes:

- ``GET /multisig/request/{said}``
- ``POST /identifiers/{name}/multisig/request``
- ``POST /identifiers/{name}/multisig/join``

Responsibilities:

- Inspect multisig request state by conversation SAID.
- Fan out signed multisig request messages to other members.
- Submit join approvals for received multisig proposals.

Primary tests:

- ``tests/app/test_grouping.py``
- ``tests/integration/test_multisig.py``
- ``tests/integration/test_multisig_join.py``
- ``tests/integration/test_multisig_interactions.py``

Exchange and IPEX Requests
--------------------------

Implementation:
``signify.app.exchanging.Exchanges`` (backed by
``signify.peer.exchanging.Exchanges``) and
``signify.app.credentialing.Ipex``

Routes:

- ``POST /identifiers/{name}/exchanges``
- ``GET /exchanges/{said}``
- ``POST /identifiers/{name}/ipex/grant``
- ``POST /identifiers/{name}/ipex/admit``

Responsibilities:

- Create recipient-specific peer ``exn`` messages and signatures.
- Send prepared exchange messages to one or more recipients.
- Retrieve exchange messages for inspection during multisig and credential
  workflows.
- Build the IPEX grant/admit messages layered on top of the peer exchange
  transport.

Primary tests:

- ``tests/peer/test_exchanging.py``
- ``tests/app/test_credentialing.py``
- ``tests/integration/test_credentials.py``
- ``tests/integration/test_multisig_credentials.py``

OOBI and Endpoint Publication Requests
--------------------------------------

Implementation:
``signify.app.coring.Oobis``, ``signify.app.ending.EndRoleAuthorizations``,
and endpoint-publication helpers on ``signify.app.aiding.Identifiers``

Routes:

- ``GET /identifiers/{name}/oobis?role={role}``
- ``POST /oobis``
- ``GET /endroles/{aid}``
- ``GET /identifiers/{name}/endroles``
- ``POST /identifiers/{name}/endroles``
- ``POST /identifiers/{name}/locschemes``

Responsibilities:

- Publish endpoint-role and location replies before attempting OOBI-based
  discovery.
- Resolve agent, witness, controller, and schema OOBIs into local state.
- Read end-role authorizations back by identifier name or AID.

Primary tests:

- ``tests/app/test_coring.py``
- ``tests/app/test_ending.py``
- ``tests/app/test_aiding.py``
- ``tests/integration/test_provisioning_and_identifiers.py``

Maintainer note:

The integration harness confirmed a sequencing rule worth keeping visible in
docs: do not query OOBIs until the ``addEndRole`` operation has completed.

Key State and Key Event Requests
--------------------------------

Implementation:
``signify.app.coring.KeyStates`` and ``signify.app.coring.KeyEvents``

Routes:

- ``GET /states?pre={pre}``
- ``POST /queries``
- ``GET /events?pre={pre}``

Responsibilities:

- Read one or more current key states.
- Submit state queries with optional sequence-number or anchor hints.
- Read key events for already-known prefixes.

Primary tests:

- ``tests/app/test_coring.py``
- ``tests/integration/test_provisioning_and_identifiers.py``

Operations, Notifications, and Escrows
--------------------------------------

Implementation:
``signify.app.coring.Operations``, ``signify.app.notifying.Notifications``,
and ``signify.app.escrowing.Escrows``

Routes:

- ``GET /operations``
- ``GET /operations/{name}``
- ``DELETE /operations/{name}``
- ``GET /notifications``
- ``PUT /notifications/{nid}``
- ``DELETE /notifications/{nid}``
- ``GET /escrows/rpy``

Responsibilities:

- Fetch, list, poll, and remove long-running operations started by identifier,
  registry, delegation, and IPEX workflows.
- Use ``Operations.wait(...)`` as the local convenience poller for completion,
  dependency waits, timeout control, and optional caller-controlled
  cancellation hooks.
- Inspect and acknowledge notification side effects created by peer and
  multisig messaging. ``Notifications.mark()`` is the primary TS-style name;
  ``markAsRead()`` remains a compatibility alias.
- Read escrowed reply state for troubleshooting and support tooling.
  ``Escrows.listReply()`` is the primary TS-style name;
  ``getEscrowReply()`` remains a compatibility alias.

Primary tests:

- ``tests/app/test_coring.py``
- ``tests/app/test_notifying.py``
- ``tests/app/test_escrowing.py``
- ``tests/integration/helpers.py`` for the main polling and notification usage

Documentation Boundaries
------------------------

This guide documents the request families that are real in the current Python
client. It should not be used to imply parity that does not exist.

Notable current gaps:

- no dedicated ``config()`` resource wrapper yet

When those surfaces are added, update this guide and the API reference in the
same change so the published docs remain aligned with the actual maintained
feature set.

That same rule applies at code level: keep module, class, and method docstrings
aligned with the maintained request surface so the autodoc pages remain useful
instead of becoming another stale layer.
