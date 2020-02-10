# infinimerge
## utility to handle incremental merge backups target
### Execution

./infinimerge.sh -v|--validate

./infinimerge.sh -l|--list _instnace_

./infinimerge.sh -c|--capture _instance name_ -r|--retention ["daily"|"yearly"|"mothly"]

./infinimerge.sh -e|--expose _snapshotOfInstance_

./infinimerge.sh -u|--unexpose _snapshotOfInstance_

### options

#### -h|--help
display usage

#### -v|--validate 
validates configuration
* verifies target directory for backup exists and mounted
* verifies expose directory exists
* verifies init file (password file) exist and readable
* verifies no open files on target directory

#### -l|--list _instance_
list available snapshot for an instnace

#### -c|--capture _instance_
creates a snapshot, lock it for desired instnace, potentially assign retention policy.

#### -e|--expose _snapshotOfInstance_ 
exposing an snapshot - create a snapshot for a locked snapshot, create an export and mount it

#### -u|--unexpose _snapshotOfinstnace_
unexposing an snapshot - umounts, delete export and snapshot



### Notes
* validate can run as a pre-step for other options (create, expose or delete)
* other options (create, expose, unexpose or list) cannot run in conjunction

### Setup 
* in order to allow running mount/umounts with non-root user the following should be on suoders file:
_%staff ALL=(ALL) NOPASSWD: /usr/bin/mount,/usr/bin/umount,/usr/sbin/mount,/usr/sbin/umount_
*Credentials - password can either be entered to .init file by executing 
echo <password> | base64 > .init 
OR 
use infinishellrc file:
_infinishell --write-default-config_
edit the file and replace 
__username__ with ibox username
__password__ with user password
__default_address__ with the InfiniBox address

* Create a config file with the following.

ibox='ibox2811' ## replace with IBOX name/passowrd. ignored if use_cred_file != "YES"

ibox_user='iweisman' --> replace with IBOX user. ignored if use_cred_file != "YES"

lock_duration=1hours --> use infinibox syntax to present lock time - 1hours, 1days 1years etc

nfs_ip='172.20.37.53' --> replace with NAS network space address

expose_dir=/INFINI/snaps --> directory for mounting snaps. should be with permission to write for the user running the script

target_dir=/INFINI/target --> directory for mounting restored image.  should be with permission to write for the user running the script

snap_prefix='infinimerge' --> an prefix to add to newly created snaps

use_sudo="/usr/bin/sudo" --> path for sudo

target_prefix="BackupTarget" --> prefix for FS name based on instnace name.

pool="perf" --> pool to check for free space before alerting the user

pool_threshold=10 --> a threshold for selected pool

use_cred_file="NO" --> whether or not to use infinishellrc

__configuration file name should be "config" and should reside on the same directory as the script__


# infinimerge
## snapc.py
_This script should run from infinimerge server_
_usage: python3 snapc.py [-h] [-s|--setup InfiniBox FQDN/IP] [-m|--mode simulation|delete]_
          -h - displays help
          -s - setup InfiniBox name, user and password
          -m - run mode (simulation or actual delete)
### notes
* setup (-s|--s) and mode (-m|--mode) cannot be used in conjunction