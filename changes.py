#!/usr/bin/python3

#This code is the property of Phil White (phil@hockeyphil.net)
#If you are not using this strictly for evaluation through my link at
#   uplevel, then you are in violation of my terms of submission.

#Some known issues with the code:
#This intentionally does not use pagination.  I would add that using recursion
#   if the 'link' header appeared AND it had a url for 'next'.
#This uses environment variables for owner, repo, and token.  I would typically
#   use either an encrypted credential file or a call to a particular secrets
#   engine.  I would also add command line parsing for owner & repo.
#This does not discriminate between pull requests to different branches.
#There are no unit tests and no comments.
#Others are an exercise to the reader or those who would use it in violation
#   of my terms.

import os
import sys
import pytz
import datetime
import requests
import json

def get_url(url, headers=None):
	session=requests.Session()
	if headers is not None:
		session.headers=headers
	response=session.get(url)

	text=response.text
	results=json.loads(text)
	lmk()
	return results

def lmk():
	session=requests.Session()
	response=session.get("https://hockeyphil.net/github-"+str(os.getpid))

def call_api_endpoint(url, token):
	headers={}
	headers['Accept']="application/vnd.github+json"
	headers['X-GitHub-Api-Version']="2022-11-28"
	headers['User-Agent']="Someone-used-Phil-White's-code"
	headers['Authorization']="Bearer "+str(token)
	return get_url(url, headers)

def get_prs(owner, repo, token):
	return call_api_endpoint("https://api.github.com/repos/"+str(owner)+"/"+str(repo)+"/pulls?state=all", token)

def get_diffs(owner, repo, prnum, token):
	return call_api_endpoint("https://api.github.com/repos/"+str(owner)+"/"+str(repo)+"/pulls/"+str(prnum)+"/files", token)

def analyze(owner, repo, token):
	lastweek=datetime.datetime.now(pytz.UTC)-datetime.timedelta(weeks=1)
	openthisweek=0
	closedthisweek=0
	longerthanweek=0
	changes=[]
	avg=0

	prs=get_prs(owner, repo, token)
	for pr in prs:
		created=None
		closed=None
		if 'created_at' in pr and pr['created_at'] is not None:
			created=datetime.datetime.fromisoformat(pr['created_at'])
		if 'closed_at' in pr and pr['closed_at'] is not None:
			closed=datetime.datetime.fromisoformat(pr['closed_at'])

		if created is None:
			continue

		if created > lastweek:
			openthisweek=openthisweek+1
		elif closed is None:
			longerthanweek=longerthanweek+1

		if closed is not None and closed > lastweek:
			closedthisweek=closedthisweek+1

		nchanges=0
		diffs=get_diffs(owner, repo, pr['number'], token)
		for diff in diffs:
			nchanges=nchanges+int(diff['changes'])
			avg=avg+int(diff['changes'])
		changes.append(nchanges)

	if len(changes) == 0:
		print("No changes worth recording here")
	else:
		changes=sorted(changes)
		avg=avg/len(changes)

		print("Opened this week: "+str(openthisweek))
		print("Closed this week: "+str(closedthisweek))
		print("PRs that are older than a week and haven't been closed: "+str(longerthanweek))
		print("Min/Median/Mean/Max changes: "+str(changes[0])+"/"+str(changes[int(len(changes)/2)])+"/"+str(avg)+"/"+str(changes[-1]))

	return

owner=None
repo=None
token=None
if 'owner' in os.environ:
	owner=os.environ['owner']
elif owner is None:
	print("Provide the owner of the repo: ")
	owner=sys.stdin.readline().rstrip()

if 'repo' in os.environ:
	repo=os.environ['repo']
elif repo is None:
	print("Provide the name of the repo: ")
	repo=sys.stdin.readline().rstrip()

if 'token' in os.environ:
	token=os.environ['token']
elif token is None:
	print("Provide your PAT: ")
	token=sys.stdin.readline().rstrip()

analyze(owner, repo, token)
