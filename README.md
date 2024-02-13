# Signifypy
Signify implementation in Python

[![Tests](https://github.com/WebOfTrust/signifypy/actions/workflows/test.yaml/badge.svg?branch=development)](https://github.com/WebOfTrust/signifypy/actions/workflows/test.yaml)
[![codecov](https://codecov.io/gh/WebOfTrust/signifypy/graph/badge.svg?token=E9VS4PNKTD)](https://codecov.io/gh/WebOfTrust/signifypy)
[![Documentation Status](https://readthedocs.org/projects/signifypy/badge/?version=latest)](https://signifypy.readthedocs.io/en/latest/?badge=latest)

## Signify - KERI Signing at the Edge

Of the five functions in a KERI agent, 

1. Key generation
2. Encrypted key storage
3. Event generation
4. Event signing
5. Event Validation

Signifypy provides key generation and event signing in a library to provide "signing at the edge".
It accomplishes this by using [libsodium](https://doc.libsodium.org/) to generate ed25519 key pairs for signing and x25519 key pairs for encrypting the
private keys, next public keys, and salts used to generate the private keys.  The encrypted private key and salts are then stored on a
remote cloud agent that never has access to the decryption keys.  New key pair sets (current and next) will be generated 
for inception and rotation events with only the public keys and blake3 hash of the next keys made available to the agent.

The communication protocol between a Signify client and [KERI](https://github.com/WebOfTrust/keri) agent will encode all cryptographic primitives as CESR base64
encoded strings for the initial implementation.  Support for binary CESR can be added in the future.

### Development

```
pip install pytest mockito
```

`pytest` to run tests.
