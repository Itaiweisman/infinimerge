#
# snapc.py
## utility to handle incremental merge backups retention
# By Itai Weisman, Solution Engineering team leader, INFINIDAT
# iweisman@infinidat.com +972-54-6755444
# Who          | When              | What
# ---------------------------------------------
# Itai Weisman | November 30 2018 | Genesis
# Itai Weisman | December 2 2019  | bug fixes
# Itai Weisman | December 10 2019 | added simulation mode

# 
#

from prettytable import PrettyTable
import sys
import os.path
from os import path
import argparse
from setup import *
from infinisdk import InfiniBox, Q
import arrow
import json
pools=[]
mode="status"
facility="infinimerge"
config_file="config.json"
now=arrow.now()
print ("Started at {}".format((now.to('local').format('YYYY-MM-DD HH:mm'))))
def get_args():
    """
    Supports the command-line arguments listed below.
    """
    parser = argparse.ArgumentParser(description="Running snap retention")
    parser.add_argument('-s', '--setup', nargs=1,metavar="InfiniBox FQDN/IP", required=False, help='setup account to use')
    parser.add_argument('-m', '--mode', nargs=1,metavar="status|delete", required=False, help='purge expired backups')
    args = parser.parse_args()
    return args
def safe_cast(val, default=0):
    try:
        if (int(val) and int(val) > 0):
            return int(val)
    except (ValueError, TypeError):
        return default
def read_config(config):
         with open(config) as f:
              config = json.load(f)
         return config
def iter_snap(config,box,mode,dataset):
    if dataset == "volumes":
        objc=box.volumes
        print ("Volumes:")
    elif dataset == "filesystems":
        print ("Filesystems:")
        objc=box.filesystems
    else:
        return False

    instancePref=config['FSInstnacePrefix']+"_"
    if mode == 'status':
        t = PrettyTable(['instance name', 'creation timestamp', 'snapshot name', 'lock state', 'expiration date', 'action'])
    for s in objc.find(type='snapshot').to_list():
        if (s.get_metadata_value("host.created_by",default=None) == facility and s.get_parent().get_type()=='MASTER' ):
            if ( s.get_children()  or (s.get_dataset_type() == 'FILESYSTEM' and s.get_exports()) or (s.get_dataset_type()=='VOLUME' and s.is_mapped()) ):
                in_use=True
                ToDel="IN-USE"
            elif ( not s.get_children() and not (s.get_dataset_type() == 'FILESYSTEM' and s.get_exports() )and not (s.get_dataset_type()=='VOLUME' and s.is_mapped()) ):
                in_use=False
                ToDel=False
            else:
                in_use=None
            #print(s.get_name(), s.get_metadata_value("retention",default=None))
            retention=safe_cast(s.get_metadata_value("retention",default='NotSet'))
            created_at=s.get_created_at() 
            pool=s.get_pool()
            pools.append(pool)

            if retention:
               #cutoff=now.shift(days=-policies[retention])
                cutoff=now.shift(days=-retention)
                keepdate=created_at.shift(days=+retention).to('local').format('YYYY-MM-DD HH:mm')
                if created_at < cutoff and not in_use:
                    Delete=True
                    ToDel="TO-DELETE"
                else:
                    Delete=False
                    if not ToDel:
                        ToDel="TO-KEEP"
            else:
                cutoff="N/A -illegal retention"
                keepdate="N/A - illegal retention"
                ToDel="IGNORE"
               
            if mode=='status':
                instance=s.get_parent().get_name().replace(instancePref,'')
                    #print ("{}  | {}  | {}  | {}  | {}  | {} | {}".format(s.get_parent().get_name(), created_at, s.get_name(), s.get_lock_state(),keepdate,ToDel ))
                t.add_row([instance, created_at.to('local').format('YYYY-MM-DD HH:mm'), s.get_name(), s.get_lock_state(),keepdate,ToDel] )
                           #print ("created at {}".format(s.get_created_at()))
                           #print ("policy is {}".format(retention))
                           #print ("expiration date {}".format(cutoff))
                           #print (cutoff)
                           #print ("{} to delete".format(s.get_name()))
            if mode=='delete' and retention and not in_use:
                if Delete:
                        
                 print ("DELETING", s.get_name())
                 s.delete()
    if mode=="status":
        print(t)

def tests(*args):
     for file in args:
         if not path.exists(file):
             print ("{} does not exist".format(file))
             sys.exit(3)
def run(*args, **kwargs):
        user,box,password=args
        simulation=False
        if kwargs["mode"] == 'delete':
                print("delete-snapshots")
        elif kwargs["mode"] == 'status':
                print ("status")
                simulation=True
                #t = PrettyTable(['instance name', 'creation timestamp', 'retention days', 'snapshot name', 'lock state', 'expiration date', 'action'])
                #print ("instance name \t | creation timestamp \t | retention days \t | snapshot name \t |  lock state \t | expiration date \t | action")
        else:
                usage()
                exit()
        config=read_config(config_file)
        auth=(args[0],args[2])
        b=InfiniBox(args[1],auth=auth)
        b.login()
        iter_snap(config,b,kwargs["mode"],"filesystems")
        iter_snap(config,b,kwargs["mode"],"volumes")

        
def set_c():
    print ("Enter User:")
    user=input()
    print ("setting up password for {}".format(user))
    return user,getpass.getpass()

def usage():
    print("usage: {} [-h] [-s InfiniBox FQDN/IP] [-m status|delete]".format(sys.argv[0]))
def check_args(args):
    if (args.setup and args.mode) or ( not args.setup and not args.mode):
        usage()
        sys.exit(2)
    if args.setup:
        u,p=set_c()
        store_c(u,p,args.setup[0],init,creds)
    if args.mode:
        #tests(policies,creds,init)
        tests(config_file,creds,init)
        u,b,p=read_c(creds,init)
        run(u,b,p,mode=args.mode[0])
args=get_args()
check_args(args)
print("\n\n")
pools_set=set(pools)
print ("Space Usage Summary:")
p = PrettyTable(['pool', 'physical capapcity (TB)', 'free capacity (TB)', 'used capacity (TB)'])


for pool in pools_set:
    name=pool.get_name()
    phys=round(pool.get_field('physical_capacity').bits/8/1000/1000/1000/1000,2)
    free=round(pool.get_field('free_physical_capacity').bits/8/1000/1000/1000/1000,2)
    used=round(pool.get_field('allocated_physical_capacity').bits/8/1000/1000/1000/1000,2)
    
    p.add_row([name,phys,free, used])
print (p)
