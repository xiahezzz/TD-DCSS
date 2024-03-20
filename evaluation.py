from charm.toolbox.pairinggroup import PairingGroup, ZR, G1, G2, GT, pair
from charm.toolbox.conversion import Conversion
import re
import time
import pandas as pd
from typing import List
from main import * 

debug = True

pattern = re.compile(r'\[\[(.*?),')
L = 128
U = 5

def KeyGenSPTest(an,mpk,ta:TA,test=False):
    N = 1
    if test:
        N=5
    df = pd.DataFrame(columns=['an','time'])
    sp = [0] * len(an)
    for i in range(len(an)):
        attr_list = [str(a) for a in range(an[i])]
        start = time.time()
        for j in range(N):
            keysp = ta.key_gen_SP(mpk,"SP"+str(i),attr_list)
        end = (time.time() - start)/N
        sp[i] = SP("SP"+str(i),mpk,keysp)
        df.loc[i] = [an[i],end]
    if test:
        df.to_csv('keygensp.csv',index=None)
    return sp

def EncapsulteTest1(dgn,pdo:PDO,test=False):
    N = 1
    if test:
        N=5
    df = pd.DataFrame(columns=['dgn','time'])
    an = 1
    policy_str = u'1 and 2 and 3'
    DCs = [0] * len(dgn)
    
    for i in range(len(dgn)):
        t1 = time.time()
        for j in range(N):
            DCI,A,DC = pdo.Encapsulate(mpk,DG[0:dgn[i]],policy_str)
        t = (time.time()-t1)/N

        df.loc[i] = [dgn[i],t]
        DCs[i] = [DCI,A,DC]
    if test:
        df.to_csv('EncapsulteTest1.csv',index=None)
    return DCs

def EncapsulteTest2(psize,pdo:PDO,test=False):
    N = 1
    if test:
        N=10
    df = pd.DataFrame(columns=['psize','time'])
    
    atts = [str(i)+" and " for i in range(psize[-1])]
    DCs = [0] * len(psize)
    
    for i in range(len(psize)):
        policy = "".join(atts[0:psize[i]-1])
        policy += str(psize[i]-1)
        t1 = time.time()
        for j in range(N):
            DCI,A,DC = pdo.Encapsulate(mpk,DG[0:10],policy)
        t = (time.time()-t1)/N

        df.loc[i] = [psize[i],t]
        DCs[i] = [DCI,A,DC]
    if test:
        df.to_csv('EncapsulteTest2.csv',index=None)
    return DCs

def EncapsulteTest3(psize,dgn,pdo:PDO,test=False):
    global DG
    N = 1
    if test:
        N=5
    df = pd.DataFrame(columns=['psize','dgn','time'])
    atts = [str(i)+" and " for i in range(psize[-1])]
    DCs = [0] * len(psize)
    
    for i in range(len(psize)):
        policy = "".join(atts[0:psize[i]-1])
        policy += str(psize[i]-1)
        t1 = time.time()
        for j in range(N):
            DCI,A,DC = pdo.Encapsulate(mpk,DG[0:dgn[i]],policy)
        t = (time.time()-t1)/N

        df.loc[i] = [psize[i],dgn[i],t]
        DCs[i] = [DCI,A,DC]
    if test:
        df.to_csv('EncapsulteTest3.csv',index=None)
    return DCs

def TaskIssueTest(pdo:PDO,mpk,A,Is,test=False):
    res = []
    N = 1
    if test:
        N=5
    df = pd.DataFrame(columns=['Is','time'])
    I = [i for i in range(Is[-1])]
    t = datetime.datetime.now().timestamp() + datetime.timedelta(days=1).total_seconds()
    for i in range(0,len(Is)):
        t1 = time.time()
        for j in range(N):
            DCI_PDO1,task1,R1,D1,A1 = pdo.TaskIssue(mpk,"SP9",DG,I[0:Is[i]],A,t)
        t = (time.time()-t1)/N
        df.loc[i] = [Is[i],t]

        res.append(task1)
    if test:
        df.to_csv('TaskIssueTest.csv',index=None)
    return res

