# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.core.keeping module

Testing authentication
"""

from keri.core import coring

from signify.core import keeping


def test_salty_keeper():
    bran = b'0123456789abcdefghijk'
    bran = coring.MtrDex.Salt_128.encode("utf-8") + b'A' + bran
    salter = coring.Salter(qb64=bran)

    # Create a Salter without specifying the AIDs salt, let it create one randomly
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

def test_randy_keeper():
    assert True