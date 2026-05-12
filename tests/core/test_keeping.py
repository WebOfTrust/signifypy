# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.core.keeping module

Testing authentication
"""

import pytest
from keri.core import coring as core_coring
from mockito import mock, verifyNoUnwantedInteractions, unstub, expect, when


def test_keeping_manager():
    from keri.core.signing import Salter
    mock_salter = mock(spec=Salter, strict=True)

    from signify.core.keeping import Manager
    manager = Manager(salter=mock_salter)

    assert manager.salter == mock_salter
    assert manager.modules == {}

    verifyNoUnwantedInteractions()
    unstub()

def test_keeping_manager_new_salty():
    from keri.core.signing import Salter
    mock_salter = mock(spec=Salter, strict=True)

    from signify.core.keeping import Manager
    manager = Manager(salter=mock_salter)

    from signify.core import keeping
    mock_keeper = mock(spec=keeping.SaltyKeeper, strict=True)
    from mockito import kwargs
    expect(keeping, times=1).SaltyKeeper(salter=mock_salter, pidx=0, **kwargs).thenReturn(mock_keeper)
    actual = manager.new('salty', 0)

    assert actual is mock_keeper

    verifyNoUnwantedInteractions()
    unstub()

def test_keeping_manager_new_randy():
    from keri.core.signing import Salter
    mock_salter = mock(spec=Salter, strict=True)

    from signify.core.keeping import Manager
    manager = Manager(salter=mock_salter)

    from signify.core import keeping
    mock_keeper = mock(spec=keeping.RandyKeeper, strict=True)
    from mockito import kwargs
    expect(keeping, times=1).RandyKeeper(salter=mock_salter, **kwargs).thenReturn(mock_keeper)
    actual = manager.new('randy', 0)

    assert actual is mock_keeper

    verifyNoUnwantedInteractions()
    unstub()

def test_keeping_manager_new_group():
    from keri.core.signing import Salter
    mock_salter = mock(spec=Salter, strict=True)

    from signify.core.keeping import Manager
    manager = Manager(salter=mock_salter)

    from signify.core import keeping
    mock_keeper = mock(spec=keeping.GroupKeeper, strict=True)
    from mockito import kwargs
    expect(keeping, times=1).GroupKeeper(mgr=manager, **kwargs).thenReturn(mock_keeper)
    actual = manager.new('group', 0)

    assert actual is mock_keeper

    verifyNoUnwantedInteractions()
    unstub()

def test_keeping_manager_new_extern():
    from keri.core.signing import Salter
    mock_salter = mock(spec=Salter, strict=True)

    from signify.core.keeping import Manager
    manager = Manager(salter=mock_salter)
    mock_mod = mock({'shim': lambda pidx, **eargs: 'foo'}, strict=True)
    mock_modules = {'et': mock_mod}
    manager.modules = mock_modules # type: ignore

    mock_shim = mock(strict=True)
    expect(mock_mod, times=1).shim(pidx=0, **{'ex': 'tern'}).thenReturn(mock_shim)

    actual = manager.new('extern', 0, extern_type='et', extern={'ex': 'tern'})

    assert actual == mock_shim

    verifyNoUnwantedInteractions()
    unstub()

def test_keeping_manager_new_extern_unknown():
    from keri.core.signing import Salter
    mock_salter = mock(spec=Salter, strict=True)

    from signify.core.keeping import Manager
    manager = Manager(salter=mock_salter)
    mock_modules = {'et': {}}
    manager.modules = mock_modules # type: ignore

    from keri.kering import ConfigurationError
    with pytest.raises(ConfigurationError, match='unsupported external module type unknown'):
        manager.new('extern', 0, extern_type='unknown', extern={'ex': 'tern'})


    verifyNoUnwantedInteractions()
    unstub()

def test_keeping_manager_get_salty():
    from keri.core.signing import Salter
    mock_salter = mock(spec=Salter, strict=True)

    from signify.core.keeping import Manager
    manager = Manager(salter=mock_salter)

    from keri.core.coring import Prefixer
    mock_prefixer = mock(spec=Prefixer, strict=True)

    from keri.core import coring
    expect(coring, times=1).Prefixer(qb64='aid1 prefix').thenReturn(mock_prefixer)

    from signify.core import keeping
    mock_keeper = mock(spec=keeping.SaltyKeeper, strict=True)
    expect(keeping, times=1).SaltyKeeper(salter=mock_salter, pidx=0, dcode='E').thenReturn(mock_keeper)

    actual = manager.get({'prefix': 'aid1 prefix', 'salty': {'dcode': 'E', 'pidx': 0}})

    assert actual is mock_keeper

    verifyNoUnwantedInteractions()
    unstub()

def test_keeping_manager_get_salty_pidx():
    from keri.core.signing import Salter
    mock_salter = mock(spec=Salter, strict=True)

    from signify.core.keeping import Manager
    manager = Manager(salter=mock_salter)

    from keri.core.coring import Prefixer
    mock_prefixer = mock(spec=Prefixer, strict=True)

    from keri.core import coring
    expect(coring, times=1).Prefixer(qb64='aid1 prefix').thenReturn(mock_prefixer)

    from keri.kering import ConfigurationError
    with pytest.raises(ConfigurationError, match="missing pidx in {'dcode': 'E'}"):
        manager.get({'prefix': 'aid1 prefix', 'salty': {'dcode': 'E'}})

    verifyNoUnwantedInteractions()
    unstub()

def test_keeping_manager_get_randy():
    from keri.core.signing import Salter
    mock_salter = mock(spec=Salter, strict=True)

    from signify.core.keeping import Manager
    manager = Manager(salter=mock_salter)

    from signify.core import keeping
    mock_keeper = mock(spec=keeping.RandyKeeper, strict=True)

    from keri.core.coring import Prefixer
    mock_prefixer = mock({'transferable': True}, spec=Prefixer, strict=True)

    from keri.core import coring
    expect(coring, times=1).Prefixer(qb64='aid1 prefix').thenReturn(mock_prefixer)

    expect(keeping, times=1).RandyKeeper(salter=mock_salter, transferable=True, dcode='E').thenReturn(mock_keeper)
    actual = manager.get({'prefix': 'aid1 prefix', 'randy': {'dcode': 'E'}})

    assert actual is mock_keeper

    verifyNoUnwantedInteractions()
    unstub()

def test_keeping_manager_get_group():
    from keri.core.signing import Salter
    mock_salter = mock(spec=Salter, strict=True)

    from signify.core.keeping import Manager
    manager = Manager(salter=mock_salter)

    from signify.core import keeping
    mock_keeper = mock(spec=keeping.GroupKeeper, strict=True)

    from keri.core.coring import Prefixer
    mock_prefixer = mock(spec=Prefixer, strict=True)

    from keri.core import coring
    expect(coring, times=1).Prefixer(qb64='aid1 prefix').thenReturn(mock_prefixer)

    expect(
        keeping,
        times=1,
    ).GroupKeeper(
        mgr=manager,
        keys=['key1'],
        ndigs=['dig1'],
    ).thenReturn(mock_keeper)
    actual = manager.get({
        'prefix': 'aid1 prefix',
        'group': {'keys': ['key1'], 'ndigs': ['dig1']},
    })

    assert actual is mock_keeper

    verifyNoUnwantedInteractions()
    unstub()

def test_keeping_manager_get_group_uses_group_ndigs_for_prior_next_snapshot():
    from keri.core.signing import Salter
    mock_salter = mock(spec=Salter, strict=True)

    from signify.core.keeping import Manager
    manager = Manager(salter=mock_salter)

    from signify.core import keeping
    mock_keeper = mock(spec=keeping.GroupKeeper, strict=True)

    from keri.core.coring import Prefixer
    mock_prefixer = mock(spec=Prefixer, strict=True)

    from keri.core import coring
    expect(coring, times=1).Prefixer(qb64='aid1 prefix').thenReturn(mock_prefixer)

    expect(
        keeping,
        times=1,
    ).GroupKeeper(
        mgr=manager,
        keys=['key1'],
        ndigs=['persisted dig'],
    ).thenReturn(mock_keeper)
    actual = manager.get({
        'prefix': 'aid1 prefix',
        'state': {'n': ['state dig']},
        'group': {'keys': ['key1'], 'ndigs': ['persisted dig']},
    })

    assert actual is mock_keeper

    verifyNoUnwantedInteractions()
    unstub()

def test_salty_keeper():
    # salty keep init mocks
    from keri.core.signing import Salter, Signer
    mock_salter = mock(spec=Salter, strict=True)
    from keri.core.coring import Verfer
    mock_verfer = mock({'qb64': 'verfer qb64'}, spec=Verfer, strict=True)
    mock_signer = mock({'verfer': mock_verfer ,'qb64': 'signer qb64'}, spec=Signer, strict=True)
    expect(mock_salter, times=1).signer(transferable=False).thenReturn(mock_signer)

    from keri.core.signing import Encrypter
    mock_encrypter = mock(spec=Encrypter, strict=True)

    from keri.core import signing
    expect(signing, times=1).Encrypter(verkey='verfer qb64').thenReturn(mock_encrypter)

    from keri.core.signing import Decrypter
    mock_decrypter= mock(spec=Decrypter, strict=True)

    from keri.core import signing
    expect(signing, times=1).Decrypter(seed='signer qb64').thenReturn(mock_decrypter)

    from keri.app.keeping import SaltyCreator
    mock_creator = mock({'salt': 'creator salt'}, spec=SaltyCreator, strict=True)
    from keri.app import keeping
    expect(keeping, times=1).SaltyCreator(stem='signify:aid', tier='low').thenReturn(mock_creator)

    from keri.core.signing import Cipher
    mock_cipher = mock({'qb64': 'cipher qb64'}, spec=Cipher, strict=True)
    expect(mock_encrypter, times=1).encrypt(
        ser='creator salt',
        code=core_coring.MtrDex.X25519_Cipher_Salt).thenReturn(mock_cipher)

    # test
    from signify.core.keeping import SaltyKeeper
    sk = SaltyKeeper(mock_salter, pidx=0)

    assert sk.params() == {'sxlt': 'cipher qb64', 'pidx': 0, 'kidx': 0, 'stem': 'signify:aid', 'tier': 'low', 'icodes': ['A'], 'ncodes': ['A'], 'dcode': 'E', 'transferable': False}

    from keri.app.keeping import Algos
    assert sk.algo == Algos.salty

    verifyNoUnwantedInteractions()
    unstub()

def test_salty_keeper_bran():
    # salty keep init mocks
    from keri.core.signing import Salter, Signer
    mock_salter = mock(spec=Salter, strict=True)
    from keri.core.coring import Verfer
    mock_verfer = mock({'qb64': 'verfer qb64'}, spec=Verfer, strict=True)
    mock_signer = mock({'verfer': mock_verfer ,'qb64': 'signer qb64'}, spec=Signer, strict=True)
    expect(mock_salter, times=1).signer(transferable=False).thenReturn(mock_signer)

    from keri.core.signing import Encrypter
    mock_encrypter = mock(spec=Encrypter, strict=True)
    
    from keri.core import signing
    expect(signing, times=1).Encrypter(verkey='verfer qb64').thenReturn(mock_encrypter)

    from keri.core.signing import Decrypter
    mock_decrypter= mock(spec=Decrypter, strict=True)
    
    from keri.core import signing
    expect(signing, times=1).Decrypter(seed='signer qb64').thenReturn(mock_decrypter)

    from keri.app.keeping import SaltyCreator
    mock_creator = mock({'salt': 'creator salt'}, spec=SaltyCreator, strict=True)

    from keri.app import keeping
    expect(keeping, times=1).SaltyCreator(salt='0AA0123456789abcdefghijk', stem='signify:aid', tier='low').thenReturn(mock_creator)

    from keri.core.signing import Cipher
    mock_cipher = mock({'qb64': 'cipher qb64'}, spec=Cipher, strict=True)
    expect(mock_encrypter, times=1).encrypt(
        ser='creator salt',
        code=core_coring.MtrDex.X25519_Cipher_Salt).thenReturn(mock_cipher)

    # test
    from signify.core.keeping import SaltyKeeper
    sk = SaltyKeeper(mock_salter, pidx=0, bran='0123456789abcdefghijk')

    assert sk.params() == {'sxlt': 'cipher qb64', 'pidx': 0, 'kidx': 0, 'stem': 'signify:aid', 'tier': 'low', 'icodes': ['A'], 'ncodes': ['A'], 'dcode': 'E', 'transferable': False}

    verifyNoUnwantedInteractions()
    unstub()


def test_salty_keeper_bran_sxlt_uses_x25519_cipher_salt():
    from keri.core import signing
    from signify.core.keeping import SaltyKeeper

    salter = signing.Salter(raw=b'0123456789abcdef')
    sk = SaltyKeeper(salter, pidx=0, bran='0123456789abcdefghijk')

    cipher = signing.Cipher(qb64=sk.params()["sxlt"])
    assert cipher.code == core_coring.MtrDex.X25519_Cipher_Salt


def test_salty_keeper_accepts_stream_cipher_salt():
    from keri.core import signing
    from signify.core.keeping import SaltyKeeper

    salter = signing.Salter(raw=b'0123456789abcdef')
    signer = salter.signer(transferable=False)
    encrypter = signing.Encrypter(verkey=signer.verfer.qb64)
    aid_salter = signing.Salter(raw=b'fedcba9876543210')
    sxlt = encrypter.encrypt(ser=aid_salter.qb64).qb64  # an unspecified code defaults to 4C variable size cipher

    assert signing.Cipher(qb64=sxlt).code == core_coring.MtrDex.X25519_Cipher_L0

    sk = SaltyKeeper(salter, pidx=0, sxlt=sxlt)

    assert sk.params()["sxlt"] == sxlt
    assert sk.creator.salt == aid_salter.qb64


def test_salty_keeper_sxlt():
    # salty keep init mocks
    from keri.core.signing import Salter, Signer
    mock_salter = mock({'qb64': 'salter qb64'}, spec=Salter, strict=True)
    from keri.core.coring import Verfer
    mock_verfer = mock({'qb64': 'verfer qb64'}, spec=Verfer, strict=True)
    mock_signer = mock({'verfer': mock_verfer ,'qb64': 'signer qb64'}, spec=Signer, strict=True)
    expect(mock_salter, times=1).signer(transferable=False).thenReturn(mock_signer)

    from keri.core.signing import Encrypter
    mock_encrypter = mock(spec=Encrypter, strict=True)
    
    from keri.core import signing
    expect(signing, times=1).Encrypter(verkey='verfer qb64').thenReturn(mock_encrypter)

    from keri.core.signing import Decrypter
    mock_decrypter= mock(spec=Decrypter, strict=True)
    
    from keri.core import signing
    expect(signing, times=1).Decrypter(seed='signer qb64').thenReturn(mock_decrypter)

    from keri.core.signing import Cipher
    mock_cipher = mock({'qb64': 'cipher qb64'}, spec=Cipher, strict=True)

    from keri.core import signing
    expect(signing, times=1).Cipher(qb64='0123456789abcdefghijk').thenReturn(mock_cipher)

    expect(mock_decrypter, times=1).decrypt(cipher=mock_cipher).thenReturn(mock_salter)

    from keri.app.keeping import SaltyCreator
    mock_creator = mock({'salt': 'creator salt'}, spec=SaltyCreator, strict=True)

    from keri.app import keeping
    expect(keeping, times=1).SaltyCreator('salter qb64', stem='signify:aid', tier='low').thenReturn(mock_creator)

    # test
    from signify.core.keeping import SaltyKeeper
    sk = SaltyKeeper(mock_salter, pidx=0, sxlt='0123456789abcdefghijk')

    assert sk.params() == {'sxlt': '0123456789abcdefghijk', 'pidx': 0, 'kidx': 0, 'stem': 'signify:aid', 'tier': 'low', 'icodes': ['A'], 'ncodes': ['A'], 'dcode': 'E', 'transferable': False}

    verifyNoUnwantedInteractions()
    unstub()

def test_salty_keeper_incept():
    # salty keep init mocks
    from keri.core.signing import Salter, Signer
    mock_salter = mock(spec=Salter, strict=True)
    from keri.core.coring import Verfer
    mock_verfer = mock({'qb64': 'verfer qb64'}, spec=Verfer, strict=True)
    mock_signer = mock({'verfer': mock_verfer ,'qb64': 'signer qb64'}, spec=Signer, strict=True)
    expect(mock_salter, times=1).signer(transferable=False).thenReturn(mock_signer)

    from keri.core.signing import Encrypter
    mock_encrypter = mock(spec=Encrypter, strict=True)
    
    from keri.core import signing
    expect(signing, times=1).Encrypter(verkey='verfer qb64').thenReturn(mock_encrypter)

    from keri.core.signing import Decrypter
    mock_decrypter= mock(spec=Decrypter, strict=True)
    
    from keri.core import signing
    expect(signing, times=1).Decrypter(seed='signer qb64').thenReturn(mock_decrypter)

    from keri.app.keeping import SaltyCreator
    mock_creator = mock({'salt': 'creator salt'}, spec=SaltyCreator, strict=True)

    from keri.app import keeping
    expect(keeping, times=1).SaltyCreator(stem='signify:aid', tier='low').thenReturn(mock_creator)

    from keri.core.signing import Cipher
    mock_cipher = mock({'qb64': 'cipher qb64'}, spec=Cipher, strict=True)
    expect(mock_encrypter, times=1).encrypt(
        ser='creator salt',
        code=core_coring.MtrDex.X25519_Cipher_Salt).thenReturn(mock_cipher)

    # incept mocks
    mock_incept_verfer = mock({'qb64': 'incept verfer qb64'}, spec=Verfer, strict=True)
    mock_incept_signer = mock({'verfer': mock_incept_verfer ,'qb64': 'incept signer qb64'}, spec=Signer, strict=True)
    expect(mock_creator, times=1).create(codes=['A'], pidx=0, kidx=0, transferable=True).thenReturn([mock_incept_signer])

    mock_incept_nverfer = mock({'qb64b': b'incept nverfer qb64b'}, spec=Verfer, strict=True)
    mock_incept_nsigner = mock({'verfer': mock_incept_nverfer ,'qb64': 'incept signer qb64'}, spec=Signer, strict=True)
    expect(mock_creator, times=1).create(codes=['A'], pidx=0, kidx=1, transferable=True).thenReturn([mock_incept_nsigner])

    from keri.core.coring import Diger
    from keri.core import coring
    mock_diger = mock({'qb64': 'diger qb64'}, spec=Diger, strict=True)
    expect(coring, times=1).Diger(ser=b'incept nverfer qb64b', code='E').thenReturn(mock_diger)

    # test
    from signify.core.keeping import SaltyKeeper
    sk = SaltyKeeper(mock_salter, pidx=0)
    verfers, digers = sk.incept(transferable=True)

    assert verfers == ['incept verfer qb64']
    assert digers == ['diger qb64']

    verifyNoUnwantedInteractions()
    unstub()

def test_salty_keeper_rotate():
    # salty keep init mocks
    from keri.core.signing import Salter, Signer
    mock_salter = mock(spec=Salter, strict=True)
    from keri.core.coring import Verfer
    mock_verfer = mock({'qb64': 'verfer qb64'}, spec=Verfer, strict=True)
    mock_signer = mock({'verfer': mock_verfer ,'qb64': 'signer qb64'}, spec=Signer, strict=True)
    expect(mock_salter, times=1).signer(transferable=False).thenReturn(mock_signer)

    from keri.core.signing import Encrypter
    mock_encrypter = mock(spec=Encrypter, strict=True)
    
    from keri.core import signing
    expect(signing, times=1).Encrypter(verkey='verfer qb64').thenReturn(mock_encrypter)

    from keri.core.signing import Decrypter
    mock_decrypter= mock(spec=Decrypter, strict=True)
    
    from keri.core import signing
    expect(signing, times=1).Decrypter(seed='signer qb64').thenReturn(mock_decrypter)

    from keri.app.keeping import SaltyCreator
    mock_creator = mock({'salt': 'creator salt'}, spec=SaltyCreator, strict=True)

    from keri.app import keeping
    expect(keeping, times=1).SaltyCreator(stem='signify:aid', tier='low').thenReturn(mock_creator)

    from keri.core.signing import Cipher
    mock_cipher = mock({'qb64': 'cipher qb64'}, spec=Cipher, strict=True)
    expect(mock_encrypter, times=1).encrypt(
        ser='creator salt',
        code=core_coring.MtrDex.X25519_Cipher_Salt).thenReturn(mock_cipher)

    # rotate mocks
    mock_rotate_verfer = mock({'qb64': 'rotate verfer qb64'}, spec=Verfer, strict=True)
    mock_rotate_signer = mock({'verfer': mock_rotate_verfer ,'qb64': 'rotate signer qb64'}, spec=Signer, strict=True)
    expect(mock_creator, times=1).create(codes=['A'], pidx=0, kidx=1, transferable=False).thenReturn([mock_rotate_signer])

    mock_rotate_nverfer = mock({'qb64b': b'rotate nverfer qb64b'}, spec=Verfer, strict=True)
    mock_rotate_nsigner = mock({'verfer': mock_rotate_nverfer ,'qb64': 'rotate signer qb64'}, spec=Signer, strict=True)
    expect(mock_creator, times=1).create(codes=['A'], pidx=0, kidx=2, transferable=True).thenReturn([mock_rotate_nsigner])

    from keri.core.coring import Diger
    from keri.core import coring
    mock_diger = mock({'qb64': 'rotate diger qb64'}, spec=Diger, strict=True)
    expect(coring, times=1).Diger(ser=b'rotate nverfer qb64b', code='E').thenReturn(mock_diger)

    # test
    from signify.core.keeping import SaltyKeeper
    sk = SaltyKeeper(mock_salter, pidx=0)
    assert sk.kidx == 0
    verfers, digers = sk.rotate(ncodes=['A'], transferable=True)

    assert sk.kidx == 1
    assert verfers == ['rotate verfer qb64']
    assert digers == ['rotate diger qb64']

    verifyNoUnwantedInteractions()
    unstub()

def test_salty_keeper_sign():
    # salty keep init mocks
    from keri.core.signing import Salter, Signer
    mock_salter = mock(spec=Salter, strict=True)
    from keri.core.coring import Verfer
    mock_verfer = mock({'qb64': 'verfer qb64'}, spec=Verfer, strict=True)
    mock_signer = mock({'verfer': mock_verfer ,'qb64': 'signer qb64'}, spec=Signer, strict=True)
    expect(mock_salter, times=1).signer(transferable=False).thenReturn(mock_signer)

    from keri.core.signing import Encrypter
    mock_encrypter = mock(spec=Encrypter, strict=True)
    
    from keri.core import signing
    expect(signing, times=1).Encrypter(verkey='verfer qb64').thenReturn(mock_encrypter)

    from keri.core.signing import Decrypter
    mock_decrypter= mock(spec=Decrypter, strict=True)
    
    from keri.core import signing
    expect(signing, times=1).Decrypter(seed='signer qb64').thenReturn(mock_decrypter)

    from keri.app.keeping import SaltyCreator
    mock_creator = mock({'salt': 'creator salt'}, spec=SaltyCreator, strict=True)

    from keri.app import keeping
    expect(keeping, times=1).SaltyCreator(stem='signify:aid', tier='low').thenReturn(mock_creator)

    from keri.core.signing import Cipher
    mock_cipher = mock({'qb64': 'cipher qb64'}, spec=Cipher, strict=True)
    expect(mock_encrypter, times=1).encrypt(
        ser='creator salt',
        code=core_coring.MtrDex.X25519_Cipher_Salt).thenReturn(mock_cipher)

    # sign mock
    expect(mock_creator, times=1).create(codes=['A'], pidx=0, kidx=0, transferable=False).thenReturn([mock_signer])

    # test
    from signify.core.keeping import SaltyKeeper
    sk = SaltyKeeper(mock_salter, pidx=0)
    
    expect(sk).__sign__( b'my ser', signers=[mock_signer], indexed=True, indices=None, ondices=None).thenReturn(['a signature'])

    ser = b'my ser'
    sigs = sk.sign(ser)

    assert sigs == ['a signature']

    verifyNoUnwantedInteractions()
    unstub()

def test_randy_keeper():
    from keri.core.signing import Salter, Signer
    mock_salter = mock(spec=Salter, strict=True)
    from keri.core.coring import Verfer
    mock_verfer = mock({'qb64': 'verfer qb64'}, spec=Verfer, strict=True)
    mock_signer = mock({'verfer': mock_verfer ,'qb64': 'signer qb64'}, spec=Signer, strict=True)
    expect(mock_salter, times=1).signer(transferable=False).thenReturn(mock_signer)

    from keri.core.signing import Encrypter
    mock_encrypter = mock(spec=Encrypter, strict=True)
    
    from keri.core import signing
    expect(signing, times=1).Encrypter(verkey='verfer qb64').thenReturn(mock_encrypter)

    from keri.core.signing import Decrypter
    mock_decrypter= mock(spec=Decrypter, strict=True)
    
    from keri.core import signing
    expect(signing, times=1).Decrypter(seed='signer qb64').thenReturn(mock_decrypter)

    from signify.core.keeping import RandyKeeper
    rk = RandyKeeper(mock_salter)

    assert rk.icodes == ["A"]
    assert rk.ncodes == ["A"]

    from keri.app.keeping import RandyCreator
    assert type(rk.creator) is RandyCreator
    
    from keri.app.keeping import Algos
    assert rk.algo == Algos.randy

    verifyNoUnwantedInteractions()
    unstub()
    
def test_randy_keeper_params():
    from keri.core.signing import Salter, Signer
    mock_salter = mock(spec=Salter, strict=True)
    from keri.core.coring import Verfer
    mock_verfer = mock({'qb64': 'verfer qb64'}, spec=Verfer, strict=True)
    mock_signer = mock({'verfer': mock_verfer ,'qb64': 'signer qb64'}, spec=Signer, strict=True)
    expect(mock_salter, times=1).signer(transferable=False).thenReturn(mock_signer)

    from keri.core.signing import Encrypter
    mock_encrypter = mock(spec=Encrypter, strict=True)
    
    from keri.core import signing
    expect(signing, times=1).Encrypter(verkey='verfer qb64').thenReturn(mock_encrypter)

    from keri.core.signing import Decrypter
    mock_decrypter= mock(spec=Decrypter, strict=True)
    
    from keri.core import signing
    expect(signing, times=1).Decrypter(seed='signer qb64').thenReturn(mock_decrypter)

    from signify.core.keeping import RandyKeeper
    rk = RandyKeeper(mock_salter, transferable=True, nxts=['nxt1', 'nxt2'], prxs=['prx1', 'prx2'])

    actual = rk.params()

    assert actual == {'nxts': ['nxt1', 'nxt2',], 'prxs': ['prx1', 'prx2'], 'transferable': True}

    verifyNoUnwantedInteractions()
    unstub()

def test_randy_keeper_incept():
    from keri.core.signing import Salter, Signer
    mock_salter = mock(spec=Salter, strict=True)
    from keri.core.coring import Verfer
    mock_verfer = mock({'qb64': 'verfer qb64'}, spec=Verfer, strict=True)
    mock_signer = mock({'verfer': mock_verfer ,'qb64': 'signer qb64'}, spec=Signer, strict=True)
    expect(mock_salter, times=1).signer(transferable=False).thenReturn(mock_signer)

    from keri.core.signing import Encrypter
    mock_encrypter = mock(spec=Encrypter, strict=True)
    
    from keri.core import signing
    expect(signing, times=1).Encrypter(verkey='verfer qb64').thenReturn(mock_encrypter)

    from keri.core.signing import Decrypter
    mock_decrypter= mock(spec=Decrypter, strict=True)
    
    from keri.core import signing
    expect(signing, times=1).Decrypter(seed='signer qb64').thenReturn(mock_decrypter)

    # start incept mocks
    from keri.app.keeping import RandyCreator
    mock_creator = mock(spec=RandyCreator, strict=True)

    # verfers mocks
    from keri.core.coring import Verfer
    from keri.core.signing import Signer
    mock_verfer = mock({'qb64': 'signer verfer qb64'}, spec=Verfer, strict=True)
    mock_signer = mock({'verfer': mock_verfer}, spec=Signer, strict=True)
    expect(mock_creator, times=1).create(codes=['A'], transferable=True).thenReturn([mock_signer])

    from keri.core.signing import Cipher
    mock_cipher = mock({'qb64': 'cipher qb64'}, spec=Cipher, strict=True)
    expect(mock_encrypter, times=1).encrypt(prim=mock_signer).thenReturn(mock_cipher)

    # digers mocks
    mock_verfer = mock({'qb64b': b'signer verfer qb64b'}, spec=Verfer, strict=True)
    mock_nsigner = mock({'verfer': mock_verfer}, spec=Signer, strict=True)
    expect(mock_creator, times=1).create(codes=['B'], transferable=True).thenReturn([mock_nsigner])
    expect(mock_encrypter, times=1).encrypt(prim=mock_nsigner).thenReturn(mock_cipher)

    from keri.core.coring import Diger
    from keri.core import coring
    mock_diger = mock({'qb64': 'diger qb64'}, spec=Diger, strict=True)
    expect(coring, times=1).Diger(ser=b'signer verfer qb64b', code='E').thenReturn(mock_diger)
    
    # test
    from signify.core.keeping import RandyKeeper
    rk = RandyKeeper(mock_salter, icodes=['A'], ncodes=['B'])    
    rk.creator = mock_creator # type: ignore

    verfers, digers = rk.incept(transferable=True)

    assert verfers == ['signer verfer qb64']
    assert digers == ['diger qb64']

    verifyNoUnwantedInteractions()
    unstub()

def test_randy_keeper_rotate():
    from keri.core.signing import Salter, Signer
    mock_salter = mock({'qb64': 'salter qb64'}, spec=Salter, strict=True)
    from keri.core.coring import Verfer
    mock_verfer = mock({'qb64': 'verfer qb64'}, spec=Verfer, strict=True)
    mock_signer = mock({'verfer': mock_verfer ,'qb64': 'signer qb64'}, spec=Signer, strict=True)
    expect(mock_salter, times=1).signer(transferable=False).thenReturn(mock_signer)

    from keri.core.signing import Encrypter
    mock_encrypter = mock(spec=Encrypter, strict=True)
    
    from keri.core import signing
    expect(signing, times=1).Encrypter(verkey='verfer qb64').thenReturn(mock_encrypter)

    from keri.core.signing import Decrypter
    mock_decrypter= mock(spec=Decrypter, strict=True)
    
    from keri.core import signing
    expect(signing, times=1).Decrypter(seed='signer qb64').thenReturn(mock_decrypter)

    # start rotate mocks
    from keri.app.keeping import RandyCreator
    mock_creator = mock(spec=RandyCreator, strict=True)

    from keri.core import coring
    from keri.core.signing import Cipher
    mock_nxt_cipher = mock({'qb64': 'cipher qb64'}, spec=Cipher, strict=True)
    when(mock_nxt_cipher).qb64.add_answer('nxt qb64')
    expect(signing, times=1).Cipher(qb64='nxt qb64').thenReturn(mock_nxt_cipher)

    # verfers mocks
    from keri.core.coring import Verfer
    from keri.core.signing import Signer
    mock_verfer = mock({'qb64': 'signer verfer qb64'}, spec=Verfer, strict=True)
    mock_signer = mock({'verfer': mock_verfer, 'qb64': 'signer qb64'}, spec=Signer, strict=True)
    expect(mock_decrypter, times=1).decrypt(cipher=mock_nxt_cipher, transferable=True).thenReturn(mock_signer)

    # digers mocks
    mock_verfer = mock({'qb64b': b'signer verfer qb64b'}, spec=Verfer, strict=True)
    mock_nsigner = mock({'verfer': mock_verfer, 'qb64': 'nsigner qb64'}, spec=Signer, strict=True)
    expect(mock_creator, times=1).create(codes=['A'], transferable=True).thenReturn([mock_nsigner])

    from keri.core.signing import Cipher
    mock_cipher = mock({'qb64': 'cipher qb64'}, spec=Cipher, strict=True)
    expect(mock_encrypter, times=1).encrypt(prim=mock_nsigner).thenReturn(mock_cipher)

    from keri.core.coring import Diger
    mock_diger = mock({'qb64': 'diger qb64'}, spec=Diger, strict=True)
    expect(coring, times=1).Diger(ser=b'signer verfer qb64b', code='E').thenReturn(mock_diger)

    # test
    from signify.core.keeping import RandyKeeper
    rk = RandyKeeper(mock_salter, ncodes=['A'], nxts=['nxt qb64'])    
    rk.creator = mock_creator # type: ignore

    verfers, digers = rk.rotate(['A'], transferable=True)

    assert verfers == ['signer verfer qb64']
    assert digers == ['diger qb64']
    assert rk.prxs == ['nxt qb64']
    assert rk.nxts == ['cipher qb64']

    verifyNoUnwantedInteractions()
    unstub()

def test_randy_keeper_sign():
    from keri.core.signing import Salter, Signer
    mock_salter = mock(spec=Salter, strict=True)
    from keri.core.coring import Verfer
    mock_verfer = mock({'qb64': 'verfer qb64'}, spec=Verfer, strict=True)
    mock_signer = mock({'verfer': mock_verfer ,'qb64': 'signer qb64'}, spec=Signer, strict=True)
    expect(mock_salter, times=1).signer(transferable=False).thenReturn(mock_signer)

    from keri.core.signing import Encrypter
    mock_encrypter = mock(spec=Encrypter, strict=True)
    
    from keri.core import signing
    expect(signing, times=1).Encrypter(verkey='verfer qb64').thenReturn(mock_encrypter)

    from keri.core.signing import Decrypter
    mock_decrypter= mock(spec=Decrypter, strict=True)
    
    from keri.core import signing
    expect(signing, times=1).Decrypter(seed='signer qb64').thenReturn(mock_decrypter)

    from keri.core.signing import Cipher
    mock_prx_cipher = mock({'qb64b': b'cipher qb64b'}, spec=Cipher, strict=True)
    expect(signing, times=1).Cipher(qb64='prx qb64').thenReturn(mock_prx_cipher)

    from keri.core.coring import Verfer
    from keri.core.signing import Signer
    mock_verfer = mock({'qb64': 'signer verfer qb64'}, spec=Verfer, strict=True)
    mock_signer = mock({'verfer': mock_verfer}, spec=Signer, strict=True)
    expect(mock_decrypter, times=1).decrypt(cipher=mock_prx_cipher, transferable=False).thenReturn(mock_signer)

    # test
    from signify.core.keeping import RandyKeeper
    rk = RandyKeeper(mock_salter, ncodes=['A'], prxs=['prx qb64'])   

    expect(rk).__sign__( b'my ser', signers=[mock_signer], indexed=True, indices=None, ondices=None).thenReturn(['a signature'])

    ser = b'my ser'
    sigs = rk.sign(ser)

    assert sigs == ['a signature']

    verifyNoUnwantedInteractions()
    unstub()

def test_group_keeper():
    from keri.core.signing import Salter
    mock_salter = mock(spec=Salter, strict=True)

    from signify.core.keeping import Manager
    manager = Manager(salter=mock_salter)

    from signify.core.keeping import GroupKeeper
    gk = GroupKeeper(mgr=manager, mhab={'m': 'hab'}, states=[{'k': ['key 1']}], rstates=[{'n': ['n dig 1']}])

    assert gk.gkeys == ['key 1']
    assert gk.gdigs == ['n dig 1']
    assert gk.gpndigs == ['n dig 1']
    assert gk.mhab == {'m': 'hab'}

    from keri.app.keeping import Algos
    assert gk.algo == Algos.group

def test_group_keeper_incept():
    from keri.core.signing import Salter
    mock_salter = mock(spec=Salter, strict=True)

    from signify.core.keeping import Manager
    manager = Manager(salter=mock_salter)

    from signify.core.keeping import GroupKeeper
    gk = GroupKeeper(mgr=manager, mhab={'m': 'hab'}, states=[{'k': ['key 1']}], rstates=[{'n': ['n dig 1']}])

    gkeys, gdigs = gk.incept()

    assert gkeys == ['key 1']
    assert gdigs == ['n dig 1']

    verifyNoUnwantedInteractions()
    unstub()

def test_group_keeper_rotate():
    from keri.core.signing import Salter
    mock_salter = mock(spec=Salter, strict=True)

    from signify.core.keeping import Manager
    manager = Manager(salter=mock_salter)

    from signify.core.keeping import GroupKeeper
    gk = GroupKeeper(mgr=manager, mhab={'m': 'hab'}, states=[{'k': ['key 1']}], rstates=[{'n': ['n dig 1']}])

    gkeys, gdigs = gk.rotate(states=[{'k': ['key 2']}], rstates=[{'n': ['n dig 2']}])

    assert gkeys == ['key 2']
    assert gdigs == ['n dig 2']

    verifyNoUnwantedInteractions()
    unstub()

def test_group_keeper_sign():
    from keri.core.signing import Salter
    mock_salter = mock(spec=Salter, strict=True)

    from signify.core.keeping import Manager
    mock_manager = Manager(salter=mock_salter)

    from signify.core.keeping import GroupKeeper
    gk = GroupKeeper(
        mgr=mock_manager,
        mhab={'state': {'k': ['key 1'], 'n': ['n dig 1']}},
        keys=['key 1'],
        ndigs=['n dig 1'],
    )

    mock_keeper = mock(strict=True)
    expect(
        mock_manager,
        times=1,
    ).get({'state': {'k': ['key 1'], 'n': ['n dig 1']}}).thenReturn(mock_keeper)

    expect(
        mock_keeper,
        times=1,
    ).sign(b'ser', indexed=True, indices=[0], ondices=[None]).thenReturn(['signatures'])

    # Unknown/non-rotation payloads must be current-only: index comes from the
    # current key list, and ondex stays None instead of being inferred from n.
    actual = gk.sign(b'ser', indexed=True)

    assert actual == ['signatures']

    verifyNoUnwantedInteractions()
    unstub()

def test_group_keeper_sign_inception_is_current_only_when_local_next_digest_is_absent():
    from keri.core import eventing
    from keri.core.coring import Diger
    from keri.core.signing import Salter

    from signify.core.keeping import GroupKeeper

    salter = Salter(raw=b'0123456789abcdef')
    signers = [
        salter.signer(path=f"member-{idx}", transferable=True)
        for idx in range(3)
    ]
    keys = [signer.verfer.qb64 for signer in signers]
    next_digests = [Diger(ser=signer.verfer.qb64b).qb64 for signer in signers]

    states = [
        {'i': f'member-{idx}', 'k': [key], 'n': [ndig]}
        for idx, (key, ndig) in enumerate(zip(keys[:2], next_digests[:2]))
    ]
    rstates = [
        {'i': 'member-1', 'k': [keys[1]], 'n': [next_digests[1]]},
        {'i': 'member-2', 'k': [keys[2]], 'n': [next_digests[2]]},
    ]
    # Regression guard: the local member signs from current keys but is absent
    # from proposed next digests, so icp must not derive an ondex from rstates.
    icp = eventing.incept(
        keys=keys[:2],
        isith='1',
        nsith='1',
        ndigs=[state['n'][0] for state in rstates],
        toad='0',
        wits=[],
    )

    mhab = {'state': {'k': [keys[0]], 'n': [next_digests[0]]}}
    mock_manager = mock(strict=True)
    mock_keeper = mock(strict=True)
    gk = GroupKeeper(
        mgr=mock_manager,
        mhab=mhab,
        states=states,
        rstates=rstates,
    )

    expect(mock_manager, times=1).get(mhab).thenReturn(mock_keeper)
    expect(
        mock_keeper,
        times=1,
    ).sign(icp.raw, indexed=True, indices=[0], ondices=[None]).thenReturn(['signatures'])

    actual = gk.sign(icp.raw, indexed=True)

    assert actual == ['signatures']

    verifyNoUnwantedInteractions()
    unstub()

def test_group_keeper_sign_interaction_is_current_only_without_next_digest_lookup():
    from keri.core import eventing
    from keri.core.coring import Diger
    from keri.core.signing import Salter

    from signify.core.keeping import GroupKeeper

    salter = Salter(raw=b'0123456789abcdef')
    signers = [
        salter.signer(path=f"member-{idx}", transferable=True)
        for idx in range(3)
    ]
    keys = [signer.verfer.qb64 for signer in signers]
    next_digests = [Diger(ser=signer.verfer.qb64b).qb64 for signer in signers]
    # Exclude the local member from proposed next digests to prove ixn signing
    # ignores gdigs/rstates and remains current-only.
    icp = eventing.incept(
        keys=keys[:2],
        isith='1',
        nsith='1',
        ndigs=next_digests[1:],
        toad='0',
        wits=[],
    )
    ixn = eventing.interact(
        pre=icp.pre,
        sn=1,
        data=[],
        dig=icp.said,
    )

    mhab = {'state': {'k': [keys[0]], 'n': [next_digests[0]]}}
    mock_manager = mock(strict=True)
    mock_keeper = mock(strict=True)
    gk = GroupKeeper(
        mgr=mock_manager,
        mhab=mhab,
        keys=keys[:2],
        ndigs=next_digests[1:],
    )

    expect(mock_manager, times=1).get(mhab).thenReturn(mock_keeper)
    expect(
        mock_keeper,
        times=1,
    ).sign(ixn.raw, indexed=True, indices=[0], ondices=[None]).thenReturn(['signatures'])

    actual = gk.sign(ixn.raw, indexed=True)

    assert actual == ['signatures']

    verifyNoUnwantedInteractions()
    unstub()

def test_group_keeper_sign_rotation_uses_prior_next_digests():
    from keri.core import eventing
    from keri.core.signing import Salter
    from keri.core.coring import Diger

    from signify.core.keeping import GroupKeeper

    salter = Salter(raw=b'0123456789abcdef')
    signers = [
        salter.signer(path=f"member-{idx}", transferable=True)
        for idx in range(4)
    ]
    keys = [signer.verfer.qb64 for signer in signers]
    prior_next_digests = [
        Diger(ser=signer.verfer.qb64b).qb64
        for signer in signers[:3]
    ]
    proposed_next_digests = [
        prior_next_digests[0],
        prior_next_digests[1],
        Diger(ser=signers[3].verfer.qb64b).qb64,
    ]
    states = [
        {'k': [key], 'n': [ndig]}
        for key, ndig in zip(keys[:3], prior_next_digests)
    ]
    rstates = [
        {'k': [keys[0]], 'n': [proposed_next_digests[0]]},
        {'k': [keys[1]], 'n': [proposed_next_digests[1]]},
        {'k': [keys[3]], 'n': [proposed_next_digests[2]]},
    ]
    icp = eventing.incept(
        keys=keys[:3],
        isith='3',
        nsith='3',
        ndigs=prior_next_digests,
        toad='0',
        wits=[],
    )
    rot = eventing.rotate(
        pre=icp.pre,
        keys=keys[:3],
        dig=icp.said,
        sn=1,
        isith='3',
        nsith='3',
        ndigs=proposed_next_digests,
        toad='0',
        wits=[],
    )

    mhab = {'state': {'k': [keys[2]], 'n': [prior_next_digests[2]]}}
    mock_manager = mock(strict=True)
    mock_keeper = mock(strict=True)
    gk = GroupKeeper(
        mgr=mock_manager,
        mhab=mhab,
        keys=keys[:3],
        ndigs=prior_next_digests,
    )
    gk.rotate(states=states, rstates=rstates)

    expect(mock_manager, times=1).get(mhab).thenReturn(mock_keeper)
    expect(
        mock_keeper,
        times=1,
    ).sign(rot.raw, indexed=True, indices=[2], ondices=[2]).thenReturn(['signatures'])

    actual = gk.sign(rot.raw, indexed=True, rotated=True)

    assert gk.gdigs == proposed_next_digests
    assert gk.gpndigs == prior_next_digests
    assert actual == ['signatures']

    verifyNoUnwantedInteractions()
    unstub()

def test_group_keeper_sign_rotated_flag_uses_prior_next_without_parsing_event():
    from keri.core.signing import Salter
    from keri.core.coring import Diger

    from signify.core.keeping import GroupKeeper

    salter = Salter(raw=b'0123456789abcdef')
    signers = [
        salter.signer(path=f"member-{idx}", transferable=True)
        for idx in range(4)
    ]
    keys = [signer.verfer.qb64 for signer in signers]
    prior_next_digests = [
        Diger(ser=signer.verfer.qb64b).qb64
        for signer in signers[:3]
    ]
    proposed_next_digests = [
        prior_next_digests[0],
        prior_next_digests[1],
        Diger(ser=signers[3].verfer.qb64b).qb64,
    ]
    states = [
        {'k': [key], 'n': [ndig]}
        for key, ndig in zip(keys[:3], prior_next_digests)
    ]
    rstates = [
        {'k': [keys[0]], 'n': [proposed_next_digests[0]]},
        {'k': [keys[1]], 'n': [proposed_next_digests[1]]},
        {'k': [keys[3]], 'n': [proposed_next_digests[2]]},
    ]

    mhab = {'state': {'k': [keys[2]], 'n': [prior_next_digests[2]]}}
    mock_manager = mock(strict=True)
    mock_keeper = mock(strict=True)
    gk = GroupKeeper(
        mgr=mock_manager,
        mhab=mhab,
        keys=keys[:3],
        ndigs=prior_next_digests,
    )
    gk.rotate(states=states, rstates=rstates)

    expect(mock_manager, times=1).get(mhab).thenReturn(mock_keeper)
    expect(
        mock_keeper,
        times=1,
    ).sign(b'not a keri event', indexed=True, indices=[2], ondices=[2]).thenReturn(['signatures'])

    # Regression guard: rotated=True is the protocol decision. Group signing
    # must not depend on parsing the serialized event to expose prior-next ondex.
    actual = gk.sign(b'not a keri event', indexed=True, rotated=True)

    assert actual == ['signatures']

    verifyNoUnwantedInteractions()
    unstub()

def test_group_keeper_params():
    from keri.core.signing import Salter
    mock_salter = mock(spec=Salter, strict=True)

    from signify.core.keeping import Manager
    mock_manager = Manager(salter=mock_salter)

    from signify.core.keeping import GroupKeeper
    gk = GroupKeeper(
        mgr=mock_manager,
        mhab={'state': {'k': ['key 1'], 'n': ['n dig 1']}},
        keys=['key 1'],
        ndigs=['n dig 1'],
    )

    actual = gk.params()

    assert actual['mhab'] == {'state': {'k': ['key 1'], 'n': ['n dig 1']}}
    assert actual['keys'] == ['key 1']
    assert actual['ndigs'] == ['n dig 1']

    verifyNoUnwantedInteractions()
    unstub()

# really there is no such thing as a ExternKeeper yet, but it provides a default for BaseKeeper
def test_extern_keeper():
    from signify.core.keeping import BaseKeeper
    bk = BaseKeeper()

    from keri.app.keeping import Algos
    assert bk.algo == Algos.extern

def test_base_keeper_sign():
    from signify.core.keeping import BaseKeeper
    
    from keri.core.signing import Signer
    mock_signer = mock(spec=Signer, strict=True)

    from keri.core.coring import Cigar
    mock_cigar = mock({'qb64': 'an unindexed signature'}, spec=Cigar, strict=True)
    expect(mock_signer, times=1).sign(b'ser bytes').thenReturn(mock_cigar)

    actual = BaseKeeper.__sign__(b'ser bytes', [mock_signer])

    assert actual[0] == 'an unindexed signature'

@pytest.mark.parametrize('indexed,indices,ondices', [
    (True, None, None),
    (True, [0], [0]),
])
def test_base_keeper_sign_indexed(indexed, indices, ondices):
    from signify.core.keeping import BaseKeeper
    
    from keri.core.signing import Signer
    mock_signer_one = mock(spec=Signer, strict=True)

    from keri.core import Siger
    mock_cigar = mock({'qb64': 'an indexed signature'}, spec=Siger, strict=True)
    expect(mock_signer_one, times=1).sign(b'ser bytes', index=0, only=False, ondex=0).thenReturn(mock_cigar)

    actual = BaseKeeper.__sign__(b'ser bytes', [mock_signer_one], indexed=indexed, indices=indices, ondices=ondices)

    assert actual[0] == 'an indexed signature'

def test_base_keeper_sign_indexed_current_only_ondex_none():
    from signify.core.keeping import BaseKeeper

    from keri.core.signing import Signer
    mock_signer_one = mock(spec=Signer, strict=True)

    from keri.core import Siger
    mock_cigar = mock({'qb64': 'a current-only indexed signature'}, spec=Siger, strict=True)
    expect(mock_signer_one, times=1).sign(
        b'ser bytes',
        index=0,
        only=True,
        ondex=None,
    ).thenReturn(mock_cigar)

    # BaseKeeper is the low-level path group keepers delegate through; None
    # means "suppress ondex" and must produce a current-only indexed signature.
    actual = BaseKeeper.__sign__(
        b'ser bytes',
        [mock_signer_one],
        indexed=True,
        indices=[0],
        ondices=[None],
    )

    assert actual[0] == 'a current-only indexed signature'

@pytest.mark.parametrize('indexed,indices,ondices,expected', [
    (True, [-1], [0], 'Invalid signing index = -1, not whole number.'),
    (True, [0], [-1], 'Invalid other signing index = -1, not None or not whole number.'),
])
def test_base_keeper_sign_indexed_boom(indexed, indices, ondices, expected):
    from signify.core.keeping import BaseKeeper
    
    from keri.core.signing import Signer
    mock_signer_one = mock(spec=Signer, strict=True)

    with pytest.raises(ValueError, match=expected):
        BaseKeeper.__sign__(b'ser bytes', [mock_signer_one], indexed=indexed, indices=indices, ondices=ondices)
