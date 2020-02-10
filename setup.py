import getpass
import zlib
import sys
import os
from base64 import urlsafe_b64encode as b64e, urlsafe_b64decode as b64d
init="."+os.path.basename(sys.argv[0])+".ini"
creds="."+os.path.basename(sys.argv[0])+".creds"
def o (data: bytes) -> bytes:
    return b64e(zlib.compress(data, 9))
def u(ob: bytes) -> bytes:
    return zlib.decompress(b64d(ob))
def store_c(u,p,b,init,creds):
    try:
           it=open(init,"wb") 
           un=open(creds,"w")
           it.write(o(p.encode()))
           un.write(u)
           un.write("\n")
           un.write(b)
           it.close()
           un.close()

    except Exception as E:
           print ("Cannot",E)
           sys.exit(8)
def read_c(creds,ini):
    try:
           h=open(ini,"rb")
           i=open(creds,"r")
           l=h.read()
           p=(u(l)).decode()
           us=i.readlines()
           return us[0].strip(),us[1],p
    except Exception as E:
           print ("cannot 2",E)