def TestDecDC1(pdo:PDO,sp:SP,mpk,Is,test=False):
    policy_str = u'1 and 2 and 3'
    DCI,A,DC = pdo.Encapsulate(mpk,DG,policy_str)

    N = 1
    if test:
        N=100
    df = pd.DataFrame(columns=['dgn','time'])
    I = [i for i in range(Is[-1])]
    
    t = datetime.datetime.now().timestamp() + datetime.timedelta(days=1).total_seconds()
    for i in range(0,len(Is)):
        
        t1 = 0
        for j in range(N):
            DCI_PDO1,task1,R1,D1,A1 = pdo.TaskIssue(mpk,"SP9",DG,I[0:Is[i]],A,t)
            PT1 = sp.AccessDc(mpk,DCI_PDO1,task1,pdo.pk)
            t2 = time.time()
            res = sp.DecDC(mpk,DCI_PDO1,DC,task1,PT1)
            t1 += time.time()-t2

            for k in range(len(res)):
                assert DG[k]==res[k]
        print(t1)
        tall = t1/N
        df.loc[i] = [Is[i],tall]
    if test:
        df.to_csv('TaskDecDC1.csv',index=None)

def TestDecDC2(pdo:PDO,sp:SP,DCs,mpk,psize,test=False):
    N = 1
    if test:
        N=10
    df = pd.DataFrame(columns=['psize','time'])
    
    
    t = datetime.datetime.now().timestamp() + datetime.timedelta(days=1).total_seconds()
    
    atts = [str(i)+" and " for i in range(psize[-1])]
    for i in range(len(psize)):
        policy = "".join(atts[0:psize[i]-1])
        policy += str(psize[i]-1)
        DCI,A,DC = pdo.Encapsulate(mpk,DG,policy)
        
        t1 = 0
        for j in range(N):
            DCI_PDO1,task1,R1,D1,A1 = pdo.TaskIssue(mpk,"SP9",DG,[m for m in range(10)],A,t)
            
            PT1 = sp.AccessDc(mpk,DCI,task1,pdo.pk)
            t2 = time.time()
            res = sp.DecDC(mpk,DCI,DC,task1,PT1)
            t1 += time.time()-t2
            
            for k in range(len(res)):
                assert DG[k]==res[k]
        print(t1)
        tall = t1/N
        df.loc[i] = [Is[i],tall]
    if test:
        df.to_csv('TaskDecDC2.csv',index=None)

def TestDecDC3(pdo:PDO,sp:SP,DCs,mpk,psize,test=False):
    N = 1
    if test:
        N=10
    df = pd.DataFrame(columns=['psize','dgn','time'])
    
    
    t = datetime.datetime.now().timestamp() + datetime.timedelta(days=1).total_seconds()
    for i in range(len(psize)):
        
        t1 = 0
        for j in range(N):
            DCI_PDO1,task1,R1,D1,A1 = pdo.TaskIssue(mpk,"SP9",DG[0:psize[i]],[m for m in range(10)],DCs[i][1],t)
            
            PT1 = sp.AccessDc(mpk,DCs[i][0],task1,pdo.pk)
            t2 = time.time()
            res = sp.DecDC(mpk,DCs[i][0],DCs[i][2],task1,PT1)
            t1 += time.time()-t2
            
            for k in range(len(res)):
                assert DG[k]==res[k]
        print(t1)
        tall = t1/N
        df.loc[i] = [psize[i],psize[i],tall]
    if test:
        df.to_csv('TaskDecDC3.csv',index=None)

