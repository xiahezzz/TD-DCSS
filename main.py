from charm.toolbox.pairinggroup import PairingGroup, ZR, G1, G2, GT, pair
from charm.toolbox.conversion import Conversion
import msp
import datetime
import math
import re
import random
import time
import copy
import pandas as pd
from typing import List
import sys
import pickle

debug = True

pattern = re.compile(r'\[\[(.*?),')
L = 128
U = 5

def generate_data_granules(u,l):
    res = [0] * u
    for i in range(u):
        res[i] = int(''.join(random.choice('01') for _ in range(l)),2)
    return res

DG = generate_data_granules(100,L)

def xor_all(DG):
    res = DG[0]
    for i in range(1,len(DG)):
        res = res ^ DG[i]
    return res

def xor_except_I(DG,I):
    res = [xor_all(DG) for _ in range(len(I))]
    
    for i in range(0,len(I)):
        res[i] = res[i]^DG[I[i]]
    return res

class TA():
    def __init__(self,group_obj:PairingGroup) -> None:
        self.group = group_obj
        self.msk = {}
    
    def h(self,m:str):
        return self.group.hash(m,ZR)
    def H1(self,m:str):
        return self.group.hash(m,G1)
    def H2(self,gt:GT,l:int):
        bytes_gt = int.from_bytes(pattern.search(gt.__str__()).group(1).encode(),byteorder='big')
        return bytes_gt & ((1<<l)-1)
    def H3(self,inputs:list):
        return self.group.hash(inputs,ZR)
    
    def setup(self):
        g1 = self.group.random(G1)
        g2 = self.group.random(G2)

        alpha = self.group.random(ZR)
        mpk = {
            "BG":{
                "g1":g1,
                "g2":g2,
                "curve":self.group
            },
            "g2_alpha":g2**alpha,
            "h":self.h,
            "H":[self.H1,self.H2,self.H3] 
        }

        msk = {
            "alpha":alpha
        }
        self.msk = msk
        return mpk

    def key_gen_SP(self,mpk,ID_SP,attr_list):
        r = self.group.random(ZR)
        sk1 = {}
        for attr in attr_list:
            attrHash = self.H1(attr)
            sk1[attr] = attrHash ** r
        sk2 = (self.H1(ID_SP)**self.msk['alpha']) * (self.H1(str(self.group.order()+1))**r)
        sk3 =  mpk['BG']['g2'] ** r
        sk4 = self.H1(ID_SP)**r
        return {'attr_list':attr_list,'sk1':sk1,'sk2':sk2,'sk3':sk3,'sk4':sk4}

    def PKeyGenPDO(self,psi):
        beta = self.group.random(ZR)
        return beta,psi**beta

class SP():
    def __init__(self,ID_SP,mpk,sk,verbose=False) -> None:
        self.sk = sk  
        self.id = ID_SP
        self.util = msp.MSP(mpk['BG']['curve'], verbose)

    def AccessDc(self,mpk,DCI,T,pk_PDO):
        P_T1 = (pair(self.sk['sk2'],DCI)*pair(self.sk['sk4'],pk_PDO))/pair(T['T1'],self.sk['sk3'])
        return P_T1

    def Dec_FABEO(self,ctxt):
        key = self.sk
        nodes = self.util.prune(ctxt['policy'], key['attr_list'])
        # print(nodes)
        if not nodes:
            print ("Policy not satisfied.")
            return None

        prod_sk = 1
        prod_ct = 1
        for node in nodes:
            attr = node.getAttributeAndIndex()
            attr_stripped = self.util.strip_index(attr)  # no need, re-use not allowed

            prod_sk *= key['sk1'][attr_stripped]
            prod_ct *= ctxt['C4'][attr]
        
        e0 = pair(key['sk2'], ctxt['C1'])
        e1 = pair(prod_sk, ctxt['C3'])
        e2 = pair(prod_ct, key['sk3'])

        kem = e0 * (e1/e2)

        return kem

    def DecDC(self,mpk,DCI,DC,T,P_T1):
        delta = mpk['H'][2]([DCI,DC['C1'],DC['C2'],DC['C3'],DC['C4']])
        
        if debug and pair(DC['V'],mpk['BG']['g2']) != pair(mpk['BG']['g1']**delta,DCI):
            print("DC may be tampered! try...")

        P_T2 = self.Dec_FABEO(DC)
        PT = P_T1*P_T2
        
        P2 = mpk['H'][1](T['T2']/PT,L)
        
        dgs = [0] * (len(T['Tw']))
        for i in range(0,len(dgs)):
            Pw = T['Tw'][i][1]/PT
            dgs[i] = DC['C2']^T['Tw'][i][0]^mpk['H'][1](Pw,L)^P2
        
        return dgs

