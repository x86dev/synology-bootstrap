#!/usr/bin/python

from collections import namedtuple # Requires at least Python 2.6.
import datetime
import getopt
import math
import os
import re # Regular expressions.
import shutil # For rmtree().
import sys

g_fDryRun = False;
g_cDupesTotal = 0;
g_cbDupesTotal = 0;
g_cbDupesRemoved = 0;
g_sLogFile = '';
g_fRecursive = False;
g_cVerbosity = 0;

tFileDupe = namedtuple('tFileDupe', 'ext, prio');

arrVideos = [ tFileDupe('mkv', 0), 
              tFileDupe('avi', 10),
              tFileDupe('wmv', 50) ];

arrDirsToDelete = [ '.*/_UNPACK_*' ];

arrFileExtsToDelete = [ 'url', 'nzb', 'exe', 'bat', 'cmd', 'scr', 'rar', 'zip' ];

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

def getModTime(sPath):
    mTime = os.path.getmtime(sPath);
    return datetime.datetime.fromtimestamp(mTime);

def deleteFile(sFile):
    global g_fDryRun;
    print("\tDeleting file: %s" % sFile);
    if g_fDryRun:
        return;
    os.remove(sFile);

def deleteDir(sDir, fRecursive):
    global g_fDryRun;
    print("\tDeleting directory: %s" % sDir);
    if g_fDryRun:
        return;
    if fRecursive:
        shutil.rmtree(sDir, ignore_errors = False);
    else:
        os.rmdir(sDir);

def fileIsMultipart(sDir, sFile):
    pass;

def cleanupDupes(sDir, fRecursive):
    global g_cDupesTotal;
    global g_cbDupesTotal;
    for sCurDir, aSubDirs, aFiles in os.walk(sDir):
        for sDir in aSubDirs:
            cleanupDupes(sDir, fRecursive);
        mtimeDir = os.path.getmtime(sCurDir);
        arrDupes = [];
        for sFile in aFiles:
            sFileAbs = os.path.join(sCurDir, sFile);
            sName, sExt = os.path.splitext(sFileAbs);
            sName = sName.lower();
            sExt = sExt.lower().translate(None, ".");
            for curVideo in arrVideos:
                if curVideo.ext == sExt:                
                    arrDupes.append(sFileAbs);
            for curExt in arrFileExtsToDelete:
                if curExt == sExt:
                    print("File \"%s\" is junk" % sFileAbs);
                    deleteFile(sFileAbs);

        if len(arrDupes) >= 2:
            print("Directory \"%s\" contains %d entries:" % (sCurDir, len(arrDupes)));
            newestTime = datetime.datetime(1970, 01, 01);
            sFileNewest = '';
            for curDupe in arrDupes:
                modTime = getModTime(curDupe);
                print("\t%s (%s)" % (curDupe, modTime));
                if modTime > newestTime:
                    sFileNewest = curDupe;
                    newestTime  = modTime;
            if sFileNewest:
                print("\tNewest file: %s" % sFileNewest);
                for curDupe in arrDupes:
                    if      curDupe != sFileNewest \
                    and not fileIsMultipart(sCurDir, curDupe):
                        g_cDupesTotal  += 1;
                        g_cbDupesTotal += os.path.getsize(curDupe);
                        deleteFile(curDupe);
            else:
                print("\tWarning: Unable to determine newest file!");

        # Delete unwanted junk.
        for sRegEx in arrDirsToDelete:
            if   re.compile(sRegEx).match(sCurDir) \
            and  sCurDir \
            and  sCurDir != "/":
                print("Directory \"%s\" is junk" % sCurDir);
                deleteDir(sCurDir, True);
        
        # Delete empty directories.
        if os.path.isdir(sCurDir) and len(os.listdir(sCurDir)) == 0:
            print("Directory \"%s\" is empty" % sCurDir);
            deleteDir(sCurDir, False);           

        # Re-apply directory modification time.
        os.utime(sCurDir, (-1, mtimeDir));

        if not fRecursive:
            break;

def printHelp():
    print("--dryrun");
    print("    Dryrun mode: No files/directories modified or deleted.");
    print("--help or -h");
    print("    Prints this help text.");
    print("--recursive or -R");
    print("    Also processes sub directories.");
    print("-v");
    print("    Increases logging verbosity. Can be specified multiple times.");
    print("\n");

def main():
    global g_cDupesTotal;
    global g_cbDupesTotal;
    global g_fDryRun;
    global g_fRecursive;
    global g_cVerbosity;

    if len(sys.argv) <= 1:
        print "Must specify a path!";
        sys.exit(2);

    sDir = sys.argv[1];

    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help"]);
    except getopt.error, msg:
        print msg;
        print "For help use --help"
        sys.exit(2);

    for o, a in opts:
        if o in ("--dryrun"):
            g_fDryRun = True;
        if o in ("-h", "--help"):
            printHelp();
            sys.exit(0);
        if o in ("-R", "--recursive"):
            g_fRecursive = True;
        if o in ("-v"):
            g_cVerbosity += 1;

    if g_fDryRun:
        print("*** Dryrun mode -- no files/directories deleted! ***");

    cleanupDupes(sDir, g_fRecursive);

    print("Total dupes: %ld (%s)" % (g_cDupesTotal, convertSize(g_cbDupesTotal)));

if __name__ == "__main__":
    main();
