# TD-DCSS
Towards Personal Data Sharing Autonomy: A Task-driven Data Capsule Sharing System (TD-DCSS)

This code repository is the implemention 
for our proposed TD-DCSS scheme. The abstract of our 
paper is shown as follow. 

>Personal data custodian services enable data owners to share their data with data consumers in a convenient manner, anytime and anywhere. However, with data hosted in these services being beyond the control of the data owners, it raises significant concerns about privacy in personal data sharing. Many schemes have been proposed to realize fine-grained access control and privacy protection in data sharing. Whereas their designs focus on the management of system administrators rather than enhancing the data owners’ privacy. In this paper, we introduce a novel task-driven personal data sharing system based on the data capsule paradigm realizing personal data sharing autonomy. Specifically, we present a tamper-resistant data capsule encapsulation method, where data capsule is the minimal unit for independent and secure personal data storage and sharing. Additionally, to realize selective sharing and informed-consent based authorization, we propose a task-driven data sharing mechanism which is resistant to collusion and EDoS attacks. Furthermore, by updating parts of the data capsules, the permissions granted to data consumers can be immediately revoked. In this way, data owners in our system can fully control their data, and share their data autonomously. Finally, we conduct a security and performance analysis, proving that our scheme is correct, sound, and secure, as well as reveals more advantageous features in practicality, compared with the state-of-the-art schemes.

## The Code 
Our implementation based the project available at https://github.com/DoreenRiepel/FABEO, adopting $\ell$ = 128 and utilizing the MNT224 curve. 
And our code, implementes in Python 3.6.9, relies on the Charm 0.50 library, PBC-0.5.14 library. 

## Install & Test
The code of TD-DCSS has been tested with Charm 0.50 and Python 3.6.9 on Ubuntu 18.04.7 LTS. 

To run the code of scheme, you can execute the command 

```python main.py```

The evaluation code can be used by 

```python evaluation.py```

## Reference

[1] J. A. Akinyele, C. Garman, I. Miers, M. W. Pagano, M. Rushanan, M. Green, and A. D. Rubin, “Charm: a framework for rapidly prototyping cryptosystems,” Journal of Cryptographic Engineering, vol. 3, pp. 111–128, 2013.

[2]D. Riepel and H. Wee, “Fabeo: Fast attribute-based encryption with
optimal security,” in Proceedings of the 2022 ACM SIGSAC Conference
on Computer and Communications Security, 2022, pp. 2491–2504.