class PDO(): 
    def __init__(self,id,mpk,verbose=False) -> None:
        self.id = id
        self.sk = ""
        self.pk = ""
        self.local = {}
        self.util = msp.MSP(mpk['BG']['curve'], verbose)
    
    def GenPsi(self,mpk):
        sigma = mpk['BG']['curve'].random(ZR)
        gamma = mpk['h'](self.id+str(sigma))
        psi = mpk['BG']['g2'] ** gamma
        self.sk = gamma
        return psi
    
    def SKeyGenPDO(self,beta,pk):
        self.pk = pk
        self.sk = self.sk*beta

    def Encapsulate(self,mpk,DG,policy_str):
        group = mpk['BG']['curve']
        a1 = generate_data_granules(1,L)[0]
        d1,y = group.random(ZR,2)
        P1 = a1
        DCI = mpk['BG']['g2'] ** d1
        C1 = mpk['BG']['g2'] ** y
        P2 = mpk['H'][1](pair(mpk['BG']['g1']**self.sk,C1),L)
        C2 = xor_all(DG) ^ P1 ^ P2
        sprime = group.random(ZR)
        C3 = mpk['BG']['g2'] ** sprime
        policy = self.util.createPolicy(policy_str)
        mono_span_prog = self.util.convert_policy_to_msp(policy)
        num_cols = self.util.len_longest_row
        v = [y]
        for i in range(num_cols-1):
            rand = group.random(ZR)
            v.append(rand)
        bHash = group.hash(str(group.order()+1), G1) # ZR+1
        ct = {}
        for attr, row in mono_span_prog.items():
            attr_stripped = self.util.strip_index(attr)
            attrHash = group.hash(attr_stripped, G1)
            len_row = len(row)
            Mivtop = sum(i[0] * i[1] for i in zip(row, v[:len_row]))
            ct[attr] = bHash ** Mivtop * attrHash ** sprime
        
        delta = mpk['H'][2]([DCI,C1,C2,C3,ct])
        V = mpk['BG']['g1'] ** (delta * d1)
        A = {"DCI":DCI,"P1":P1,"d":d1,"y":y}
        self.local = {DCI:A}
        return DCI,A,{'policy':policy,'C1':C1,'C2':C2,'C3':C3,'C4':ct,"V":V}

    def TaskIssue(self,mpk,ID_SP,DG,I,A,t):
        group = mpk['BG']['curve']

        T1 = mpk['H'][0](ID_SP)**self.sk * mpk['H'][0](str(group.order()+1))**A['d']
        P_T1 = pair(mpk['H'][0](ID_SP)**A['d'],mpk['g2_alpha'])
        P_T2 = pair(mpk['H'][0](ID_SP)**A['y'],mpk['g2_alpha'])
        PT = P_T1*P_T2

        T2 = PT * pair(mpk['BG']['g1']**self.sk,mpk['BG']['g2']**A['y'])

        DGs = xor_except_I(DG,I)
        Tw = []

        for i in range(0,len(I)):
            w = group.random(ZR)
            Pw = pair(mpk['H'][0](ID_SP)**w,mpk['g2_alpha'])
            a = DGs[i]^A['P1']^mpk['H'][1](Pw,L)
            b = PT*Pw
            Tw.append((a,b))
        
        
        task = {'T1':T1,'T2':T2,'Tw':Tw}

        a_c1 = generate_data_granules(1,L)[0]
        d_c1 = group.random(ZR)
        B = {}
        B['DCI'] = A['DCI']*(mpk['BG']['g2'] ** d_c1)
        B['P1'] = A['P1']^a_c1
        B['d'] = A['d'] + d_c1
        B['y'] = A['y']
        return A['DCI'],task,{'R1':mpk['BG']['g1']**B['d'],'R2':B['DCI'],'R3':a_c1},{'D1':P_T1,'D2':t},B

