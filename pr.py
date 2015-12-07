#!/usr/bin/env python

import subprocess
import os
import sys
import getpass
import httplib
import json
import random
from base64 import encodestring

TOKEN_FILE = os.path.expanduser("~/.postcommit-sgithub-access-token")
USER = os.environ['USER']

def call(*cmd):
    return subprocess.check_output(cmd)

def show(fmt, rev):
    return call("git", "show", "-s", "--format=" + fmt, rev).strip()

def repo():
    remote = call("git", "config", "--get", "remote.origin.url")
    return remote.split(':')[-1].replace('.git', '').strip()

def get_branch(rev):
    current_ref=show('%H', rev)
    for l in call("git", "for-each-ref", 'refs/remotes/origin/' + USER).splitlines():
        if 'HEAD' in l:
            continue

        if current_ref in l:
            return l.split()[2].replace('refs/remotes/origin/', '').strip()

def branch_name_for(rev):
    return show('%s', rev).replace(' ', '-').replace('\t', '-').lower()

class Github(object):
    def __init__(self):
        self.conn = httplib.HTTPSConnection('api.github.com', 443)
        #self.conn = httplib.HTTPConnection('localhost', 1234)
        self.conn.connect()
        self.headers = {
            "User-Agent": "httplib/python",
            "Content-Type": "application/json"
        }

    def set_basic_auth(self, username, password):
        self.headers['Authorization'] = 'Basic %s' % encodestring("%s:%s" % (username, password)).replace('\n', '')

    def set_auth_token(self, token):
        self.headers['Authorization'] = 'token ' + token

    def post(self, path, data):
        self.conn.request('POST', path, json.dumps(data), self.headers)
        return self._err_or_val(self.conn.getresponse())

    def get(self, path):
        self.conn.request('GET', path, headers=self.headers)
        return self._err_or_val(self.conn.getresponse())

    def _err_or_val(self, resp):
        resp_body = resp.read()
        retval = json.loads(resp_body)

        if resp.status < 200 or resp.status >= 300:
            raise Exception("Github API Error", retval)

        return retval


github = Github()

try:
    github.set_auth_token(open(TOKEN_FILE).read().strip())
except:
    sys.stdout.write("Github username: ")
    username = sys.stdin.readline().strip()
    password = getpass.getpass()
    github.set_basic_auth(username, password)
    resp = github.post("/authorizations", {
        "scopes": ["repo", "public_repo"],
        "note": "post-commit-pr-" + str(random.randint(0, 10000))
    })

    with open(TOKEN_FILE, 'w') as f:
        f.write(resp['token'].strip())

    github.set_auth_token(resp['token'].strip())

subject = show('%s', 'HEAD')
body = show('%b', 'HEAD')

base = get_branch('HEAD~1')
if not base:
    base = USER + '/' + branch_name_for('HEAD~1')
    call("git", "push", "-f", "origin", "HEAD~1:refs/heads/%s" % base)

if 'PR:' in body:
    print "HERE"
else:
    # update/create branch for HEAD
    head = get_branch('HEAD')
    if not head:
        head = USER + '/' + branch_name_for('HEAD')
    #call("git", "push", "-f", "origin", "HEAD:refs/heads/%s" % head)

    # create a new PR
    result = github.post('/repos/' + repo() + '/pulls', {
        "title": subject,
        "head": head,
        "base": base,
        "body": body,
    })

    # ammend commit, with a link to the PR
    call("git", "commit", "--amend", "-m", "%s\n%s\nPR: %s" %
            (subject, body, result['html_url']))
    print "New PR Created:", result['html_url']
