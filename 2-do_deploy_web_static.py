#!/usr/bin/python3
"""Deploy archive!"""

from fabric.api import local, env, put, run
import os
import re
from datetime import datetime

env.user = 'ubuntu'
env.hosts = ['54.91.121.160', '18.208.248.34']


def do_pack():
    """Do pack function
    Return: Archive path if successful, None if not"""

    local("mkdir -p versions")
    result = local("tar -cvzf versions/web_static_{}.tgz web_static"
                   .format(datetime.strftime(datetime.now(), "%Y%m%d%H%M%S")),
                   capture=True)
    if result.failed:
        return None
    return result


def do_deploy(archive_path):
    """Deploy our servers"""

    if not os.path.isfile(archive_path):
        return False

    filename_regex = re.compile(r'[^/]+(?=\.tgz$)')
    match = filename_regex.search(archive_path)

    # Upload the archive to the /tmp/ directory of the web server
    archive_filename = match.group(0)
    result = put(archive_path, "/tmp/{}.tgz".format(archive_filename))
    if result.failed:
        return False

    result = run(
        "mkdir -p /data/web_static/releases/{}/".format(archive_filename))
    if result.failed:
        return False
    result = run("tar -xzf /tmp/{}.tgz -C /data/web_static/releases/{}/"
                 .format(archive_filename, archive_filename))
    if result.failed:
        return False

    # Delete the archive from the web server
    # (Assumption: no other file with extension .tgz exists
    #  in the /tmp/ directory)
    result = run("rm /tmp/{}.tgz".format(archive_filename))
    if result.failed:
        return False
    result = run("mv /data/web_static/releases/{}"
                 "/web_static/* /data/web_static/releases/{}/"
                 .format(archive_filename, archive_filename))
    if result.failed:
        return False
    result = run("rm -rf /data/web_static/releases/{}/web_static"
                 .format(archive_filename))
    if result.failed:
        return False

    # Delete the symbolic link /data/web_static/current from the web server
    result = run("rm -rf /data/web_static/current")
    if result.failed:
        return False

    #  Create a new the symbolic link /data/web_static/current
    #  on the web server, linked to the new version of your code
    result = run("ln -s /data/web_static/releases/{}/ /data/web_static/current"
                 .format(archive_filename))
    if result.failed:
        return False

    return True