class CS():
    def __init__(self) -> None:
        self.capsules = {}
        self.downloads = {}
        self.revokes = {}
    
    def put_DC(self,DCI,DC):
        self.capsules[DCI] = DC

    def put_RD(self,DCI,R,D):
        self.downloads[DCI] = D
        self.revokes[DCI] = R
    
    def UpdateDC(self,mpk,DCI):
        newDC = {}
        R1,R2,R3 = self.revokes[DCI]['R1'],self.revokes[DCI]['R2'],self.revokes[DCI]['R3']
        del self.revokes[DCI]
        DC = self.capsules[DCI]
        del self.capsules[DCI]

        newDCI = R2
        
        newDC['C2'] = DC['C2']^R3
        delta = mpk['H'][2]([newDCI,DC['C1'],newDC['C2'],DC['C3'],DC['C4']])
        newDC['V'] = R1 ** delta
        newDC['C1'] = DC['C1']
        newDC['C3'] = DC['C3']
        newDC['C4'] = DC['C4']
        newDC['policy'] = DC['policy']
        self.capsules[newDCI] = newDC
        return newDCI,newDC
    
    def DownloadDC(self,DCI,P_T1):
        assert datetime.datetime.now().timestamp() < self.downloads[DCI]['D2'] and P_T1 == self.downloads[DCI]['D1']
        del self.downloads[DCI]
        DC = self.capsules[DCI]
        return DC

if __name__ == "__main__":
    # instantiate a bilinear pairing map
    pairing_group = PairingGroup('MNT224')
    n = 1

    #init ta
    ta = TA(pairing_group)
    mpk = ta.setup()

    #init CS
    cs = CS()
    
    #SP register
    attr_list = ['1','2','3']
    sk_SP1 = ta.key_gen_SP(mpk,"SP1",attr_list)
    sp1 = SP("SP1",mpk,sk_SP1)

    #PDO register
    pdo1 = PDO("PDO1",mpk)
    psi = pdo1.GenPsi(mpk)
    beta,pk = ta.PKeyGenPDO(psi)
    pdo1.SKeyGenPDO(beta,pk)
        
    #PDO encapsulate data
    DG = generate_data_granules(U,L)
    DG = [int.from_bytes(u'TD-DCAC win!'.encode(),'big'),int.from_bytes(u'hduer!'.encode(),'big')]
    policy_str = u'((1 and 3) and (2 OR 4))'
    DCI,A,DC = pdo1.Encapsulate(mpk,DG,policy_str)
    cs.put_DC(DCI,DC)

    #PDO issues task
    I = [0,1]
    t = datetime.datetime.now().timestamp() + datetime.timedelta(days=1).total_seconds()
    DCI_PDO1,task1,R1,D1,A1 = pdo1.TaskIssue(mpk,"SP1",DG,I,A,t)
    cs.put_RD(DCI_PDO1,R1,D1)

    newDCI,newDC = cs.UpdateDC(mpk,DCI)

    DCI_PDO2,task2,R2,D2,A2 = pdo1.TaskIssue(mpk,"SP1",DG,I,A1,t)
    cs.put_RD(DCI_PDO2,R2,D2)
    #SP Decrypt DC
    P_T1 = sp1.AccessDc(mpk,DCI_PDO2,task2,pdo1.pk)
    #cs check P_T1 and expired time
    DC_CS2 = cs.DownloadDC(DCI_PDO2,P_T1)
    #cs update DC
    #DCI_CS2,DC2 = cs.UpdateDC(mpk,DCI_PDO1)
    #Dec
    res = sp1.DecDC(mpk,DCI_PDO2,DC_CS2,task2,P_T1)
    print("DG:",DG)
    print("res1:",res[0].to_bytes(L//8,"big"),res[1].to_bytes(L//8,"big"))