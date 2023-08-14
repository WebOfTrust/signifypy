# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.clienting module

Ecosystem necessary for app tests
"""
import multicommand
import os
import multiprocessing
import socket
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


class Ecosystem():
    all_processes = []
    aids = []

    def __init__(self, aids:list):
        self.aids=aids
        self.setup()
        
    def setup(self):
        self.resetTestDirs(self.aids)
        self.runWitnessDaemon()
        self.runKeriaDaemon()
        
    def teardown(self):
        for name,port,process in self.all_processes:
            print(f"Terminating processes {name} on port {port}: {process}")
            process.terminate()
            self.wait_for_service_stop(name, port)
            print(f"Terminated processes {name} on port {port}: {process}")

    def is_port_in_use(self, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
            except socket.error as e:
                return True  # Port is in use
            return False  # Port is not in use
            
    def is_local_service_running(self, name, port):
        time.sleep(1)
        assert self.is_port_in_use(port) == False 
        # if self.is_port_in_use(port):

            # raise socket.error(f"Service {name} port {port} is in use, so we can't run the unit test services!")
        # else:
        #     print(f"Port {port} is available!")
            
    def wait_for_service_start(self, name, port, timeout=10):
        count = 0
        time.sleep(1)
        while(not self.is_port_in_use(port)):
            print(f"Waiting for service {name} on port {port} to start")
            time.sleep(1)
            count += 1
            if(count > timeout):
                raise TimeoutError(f"Service {name} on port {port} did not start in time!")
        time.sleep(1)
        
    def wait_for_service_stop(self, name, port, timeout=10):
        count = 0
        time.sleep(1)
        while(self.is_port_in_use(port)):
            print(f"Waiting for service {name} on port {port} to stop")
            time.sleep(1)
            count += 1
            assert count > timeout == False
                # raise TimeoutError(f"Service {name} on port {port} did not stop in time!")
        time.sleep(1)
        print(f"Service {name} on port {port} is stopped")
            
    def spawn_service(self, name, port, func, args):
        p = multiprocessing.Process(target=func,args=args)
        # process can't be a daemon or it will fail when hio processes start
        p.daemon = False
        p.start()
        self.all_processes.insert(0, (name,port,p))
        # wThread=threading.Thread(target=func, args=[])
        # wThread.daemon=True
        # wThread.start()
        
    def runKeria(self):
        kstart.runAgent(kname,
                        base,
                        kbran,
                        adminport,
                        httpport,
                        bootport,
                        configFile,
                        configDir,
                        0.0)

    def runDemoWitness(self):    
        parser = multicommand.create_parser(commands)
        args = parser.parse_args(["witness", "demo"])
                                #   os.path.join(TEST_DIR, "non-transferable-sample.json")])
        assert args.handler is not None
        doers = args.handler(args)

        directing.runController(doers=doers)

    def resetTestDirs(self, pres:list):
        print("Resetting test dirs")
        for pre in pres:
            print(f"Removing test dir: {pre}")
            Helpers.remove_test_dirs(pre)
        
    def runWitnessDaemon(self):
        print("Starting witness daemon thread")
        name = "witness"
        port = whttp
        self.is_local_service_running(name, port)
        # Start witness network
        self.spawn_service(name, port, self.runDemoWitness,())
        self.wait_for_service_start(name, port)
        # return self.all_processes

    def runKeriaDaemon(self):
        print("Starting keria daemon thread")
        name = "keria"
        port = adminport  
        self.is_local_service_running(name, port)
        #start keria cloud agent
        self.spawn_service(name, port, self.runKeria,())
        self.wait_for_service_start(name, port)
        # return self.all_processes