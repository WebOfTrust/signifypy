# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.core.authing module

Testing authentication
"""
import json

from keri.help import helping


def test_aid_classes(mockHelpingNowUTC):
    gaid = {
        'name': 'multisig',
        'group': {
            "smids": [
                {'i': "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY", "s": 0},
                {'i': "EBPtjiAY9ITdvScWFGeeCu3Pf6_CFFr57siQqffVt9Of", "s": 0},
                {'i': "EMYBtOuBKVdp3KdW_QM__pi-UAWfrewlDyiqGcbIbopR", "s": 0}
            ],
            "rmids": [
                {'i': "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY", "s": 0},
                {'i': "EBPtjiAY9ITdvScWFGeeCu3Pf6_CFFr57siQqffVt9Of", "s": 0},
                {'i': "EMYBtOuBKVdp3KdW_QM__pi-UAWfrewlDyiqGcbIbopR", "s": 0}
            ]
        }
    }

    said = {
        'name': 'salty',
        'salt': {'stem': 'signify:aid', 'pidx': 3, 'tier': 'low', 'temp': False}
    }

    raid = {
        "name": "randy",
        "prxs": [
            "1AAHC_k_5j9YBguCRIYJW7cWVdQB4WxPKx-lyIt7zKE6AmcFm8vrqzY9jPHk6i3CaMvax5gXzqGeCH31lFqwjnTmlDERap2kDf0x",
            "1AAH-XH8-4DOpGJP3jXC6jNba_cAe3D70zFgI38BUimz2n7i0IhTGQv2JqMVIGJpocyHnZuKu3e3_MG716E6_ITvypdKyUoPzc5z"
            ],
        "nxts": [
            "1AAHaLPcGa2Qb8R8tTd3ngY_BICuDrdAOQNSi0mZo_xIhRw8-szaJBx5HiVtwRYugdtKBjjcL5tFpplq8PW802OogIZdfxrwKZuw",
            "1AAHNr77U89r6Pa9E2_rWf26fIa2LdqFMMJ-3chFSIeUkGvFawGeRb0JekA60L4G-XLrPPkqvWPfujCExOFRbUscwsLLva786OvV"
            ],
    }