def test():
    pairing_group = PairingGroup('MNT224')
    n = 1
    ta = TA(pairing_group)

    pairing_group.InitBenchmark()
    pairing_group.StartBenchmark(["RealTime"])
    for i in range(n):
        mpk = ta.setup()
    pairing_group.EndBenchmark()
    print("Setup:",pairing_group.GetBenchmark("RealTime")/n)

    attr_list = ['1','2','3']
    pairing_group.InitBenchmark()
    pairing_group.StartBenchmark(["RealTime"])
    for i in range(n):
        sk_SP1 = ta.key_gen_SP(mpk,"SP1",attr_list)
    pairing_group.EndBenchmark()
    print("KeyGenSP:",pairing_group.GetBenchmark("RealTime")/n)

    sp1 = SP("SP1",mpk,sk_SP1)

    
    pdo1 = PDO("PDO1",mpk)
    t = [0,0]
    for i in range(n):
        t1 = time.time()
        psi = pdo1.GenPsi(mpk)
        t[0] += time.time()-t1

        t2 = time.time()
        beta,pk = ta.PKeyGenPDO(psi)
        t[1] += time.time()-t2

        t3 = time.time()
        pdo1.SKeyGenPDO(beta,pk)
        t[0] += time.time()-t3
    print("KenGenPDO(PDO):",t[0]/n,"KenGenPDO(TA):",t[1]/n)

    DG = generate_data_granules(5,128)
    
    policy_str = u'((1 and 3) and (2 OR 4))'
    enc_start = time.time()
    for i in range(n):
        DCI,A,DC = pdo1.Encapsulate(mpk,DG,policy_str)
    print("encapsulate:",(time.time()-enc_start)/n)
    

    cs = CS()
    cs.put_DC(DCI,DC)
    print(DG)
    I = [0,1,2,3,4]
    t = datetime.datetime.now().timestamp() + datetime.timedelta(days=1).total_seconds()
    enc_start = time.time()
    for i in range(n):
        DCI,task,R,D,A_new = pdo1.TaskIssue(mpk,"SP1",DG,I,A,t)
    print("TaskIssue:",(time.time()-enc_start)/n)
    
    
    P_T1 = sp1.AccessDc(mpk,DCI,task,pdo1.pk)

    print(sp1.DecDC(mpk,DCI,DC,task,P_T1))


def spaceKey(sp:SP):
    res = 0

    for v in sp.sk['sk1'].values():
        res += v.__sizeof__()
    
    res += sp.sk['sk2'].__sizeof__()
    res += sp.sk['sk3'].__sizeof__()
    res += sp.sk['sk4'].__sizeof__()

    return res

def spaceCT(ct):
    res = 0
    
    res += ct['policy'].__sizeof__()

    res += ct['C1'].__sizeof__()
    res += len(pickle.dumps(ct['C2']))
    res += ct['C3'].__sizeof__()
    for v in ct['C4'].values():
        res += v.__sizeof__()
    res += ct['V'].__sizeof__()

    return res

def spaceTask(task):
    res = 0
    
    res += task['T1'].__sizeof__()
    res += task['T2'].__sizeof__()
    for i in task['Tw']:
        res += i[0].__sizeof__()
        res += i[1].__sizeof__()

    return res



