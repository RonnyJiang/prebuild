#!/usr/bin/env python
# -*- coding: utf-8 -*-
# lt1.py command groups main python files
#

import sys
import os
import shlex
import subprocess
import shutil
import hashlib
import base64

GIT = 'git'

TOOLS_URL = "Z2Vycml0LmNoaW5hLWxpYW50b25nLmNvbToyMDg5L3ZlbnVzL3Rvb2xzL2NvbW1hbmQ="
TOOLS_REV = "master"

TOOLS_CONFIG = ".lt1.py"
TOOLS_DIR = "tools"
TOOLS_MAIN = "main.py"
TOOLS_GIT = ".git"
TOOLS_CMDS = "internal.py"
TOOLS_LOG = "run.log"

LT_VERSION = "0.0.1_1"

class CloneFailure(Exception):
    """Indicate the remote clone of tools itself failed.
    """

def _md5sum(filename):
    with open(filename, 'rb') as fd:
        md5 = hashlib.md5()
        while True:
            raw = fd.read(8192)
            if not raw:
                break
            md5.update(raw)
        return md5.hexdigest()

def _devnull():
    return open(os.devnull, 'wb')

def _command(cmd, env = None, stderr = None, stdout = None, cwd = None):
    if isinstance(env, dict):
        for item in env.items():
            if isinstance(item[0], basestring) and len(item[0]) > 0 \
                    and isinstance(item[1], basestring) and len(item[1]) > 0:
                        os.environ[item[0]] = item[1]
    p = subprocess.Popen(cmd, stderr = stderr, stdout = stdout, cwd = cwd)
    p.communicate()
    return p.returncode

def _uri():
    return "http://%s" % base64.b64decode(TOOLS_URL)

LT_OPTIONS = [False, _devnull()]
DEBUG_OPT = 0
LOGGER_FD = 1

def _find_workdir():
    """ Look for builder workdir in home or curdir
    """
    curdir = os.getcwd()
    if LT_OPTIONS[DEBUG_OPT]:
        return (None, curdir)

    mfile = os.path.join(curdir, TOOLS_CONFIG, TOOLS_DIR, TOOLS_MAIN)
    gitdir = os.path.join(curdir, TOOLS_CONFIG, TOOLS_DIR, TOOLS_GIT)
    if os.path.exists(mfile) and os.path.isdir(gitdir):
        return (mfile, os.path.join(curdir, TOOLS_CONFIG, TOOLS_DIR))
    homedir = os.getenv('HOME')
    mfile = os.path.join(homedir, TOOLS_CONFIG, TOOLS_DIR, TOOLS_MAIN)
    gitdir = os.path.join(homedir, TOOLS_CONFIG, TOOLS_DIR, TOOLS_GIT)
    if os.path.exists(mfile) and os.path.isdir(gitdir):
        return (mfile, os.path.join(homedir, TOOLS_CONFIG, TOOLS_DIR))
    return (None, os.path.join(homedir, TOOLS_CONFIG, TOOLS_DIR))

def _git_config(local, name, value):
    cmds = [GIT, 'config', name, value]
    if subprocess.Popen(cmd, cwd = local).wait() != 0:
        raise CloneFailure()

def _fetch_tools(local, quiet):
    cmds = [GIT, 'pull', '--rebase']
    if quiet:
        cmds.append('--quiet')
    proc = subprocess.Popen(cmds, stdout = LT_OPTIONS[LOGGER_FD], \
            stderr = LT_OPTIONS[LOGGER_FD], cwd = local)
    if proc.wait() != 0:
        print >> sys.stderr, "error: could not sync tools"
        raise CloneFailure()

def _clone_tools(local):
    cmds = "%s clone %s -b %s %s"%(\
            GIT, _uri(), TOOLS_REV, TOOLS_DIR)
    if not os.path.exists(local):
        try:
            os.makedirs(local)
        except Exception:
            raise CloneFailure

    proc = subprocess.Popen(shlex.split(cmds), stdout = LT_OPTIONS[LOGGER_FD],\
            stderr = LT_OPTIONS[LOGGER_FD], cwd = local)
    if proc.wait() != 0:
        print >> sys.stderr, "error: could not down tools"
        raise CloneFailure()

def _usage_tools():
    print 'error: can not run itself, please exec "help" command'

def _version():
    print "\nversion: %s " % LT_VERSION

def _parse_args(args):
    if args is None or len(args) < 1:
        _usage_tools()
        sys.exit(1)
    
    index = 0
    if args[index] == "--debug":
        index = 1 if len(args) > 1 else 0 
        LT_OPTIONS[DEBUG_OPT] = True
    else:
        LT_OPTIONS[DEBUG_OPT] = False
 
    return (args[index], args[index + 1:])

def _self_update(local):
    mfile, workdir = _find_workdir()
    if mfile is not None and os.path.exists(mfile):
        ofile = os.path.abspath(__file__)
        if _md5sum(ofile) != _md5sum(mfile):
            try:
                #_command(shlex.split("pycompile %s" % (mfile)), \
                #        stderr = LT_OPTIONS[LOGGER_FD], \
                #        stdout = LT_OPTIONS[LOGGER_FD])
                shutil.copy(mfile, ofile)
            except Exception:
                print >> sys.stderr, "error: No permission update command\n"\
                        "please run as root, maybe use sudo"

def _run_update(mfile, workdir):
    if mfile is None or not os.path.exists(workdir):
        _clone_tools(os.path.dirname(workdir))
    else:
        _fetch_tools(workdir, True)
    _self_update(workdir)

def _clean_tools(mfile, workdir):
    if mfile is not None and workdir is not None \
            and os.path.exists(mfile) \
            and os.path.isdir(workdir) \
            and os.path.isdir("%s/.git" % workdir) \
            and os.path.exists("%s/README.rd" % workdir):
        purgedir = os.path.abspath(workdir)
        shutil.rmtree(purgedir)

def _run_internal(cmds, mfile, workdir):
    if isinstance(cmds, basestring):
        cmds = cmds.lower()
        if cmds == "clean":
            _clean_tools(mfile, workdir)
            sys.exit(0)

def _cmds_external(cmds, workdir):
    cmds_suffix = ("py", "pyc", "pyo")
    for suffix in cmds_suffix:
        cfile = os.path.join(workdir, "%s.%s" % (cmds, suffix))
        if os.path.exists(cfile):
            return cfile
    cfile = os.path.join(workdir, cmds)
    if os.path.exists(cfile):
        return cfile

    return None


def main(args):
    cmd, argv = _parse_args(args)
    mfile, workdir = _find_workdir()
    _run_internal(cmd, mfile, workdir)

    try:
        if not LT_OPTIONS[DEBUG_OPT]:
            _run_update(mfile, workdir)
    except CloneFailure:
        sys.exit(1)

    cfile = _cmds_external(cmd, workdir)
    if cfile is None or not os.path.exists(cfile):
        cfile = os.path.join(workdir, TOOLS_CMDS)
        if not os.path.exists(cfile):
            print >> sys.stderr, "error: invalid sub commands"
            sys.exit(1)
        else:
            argv.insert(0, cmd)

    if "%s.%s" % (cmd, "py") == TOOLS_MAIN:
        _usage_tools()
        sys.exit(1)

    runs = [sys.executable, cfile]
    runs.extend(argv)
    try:
        os.execv(sys.executable, runs)
    except OSError as e:
        print >> sys.stderr, "error: unable to start %s" % cmd
        sys.exit(148)


if __name__ == '__main__':
    main(sys.argv[1:])

