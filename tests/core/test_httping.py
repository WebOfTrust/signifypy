# -*- encoding: utf-8 -*-
from signify.core import httping

def test_parseRangeHeader():
    out = httping.parseRangeHeader("aids 0-1/2")
    
    assert out[0] == 0
    assert out[1] == 1
    assert out[2] == 2