# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.core.keeping module

Testing authentication
"""

from mockito import mock, verifyNoUnwantedInteractions, unstub, expect
import pytest

def test_keeping_manager():
    from keri.core.coring import Salter
    mock_salter = mock(spec=Salter, strict=True)

    from signify.core.keeping import Manager
    manager = Manager(salter=mock_salter)

    assert manager.salter == mock_salter
    assert manager.modules == {}

    verifyNoUnwantedInteractions()
    unstub()

def test_keeping_manager_new_salty():
    from keri.core.coring import Salter
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
    from keri.core.coring import Salter
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
    from keri.core.coring import Salter
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
    from keri.core.coring import Salter
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
    from keri.core.coring import Salter
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
    from keri.core.coring import Salter
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

    actual = manager.get({'prefix': 'aid1 prefix', 'pidx': 0, 'salty': {'dcode': 'E'}})

    assert actual is mock_keeper

    verifyNoUnwantedInteractions()
    unstub()

def test_keeping_manager_get_salty_pidx():
    from keri.core.coring import Salter
    mock_salter = mock(spec=Salter, strict=True)

    from signify.core.keeping import Manager
    manager = Manager(salter=mock_salter)

    from keri.core.coring import Prefixer
    mock_prefixer = mock(spec=Prefixer, strict=True)

    from keri.core import coring
    expect(coring, times=1).Prefixer(qb64='aid1 prefix').thenReturn(mock_prefixer)

    from keri.kering import ConfigurationError
    with pytest.raises(ConfigurationError, match="missing pidx in {'prefix': 'aid1 prefix', 'salty': {'dcode': 'E'}}"):
        manager.get({'prefix': 'aid1 prefix', 'salty': {'dcode': 'E'}})

    verifyNoUnwantedInteractions()
    unstub()

def test_keeping_manager_get_randy():
    from keri.core.coring import Salter
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
    from keri.core.coring import Salter
    mock_salter = mock(spec=Salter, strict=True)

    from signify.core.keeping import Manager
    manager = Manager(salter=mock_salter)

    from signify.core import keeping
    mock_keeper = mock(spec=keeping.GroupKeeper, strict=True)

    from keri.core.coring import Prefixer
    mock_prefixer = mock(spec=Prefixer, strict=True)

    from keri.core import coring
    expect(coring, times=1).Prefixer(qb64='aid1 prefix').thenReturn(mock_prefixer)

    expect(keeping, times=1).GroupKeeper(mgr=manager, keys=['key1'], ndigs=['dig1']).thenReturn(mock_keeper)
    actual = manager.get({'prefix': 'aid1 prefix', 'group': {'keys': ['key1'], 'ndigs': ['dig1']}})

    assert actual is mock_keeper

    verifyNoUnwantedInteractions()
    unstub()

def test_salty_keeper():
    # salty keep init mocks
    from keri.core.coring import Salter, Signer
    mock_salter = mock(spec=Salter, strict=True)
    from keri.core.coring import Verfer
    mock_verfer = mock({'qb64': 'verfer qb64'}, spec=Verfer, strict=True)
    mock_signer = mock({'verfer': mock_verfer ,'qb64': 'signer qb64'}, spec=Signer, strict=True)
    expect(mock_salter, times=1).signer(transferable=False).thenReturn(mock_signer)

    from keri.core.coring import Encrypter
    mock_encrypter = mock(spec=Encrypter, strict=True)
    
    from keri.core import coring
    expect(coring, times=1).Encrypter(verkey='verfer qb64').thenReturn(mock_encrypter)

    from keri.core.coring import Decrypter
    mock_decrypter= mock(spec=Decrypter, strict=True)
    
    from keri.core import coring
    expect(coring, times=1).Decrypter(seed='signer qb64').thenReturn(mock_decrypter)

    from keri.app.keeping import SaltyCreator
    mock_creator = mock({'salt': 'creator salt'}, spec=SaltyCreator, strict=True)
    from keri.app import keeping
    expect(keeping, times=1).SaltyCreator(stem='signify:aid', tier='low').thenReturn(mock_creator)

    from keri.core.coring import Cipher
    mock_cipher = mock({'qb64': 'cipher qb64'}, spec=Cipher, strict=True)
    expect(mock_encrypter, times=1).encrypt('creator salt').thenReturn(mock_cipher)

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
    from keri.core.coring import Salter, Signer
    mock_salter = mock(spec=Salter, strict=True)
    from keri.core.coring import Verfer
    mock_verfer = mock({'qb64': 'verfer qb64'}, spec=Verfer, strict=True)
    mock_signer = mock({'verfer': mock_verfer ,'qb64': 'signer qb64'}, spec=Signer, strict=True)
    expect(mock_salter, times=1).signer(transferable=False).thenReturn(mock_signer)

    from keri.core.coring import Encrypter
    mock_encrypter = mock(spec=Encrypter, strict=True)
    
    from keri.core import coring
    expect(coring, times=1).Encrypter(verkey='verfer qb64').thenReturn(mock_encrypter)

    from keri.core.coring import Decrypter
    mock_decrypter= mock(spec=Decrypter, strict=True)
    
    from keri.core import coring
    expect(coring, times=1).Decrypter(seed='signer qb64').thenReturn(mock_decrypter)

    from keri.app.keeping import SaltyCreator
    mock_creator = mock({'salt': 'creator salt'}, spec=SaltyCreator, strict=True)

    from keri.app import keeping
    expect(keeping, times=1).SaltyCreator(salt='0AA0123456789abcdefghijk', stem='signify:aid', tier='low').thenReturn(mock_creator)

    from keri.core.coring import Cipher
    mock_cipher = mock({'qb64': 'cipher qb64'}, spec=Cipher, strict=True)
    expect(mock_encrypter, times=1).encrypt('creator salt').thenReturn(mock_cipher)

    # test
    from signify.core.keeping import SaltyKeeper
    sk = SaltyKeeper(mock_salter, pidx=0, bran='0123456789abcdefghijk')

    assert sk.params() == {'sxlt': 'cipher qb64', 'pidx': 0, 'kidx': 0, 'stem': 'signify:aid', 'tier': 'low', 'icodes': ['A'], 'ncodes': ['A'], 'dcode': 'E', 'transferable': False}

    verifyNoUnwantedInteractions()
    unstub()

def test_salty_keeper_sxlt():
    # salty keep init mocks
    from keri.core.coring import Salter, Signer
    mock_salter = mock({'qb64': 'salter qb64'}, spec=Salter, strict=True)
    from keri.core.coring import Verfer
    mock_verfer = mock({'qb64': 'verfer qb64'}, spec=Verfer, strict=True)
    mock_signer = mock({'verfer': mock_verfer ,'qb64': 'signer qb64'}, spec=Signer, strict=True)
    expect(mock_salter, times=1).signer(transferable=False).thenReturn(mock_signer)

    from keri.core.coring import Encrypter
    mock_encrypter = mock(spec=Encrypter, strict=True)
    
    from keri.core import coring
    expect(coring, times=1).Encrypter(verkey='verfer qb64').thenReturn(mock_encrypter)

    from keri.core.coring import Decrypter
    mock_decrypter= mock(spec=Decrypter, strict=True)
    
    from keri.core import coring
    expect(coring, times=1).Decrypter(seed='signer qb64').thenReturn(mock_decrypter)

    from keri.core.coring import Cipher
    mock_cipher = mock({'qb64': 'cipher qb64'}, spec=Cipher, strict=True)

    from keri.core import coring
    expect(coring, times=1).Cipher(qb64='0123456789abcdefghijk').thenReturn(mock_cipher)

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
    from keri.core.coring import Salter, Signer
    mock_salter = mock(spec=Salter, strict=True)
    from keri.core.coring import Verfer
    mock_verfer = mock({'qb64': 'verfer qb64'}, spec=Verfer, strict=True)
    mock_signer = mock({'verfer': mock_verfer ,'qb64': 'signer qb64'}, spec=Signer, strict=True)
    expect(mock_salter, times=1).signer(transferable=False).thenReturn(mock_signer)

    from keri.core.coring import Encrypter
    mock_encrypter = mock(spec=Encrypter, strict=True)
    
    from keri.core import coring
    expect(coring, times=1).Encrypter(verkey='verfer qb64').thenReturn(mock_encrypter)

    from keri.core.coring import Decrypter
    mock_decrypter= mock(spec=Decrypter, strict=True)
    
    from keri.core import coring
    expect(coring, times=1).Decrypter(seed='signer qb64').thenReturn(mock_decrypter)

    from keri.app.keeping import SaltyCreator
    mock_creator = mock({'salt': 'creator salt'}, spec=SaltyCreator, strict=True)

    from keri.app import keeping
    expect(keeping, times=1).SaltyCreator(stem='signify:aid', tier='low').thenReturn(mock_creator)

    from keri.core.coring import Cipher
    mock_cipher = mock({'qb64': 'cipher qb64'}, spec=Cipher, strict=True)
    expect(mock_encrypter, times=1).encrypt('creator salt').thenReturn(mock_cipher)

    # incept mocks
    mock_incept_verfer = mock({'qb64': 'incept verfer qb64'}, spec=Verfer, strict=True)
    mock_incept_signer = mock({'verfer': mock_incept_verfer ,'qb64': 'incept signer qb64'}, spec=Signer, strict=True)
    expect(mock_creator, times=1).create(codes=['A'], pidx=0, kidx=0, transferable=True).thenReturn([mock_incept_signer])

    mock_incept_nverfer = mock({'qb64b': b'incept nverfer qb64b'}, spec=Verfer, strict=True)
    mock_incept_nsigner = mock({'verfer': mock_incept_nverfer ,'qb64': 'incept signer qb64'}, spec=Signer, strict=True)
    expect(mock_creator, times=1).create(codes=['A'], pidx=0, kidx=1, transferable=True).thenReturn([mock_incept_nsigner])

    from keri.core.coring import Diger
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
    from keri.core.coring import Salter, Signer
    mock_salter = mock(spec=Salter, strict=True)
    from keri.core.coring import Verfer
    mock_verfer = mock({'qb64': 'verfer qb64'}, spec=Verfer, strict=True)
    mock_signer = mock({'verfer': mock_verfer ,'qb64': 'signer qb64'}, spec=Signer, strict=True)
    expect(mock_salter, times=1).signer(transferable=False).thenReturn(mock_signer)

    from keri.core.coring import Encrypter
    mock_encrypter = mock(spec=Encrypter, strict=True)
    
    from keri.core import coring
    expect(coring, times=1).Encrypter(verkey='verfer qb64').thenReturn(mock_encrypter)

    from keri.core.coring import Decrypter
    mock_decrypter= mock(spec=Decrypter, strict=True)
    
    from keri.core import coring
    expect(coring, times=1).Decrypter(seed='signer qb64').thenReturn(mock_decrypter)

    from keri.app.keeping import SaltyCreator
    mock_creator = mock({'salt': 'creator salt'}, spec=SaltyCreator, strict=True)

    from keri.app import keeping
    expect(keeping, times=1).SaltyCreator(stem='signify:aid', tier='low').thenReturn(mock_creator)

    from keri.core.coring import Cipher
    mock_cipher = mock({'qb64': 'cipher qb64'}, spec=Cipher, strict=True)
    expect(mock_encrypter, times=1).encrypt('creator salt').thenReturn(mock_cipher)

    # rotate mocks
    mock_rotate_verfer = mock({'qb64': 'rotate verfer qb64'}, spec=Verfer, strict=True)
    mock_rotate_signer = mock({'verfer': mock_rotate_verfer ,'qb64': 'rotate signer qb64'}, spec=Signer, strict=True)
    expect(mock_creator, times=1).create(codes=['A'], pidx=0, kidx=1, transferable=False).thenReturn([mock_rotate_signer])

    mock_rotate_nverfer = mock({'qb64b': b'rotate nverfer qb64b'}, spec=Verfer, strict=True)
    mock_rotate_nsigner = mock({'verfer': mock_rotate_nverfer ,'qb64': 'rotate signer qb64'}, spec=Signer, strict=True)
    expect(mock_creator, times=1).create(codes=['A'], pidx=0, kidx=2, transferable=True).thenReturn([mock_rotate_nsigner])

    from keri.core.coring import Diger
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
    from keri.core.coring import Salter, Signer
    mock_salter = mock(spec=Salter, strict=True)
    from keri.core.coring import Verfer
    mock_verfer = mock({'qb64': 'verfer qb64'}, spec=Verfer, strict=True)
    mock_signer = mock({'verfer': mock_verfer ,'qb64': 'signer qb64'}, spec=Signer, strict=True)
    expect(mock_salter, times=1).signer(transferable=False).thenReturn(mock_signer)

    from keri.core.coring import Encrypter
    mock_encrypter = mock(spec=Encrypter, strict=True)
    
    from keri.core import coring
    expect(coring, times=1).Encrypter(verkey='verfer qb64').thenReturn(mock_encrypter)

    from keri.core.coring import Decrypter
    mock_decrypter= mock(spec=Decrypter, strict=True)
    
    from keri.core import coring
    expect(coring, times=1).Decrypter(seed='signer qb64').thenReturn(mock_decrypter)

    from keri.app.keeping import SaltyCreator
    mock_creator = mock({'salt': 'creator salt'}, spec=SaltyCreator, strict=True)

    from keri.app import keeping
    expect(keeping, times=1).SaltyCreator(stem='signify:aid', tier='low').thenReturn(mock_creator)

    from keri.core.coring import Cipher
    mock_cipher = mock({'qb64': 'cipher qb64'}, spec=Cipher, strict=True)
    expect(mock_encrypter, times=1).encrypt('creator salt').thenReturn(mock_cipher)

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
    from keri.core.coring import Salter, Signer
    mock_salter = mock(spec=Salter, strict=True)
    from keri.core.coring import Verfer
    mock_verfer = mock({'qb64': 'verfer qb64'}, spec=Verfer, strict=True)
    mock_signer = mock({'verfer': mock_verfer ,'qb64': 'signer qb64'}, spec=Signer, strict=True)
    expect(mock_salter, times=1).signer(transferable=False).thenReturn(mock_signer)

    from keri.core.coring import Encrypter
    mock_encrypter = mock(spec=Encrypter, strict=True)
    
    from keri.core import coring
    expect(coring, times=1).Encrypter(verkey='verfer qb64').thenReturn(mock_encrypter)

    from keri.core.coring import Decrypter
    mock_decrypter= mock(spec=Decrypter, strict=True)
    
    from keri.core import coring
    expect(coring, times=1).Decrypter(seed='signer qb64').thenReturn(mock_decrypter)

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
    from keri.core.coring import Salter, Signer
    mock_salter = mock(spec=Salter, strict=True)
    from keri.core.coring import Verfer
    mock_verfer = mock({'qb64': 'verfer qb64'}, spec=Verfer, strict=True)
    mock_signer = mock({'verfer': mock_verfer ,'qb64': 'signer qb64'}, spec=Signer, strict=True)
    expect(mock_salter, times=1).signer(transferable=False).thenReturn(mock_signer)

    from keri.core.coring import Encrypter
    mock_encrypter = mock(spec=Encrypter, strict=True)
    
    from keri.core import coring
    expect(coring, times=1).Encrypter(verkey='verfer qb64').thenReturn(mock_encrypter)

    from keri.core.coring import Decrypter
    mock_decrypter= mock(spec=Decrypter, strict=True)
    
    from keri.core import coring
    expect(coring, times=1).Decrypter(seed='signer qb64').thenReturn(mock_decrypter)

    from signify.core.keeping import RandyKeeper
    rk = RandyKeeper(mock_salter, transferable=True, nxts=['nxt1', 'nxt2'], prxs=['prx1', 'prx2'])

    actual = rk.params()

    assert actual == {'nxts': ['nxt1', 'nxt2',], 'prxs': ['prx1', 'prx2'], 'transferable': True}

    verifyNoUnwantedInteractions()
    unstub()

def test_randy_keeper_incept():
    from keri.core.coring import Salter, Signer
    mock_salter = mock(spec=Salter, strict=True)
    from keri.core.coring import Verfer
    mock_verfer = mock({'qb64': 'verfer qb64'}, spec=Verfer, strict=True)
    mock_signer = mock({'verfer': mock_verfer ,'qb64': 'signer qb64'}, spec=Signer, strict=True)
    expect(mock_salter, times=1).signer(transferable=False).thenReturn(mock_signer)

    from keri.core.coring import Encrypter
    mock_encrypter = mock(spec=Encrypter, strict=True)
    
    from keri.core import coring
    expect(coring, times=1).Encrypter(verkey='verfer qb64').thenReturn(mock_encrypter)

    from keri.core.coring import Decrypter
    mock_decrypter= mock(spec=Decrypter, strict=True)
    
    from keri.core import coring
    expect(coring, times=1).Decrypter(seed='signer qb64').thenReturn(mock_decrypter)

    # start incept mocks
    from keri.app.keeping import RandyCreator
    mock_creator = mock(spec=RandyCreator, strict=True)

    # verfers mocks
    from keri.core.coring import Signer, Verfer
    mock_verfer = mock({'qb64': 'signer verfer qb64'}, spec=Verfer, strict=True)
    mock_signer = mock({'verfer': mock_verfer}, spec=Signer, strict=True)
    expect(mock_creator, times=1).create(codes=['A'], transferable=True).thenReturn([mock_signer])

    from keri.core.coring import Cipher
    mock_cipher = mock({'qb64': 'cipher qb64'}, spec=Cipher, strict=True)
    expect(mock_encrypter, times=1).encrypt(matter=mock_signer).thenReturn(mock_cipher)

    # digers mocks
    mock_verfer = mock({'qb64b': b'signer verfer qb64b'}, spec=Verfer, strict=True)
    mock_nsigner = mock({'verfer': mock_verfer}, spec=Signer, strict=True)
    expect(mock_creator, times=1).create(codes=['B'], transferable=True).thenReturn([mock_nsigner])
    expect(mock_encrypter, times=1).encrypt(matter=mock_nsigner).thenReturn(mock_cipher)

    from keri.core.coring import Diger
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
    from keri.core.coring import Salter, Signer
    mock_salter = mock(spec=Salter, strict=True)
    from keri.core.coring import Verfer
    mock_verfer = mock({'qb64': 'verfer qb64'}, spec=Verfer, strict=True)
    mock_signer = mock({'verfer': mock_verfer ,'qb64': 'signer qb64'}, spec=Signer, strict=True)
    expect(mock_salter, times=1).signer(transferable=False).thenReturn(mock_signer)

    from keri.core.coring import Encrypter
    mock_encrypter = mock(spec=Encrypter, strict=True)
    
    from keri.core import coring
    expect(coring, times=1).Encrypter(verkey='verfer qb64').thenReturn(mock_encrypter)

    from keri.core.coring import Decrypter
    mock_decrypter= mock(spec=Decrypter, strict=True)
    
    from keri.core import coring
    expect(coring, times=1).Decrypter(seed='signer qb64').thenReturn(mock_decrypter)

    # start rotate mocks
    from keri.app.keeping import RandyCreator
    mock_creator = mock(spec=RandyCreator, strict=True)

    from keri.core import coring
    from keri.core.coring import Cipher
    mock_nxt_cipher = mock(spec=Cipher, strict=True)
    expect(coring, times=1).Cipher(qb64='nxt qb64').thenReturn(mock_nxt_cipher)

    # verfers mocks
    from keri.core.coring import Signer, Verfer
    mock_verfer = mock({'qb64': 'signer verfer qb64'}, spec=Verfer, strict=True)
    mock_signer = mock({'verfer': mock_verfer}, spec=Signer, strict=True)
    expect(mock_decrypter, times=1).decrypt(cipher=mock_nxt_cipher, transferable=True).thenReturn(mock_signer)

    # digers mocks
    mock_verfer = mock({'qb64b': b'signer verfer qb64b'}, spec=Verfer, strict=True)
    mock_nsigner = mock({'verfer': mock_verfer}, spec=Signer, strict=True)
    expect(mock_creator, times=1).create(codes=['A'], transferable=True).thenReturn([mock_nsigner])

    from keri.core.coring import Cipher
    mock_cipher = mock({'qb64': 'cipher qb64'}, spec=Cipher, strict=True)
    expect(mock_encrypter, times=1).encrypt(matter=mock_nsigner).thenReturn(mock_cipher)

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

    verifyNoUnwantedInteractions()
    unstub()

def test_randy_keeper_sign():
    from keri.core.coring import Salter, Signer
    mock_salter = mock(spec=Salter, strict=True)
    from keri.core.coring import Verfer
    mock_verfer = mock({'qb64': 'verfer qb64'}, spec=Verfer, strict=True)
    mock_signer = mock({'verfer': mock_verfer ,'qb64': 'signer qb64'}, spec=Signer, strict=True)
    expect(mock_salter, times=1).signer(transferable=False).thenReturn(mock_signer)

    from keri.core.coring import Encrypter
    mock_encrypter = mock(spec=Encrypter, strict=True)
    
    from keri.core import coring
    expect(coring, times=1).Encrypter(verkey='verfer qb64').thenReturn(mock_encrypter)

    from keri.core.coring import Decrypter
    mock_decrypter= mock(spec=Decrypter, strict=True)
    
    from keri.core import coring
    expect(coring, times=1).Decrypter(seed='signer qb64').thenReturn(mock_decrypter)

    from keri.core import coring
    from keri.core.coring import Cipher
    mock_prx_cipher = mock({'qb64b': b'cipher qb64b'}, spec=Cipher, strict=True)
    expect(coring, times=1).Cipher(qb64='prx qb64').thenReturn(mock_prx_cipher)

    from keri.core.coring import Signer, Verfer
    mock_verfer = mock({'qb64': 'signer verfer qb64'}, spec=Verfer, strict=True)
    mock_signer = mock({'verfer': mock_verfer}, spec=Signer, strict=True)
    expect(mock_decrypter, times=1).decrypt(ser=b'cipher qb64b', transferable=False).thenReturn(mock_signer)

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
    from keri.core.coring import Salter
    mock_salter = mock(spec=Salter, strict=True)

    from signify.core.keeping import Manager
    manager = Manager(salter=mock_salter)

    from signify.core.keeping import GroupKeeper
    gk = GroupKeeper(mgr=manager, mhab={'m': 'hab'}, states=[{'k': ['key 1']}], rstates=[{'n': ['n dig 1']}])

    assert gk.gkeys == ['key 1']
    assert gk.gdigs == ['n dig 1']
    assert gk.mhab == {'m': 'hab'}

    from keri.app.keeping import Algos
    assert gk.algo == Algos.group

def test_group_keeper_incept():
    from keri.core.coring import Salter
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
    from keri.core.coring import Salter
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
    from keri.core.coring import Salter
    mock_salter = mock(spec=Salter, strict=True)

    from signify.core.keeping import Manager
    mock_manager = Manager(salter=mock_salter)

    from signify.core.keeping import GroupKeeper
    gk = GroupKeeper(mgr=mock_manager, mhab={'state': {'k': ['key 1'], 'n': ['n dig 1']}}, keys=['key 1'], ndigs=['n dig 1'])

    from signify.core.keeping import BaseKeeper
    mock_keeper = mock(strict=True)
    expect(mock_manager, times=1).get({'state': {'k': ['key 1'], 'n': ['n dig 1']}}).thenReturn(mock_keeper)

    expect(mock_keeper, times=1).sign(b'ser', indexed=True, indices=[0], ondices=[0]).thenReturn(['signatures'])

    actual = gk.sign(b'ser', indexed=True)

    assert actual == ['signatures']

    verifyNoUnwantedInteractions()
    unstub()

def test_group_keeper_params():
    from keri.core.coring import Salter
    mock_salter = mock(spec=Salter, strict=True)

    from signify.core.keeping import Manager
    mock_manager = Manager(salter=mock_salter)

    from signify.core.keeping import GroupKeeper
    gk = GroupKeeper(mgr=mock_manager, mhab={'state': {'k': ['key 1'], 'n': ['n dig 1']}}, keys=['key 1'], ndigs=['n dig 1'])

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
    
    from keri.core.coring import Signer
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
    
    from keri.core.coring import Signer
    mock_signer_one = mock(spec=Signer, strict=True)

    from keri.core.coring import Siger
    mock_cigar = mock({'qb64': 'an indexed signature'}, spec=Siger, strict=True)
    expect(mock_signer_one, times=1).sign(b'ser bytes', index=0, only=False, ondex=0).thenReturn(mock_cigar)

    actual = BaseKeeper.__sign__(b'ser bytes', [mock_signer_one], indexed=indexed, indices=indices, ondices=ondices)

    assert actual[0] == 'an indexed signature'

@pytest.mark.parametrize('indexed,indices,ondices,expected', [
    (True, [-1], [0], 'Invalid signing index = -1, not whole number.'),
    (True, [0], [-1], 'Invalid other signing index = -1, not None or not whole number.'),
])
def test_base_keeper_sign_indexed_boom(indexed, indices, ondices, expected):
    from signify.core.keeping import BaseKeeper
    
    from keri.core.coring import Signer
    mock_signer_one = mock(spec=Signer, strict=True)

    with pytest.raises(ValueError, match=expected):
        BaseKeeper.__sign__(b'ser bytes', [mock_signer_one], indexed=indexed, indices=indices, ondices=ondices)