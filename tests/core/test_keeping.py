# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.core.keeping module

Testing authentication
"""

from mockito import mock, patch, verifyNoUnwantedInteractions, when, unstub, expect

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
    when(keeping).SaltyKeeper(salter=mock_salter, pidx=0, **kwargs).thenReturn(mock_keeper)
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
    when(keeping).RandyKeeper(salter=mock_salter, **kwargs).thenReturn(mock_keeper)
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
    when(keeping).GroupKeeper(mgr=manager, **kwargs).thenReturn(mock_keeper)
    actual = manager.new('group', 0)

    assert actual is mock_keeper

    verifyNoUnwantedInteractions()
    unstub()

def test_salty_keeper():
    bran = b'0123456789abcdefghijk'
    from keri.core import coring
    bran = coring.MtrDex.Salt_128.encode("utf-8") + b'A' + bran
    salter = coring.Salter(qb64=bran)

    from signify.core import keeping
    # Create a Salter withactual specifying the AIDs salt, let it create one randomly
    keeper = keeping.SaltyKeeper(salter=salter, pidx=0, kidx=0)
    verfers, ndigs = keeper.incept(transferable=True)
    assert len(verfers) == 1
    assert coring.Matter(qb64=verfers[0]).code == coring.MtrDex.Ed25519
    assert verfers[0] != "DPmhSfdhCPxr3EqjxzEtF8TVy0YX7ATo0Uc8oo2cnmY9"  # this seems dumb
    assert len(ndigs) == 1
    assert coring.Matter(qb64=ndigs[0]).code == coring.MtrDex.Blake3_256
    assert ndigs[0] != "EAORnRtObOgNiOlMolji-KijC_isa3lRDpHCsol79cOc"  # this seems dumb

    # Now lets use the same salt as the passcode (not advisable) so we have some determinism
    signer = salter.signer(transferable=False)
    encrypter = coring.Encrypter(verkey=signer.verfer.qb64)
    sxlt = encrypter.encrypt(matter=coring.Matter(qb64b=bran)).qb64

    keeper = keeping.SaltyKeeper(salter=salter, pidx=0, kidx=0, sxlt=sxlt)
    verfers, ndigs = keeper.incept(transferable=True)
    assert len(verfers) == 1
    assert verfers[0] == "DPmhSfdhCPxr3EqjxzEtF8TVy0YX7ATo0Uc8oo2cnmY9"
    assert len(ndigs) == 1
    assert ndigs[0] == "EAORnRtObOgNiOlMolji-KijC_isa3lRDpHCsol79cOc"

    params = keeper.params()
    assert params['pidx'] == 0
    assert params['kidx'] == 0
    assert params['dcode'] == 'E'
    assert params['icodes'] == ['A']
    assert params['ncodes'] == ['A']
    assert params['stem'] == 'signify:aid'
    assert params['transferable'] is True

    ser = b'I like salty keys that have a salt per AID not tied to the passcode'
    sigs = keeper.sign(ser=ser, indexed=True)
    assert len(sigs) == 1
    assert sigs[0] == 'AAA7tNQo83P-4wvFcnROAn_YPmcVo1ywESOwhXs0FBwQroeeSrRFjr0gK20lu8ZOsg3fKxbJzXlzZbYKfryFv4kC'

    verfers, ndigs = keeper.rotate(ncodes=[coring.MtrDex.Ed25519_Seed], transferable=True)
    assert len(verfers) == 1
    assert verfers[0] == "DHgomzINlGJHr-XP3sv2ZcR9QsIEYS3LJhs4KRaZYKly"
    assert len(ndigs) == 1
    assert ndigs[0] == "EJMovBlrBuD6BVeUsGSxLjczbLEbZU9YnTSud9K4nVzk"
    assert keeper.pidx == 0
    assert keeper.kidx == 1

    params = keeper.params()
    assert params['pidx'] == 0
    assert params['kidx'] == 1
    assert params['dcode'] == 'E'
    assert params['icodes'] == ['A']
    assert params['ncodes'] == ['A']
    assert params['stem'] == 'signify:aid'
    assert params['transferable'] is True

    # Sign something after the rotation, get a different signature
    sigs = keeper.sign(ser=ser, indexed=True)
    assert len(sigs) == 1
    assert sigs[0] == 'AAAMgsRDpbMrLGJt4RX6uDMA1eCJ7eJ6tKIuLQzBY-lh9fGWe-A3v8_dDUzZDPzuokEnPfe_u7QBWNeEV6DkaHMN'

    # Recreate the Salter at this kidx and get the same signature
    keeper = keeping.SaltyKeeper(salter=salter, pidx=0, kidx=1, sxlt=sxlt)
    sigs = keeper.sign(ser=ser, indexed=True)
    assert len(sigs) == 1
    assert sigs[0] == 'AAAMgsRDpbMrLGJt4RX6uDMA1eCJ7eJ6tKIuLQzBY-lh9fGWe-A3v8_dDUzZDPzuokEnPfe_u7QBWNeEV6DkaHMN'

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
