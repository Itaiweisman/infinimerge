# infinimerge
A backup and restore utility for very large Oracle databases that leverages RMAN incremental merge technology 

For Very Large Oracle Databases, InfiniMerge can reduce the backup time by a factor of x30 and the restore time by a factor of x100 

Infinimerge is a backup utility for Oracle databases on the scale of 10s to 100s of TBs. The utility manages InfiniBox/InfiniGuard snapshots to capture RMAN incremental merge backups, provides block-level-incremental-forever backups and near-instant restore. 

## InfiniMerge main features
* 7x9s availability with Active-Active-Active topology
* Performance – Up to 6GB/s BCT throughput (changes only, Incremental forever)
* Can leverage BCT for low servers’ overhead
* Backed-up images are stored in native format
* Near instant switch-to-copy restore, online data move
* Easy recovery/validation, and Dev/Test usage 
* Replication to a remote site with different retention policies per each site
* Snapshot-Lock and Data-encryption
* DBA self service option
* No backup-software licensing costs for 100s TB databases
* NFS, iSCSI, FC supported
* Changed blocks + Compression (No Dedupe, but not significant)
* Management via CLI/API/Host-tools (No GUI)
* Zero data loss recovery option


## Details 

_The infinimerge tool is consist of 2 utilities:_

* _InfiniMerge backup_ (infinimerge.sh) - the utility capture and restore InfiniBox snapshots that contain Oracle Incremental merge backups. 
* _InfiniMerge Life Cycle Manager_ (snapc2.py) - this utility deletes expired backups (snapshots) 
* InfiniMerge backup Manager - Utility to handle incremental merge backups target
**Execution**
./infinimerge.sh -h|–help                                               # Display usage

./infinimerge.sh –v|–validate                                         # Check settings

./infinimerge.sh -c|--capture {instance} –r{DAYS} [-L]   # Take a snap for the given time, SnapLock option

./infinimerge.sh -l|--list {instance}                                  # Show snapshots

./infinimerge.sh -e|--expose {snapshot}                        # Take a Snap-of-snap and Expose it to the host

./infinimerge.sh -u|--unexpose {snapshotOfInstance}   # unmount and delete the Snap-of-snap

##Options
**-h|--help**
display usage

**-v|--validate**
validates configuration

verifies target directory for backup exists and mounted
verifies expose directory exists
verifies init file (password file) exist and readable
verifies no open files on target directory
**-l|--list instance**
list available snapshot for an instnace

**-c|--capture instance**
creates a snapshot, lock it for desired instnace

**-e|--expose snapshotOfInstance**
exposing an snapshot - create a snapshot for a locked snapshot, create an export and mount it

**-u|--unexpose snapshotOfinstnace**
unexposing an snapshot - umounts, delete export and snapshot

##Notes
* validate can run as a pre-step for other options (create, expose or delete)
* other options (create, expose, unexpose or list) cannot run in conjunction

## Initial Setup (One time only):
* On the InfiniGuard system: 
* Create a dedicated pool on the InfiniGuard

pool.create name=InfiniMerge physical_capacity=500TB ssd_cache=no compression=yes emergency_buffer=UNLIMITED

Create a new user on the InfiniGuard as a pool-admin and assign it to the relevant pool 

user.create role=POOL_ADMIN name=InfiniMerge password=InfiniMerge email=a.a@a.com
pool.add_admin user=InfiniMerge pool=InfiniMerge 

Set the NetworkSpace (NAS/iSCSI) or create IBOX host (SAN)

Create volume (Block mode) or filesystem (Filesystem mode), call it {snap_prefix}_{DB_NAME} (example: InfiniMerge_orcl) 
fs.create name=InfiniMerge_orcl size=200TB pool=InfiniMerge snapshot_directory_accessible=yes thin=yes ssd_cache=no compression=yes
vol.create name=InfiniMerge_orcl size=200TB pool=InfiniMerge thin=yes ssd_cache=no compression=yes
Create the host (Block mode only) and set the WWN initiators to it 
 host.create name=<DB_SERVER_NAME>
host.add_port host=<DB_SERVER_NAME> port=<Initiator_1 WWN>,<Initiator_2 WWN>,<Initiator_3 WWN>...

