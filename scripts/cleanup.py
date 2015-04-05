#!/usr/bin/python

from collections import namedtuple # Requires at least Python 2.6.
import datetime
import getopt
import math
import os
import re # Regular expressions.
import shutil # For rmtree().
import sys

g_bDryRun = True;
g_cbDupesTotal = 0;
g_cbDupesRemoved = 0;
g_sLogFile = '';
g_bRecursive = True;
g_cVerbosity = 0;

tFileDupe = namedtuple('tFileDupe', 'ext, prio');

arrVideos = [ tFileDupe('mkv', 0), 
              tFileDupe('avi', 10),
              tFileDupe('wmv', 50) ];

arrDirsToDelete = [ '.*/_UNPACK_*' ];

sDir = "/media/ds212/movies" #sys.argv[1]

# Taken from: http://stackoverflow.com/questions/5194057/better-way-to-convert-file-sizes-in-python
# Slightly modified to handle byte sizes as well.
def convertSize(size):
    if size:
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB");   
        i = int(math.floor(math.log(size,1024)));
        p = math.pow(1024,i);
        s = round(size/p,2);
        if (s > 0):
            return '%s %s' % (s,size_name[i]);
    return '0B';

def getFileModTime(sFile):
    mTime = os.path.getmtime(sFile);
    return datetime.datetime.fromtimestamp(mTime);

def deleteFile(sFile):
    global g_bDryRun;
    print("\tDeleting file: %s" % sFile);
    if g_bDryRun:
        return;
    os.remove(sFile);

def deleteDir(sDir, fRecursive):
    global g_bDryRun;
    print("\tDeleting directory: %s" % sDir);
    if g_bDryRun:
        return;
    if fRecursive:
        shutil.rmtree(sDir, ignore_errors = False);
    else:
        os.rmdir(sDir);

def cleanupDupes(sDir, fRecursive):
    global g_cbDupesTotal;
    for sCurDir, aSubDirs, aFiles in os.walk(sDir):
        for sDir in aSubDirs:
            cleanupDupes(sDir, fRecursive);
        arrDupes = [];
        for sFile in aFiles:
            sFileAbs = os.path.join(sCurDir, sFile);
            sName, sExt = os.path.splitext(sFileAbs);
            sName = sName.lower();
            sExt = sExt.lower().translate(None, ".");
            for curVideo in arrVideos:
                if curVideo.ext == sExt:
                    arrDupes.append(sFileAbs);
        if len(arrDupes) >= 2:
            print("Directory \"%s\" contains %d entries:" % (sCurDir, len(arrDupes)));
            newestTime = datetime.datetime(1970, 01, 01);
            sFileNewest = '';
            for curDupe in arrDupes:
                modTime = getFileModTime(curDupe);
                print("\t%s (%s)" % (curDupe, modTime));
                if modTime > newestTime:
                    sFileNewest = curDupe;
                    newestTime  = modTime;
            if sFileNewest:
                print("\tNewest file: %s" % sFileNewest);
                for curDupe in arrDupes:
                    if curDupe != sFileNewest:
                        g_cbDupesTotal += os.path.getsize(curDupe);
                        deleteFile(curDupe);
            else:
                print("\tWarning: Unable to determine newest file!");
        
        # Delete empty directories.
        if os.path.isdir(sCurDir) and len(os.listdir(sCurDir)) == 0:
            print("Directory \"%s\" is empty" % sCurDir);
            deleteDir(sCurDir, False);           
        else:
            # Delete unwanted junk.
            for sRegEx in arrDirsToDelete:
                if   re.compile(sRegEx).match(sCurDir) \
                and  sCurDir \
                and  sCurDir != "/":
                    print("Directory \"%s\" is junk" % sCurDir);
                    deleteDir(sCurDir, True);

        if not fRecursive:
            break;

def main():
    global g_cbDupesTotal;
    global g_bDryRun;
    global g_bRecursive;

    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help"]);
    except getopt.error, msg:
        print msg;
        print "for help use --help"
        sys.exit(2);

    for o, a in opts:
        if o in ("-h", "--help"):
            print __doc__
            sys.exit(0);

    if g_bDryRun:
        print("*** Dryrun mode -- no files/directories deleted! ***");

    cleanupDupes(sDir, g_bRecursive);

    print("Total dupes: %s (%ld bytes)" % (convertSize(g_cbDupesTotal), g_cbDupesTotal));

if __name__ == "__main__":
    main();
