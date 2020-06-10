#!/usr/bin/ksh93
#
# incre_merge
## utility to handle incremental merge backups target
# By Itai Weisman, Solution Engineering team leader, INFINIDAT
# iweisman@infinidat.com +972-54-6755444
# Who          | When              | What
# ---------------------------------------------
# Itai Weisman | November 27 2018 | Genesis
# Itai Weisman | December 19 2019 | added support for Non-root user
# Itai Weisman | January   7 2019 | added tests for failed mount/unmount options
# Itai Weisman | Februrary 3 2019 | changed list snapshot ordering
# Itai Weisman | October 10 2019  | allowing day based retention
# 
#
### Execution
#
#./infinimerge.sh -v|--validate
#
#./infinimerge.sh -l|--list _instnace_
#
#./infinimerge.sh -c|--capture _instnace name_ [-r|--retention "daily"|"weekly"|"monthly"] <-L|--lock> 
#
#./infinimerge.sh -e|--expose _snapshotOfInstance_
#
#./infinimerge.sh -u|--unexpose _snapshotOfInstance_
#
### options
#
#### -h|--help
#display usage
#
#### -v|--validate 
#validates configuration
#* verifies target directory for backup exists and mounted
#* verifies expose directory exists
#* verifies init file (password file) exist and readable
#* verifies no open files on target directory

#### -l|--list _instnace_
#list available snapshot for an instnace
#
#### -c|--capture _instance_
#creates a snapshot, lock it for desired instnace
#
#### -e|--expose _snapshotOfInstance_ 
#exposing an snapshot - create a snapshot for a locked snapshot, create an export and mount it
#### -u|--unexpose _snapshotOfinstnace_
#unexposing an snapshot - umounts, delete export and snapshot
### Notes
#* validate can run as a pre-step for other options (create, expose or delete)
#* other options (create, expose) must have an instance name and cannot run in conjunction
log=`basename $0`.log
echo >> ${log} 2>&1
echo >> ${log} 2>&1
echo >> ${log} 2>&1
date >> ${log} 2>&1
echo "Started " | tee -a ${log}
os=`uname`
if [ "$os" == "SunOS" ] ; then
   print_cmd="print"
elif [ "$os" == "Linux" -o "$os" == "AIX" ] ; then
   print_cmd="printf"
else
    echo "Operating system isn't supported" | tee -a ${log}
    exit 200
fi

config="./config"
if [ ! -f $config ] ; then
  echo "config file couldn't found ; exiting" | tee -a ${log}
  exit 100
fi
. $config
if [ "$mode" == "volume" -a "$os" == "Linux" ] ; then
  func="./incre_merge2-volume"
elif [ "$mode" == "filesystem" ] ; then
  func="./incre_merge2-filesystem"
else 
  $print_cmd "mode parameter is set incorrectly or selected mode not supported" | tee -a ${log}
  exit 20
fi
if [ -f $func ] ; then
.  $func
else
   echo "function file ($func)r does not exist ; exiting" | tee -a ${log}
   exit 5
fi
#$print_cmd ok
 
set_retention="NO"
LOCK="NO"
POSITIONAL=()
functional=0
non_functional=0
usage() 
{
	echo "usage:"
	echo "`basename $0`"
	echo " -v|--validates "
	echo "    validates configuration"
	echo " -e|--expose <instance_name>"
	echo "	expose an instnace" 
	echo " -u|--unexpose <instance_name>"
	echo "   unexpose an instance"
	echo " -c|--capture <instance_name> -r|--retenion days [-L|--LOCK] "
        echo "	capture a snapshot for an instance for a retetion , potentially with setting up a lock"
    echo " -l|--list <instance_name>"
        echo "	list available snapshot(s) for an instance"
	echo "  -h|--help "
        echo "	shows this help "

}
if [[ $# -eq 0 ]] ; then
      usage
      exit 2
fi 

while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -v|--validate)
    VALIDATES="YES"
    shift # past argument
    ;;
    -L|--LOCK)
    LOCK="YES"
    shift
    ;;
    -e|--expose)
    FS="$2"
    if [ -z "$FS" ] ; then
       $print_cmd "expose option requires an instance name ; exiting "| tee -a ${log}
       usage
       exit 4
       fi
    operation="expose"
    shift # past argument
    shift # past value
    ((functional=$functional+1))
    ;;
    -u|--unexpose)
    FS="$2"
    if [ -z "$FS" ] ; then
       $print_cmd "unexpose option requires an instance name ; exiting " | tee -a ${log}
       usage
       exit 4
       fi
    operation="unexpose"
    shift # past argument
    shift # past value
    ((functional=$functional+1))
    ;;
    -r|--retention)
    retention=$2
    if [ -z "${retention//[0-9]}" ] && [ -n "$retention" ] ; then 
    set_retention="YES"
    shift # past argument
    shift # past value
    else
        $print_cmd "retention must be provided as an integer " | tee -a ${log}
        usage 
        exit 3
    fi
    ;;
    -c|--capture)
    FS="$2"
    if [ -z "$FS" ] ; then
       $print_cmd "capture option requires an instance name ; exiting" | tee -a ${log}
       usage
       exit 4
       fi
    operation="create"
    shift # past argument
    shift # past value
    ((functional=$functional+1))
    ;;
    -l|--list)
    FS="$2"
    if [ -z "$FS" ] ; then
       $print_cmd "snap list option requires an instance name ; exiting "| tee -a ${log}
       usage
       exit 4
       fi
    operation="list"
    shift # past argument
    shift # past value
    ((functional=$functional+1))
    ;;
    *)    # unknown option
    non_functional=1
    POSITIONAL+=("$1") # save it in an array for later
    shift # past argument
    ;;
esac
done
if [ $non_functional -eq 1 -o $functional -gt 1 ] ; then
	usage
	exit 2
fi
if [ "$VALIDATES" == "YES" ] ; then
	validates
fi
case $operation in 
     expose)
	expose $FS
	;;
     unexpose)
	unexpose $FS
	;;
     create)
     if [ "$set_retention" == "NO" ] ; then
         echo "capture requires retention set "| tee -a ${log}
         usage
         exit 3
         fi
	create_snap $FS $LOCK
        ;;
             list)
	list_snaps $FS
        ;;
esac


