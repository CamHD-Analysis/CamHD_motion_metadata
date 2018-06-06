

import subprocess


def git_revision(infile):
    git_rev = subprocess.check_output(["git", "log", "-n 1",
                                      "--pretty=format:%H",  "--", infile],
                                      encoding='utf8')
    return git_rev
