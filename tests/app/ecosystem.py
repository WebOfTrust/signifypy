# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.clienting module

Ecosystem necessary for app tests
"""
import multicommand
import os
import multiprocessing
import time

from keri.app import directing
from keri.app.cli import commands

from keria.app.cli.commands import start as kstart
from keria.testing.testing_helper import Helpers

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
cwd = os.getcwd()

host="localhost"
adminport=3901
httpport=3902
bootport=3903
agentPre = "EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei"
ctrlPre = "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"
delPre = "EAJebqSr39pgRfLdrYiSlFQCH2upN4J1b63Er1-3werj"
base=""
kname="keria"
kbran=""
wname="witness"
wbase=""
walias="witness"
wbran=""
wtcp=5631
whttp=5632
wexpire=0.0
bran = "0123456789abcdefghijk"
burl = f"http://{host}:{bootport}/boot"
url = f"http://{host}:{adminport}"
configDir=f"{cwd}/tests/"
configFile="demo-witness-oobis.json"
wconfigDir=f"{cwd}/tests/"
wconfigFile="demo-witness-oobis.json"
wit1 = "BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha"
wit2 = "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM"
wit3 = "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX"

all_processes = []

def threadme(func,args):
    p = multiprocessing.Process(target=func,args=args)
    p.daemon = False
    p.start()
    all_processes.append(p)
    # wThread=threading.Thread(target=func, args=[])
    # wThread.daemon=True
    # wThread.start()
    
def runKeria():
    kstart.runAgent(kname,
                    base,
                    kbran,
                    adminport,
                    httpport,
                    bootport,
                    configFile,
                    configDir,
                    0.0)

def runDemoWitness():
    parser = multicommand.create_parser(commands)
    args = parser.parse_args(["witness", "demo"])
                            #   os.path.join(TEST_DIR, "non-transferable-sample.json")])
    assert args.handler is not None
    doers = args.handler(args)

    directing.runController(doers=doers)

def resetTestDirs(pres:list):
    print("Resetting test dirs")
    for pre in pres:
        print(f"Removing test dir: {pre}")
        Helpers.remove_test_dirs(pre)
    
def runWitnessDaemon():
    print("Starting witness daemon thread")
    # Start witness network
    threadme(runDemoWitness,())
    return all_processes

def runKeriaDaemon():
    print("Starting keria daemon thread")    
    #start keria cloud agent
    threadme(runKeria,())
    return all_processes