if __name__ == "__main__":
    '''
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

    N1 = 1
    #PDO register
    pdo1 = PDO("PDO1",mpk)
    t1 = time.time()
    for i in range(N1):
        psi = pdo1.GenPsi(mpk)
    print((time.time()-t1)/N1)
    t1 = time.time()
    for i in range(N1):
        beta,pk = ta.PKeyGenPDO(psi)
    print((time.time()-t1)/N1)
    t1 = time.time()
    for i in range(N1):
        pdo1.SKeyGenPDO(beta,pk)
    print((time.time()-t1)/N1)
    
    
    #PDO encapsulate data
    DG = generate_data_granules(U,L)
    #DG = [int.from_bytes(u'zmn sooocute!'.encode(),'big'),int.from_bytes(u'hduer!'.encode(),'big'),int.from_bytes(u'sk:1243'.encode(),'big')]
    policy_str = '((1 and 3) and (2 OR 4))'
    DCI,A,DC = pdo1.Encapsulate(mpk,DG,policy_str)
    cs.put_DC(DCI,DC)

    #PDO issues task
    I = [0,1,2]
    t = datetime.datetime.now().timestamp() + datetime.timedelta(days=1).total_seconds()
    DCI_PDO1,task1,R1,D1,A1 = pdo1.TaskIssue(mpk,"SP1",DG,I,A,t)
    cs.put_RD(DCI_PDO1,R1,D1)

    #SP Decrypt DC
    N2 = 1
    t1 = time.time()
    for i in range(N2):
        P_T1 = sp1.AccessDc(mpk,DCI_PDO1,task1,pdo1.pk)
    print((time.time()-t1)/N2)

    #cs check P_T1 and expired time
    DC_CS1 = cs.DownloadDC(DCI_PDO1,P_T1)
    #cs update DC
    N2 = 1
    t1 = time.time()
    for i in range(N2):
        DCI_CS2,DC2 = cs.UpdateDC(mpk,DCI_PDO1)
    print((time.time()-t1)/N2)
    #Dec
    res = sp1.DecDC(mpk,DCI_PDO1,DC_CS1,task1,P_T1)
    print("DG:",DG)
    print("res1:",res[0].to_bytes(L//8,"big"),res[1].to_bytes(L//8,"big"),res[2].to_bytes(L//8,"big"))
    
    #Dec (old task and new DC)
    res = sp1.DecDC(mpk,DCI_PDO1,DC2,task1,P_T1)
    print("res1(old task and new DC):",res[0].to_bytes(L//8,"big"),res[1].to_bytes(L//8,"big"))

    #SP2 register(satisfy the access policy and steal(or collusion with the user who has tasks) a task)
    attr_list = ['1','2','3']
    sk_SP2 = ta.key_gen_SP(mpk,"SP2",attr_list)
    sp2 = SP("SP2",mpk,sk_SP2)

    #SP2 Decrypt DC
    P_T1_2 = sp2.AccessDc(mpk,DCI_PDO1,task1,pdo1.pk)
    res_2 = sp2.DecDC(mpk,DCI_PDO1,DC_CS1,task1,P_T1_2)
    print("res2(1):",res_2[0].to_bytes(L//8,"big"),res_2[1].to_bytes(L//8,"big"))

    #SP2 Decrypt DC(SP1 send the P_T1)
    res_2 = sp2.DecDC(mpk,DCI_PDO1,DC_CS1,task1,P_T1)
    print("res2(2):",res_2[0].to_bytes(L//8,"big"),res_2[1].to_bytes(L//8,"big"))


    #issue task to sp2
    DCI_PDO2,task2,R2,D2,A2 = pdo1.TaskIssue(mpk,"SP2",DG,[2],A1,t)
    cs.put_RD(DCI_PDO2,R2,D2)
    
    
    P_T1_2 = sp2.AccessDc(mpk,DCI_PDO2,task2,pdo1.pk)
    DC_CS2 = cs.DownloadDC(DCI_PDO2,P_T1_2)
    
    DCI_CS3,DC3 = cs.UpdateDC(mpk,DCI_PDO2)
    res_3 = sp2.DecDC(mpk,DCI_PDO2,DC_CS2,task2,P_T1_2)
    
    print("res2(3):",res_3[0].to_bytes(L//8,"big"))'''
    
    pairing_group = PairingGroup('MNT224')
    n = 1
    
    #init ta
    ta = TA(pairing_group)
    mpk = ta.setup()

    
    an = [i for i in range(10,110,10)]
    print("test key gen sp, number of attributes",an)
    sps:List[SP] = KeyGenSPTest(an,mpk,ta)
    
    pdo = PDO("PDO1",mpk)
    
    print("test key gen pdo")
    t1 = time.time()
    psi = pdo.GenPsi(mpk)
    t1 = time.time()-t1
    t2 = time.time()
    beta,pk = ta.PKeyGenPDO(psi)
    t2 = time.time()-t2
    t3 = time.time()
    pdo.SKeyGenPDO(beta,pk)
    t3 = time.time()-t3
    print("t1:%f,t2:%f,t3:%f-->DO:%f,TA:%f"%(t1,t2,t3,t1+t3,t2))
    
    dgn = [i for i in range(10,110,10)]
    print("test encapsulate: policy size = 3, number of data granules(L=128) :",dgn)
    DCs_1 = EncapsulteTest1(dgn,pdo,False)
    psize = [i for i in range(10,110,10)]
    print("test encapsulate: policy size = ",psize,", number of data granules(L=128) : 10")
    DCs_2 = EncapsulteTest2(psize,pdo,False)
    print("test encapsulate: policy size = ",psize,", number of data granules(L=128) : ",dgn)
    DCs_3 = EncapsulteTest3(psize,dgn,pdo,False)

    
    Is = [i for i in range(10,110,10)]

    df = pd.DataFrame(columns=['dgn','size'])

    
    tasks = TaskIssueTest(pdo,mpk,DCs_3[9][1],Is)
    count = 0
    for i in tasks:
        df.loc[count] = an[count],spaceTask(i)
        count+=1
    #df.to_csv('task.csv',index=None)
    

    
    
    
    

    

    

    
    
    

    

    

    

    
    

    


   

    


    




    
    