Map (Block mode) or export (Filesystem mode) the volume/filesystem to the host
fs.export.create fs=InfiniMerge_orcl  export_path=/InfiniMerge_orcl 
vol.map host=<DB_SERVER_NAME> vol=InfiniMerge_orcl 

On the Database server: 
Install InfiniShell (for NAS) or HPT (for SAN) on the server 
Set the InfiniGuard credentials to the user

For NAS - use infinishellrc file: 

infinishell --write-default-config

edit the file and replace 

username with ibox username 

password with user password 

default_address with the InfiniBox address

For SAN - use Infinihost 
infinihost credentials set [--system=SYSTEM] [<username> [<password>]]
If iSCSI is used, connect the server to the InfiniGuard iSCSI interface
infinihost iscsi connect <management-ip> [--netspace=NETSPACE] [--hostname=HOSTNAME] [--security=SECURITY] [(--fix | --auto-fix)]
Verify the host settings
infinihost setting check [(--fix | --auto-fix)]
Set the sudoers file to allow running mount/umounts with non-root user: 

%staff ALL=(ALL) NOPASSWD: /usr/bin/mount,/usr/bin/umount,/usr/sbin/mount,/usr/sbin/umount

Set the configuration file - On the directory where infinimerge utility is located, edit the "./config" file (should be aligned with the configuration above)
nfs_ip='172.20.37.53' --> replace with NAS network space address (for NAS option only) 
target_dir=/InfiniMerge/target --> target directory for backups

expose_dir=/InfiniMerge/snaps --> directory for mounting snaps

use_sudo="/usr/bin/sudo" --> path for sudo

snap_prefix=‘InfiniMerge' --> an prefix to add to newly created snaps

target_prefix="InfiniMerge" --> prefix for FS name based on instnace name

pool=“InfiniMerge" --> pool to check for free space before alerting the user

mode=filesystem --> connectivity mode – filesystem or block

Create mountpoints
<expose_dir> 
<target_dir>
chown the mountpoints <oracle_uid>:<oracle_gid> 
<expose_dir> 
<target_dir>
For Block mode, create the filesystem on the volume and mount it to the host 
infinihost volume provision <vol_sizr> --name=BackupTarget_<$ORACLE_SID --thin=yes --filesystem=ext3 --pool=<pool_name> --mount=<target_dir> --system=<ibox> --yes
infinihost volume mount....
For File mode, Mount the InfiniGuard volume or NFS-share to the local filesystem 
Linux: mount (-o nolock) <nfs_ip>:/InfiniMerge_orcl   /InfiniMerge/target
Solaris: mount -F nfs -o rw,bg,hard,nointr,rsize=32768,wsize=32768,proto=tcp,noac,vers=3,forcedirectio <nfs_ip>:InfiniMerge_orcl  /InfiniMerge/target
Add the mount to /etc/fstab (Solaris - /etc/vfstab)





Recovering the database 
If a recovery is needed, it can be recovered from the snapshot 

The following are the required steps to recover the database and performed on the database server

infinimetrge -l [ORACLE_INSTANCE]           #Choose the snapshot that was taken at the requested time
Infinimerge -e [SNAPSHOT_NAME]
RMAN> catalog start with '<PATH to Snapshot>'
RMAN> Switch database to copy; 
SQL> Select file# , fuzzy, checkpoint_time, checkpoint_change# from v$datafile_header;    #Check the [SCN] under the CHECKPOINT_CHANGE column
RMAN> Recover database until [SCN] ; 
RMAN> Alter database open resetlogs ;
The recovery process should take few minutes regardless database size 

InfiniMerge Life Cycle Manager - utility that deletes expired snapshots 
Consumption methods
The InfiniMerge Life Cycle Manager utility is available as a set of Linux RPM, or as a VMware OVF file 

code is available in Gitlab. 

Execution
./snapc.py -m status - shows a table with all the backups/snapshots taken for all the oracle instances, with the expiration date

./snapc.py -m delete - deletes backup/snapshots that are expired 





./snapc.py -s <IBOX name> - one time only, sets the initial settings for this utility (username, password) 

TBD....
