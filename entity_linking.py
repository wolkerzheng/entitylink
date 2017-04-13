#encoding=utf8
import MySQLdb
import networkx as nx
import datetime as dt
import threading
import wikipedia
import matplotlib.pyplot as plt
import random
from candidate_generation import *

import sys
reload(sys)
sys.setdefaultencoding('utf8')
#######################################################################################
def redirect(entity):
	conn= MySQLdb.connect(host='192.168.140.98',port=3306,user='root',passwd = '**',db ='entitylinkdb')
	cur = conn.cursor()	
	mysql = "select redirectname from redirect where entityname =\"" + entity + "\""
	cur.execute(mysql)
	resultlist = cur.fetchall()
	if cur: cur.close()
	if conn: conn.commit();conn.close()

	if resultlist:
		return resultlist[0][0]
	else:
		return entity

'''
这几个评测文件比较老，里面真正的链接实体并不是最终实体，例如真正指向的实体为"The people's Republic of China"时，我们重定向为维基百科页显示的标题"China"
'''

#######################################################################################

def getEntity(mention,entityname):
	candidatelist = []
	if mention == '':
		return candidatelist
	else:
		conn= MySQLdb.connect(host='192.168.140.98',port=3306,user='root',passwd = '**',db ='entitylinkdb')
		cur = conn.cursor()
		mysql = "select entityname from labels  where match(entitystr) against (\""+mention+"\" in natural language mode) limit 7"
		#mysql = "select entityname from labels  where match(entitystr) against (\""+mention+"\" in boolean mode) limit 4"
		cur.execute(mysql)
		resultlist = cur.fetchall()
		for each in resultlist:
			if "_(" + mention + ")" in each[0]:
				continue
			if entityname.lower() == each[0].lower():
				continue
			candidatelist.append(each[0])
		if entityname in candidatelist:
			pass
		else:
			candidatelist.append(entityname)
		cur.close()
		conn.commit()
		conn.close()
		return candidatelist

def getEntity1(mention):
	candidatelist = []
	if mention == '':
		return candidatelist
	else:
		conn= MySQLdb.connect(host='192.168.140.98',port=3306,user='root',passwd = '**',db ='entitylinkdb')
		cur = conn.cursor()
		mysql = "select entityname from labels  where match(entitystr) against (\""+mention+"\" in natural language mode) limit 7"
		#mysql = "select entityname from labels  where match(entitystr) against (\""+mention+"\" in boolean mode) limit 4"
		cur.execute(mysql)
		resultlist = cur.fetchall()
		for each in resultlist:
			candidatelist.append(each[0])
		cur.close()
		conn.commit()
		conn.close()
		candidatelist1 = []
		for can in candidatelist:
			num = 0
			for can1 in candidatelist1:
				if can.lower() == can1.lower():
					num += 1
					break
			if num == len(candidatelist1):
				candidatelist1.append(can)

		return candidatelist1
'''
该方法利用mysql中fulltext全文搜索模式获取候选实体并去掉候选实体集中一些重复的实体，例如Jordan与jordan表示同一个实体
'''

#######################################################################################

'''
通过Wikipedia API加多线程获取候选实体集
'''
def getentitybywiki(mention,maxnum):
	resultlist = wikipedia.search(mention,results=maxnum)
	returnlist = []
	for each in resultlist:
		returnlist.append("_".join(each.encode("utf-8").split()))
	return returnlist

class getEntityByWiki(threading.Thread):
	def __init__(self,mention,maxnum):
		threading.Thread.__init__(self)
		self.mention = mention
		self.maxnum = maxnum
		self.resultlist = []

	def run(self):
		self.resultlist = getentitybywiki(self.mention,self.maxnum)

#######################################################################################
'''
获得各个测试文件中的每篇文档中的实体指称与目标实体
'''

def get_tackbp2014_Candidate():
	conn= MySQLdb.connect(host='192.168.140.98',port=3306,user='root',passwd = '**',db ='entitylinkdb')
	cur = conn.cursor()
	stmt1 = "select distinct docid from tac_kbp_2014"
	cur.execute(stmt1)
	docs = cur.fetchall()
	entitydoc = []
	for doc in docs:
		entitydoc.append(doc[0])

	docmention = {}
	for doc in entitydoc:
		sql = "select mention,entityname from tac_kbp_2014 where docid = \"" + doc + "\""
		cur.execute(sql)
		result = cur.fetchall()
		mentionlist = []
		for mention,entityname in result:
			mentionlist.append([mention,redirect(entityname)])
		docmention[doc] = mentionlist

	doccandidate = {}
	for doc in entitydoc:
		mentionlist = docmention[doc]#0:mention 1:targetentity
		entitydic = {}
		for mention,entityname in mentionlist:
			candidatelist = getEntity1(mention,entityname)
			entitydic[mention] = candidatelist
		doccandidate[doc] = [entitydic,mentionlist]
		print doc
		print entitydic
	return entitydoc,doccandidate
###获取实体指称和目标实体
def get_aidaee_Candidate():
	infile = open("apw_eng_201010.tsv","r").readlines()
	entitydoc = []
	docmention = {}
	for line in infile:
		ls = line.strip().split("\t")
		docid = ls[4]
		mention = '_'.join(ls[1].split())
		if ls[2] == "--OOKBE--":
			entityname = "NULL"
		else:
			entityname = ls[3][len("http://en.wikipedia.org/wiki/"):]
		if docid not in entitydoc:
			entitydoc.append(docid)
		if docid not in docmention.keys():
			docmention[docid] = []
		docmention[docid].append([mention,redirect(entityname)])
	return entitydoc,docmention

#######################################################################################
'''
对TAC-KBP 2014使用基于搜索规则、先验概率与搜索规则相结合、Wikipedia API三种方法获取实体指称的获选实体集
'''

def get_tackbp2014_CandidateByWiki():
	conn= MySQLdb.connect(host='192.168.140.98',port=3306,user='root',passwd = '**',db ='entitylinkdb')
	cur = conn.cursor()
	stmt1 = "select distinct docid from tac_kbp_2014"
	cur.execute(stmt1)
	docs = cur.fetchall()
	entitydoc = []
	for doc in docs:
		entitydoc.append(doc[0])

	docmention = {}
	for doc in entitydoc:
		sql = "select mention,entityname from tac_kbp_2014 where docid = \"" + doc + "\""
		cur.execute(sql)
		result = cur.fetchall()
		mentionlist = []
		for mention,entityname in result:
			mentionlist.append([mention,redirect(entityname)])
		docmention[doc] = mentionlist

	doccandidate = {}
	for doc in entitydoc:
		threads = []
		resultlist = []
		mentionlist = docmention[doc]
		for mention,entity in mentionlist:
			threads.append(getEntityByWiki(mention,5))
		for t in threads:
	 		t.start()
	 	for t in threads:
	 		t.join()
	 		resultlist.append(t.resultlist)
	 	entitydic = {}
	 	for i in range(len(mentionlist)):
	 		entitydic[mentionlist[i][0]] = resultlist[i]
	 		if resultlist[i]==[]:
	 			entitydic[mentionlist[i][0]] = getEntity1(mentionlist[i][0])
		doccandidate[doc] = [entitydic,mentionlist]
		print doc
		print entitydic
	return entitydoc,doccandidate

def get_tackbp2014_CandidateByRule():	 	
	conn= MySQLdb.connect(host='192.168.140.98',port=3306,user='root',passwd = '**',db ='entitylinkdb')
	cur = conn.cursor()
	stmt1 = "select distinct docid from tac_kbp_2014"
	cur.execute(stmt1)
	docs = cur.fetchall()
	entitydoc = []
	for doc in docs:
		entitydoc.append(doc[0])

	docmention = {}
	for doc in entitydoc:
		sql = "select mention,entityname from tac_kbp_2014 where docid = \"" + doc + "\""
		cur.execute(sql)
		result = cur.fetchall()
		mentionlist = []
		for mention,entityname in result:
			mentionlist.append([mention,redirect(entityname)])
		docmention[doc] = mentionlist

	doccandidate = {}
	for doc in entitydoc:
		mentionlist = docmention[doc]#0:mention 1:targetentity
		entitydic = {}
		for mention,entityname in mentionlist:
			candidatelist = getCanByRule(mention)
			entitydic[mention] = candidatelist
		doccandidate[doc] = [entitydic,mentionlist]
		print doc
		print entitydic
	return entitydoc,doccandidate

def get_tackbp2014_CandidateByPriorRule():
	conn= MySQLdb.connect(host='192.168.140.98',port=3306,user='root',passwd = '**',db ='entitylinkdb')
	cur = conn.cursor()
	stmt1 = "select distinct docid from tac_kbp_2014"
	cur.execute(stmt1)
	docs = cur.fetchall()
	entitydoc = []
	for doc in docs:
		entitydoc.append(doc[0])

	docmention = {}
	for doc in entitydoc:
		sql = "select mention,entityname from tac_kbp_2014 where docid = \"" + doc + "\""
		cur.execute(sql)
		result = cur.fetchall()
		mentionlist = []
		for mention,entityname in result:
			mentionlist.append([mention,redirect(entityname)])
		####jinxing windows qiefen

		docmention[doc] = mentionlist

	doccandidate = {}
	for doc in entitydoc:
		mentionlist = docmention[doc]#0:mention 1:targetentity
		entitydic = {}
		for mention,entityname in mentionlist:
			candidatelist = getCanByPriorRule(mention)
			entitydic[mention] = candidatelist
		doccandidate[doc] = [entitydic,mentionlist]
		print doc
		print entitydic
	if cur: cur.close()
	if conn: conn.commit();conn.close()
	return entitydoc,doccandidate

#######################################################################################

'''
对AIDA-EE使用基于搜索规则、先验概率与搜索规则相结合两种方法获取实体指称的获选实体集
'''
def get_aidaee_CandidateByEdictDist():
	infile = open("apw_eng_201010.tsv", "r").readlines()
	entitydoc = []
	docmention = {}
	for line in infile:
		ls = line.strip().split("\t")
		docid = ls[4]
		mention = '_'.join(ls[1].split())
		if ls[2] == "--OOKBE--":
			entityname = "NULL"
		else:
			entityname = ls[3][len("http://en.wikipedia.org/wiki/"):]
		if docid not in entitydoc:
			entitydoc.append(docid)
		if docid not in docmention.keys():
			docmention[docid] = []
		docmention[docid].append([mention, redirect(entityname)])
	doccandidate = {}
	for doc in entitydoc:
		mentionlist = docmention[doc]#0:mention 1:targetentity
		entitydic = {}
		for mention,entityname in mentionlist:
			candidatelist = getCandidateByEditdistance(mention,6)
			entitydic[mention] = candidatelist
		doccandidate[doc] = [entitydic,mentionlist]
		# print doc
		# print entitydic
	return entitydoc,doccandidate
	pass
def get_aidaee_CandidateByRule():
	infile = open("apw_eng_201010.tsv","r").readlines()
	entitydoc = []
	docmention = {}
	for line in infile:
		ls = line.strip().split("\t")
		docid = ls[4]
		mention = '_'.join(ls[1].split())
		if ls[2] == "--OOKBE--":
			entityname = "NULL"
		else:
			entityname = ls[3][len("http://en.wikipedia.org/wiki/"):]
		if docid not in entitydoc:
			entitydoc.append(docid)
		if docid not in docmention.keys():
			docmention[docid] = []
		docmention[docid].append([mention,redirect(entityname)])
	doccandidate = {}
	for doc in entitydoc:
		mentionlist = docmention[doc]#0:mention 1:targetentity
		entitydic = {}
		for mention,entityname in mentionlist:
			candidatelist = getCanByRule(mention)
			entitydic[mention] = candidatelist
		doccandidate[doc] = [entitydic,mentionlist]
		# print doc
		# print entitydic
	return entitydoc,doccandidate

def get_aidaee_CandidateByPriorRule():
	infile = open("apw_eng_201010.tsv","r").readlines()
	entitydoc = []
	docmention = {}
	for line in infile:
		ls = line.strip().split("\t")
		docid = ls[4]
		mention = '_'.join(ls[1].split())
		if ls[2] == "--OOKBE--":
			entityname = "NULL"
		else:
			entityname = ls[3][len("http://en.wikipedia.org/wiki/"):]
		if docid not in entitydoc:
			entitydoc.append(docid)
		if docid not in docmention.keys():
			docmention[docid] = []
		docmention[docid].append([mention,redirect(entityname)])
	doccandidate = {}
	for doc in entitydoc:
		mentionlist = docmention[doc]#0:mention 1:targetentity
		entitydic = {}
		for mention,entityname in mentionlist:
			candidatelist = getCanByPriorRule(mention)
			entitydic[mention] = candidatelist
		doccandidate[doc] = [entitydic,mentionlist]
		# print doc
		# print entitydic
	return entitydoc,doccandidate

#######################################################################################

'''
对AIDA-YAGO使用基于搜索规则、先验概率与搜索规则相结合两种方法获取实体指称的获选实体集
'''

def processEntityStr(entityStr):
    entityStr='_'.join(entityStr.split())
    return entityStr

def get_aidayago_CandidateByPriorRule():
	entitydoc = []
	docmention = {}
	docid = ''
	infile = open('AIDA-YAGO2-dataset.tsv','r')
	for line in infile:
		ls = line.strip().split('\t')
		if len(ls)==1 and '-DOCSTART-' in ls[0] and docid!=ls[0]:
			docid = ls[0]
			entitydoc.append(docid)
			docmention[docid] = []
		elif (len(ls)==7 or len(ls)==6) and ls[1]!='I':
			mention = processEntityStr(ls[2])
			entity = ls[4][len('http://en.wikipedia.org/wiki/'):]
			docmention[docid].append([mention,redirect(entity)])
	doccandidate = {}
	for doc in entitydoc:
		mentionlist = docmention[doc]#0:mention 1:targetentity
		entitydic = {}
		for mention,entityname in mentionlist:
			candidatelist = getCanByPriorRule(mention)
			entitydic[mention] = candidatelist
		doccandidate[doc] = [entitydic,mentionlist]
		print doc
		print entitydic
	return entitydoc,doccandidate

def get_aidayago_CandidateByRule():
	entitydoc = []
	docmention = {}
	docid = ''
	infile = open('AIDA-YAGO2-dataset.tsv','r')
	for line in infile:
		ls = line.strip().split('\t')
		if len(ls)==1 and '-DOCSTART-' in ls[0] and docid!=ls[0]:
			docid = ls[0]
			entitydoc.append(docid)
			docmention[docid] = []
		elif (len(ls)==7 or len(ls)==6) and ls[1]!='I':
			mention = processEntityStr(ls[2])
			entity = ls[4][len('http://en.wikipedia.org/wiki/'):]
			docmention[docid].append([mention,redirect(entity)])
	doccandidate = {}
	for doc in entitydoc:
		mentionlist = docmention[doc]#0:mention 1:targetentity
		entitydic = {}
		for mention,entityname in mentionlist:
			candidatelist = getCanByRule(mention)
			entitydic[mention] = candidatelist
		doccandidate[doc] = [entitydic,mentionlist]
		print doc
		print entitydic
	return entitydoc,doccandidate

def get_aidayago_CandidateByEditDistance():
	entitydoc = []
	docmention = {}
	docid = ''
	infile = open('AIDA-YAGO2-dataset.tsv','r')
	for line in infile:
		ls = line.strip().split('\t')
		if len(ls)==1 and '-DOCSTART-' in ls[0] and docid!=ls[0]:
			docid = ls[0]
			entitydoc.append(docid)
			docmention[docid] = []
		elif (len(ls)==7 or len(ls)==6) and ls[1]!='I':
			mention = processEntityStr(ls[2])
			entity = ls[4][len('http://en.wikipedia.org/wiki/'):]
			docmention[docid].append([mention,redirect(entity)])
	doccandidate = {}
	for doc in entitydoc:
		mentionlist = docmention[doc]#0:mention 1:targetentity
		entitydic = {}
		for mention,entityname in mentionlist:
			candidatelist = getCandidateByEditdistance(mention,6)
			entitydic[mention] = candidatelist
		doccandidate[doc] = [entitydic,mentionlist]
	return entitydoc,doccandidate

#######################################################################################

def getCandidateSet(mentioncanlist): #若候选实体集中有重复的实体，去重
	candidatelist = []
	for mentioncan in mentioncanlist:
		candidatelist.extend(mentioncan[1])
	return candidatelist
#######################################################################################
#get no directed pair 

'''
构建图时有两种方法，一种是有向图，一种是无向图。效果差不多，无向图运行效率更高一些。
'''

def getEntityPair1(entitydic):
	entitypairarray = []
	for entity1 in entitydic.keys():
		for entity2 in entitydic.keys():
			if entity1 != entity2:
				for each1 in entitydic[entity1]:
					for each2 in entitydic[entity2]:
						entitypairarray.append([each1,each2])
	entitypairarraynew = []
	for entitypair in entitypairarray:
		entity1,entity2 = entitypair
		if [entity2,entity1] not in entitypairarraynew:
			entitypairarraynew.append(entitypair)
	return entitypairarraynew

#get the directed pair
def getEntityPair(entitydic):
	entitypairarray = []
	for entity1 in entitydic.keys():
		for entity2 in entitydic.keys():
			if entity1 != entity2:
				for each1 in entitydic[entity1]:
					for each2 in entitydic[entity2]:
						entitypairarray.append([each1,each2])
	return entitypairarray

def splitDicToKsize(entitydic,kSize=5):
	"""
	将字典切分，但是切分并不按字典顺序切分
	:param entitydic:
	:param kSize:
	:return:
	"""
	resList = []
	dicLen = len(entitydic)
	startPoint = 0
	endPoint = 0
	tmp = dicLen
	Dictlist =  entitydic.keys() #转换成list
	print Dictlist
	while startPoint < dicLen:

		tmpDict = {}
		if tmp - kSize > 0:
			endPoint = startPoint + kSize
		else:
			endPoint = startPoint + tmp
		splitentitylist = Dictlist[startPoint:endPoint]
		for key in splitentitylist:
			tmpDict[key] = entitydic[key]
		print tmpDict
		resList.append(tmpDict)
		startPoint = endPoint

	return resList






#######################################################################################

def getSQL(entitypair,len):#
	mysql = 'select a.entityname,a.linkname'
	for i in range(len-1):
		mysql = mysql + ',' + chr(98+i) +'.linkname'
	mysql = mysql + ' from pagelinks as a '
	for i in range(len-1):
		mysql = mysql + 'join pagelinks as ' + chr(98+i) + ' '
	mysql = mysql + "where a.entityname = \""+entitypair[0]+"\" and " + chr(98+len-2) + ".linkname = \""+entitypair[1]+"\""
	for i in range(len-1):
		mysql = mysql + ' and ' + chr(98+i-1) + '.linkname = ' + chr(98+i) + '.entityname'
	return mysql

#######################################################################################

# a way that are just suitable for path of 2
'''
当构建实体对为有向图时，若仅考虑中间结点不超过1个的情况
'''
def getPairPath(entitypair):
	if "\"" in entitypair[0]:
		entitypair[0] = entitypair[0].replace("\"","")
	if "\"" in entitypair[1]:
		entitypair[1] = entitypair[1].replace("\"","")
	"mysql1:a->b"
	"mysql2:a<-b"
	"mysql3:a->()->b"
	"mysql4:a<-()<-b"
	"mysql5:a->()<-b"
	"mysql6:a<-()->b"
	patharray = []
	conn= MySQLdb.connect(host='192.168.140.98',port=3306,user='root',passwd = '**',db ='entitylinkdb')
	cur = conn.cursor()
	mysql1 = "select entityname,linkname from pagelinks where entityname = \""+entitypair[0]+"\" and linkname = \""+entitypair[1]+"\""
	mysql2 = "select entityname,linkname from pagelinks where entityname = \""+entitypair[1]+"\" and linkname = \""+entitypair[0]+"\""
	mysql3 = "select a.entityname,a.linkname,b.linkname from pagelinks as a join pagelinks as b where a.entityname=%s and a.linkname = b.entityname and b.linkname=%s"
	mysql4 = "select b.entityname,b.linkname,a.linkname from pagelinks as a join pagelinks as b where a.linkname=%s and b.linkname = a.entityname and b.entityname=%s"
	mysql5 = "select a.linkname from pagelinks as a join pagelinks as b where a.entityname=%s and b.linkname=a.linkname and b.entityname=%s"
	mysql6 = "select a.entityname from pagelinks as a join pagelinks as b where a.linkname=%s and b.entityname=a.entityname and b.linkname=%s"
	cur.execute(mysql1)
	resultlist = cur.fetchall()
	for eachresult in resultlist:
		patharray.append(eachresult)
	cur.execute(mysql2)
	resultlist = cur.fetchall()
	for eachresult in resultlist:
		patharray.append(eachresult)
	cur.execute(mysql3,(entitypair[0],entitypair[1]))
	resultlist = cur.fetchall()
	for eachresult in resultlist:
		patharray.append(eachresult)
	cur.execute(mysql4,(entitypair[0],entitypair[1]))
	resultlist = cur.fetchall()
	for eachresult in resultlist:
		patharray.append(eachresult)
	cur.execute(mysql5,(entitypair[0],entitypair[1]))
	resultlist = cur.fetchall()
	for eachresult in resultlist:
		patharray.append((entitypair[0],eachresult[0]))
		patharray.append((entitypair[1],eachresult[0]))
	cur.execute(mysql6,(entitypair[0],entitypair[1]))
	resultlist = cur.fetchall()
	for eachresult in resultlist:
		patharray.append((eachresult[0],entitypair[0]))
		patharray.append((eachresult[0],entitypair[1]))
	if cur: cur.close()
	if conn: conn.commit();conn.close()
	return patharray

def getPairArrayPath(entitypairarray):
	patharray = []
	for entitypair in entitypairarray:
		path = getPairPath(entitypair)
		patharray.extend(path)
	return patharray

#######################################################################################

'''
构建图为无向图时，仅考虑中间结点不超过2的情况
'''

def getPairPath1(entitypair):
	if "\"" in entitypair[0]:
		entitypair[0] = entitypair[0].replace("\"","")
	if "\"" in entitypair[1]:
		entitypair[1] = entitypair[1].replace("\"","")
	patharray = []
	conn= MySQLdb.connect(host='192.168.140.98',port=3306,user='root',passwd = '**',db ='entitylinkdb')
	cur1 = conn.cursor()
	cur2 = conn.cursor()
	cur3 = conn.cursor()
	cur4 = conn.cursor()
	mysql1 = "select entityname,linkname from pagelinks where entityname = \""+entitypair[0]+"\" and linkname = \""+entitypair[1]+"\""
	mysql2 = "select entityname,linkname from pagelinks where entityname = \""+entitypair[1]+"\" and linkname = \""+entitypair[0]+"\""
	mysql3 = "select entityname,linkname from pagelinks where entityname = \""+entitypair[0]+"\""
	mysql4 = "select entityname,linkname from pagelinks where entityname = \""+entitypair[1]+"\""
	cur1.execute(mysql1)
	resultlist = cur1.fetchall()
	for eachresult in resultlist:
		patharray.append(eachresult)
	cur2.execute(mysql2)
	resultlist = cur2.fetchall()
	for eachresult in resultlist:
		patharray.append(eachresult)
	linkset1 = []
	linkset2 = []
	cur3.execute(mysql3)
	resultlist = cur3.fetchall()
	for eachresult in resultlist:
		linkset1.append(eachresult)
	cur4.execute(mysql4)
	resultlist = cur4.fetchall()
	for eachresult in resultlist:
		linkset2.append(eachresult)
	for entityname1,linkname1 in linkset1:
		for entityname2,linkname2 in linkset2:
			if linkname1 == linkname2:
				#print entityname1,linkname1
				#print entityname2,linkname2
				patharray.append((entityname1,linkname1))
				patharray.append((entityname2,linkname2))
	# if cur: cur.close()
	if conn: conn.commit();conn.close()
	return patharray

def getPairArrayPath1(entitypairarray):
	patharray = []
	for entitypair in entitypairarray:
		path = getPairPath1(entitypair)
		patharray.extend(path)
	return patharray

#######################################################################################

'''
当构建为有向时，可设置任意边长，但仅考虑a->....->b的情况
'''

def getPairPath2(entitypair,len):
	patharray = []
	conn= MySQLdb.connect(host='192.168.140.98',port=3306,user='root',passwd = '***',db ='entitylinkdb')
	cur = conn.cursor()
	mysql = getSQL(entitypair,len)
	cur.execute(mysql)
	resultlist = cur.fetchall()
	for eachresult in resultlist:
		print eachresult
		patharray.append(eachresult)
	if cur: cur.close()
	if conn: conn.commit();conn.close()
	return patharray

def getPairArrayPath2(entitypairarray,len):
	patharray = []
	for entitypair in entitypairarray:
		path = getPairPath2(entitypair,len)
		patharray.extend(path)
	return patharray

#######################################################################################

'''
获取边和结点构建图
'''
def getEdges(patharray):
	edges = []
	nodes = []
	for eachpath in patharray:
		for i in range(len(eachpath)-1):
			edges.append((eachpath[i],eachpath[i+1]))
		for node in eachpath:
			nodes.append(node)
	nodes = list(set(nodes))
	edges = list(set(edges))
	return edges,nodes

#######################################################################################

'''
构建有向图，直接计算pagerank值
'''
def getGraphByStandardPagelink(entitydic,edges,nodes):
	G = nx.DiGraph()
	G.add_nodes_from(nodes)
	G.add_edges_from(edges)
	#nx.draw(G,with_labels = True)
	#plt.show()
	pr = nx.pagerank(G)
	predict = {}
	for key in entitydic.keys():
		if entitydic[key] == []:
			predict[key] = "NULL"
		else:
			value = 0
			for canentity in entitydic[key]:
				entityvalue = pr[canentity]
				if entityvalue>value:
					value = entityvalue
					predictentity = canentity
			predict[key] = predictentity
	return predict

#######################################################################################

'''
构建无向图，直接计算pagerank值
'''
def getGraphByStandardPagelink1(entitydic,edges,nodes):
	G = nx.Graph()
	G.add_nodes_from(nodes)
	G.add_edges_from(edges)
	#nx.draw(G,with_labels = True)
	#plt.show()
	pr = nx.pagerank(G)
	predict = {}
	for key in entitydic.keys():
		if entitydic[key] == []:
			predict[key] = "NULL"
		else:
			value = 0
			for canentity in entitydic[key]:
				entityvalue = pr[canentity]
				if entityvalue>value:
					value = entityvalue
					predictentity = canentity
			predict[key] = predictentity
	return predict

#######################################################################################

'''
使用贪婪方法计算每个节点的pagerank值
'''
def getGraphByGreedSearch(entitydic,edges,nodes):
	print '使用贪婪算法计算pagerank'
	G = nx.Graph()
	G.add_nodes_from(nodes)
	G.add_edges_from(edges)
	predict = {}
	while entitydic:
		value = 0
		key = ""
		pr = nx.pagerank(G)
		entitylist = entitydic.items()
		candiList = set()
		for k,v in entitylist:
			candiList = candiList | set(v)
			for canentity in v:
				entityvalue = pr[canentity]
				if entityvalue>value:
					value = entityvalue
					targetentity = canentity
					key = k
		predict[key] = targetentity
		# print key,targetentity
		removelist = []
		if key!="":
			removelist = set(entitydic[key])
			# print predict[key],entitydic[key]
			removelist.remove(predict[key])

		removelist =list(removelist.difference(candiList))
		G.remove_nodes_from(removelist)
		entitydic.pop(key)
	return predict

def getPageRankByGreedSearch(entitydic):

	"""
	在每个图获取得到最大的pagerank后重新更新图
	:param entitydic: 字典，ｋｅｙ为ｍｅｎｔｉｏｎ，ｖａｌｕｅ为候选实体集链表[]
	:param edges:
	:param nodes:
	:return:
	"""
	predict = {}
	mentionList = entitydic.keys()  #未进行计算的实体
	mentionCompuList = []  			#已经计算过的实体
	while mentionList!=None:
		entitypairarray = getEntityPair1(entitydic)
		patharray = getPairArrayPath1(entitypairarray)
		edges, nodes = getEdges(patharray)
		print "edges:" + str(len(nodes))
		for m in entitydic.items():
			for n in m[1]:
				nodes.append(n)
		nodes = list(set(nodes))
		print "nodes:" + str(len(nodes))

		predictTmp = getMinPageRankByStandardPagelink(entitydic,mentionCompuList, edges, nodes)
		if predictTmp != None:
			entitydic[predictTmp.keys()[0]] = predictTmp[predictTmp.keys()[0]]
			mentionCompuList.append(predictTmp.keys()[0])
			mentionList.remove(predictTmp.keys()[0])
		predict = dict(predict, **predictTmp)
	return predict

def getMinPageRankByStandardPagelink(entitydic,mentionCompuList, edges, nodes):
	"""
	获取图中最大的一个ｐａｇｅｒａｎｋ
	:param entitydic:
	:param edges:
	:param nodes:
	:return:
	"""
	G = nx.Graph()
	G.add_nodes_from(nodes)
	G.add_edges_from(edges)
	pr = nx.pagerank(G)
	predict = {}
	maxkey = None
	value = 0
	for key in entitydic.keys():
		if entitydic[key] != []:
			#
			for canentity in entitydic[key]:
				entityvalue = pr[canentity]
				if entityvalue > value and canentity not in mentionCompuList:
					maxkey = key
					value = entityvalue
					predictentity = canentity
	predict[key] = predictentity
	return predict
#######################################################################################	
'''
使用蒙特卡罗算法计算图中的结点值
'''
def getGraphByRandomWalk(edges,nodes):
	pass

#######################################################################################
'''
若文章过长，文章头与文章尾的实体可能没有太多的关联，可使用将文章分段分别构建图
'''
def entitydic_split(targetlist,edges,nodes,split_len):



	pass

#######################################################################################

def tackbp2014_main():
	starttime = dt.datetime.now()
	entitydoc,doccandidate = get_tackbp2014_CandidateByRule()
	# entitydoc,doccandidate = get_tackbp2014_CandidateByPriorRule()
	#entitydoc,doccandidate = get_tackbp2014_Candidate()
	print "Candidate entity complete!"
	correctnumber = 0
	totalnumber = 0
	prenullnumber = 0
	realnullnumber = 0
	totaldoc = len(entitydoc)
	currentdoc = 0
	#随机取100篇tac_kbp文档
	random.shuffle(entitydoc)
	getCandidateEntityPrecision(entitydoc, doccandidate)
	addTargetEntityToCandidate(entitydoc, doccandidate)
	# print entitydoc
	for doc in entitydoc[0:30]:
		currentdoc += 1
		print doc + "(" + str(currentdoc) + "/" + str(totaldoc) + "):"
		starttime0 = 0
		endtime0 = 0
		cn = 0
		tm = 0
		starttime0 = dt.datetime.now()
		entitydic,targetlist = doccandidate[doc]

		if len(entitydic) == 1:
			totalnumber += 1
			tm += 1
			if entitydic[targetlist[0][0]] == []:
				prenullnumber += 1
			if targetlist[0][1] == "NULL":
				realnullnumber += 1
			if targetlist[0][1].lower() == entitydic[targetlist[0][0]][0].lower():
				correctnumber += 1
				cn += 1
			print "mention:" + targetlist[0][0] + "   target:" + targetlist[0][1] + "     predict:" + entitydic[targetlist[0][0]][0]
		else:
			entitypairarray = getEntityPair(entitydic)
			patharray = getPairArrayPath(entitypairarray)
			edges,nodes = getEdges(patharray)
			print "edges:" + str(len(nodes))
			for m in entitydic.items():
				for n in m[1]:
					nodes.append(n)
			nodes = list(set(nodes))
			print "nodes:" + str(len(nodes))
			predict = getGraphByStandardPagelink(entitydic,edges,nodes)
			for mention,target in targetlist:
				totalnumber += 1
				tm += 1
				if predict[mention] == "NULL":
					prenullnumber += 1
				if target == "NULL":
					realnullnumber += 1
				if predict[mention].lower() == target.lower():
					correctnumber += 1
					cn += 1
				print "mention:" + mention + "   target:" + target + "     predict:" + predict[mention]
		endtime0 = dt.datetime.now()
		print "doc_totalnumber:" + str(tm)
		print "doc_correctnumber:" + str(cn)
		print "doc_precious:" + str(float(cn)/tm)
		print "doc_runtime:" + str(endtime0 - starttime0)
		print "***************************************************"
	print "totalnumber:" + str(totalnumber)
	print "correctnumber:" + str(correctnumber)
	print "prenullnumber:" + str(prenullnumber)
	print "realnullnumber:" + str(realnullnumber)
	precious = float(correctnumber - prenullnumber)/(totalnumber - prenullnumber)
	recall = float(correctnumber - prenullnumber)/(totalnumber - realnullnumber)
	print "precious:" + str(precious)
	print "recall:" + str(recall)
	print "F1:" + str((2*precious*recall)/(precious+recall))
	endtime = dt.datetime.now()

	correctnumber = 0
	totalnumber = 0
	prenullnumber = 0
	realnullnumber = 0
	totaldoc = len(entitydoc)
	currentdoc = 0
	for doc in entitydoc[0:30]:
		currentdoc += 1
		print doc + "(" + str(currentdoc) + "/" + str(totaldoc) + "):"
		starttime0 = 0
		endtime0 = 0
		cn = 0
		tm = 0
		starttime0 = dt.datetime.now()
		entitydic,targetlist = doccandidate[doc]

		if len(entitydic) == 1:
			totalnumber += 1
			tm += 1
			if entitydic[targetlist[0][0]] == []:
				prenullnumber += 1
			if targetlist[0][1] == "NULL":
				realnullnumber += 1
			if targetlist[0][1].lower() == entitydic[targetlist[0][0]][0].lower():
				correctnumber += 1
				cn += 1
			print "mention:" + targetlist[0][0] + "   target:" + targetlist[0][1] + "     predict:" + entitydic[targetlist[0][0]][0]
		else:
			entitypairarray = getEntityPair(entitydic)
			patharray = getPairArrayPath(entitypairarray)
			edges,nodes = getEdges(patharray)
			print "edges:" + str(len(nodes))
			for m in entitydic.items():
				for n in m[1]:
					nodes.append(n)
			nodes = list(set(nodes))
			print "nodes:" + str(len(nodes))
			# predict = getGraphByStandardPagelink(entitydic,edges,nodes)
			predict =	getGraphByGreedSearch(entitydic,edges,nodes)
			for mention,target in targetlist:
				totalnumber += 1
				tm += 1
				if predict[mention] == "NULL":
					prenullnumber += 1
				if target == "NULL":
					realnullnumber += 1
				if predict[mention].lower() == target.lower():
					correctnumber += 1
					cn += 1
				print "mention:" + mention + "   target:" + target + "     predict:" + predict[mention]
		endtime0 = dt.datetime.now()
		print "doc_totalnumber:" + str(tm)
		print "doc_correctnumber:" + str(cn)
		print "doc_precious:" + str(float(cn)/tm)
		print "doc_runtime:" + str(endtime0 - starttime0)
		print "***************************************************"
	print "totalnumber:" + str(totalnumber)
	print "correctnumber:" + str(correctnumber)
	print "prenullnumber:" + str(prenullnumber)
	print "realnullnumber:" + str(realnullnumber)
	precious = float(correctnumber - prenullnumber)/(totalnumber - prenullnumber)
	recall = float(correctnumber - prenullnumber)/(totalnumber - realnullnumber)
	print "precious:" + str(precious)
	print "recall:" + str(recall)
	print "F1:" + str((2*precious*recall)/(precious+recall))
	endtime = dt.datetime.now()
	print "runtime:" + str(endtime - starttime)

def aida_ee_201010_main():
	starttime = dt.datetime.now()
	print 'aida_ee_pr'
	# entitydoc,doccandidate = get_aidaee_CandidateByRule()

	entitydoc,doccandidate = get_aidaee_CandidateByPriorRule()
	#entitydoc,doccandidate = get_aidaee_Candidate()
	print "Candidate entity complete!"
	correctnumber = 0
	totalnumber = 0
	prenullnumber = 0
	realnullnumber = 0
	totaldoc = len(entitydoc)
	currentdoc = 0
	kSize = 5 ###分割成5个实体一组
	ktmp = 0
	startPoint,endPoint = 0,0
	random.shuffle(entitydoc)
	getCandidateEntityPrecision(entitydoc,doccandidate)
	addTargetEntityToCandidate(entitydoc,doccandidate)

	for doc in entitydoc[0:15]:
		currentdoc += 1
		print doc + "(" + str(currentdoc) + "/" + str(totaldoc) + "):"
		starttime0 = 0
		endtime0 = 0
		cn = 0
		tm = 0
		starttime0 = dt.datetime.now()
		entitydic,targetlist = doccandidate[doc]

		if len(entitydic) == 1:
			totalnumber += 1
			tm += 1
			if entitydic[targetlist[0][0]] == []:
				prenullnumber += 1
			if targetlist[0][1] == "NULL":
				realnullnumber += 1
			if targetlist[0][1].lower() == entitydic[targetlist[0][0]][0].lower():
				correctnumber += 1
				cn += 1
			print "mention:" + targetlist[0][0] + "   target:" + targetlist[0][1] + "     predict:" + entitydic[targetlist[0][0]][0]
		else:
			# entitydicList = splitDicToKsize(entitydic, kSize=60)
			# predict = {}
			# for entitydicTmp in entitydicList:
			entitypairarray = getEntityPair1(entitydic)
			patharray = getPairArrayPath1(entitypairarray)
			edges,nodes = getEdges(patharray)
			print "edges:" + str(len(nodes))
			for m in entitydic.items():
				for n in m[1]:
					nodes.append(n)
			nodes = list(set(nodes))
			print "nodes:" + str(len(nodes))
			predict = getGraphByStandardPagelink1(entitydic,edges,nodes)
			# predict = dict(predict, **predictTmp)
			for mention,target in targetlist:
				totalnumber += 1
				tm += 1
				if predict[mention] == "NULL":
					prenullnumber += 1
				if target == "NULL":
					realnullnumber += 1
				if predict[mention].lower() == target.lower():
					correctnumber += 1
					cn += 1
				print "mention:" + mention + "   target:" + target + "     predict:" + predict[mention]

		endtime0 = dt.datetime.now()
		print "doc_totalnumber:" + str(tm)
		print "doc_correctnumber:" + str(cn)
		print "doc_precious:" + str(float(cn)/tm)
		print "doc_runtime:" + str(endtime0 - starttime0)
		print "***************************************************"
	print "totalnumber:" + str(totalnumber)
	print "correctnumber:" + str(correctnumber)
	print "prenullnumber:" + str(prenullnumber)
	print "realnullnumber:" + str(realnullnumber)
	precious = float(correctnumber - prenullnumber)/(totalnumber - prenullnumber)
	recall = float(correctnumber - prenullnumber)/(totalnumber - realnullnumber)
	print "precious:" + str(precious)
	print "recall:" + str(recall)
	print "F1:" + str((2*precious*recall)/(precious+recall))
	endtime = dt.datetime.now()

	##贪心算法
	print '贪婪计算pagerank'
	correctnumber = 0
	totalnumber = 0
	prenullnumber = 0
	realnullnumber = 0
	totaldoc = len(entitydoc)
	currentdoc = 0
	for doc in entitydoc[0:15]:
		currentdoc += 1
		print doc + "(" + str(currentdoc) + "/" + str(totaldoc) + "):"
		starttime0 = 0
		endtime0 = 0
		cn = 0
		tm = 0
		starttime0 = dt.datetime.now()
		entitydic,targetlist = doccandidate[doc]

		if len(entitydic) == 1:
			totalnumber += 1
			tm += 1
			if entitydic[targetlist[0][0]] == []:
				prenullnumber += 1
			if targetlist[0][1] == "NULL":
				realnullnumber += 1
			if targetlist[0][1].lower() == entitydic[targetlist[0][0]][0].lower():
				correctnumber += 1
				cn += 1
			print "mention:" + targetlist[0][0] + "   target:" + targetlist[0][1] + "     predict:" + entitydic[targetlist[0][0]][0]
		else:
			entitypairarray = getEntityPair1(entitydic)
			patharray = getPairArrayPath1(entitypairarray)
			edges,nodes = getEdges(patharray)
			print "edges:" + str(len(nodes))
			for m in entitydic.items():
				for n in m[1]:
					nodes.append(n)
			nodes = list(set(nodes))
			print "nodes:" + str(len(nodes))
			predict = getGraphByGreedSearch(entitydic,edges,nodes)
			for mention,target in targetlist:
				totalnumber += 1
				tm += 1
				if predict[mention] == "NULL":
					prenullnumber += 1
				if target == "NULL":
					realnullnumber += 1
				if predict[mention].lower() == target.lower():
					correctnumber += 1
					cn += 1
				print "mention:" + mention + "   target:" + target + "     predict:" + predict[mention]

		endtime0 = dt.datetime.now()
		print "doc_totalnumber:" + str(tm)
		print "doc_correctnumber:" + str(cn)
		print "doc_precious:" + str(float(cn)/tm)
		print "doc_runtime:" + str(endtime0 - starttime0)
		print "***************************************************"
	print "totalnumber:" + str(totalnumber)
	print "correctnumber:" + str(correctnumber)
	print "prenullnumber:" + str(prenullnumber)
	print "realnullnumber:" + str(realnullnumber)
	precious = float(correctnumber - prenullnumber)/(totalnumber - prenullnumber)
	recall = float(correctnumber - prenullnumber)/(totalnumber - realnullnumber)
	print "precious:" + str(precious)
	print "recall:" + str(recall)
	print "F1:" + str((2*precious*recall)/(precious+recall))
	endtime = dt.datetime.now()
	print "runtime:" + str(endtime - starttime)

def addTargetEntityToCandidate(entitydoc,doccandidate):
	"""

	生成候选实体集的时候,并不能保证真正的目标实体包含在候选实体集中,
	如果目标实体未包含在候选实体集中,将目标实体加入到候选实体集中,
	测试基于图方法的实体链接方法
	:param entitydoc:
	:param doccandidate:
	:return:
	"""
	for docId in entitydoc:
		entitydic, targetlist = doccandidate[docId]
		# print  targetlist
		for mention, target in targetlist:

			if target not in entitydic[mention]:
				entitydic[mention].append(target)

	print '覆盖成功'


def aidayago_main():
	starttime = dt.datetime.now()
	# entitydoc,doccandidate = get_aidayago_CandidateByRule()
	entitydoc,doccandidate = get_aidayago_CandidateByPriorRule()
	# entitydoc,doccandidate = get_aidayago_Candidate()
	print "Candidate entity complete!"
	correctnumber = 0
	totalnumber = 0
	prenullnumber = 0
	realnullnumber = 0
	totaldoc = len(entitydoc)
	currentdoc = 0
	# random.shuffle(entitydoc)
	print '计算该100篇内覆盖率'
	getCandidateEntityPrecision(entitydoc, doccandidate)
	addTargetEntityToCandidate(entitydoc, doccandidate)
	getCandidateEntityPrecision(entitydoc, doccandidate)
	for doc in entitydoc:
		currentdoc += 1
		print doc + "(" + str(currentdoc) + "/" + str(totaldoc) + "):"
		starttime0 = 0
		endtime0 = 0
		cn = 0
		tm = 0
		starttime0 = dt.datetime.now()
		entitydic,targetlist = doccandidate[doc]
		if len(entitydic) == 0:
			continue
		if len(entitydic) == 1:
			totalnumber += 1
			tm += 1
			if entitydic[targetlist[0][0]] == []:
				prenullnumber += 1
			if targetlist[0][1] == "NULL":
				realnullnumber += 1
			if targetlist[0][1].lower() == entitydic[targetlist[0][0]][0].lower():
				correctnumber += 1
				cn += 1
			print "mention:" + targetlist[0][0] + "   target:" + targetlist[0][1] + "     predict:" + entitydic[targetlist[0][0]][0]
		else:
			entitypairarray = getEntityPair1(entitydic)
			patharray = getPairArrayPath1(entitypairarray)
			edges,nodes = getEdges(patharray)
			print "edges:" + str(len(nodes))
			for m in entitydic.items():
				for n in m[1]:
					nodes.append(n)
			nodes = list(set(nodes))
			print "nodes:" + str(len(nodes))
			predict = getGraphByStandardPagelink1(entitydic,edges,nodes)
			# predict = getGraphByGreedSearch(entitydic,edges,nodes)
			for mention,target in targetlist:
				totalnumber += 1
				tm += 1
				if predict[mention] == "NULL":
					prenullnumber += 1
				if target == "NULL":
					realnullnumber += 1
				if predict[mention].lower() == target.lower():
					correctnumber += 1
					cn += 1
				print "mention:" + mention + "   target:" + target + "     predict:" + predict[mention]
		endtime0 = dt.datetime.now()
		print "doc_totalnumber:" + str(tm)
		print "doc_correctnumber:" + str(cn)
		print "doc_precious:" + str(float(cn)/tm)
		print "doc_runtime:" + str(endtime0 - starttime0)
		print "***************************************************"
	print "totalnumber:" + str(totalnumber)
	print "correctnumber:" + str(correctnumber)
	print "prenullnumber:" + str(prenullnumber)
	print "realnullnumber:" + str(realnullnumber)
	precious = float(correctnumber - prenullnumber)/(totalnumber - prenullnumber)
	recall = float(correctnumber - prenullnumber)/(totalnumber - realnullnumber)
	print "precious:" + str(precious)
	print "recall:" + str(recall)
	print "F1:" + str((2*precious*recall)/(precious+recall))
	endtime = dt.datetime.now()
	print "runtime:" + str(endtime - starttime)
	##########################################################################################
	correctnumber = 0
	totalnumber = 0
	prenullnumber = 0
	realnullnumber = 0
	# totaldoc = len(entitydoc)
	currentdoc = 0
	# random.shuffle(entitydoc)
	for doc in entitydoc:
		currentdoc += 1
		print doc + "(" + str(currentdoc) + "/" + str(totaldoc) + "):"
		starttime0 = 0
		endtime0 = 0
		cn = 0
		tm = 0
		starttime0 = dt.datetime.now()
		entitydic, targetlist = doccandidate[doc]
		if len(entitydic) == 0:
			continue
		if len(entitydic) == 1:
			totalnumber += 1
			tm += 1
			if entitydic[targetlist[0][0]] == []:
				prenullnumber += 1
			if targetlist[0][1] == "NULL":
				realnullnumber += 1
			if targetlist[0][1].lower() == entitydic[targetlist[0][0]][0].lower():
				correctnumber += 1
				cn += 1
			print "mention:" + targetlist[0][0] + "   target:" + targetlist[0][1] + "     predict:" + \
				  entitydic[targetlist[0][0]][0]
		else:
			entitypairarray = getEntityPair1(entitydic)
			patharray = getPairArrayPath1(entitypairarray)
			edges, nodes = getEdges(patharray)
			print "edges:" + str(len(nodes))
			for m in entitydic.items():
				for n in m[1]:
					nodes.append(n)
			nodes = list(set(nodes))
			print "nodes:" + str(len(nodes))
			# predict = getGraphByStandardPagelink1(entitydic, edges, nodes)
			predict = getGraphByGreedSearch(entitydic,edges,nodes)
			for mention, target in targetlist:
				totalnumber += 1
				tm += 1
				if predict[mention] == "NULL":
					prenullnumber += 1
				if target == "NULL":
					realnullnumber += 1
				if predict[mention].lower() == target.lower():
					correctnumber += 1
					cn += 1
				print "mention:" + mention + "   target:" + target + "     predict:" + predict[mention]
		endtime0 = dt.datetime.now()
		print "doc_totalnumber:" + str(tm)
		print "doc_correctnumber:" + str(cn)
		print "doc_precious:" + str(float(cn) / tm)
		print "doc_runtime:" + str(endtime0 - starttime0)
		print "***************************************************"
	print "totalnumber:" + str(totalnumber)
	print "correctnumber:" + str(correctnumber)
	print "prenullnumber:" + str(prenullnumber)
	print "realnullnumber:" + str(realnullnumber)
	precious = float(correctnumber - prenullnumber) / (totalnumber - prenullnumber)
	recall = float(correctnumber - prenullnumber) / (totalnumber - realnullnumber)
	print "precious:" + str(precious)
	print "recall:" + str(recall)
	print "F1:" + str((2 * precious * recall) / (precious + recall))
	endtime = dt.datetime.now()
	print "runtime:" + str(endtime - starttime)

def aida_ee_201010_main1():
	starttime = dt.datetime.now() 
	entitydoc,docmention = get_aidaee_Candidate()
	# entitydoc, doccandidate = get_aidaee_CandidateByRule()
	# entitydoc,doccandidate = get_aidaee_CandidateByPriorRule()
	correctnumber = 0
	nullnumber = 0
	totalnumber = 0
	for doc in entitydoc:
		print doc + ":"
		starttime0 = 0
		endtime0 = 0
		cn = 0
		tm = 0
		nm = 0
		starttime0 = dt.datetime.now()
		doclist = docmention[doc]
		targetlist = []
		entitydic = {}
		for mention,entityname in doclist:
			if entityname == "NULL":
				nm += 1
				tm += 1
				nullnumber += 1
				totalnumber += 1
			else:
				targetlist.append([mention,entityname])
				entitydic[mention] = getEntity(mention,entityname)
		entitydicList = splitDicToKsize(entitydic,kSize=5)
		predict = {}
		for entitydicTmp in entitydicList:
			# entitypairarray = getEntityPair1(entitydic)
			entitypairarray = getEntityPair1((entitydicTmp))
			patharray = getPairArrayPath1(entitypairarray)
			edges,nodes = getEdges(patharray)
			print "edges:" + str(len(nodes))
			for m in entitydic.items():
				for n in m[1]:
					nodes.append(n)
			nodes = list(set(nodes))
			print "nodes:" + str(len(nodes))
			# predict = getGraphByStandardPagelink1(entitydic,edges,nodes)
			predictTmp = getGraphByStandardPagelink1((entitydicTmp), edges, nodes)
			predict = dict(predict,**predictTmp)
		for mention,target in targetlist:
			totalnumber += 1
			tm += 1
			if predict[mention] == target:
				correctnumber += 1
				cn += 1
				# print 1111111111
			print "mention:" + mention + "   target:" + target + "     predict:" + predict[mention]
		endtime0 = dt.datetime.now()
		print "doc_totalnumber:" + str(tm)
		print "doc_correctnumber:" + str(cn)
		print "doc_nullnumber:" + str(nm)
		print "doc_precious:" + str(float(cn)/(tm-nm))
		print "doc_recall:" + str(float(cn)/tm)
		print "doc_runtime:" + str(endtime0 - starttime0)
		print "***************************************************"
	print "totalnumber:" + str(totalnumber)
	print "correctnumber:" + str(correctnumber)
	print "nullnumber:" + str(nullnumber)
	precious = float(correctnumber)/(totalnumber - nullnumber)
	recall = float(correctnumber)/totalnumber
	f_measure = 2*precious*recall/(precious+recall)
	print "precious:" + str(precious)
	print "recall:" + str(recall)
	print "F-measure:" + str(f_measure)
	endtime = dt.datetime.now()
	print "runtime:" + str(endtime - starttime)	

def test():
	cn = 0
	tm = 0
	entitydic = {'Giffords': ['Giffords', 'Gabrielle_Giffords', 'Gabrielle_giffords'], 'NBC': ['NBC', 'Major_League_Baseball_on_NBC', 'NBC_Sports', 'NFL_on_NBC', 'NHL_on_NBC', 'Weapon_of_mass_destruction', 'NBA_on_NBC', 'Olympics_on_NBC', 'NBC_Sunday_Night_Football', 'NBC_Red_Network'], 'Hallmark': ['Hallmark', 'Hallmark_Cards', 'Hallmark', 'Hallmark_Channel', 'Hallmark_Channel_(UK)', 'Hallmark_Channel_(International)', 'Hallmark,_Louisville', 'Diva_Universal_(Asia)', 'Hallmark_Channel_(Italy)', 'Hallmark_Institute_of_Photography'], 'Palin': ['Sarah_Palin', 'Michael_Palin', 'Brett_Palin', 'Bristol_Palin', 'Harold_Palin', 'Leo_Palin', 'Robert_Palin', 'John_Henry_Palin', 'Leigh_Palin', 'Todd_Palin']}
	targetlist = [['Hallmark','Hallmark_Cards'],['Palin','Sarah_Palin'],['Giffords','Gabrielle_Giffords'],['Palin','Sarah_Palin'],['Palin','Sarah_Palin'],['NBC','NBC']]
	entitypairarray = getEntityPair1(entitydic)
	patharray = getPairArrayPath1(entitypairarray)
	edges,nodes = getEdges(patharray)
	print "edges:" + str(len(nodes))
	for m in entitydic.items():
		for n in m[1]:
			nodes.append(n)
	nodes = list(set(nodes))
	print "nodes:" + str(len(nodes))
	predict = getGraphByStandardPagelink1(entitydic,edges,nodes)
	for mention,target in targetlist:
		tm = tm + 1
		if predict[mention] == target:
			cn = cn + 1
		print "mention:" + mention + "   target:" + target + "     predict:" + predict[mention]
	print "doc_totalnumber:" + str(tm)
	print "doc_correctnumber:" + str(cn)

def test1():
	starttime = dt.datetime.now()
	#entitydoc,doccandidate = get_aidayago_CandidateByRule()
	entitydoc,doccandidate = get_aidayago_CandidateByPriorRule()
	#entitydoc,doccandidate = get_aidayago_Candidate()
	print "Candidate entity complete!"
	correctnumber = 0
	totalnumber = 0
	prenullnumber = 0
	realnullnumber = 0
	totaldoc = len(entitydoc)
	currentdoc = 0
	currentdoc += 1
	starttime0 = 0
	endtime0 = 0
	cn = 0
	tm = 0
	starttime0 = dt.datetime.now()
	entitydic,targetlist = doccandidate['-DOCSTART- (25 PRESS)']

	if len(entitydic) == 1:
		totalnumber += 1
		tm += 1
		if entitydic[targetlist[0][0]] == []:
			prenullnumber += 1
		if targetlist[0][1] == "NULL":
			realnullnumber += 1
		if targetlist[0][1].lower() == entitydic[targetlist[0][0]][0].lower():
			correctnumber += 1
			cn += 1
		print "mention:" + targetlist[0][0] + "   target:" + targetlist[0][1] + "     predict:" + entitydic[targetlist[0][0]][0]
	else:
		entitypairarray = getEntityPair1(entitydic)
		patharray = getPairArrayPath1(entitypairarray)
		edges,nodes = getEdges(patharray)
		print "edges:" + str(len(nodes))
		for m in entitydic.items():
			for n in m[1]:
				nodes.append(n)
		nodes = list(set(nodes))
		print "nodes:" + str(len(nodes))
		predict = getGraphByStandardPagelink1(entitydic,edges,nodes)
		for mention,target in targetlist:
			totalnumber += 1
			tm += 1
			if predict[mention] == "NULL":
				prenullnumber += 1
			if target == "NULL":
				realnullnumber += 1
			if predict[mention].lower() == target.lower():
				correctnumber += 1
				cn += 1
			print "mention:" + mention + "   target:" + target + "     predict:" + predict[mention]
	endtime0 = dt.datetime.now()
	print "doc_totalnumber:" + str(tm)
	print "doc_correctnumber:" + str(cn)
	print "doc_precious:" + str(float(cn)/tm)
	print "doc_runtime:" + str(endtime0 - starttime0)
	print "***************************************************"
	print "totalnumber:" + str(totalnumber)
	print "correctnumber:" + str(correctnumber)
	print "prenullnumber:" + str(prenullnumber)
	print "realnullnumber:" + str(realnullnumber)
	precious = float(correctnumber - prenullnumber)/(totalnumber - prenullnumber)
	recall = float(correctnumber - prenullnumber)/(totalnumber - realnullnumber)
	print "precious:" + str(precious)
	print "recall:" + str(precious)
	print "F1:" + str((2*precious*recall)/(precious+recall))
	endtime = dt.datetime.now()
	print "runtime:" + str(endtime - starttime)



def aida_ee_201010_main_k_windows(k):
	"""

	:param k:
	:return:
	"""
	starttime = dt.datetime.now()
	entitydoc,doccandidate = get_aidaee_CandidateByRule()
	#entitydoc,doccandidate = get_aidaee_CandidateByPriorRule()
	#entitydoc,doccandidate = get_aidaee_Candidate()
	print "Candidate entity complete!"
	correctnumber = 0
	totalnumber = 0
	prenullnumber = 0
	realnullnumber = 0
	totaldoc = len(entitydoc)
	currentdoc = 0
	for doc in entitydoc:
		currentdoc += 1
		print doc + "(" + str(currentdoc) + "/" + str(totaldoc) + "):"
		starttime0 = 0
		endtime0 = 0
		cn = 0
		tm = 0
		starttime0 = dt.datetime.now()
		entitydic,targetlist = doccandidate[doc]

		if len(entitydic) == 1:
			totalnumber += 1
			tm += 1
			if entitydic[targetlist[0][0]] == []:
				prenullnumber += 1
			if targetlist[0][1] == "NULL":
				realnullnumber += 1
			if targetlist[0][1].lower() == entitydic[targetlist[0][0]][0].lower():
				correctnumber += 1
				cn += 1
			print "mention:" + targetlist[0][0] + "   target:" + targetlist[0][1] + "     predict:" + entitydic[targetlist[0][0]][0]
		else:
			entitypairarray = getEntityPair1(entitydic)
			patharray = getPairArrayPath1(entitypairarray)
			edges,nodes = getEdges(patharray)
			print "edges:" + str(len(nodes))
			for m in entitydic.items():
				for n in m[1]:
					nodes.append(n)
			nodes = list(set(nodes))
			print "nodes:" + str(len(nodes))
			predict = getGraphByStandardPagelink1(entitydic,edges,nodes)
			for mention,target in targetlist:
				totalnumber += 1
				tm += 1
				if predict[mention] == "NULL":
					prenullnumber += 1
				if target == "NULL":
					realnullnumber += 1
				if predict[mention].lower() == target.lower():
					correctnumber += 1
					cn += 1
				print "mention:" + mention + "   target:" + target + "     predict:" + predict[mention]
		endtime0 = dt.datetime.now()
		print "doc_totalnumber:" + str(tm)
		print "doc_correctnumber:" + str(cn)
		print "doc_precious:" + str(float(cn)/tm)
		print "doc_runtime:" + str(endtime0 - starttime0)
		print "***************************************************"
	print "totalnumber:" + str(totalnumber)
	print "correctnumber:" + str(correctnumber)
	print "prenullnumber:" + str(prenullnumber)
	print "realnullnumber:" + str(realnullnumber)
	precious = float(correctnumber - prenullnumber)/(totalnumber - prenullnumber)
	recall = float(correctnumber - prenullnumber)/(totalnumber - realnullnumber)
	print "precious:" + str(precious)
	print "recall:" + str(recall)
	print "F1:" + str((2*precious*recall)/(precious+recall))
	endtime = dt.datetime.now()
	print "runtime:" + str(endtime - starttime)

def aida_ee_201010_main_Greedy():
	starttime = dt.datetime.now()
	# entitydoc,doccandidate = get_aidaee_CandidateByRule()
	entitydoc,doccandidate = get_aidaee_CandidateByPriorRule()
	#entitydoc,doccandidate = get_aidaee_Candidate()
	print "Candidate entity complete!"
	correctnumber = 0
	totalnumber = 0
	prenullnumber = 0
	realnullnumber = 0
	totaldoc = len(entitydoc)
	currentdoc = 0
	kSize = 5 ###分割成5个实体一组
	ktmp = 0
	startPoint,endPoint = 0,0
	##随机洗牌
	# random.shuffle(entitydoc)
	print entitydoc[0:10]
	for doc in entitydoc[0:10]:
		currentdoc += 1
		print doc + "(" + str(currentdoc) + "/" + str(totaldoc) + "):"
		starttime0 = 0
		endtime0 = 0
		cn = 0
		tm = 0
		starttime0 = dt.datetime.now()
		entitydic,targetlist = doccandidate[doc]

		if len(entitydic) == 1:
			totalnumber += 1
			tm += 1
			if entitydic[targetlist[0][0]] == []:
				prenullnumber += 1
			if targetlist[0][1] == "NULL":
				realnullnumber += 1
			if targetlist[0][1].lower() == entitydic[targetlist[0][0]][0].lower():
				correctnumber += 1
				cn += 1
			print "mention:" + targetlist[0][0] + "   target:" + targetlist[0][1] + "     predict:" + entitydic[targetlist[0][0]][0]
		else:
			predict = {}
			entitypairarray = getEntityPair1(entitydic)
			patharray = getPairArrayPath1(entitypairarray)
			edges, nodes = getEdges(patharray)
			print "edges:" + str(len(nodes))
			for m in entitydic.items():
				for n in m[1]:
					nodes.append(n)
			nodes = list(set(nodes))
			print "nodes:" + str(len(nodes))
			# predict = getGraphByGreedSearch(entitydic, edges, nodes)
			predict = getGraphByStandardPagelink1(entitydic, edges, nodes)
			for mention,target in targetlist:
				totalnumber += 1
				tm += 1
				if predict[mention] == "NULL":
					prenullnumber += 1
				if target == "NULL":
					realnullnumber += 1
				if predict[mention].lower() == target.lower():
					correctnumber += 1
					cn += 1
				print "mention:" + mention + "   target:" + target + "     predict:" + predict[mention]

		endtime0 = dt.datetime.now()
		print "doc_totalnumber:" + str(tm)
		print "doc_correctnumber:" + str(cn)
		print "doc_precious:" + str(float(cn)/tm)
		print "doc_runtime:" + str(endtime0 - starttime0)
		print "***************************************************"
	print "totalnumber:" + str(totalnumber)
	print "correctnumber:" + str(correctnumber)
	print "prenullnumber:" + str(prenullnumber)
	print "realnullnumber:" + str(realnullnumber)
	precious = float(correctnumber - prenullnumber)/(totalnumber - prenullnumber)
	recall = float(correctnumber - prenullnumber)/(totalnumber - realnullnumber)
	print "precious:" + str(precious)
	print "recall:" + str(recall)
	print "F1:" + str((2*precious*recall)/(precious+recall))
	endtime = dt.datetime.now()
	print "runtime:" + str(endtime - starttime)


def testCandidateEntityPrecision():
	"""
	测试相关方法的候选实体的覆盖率
	:return:
	"""
	starttime = dt.datetime.now()

	# entitydoc,doccandidate = get_tackbp2014_CandidateByRule()
	entitydoc, doccandidate = get_aidayago_CandidateByRule()
	print '规则搜索生成候选实体：'
	getCandidateEntityPrecision(entitydoc, doccandidate)

	print '先验规则生成候选实体：'
	# entitydoc, doccandidate = get_tackbp2014_CandidateByPriorRule() #0.7982
	entitydoc, doccandidate = get_aidayago_CandidateByPriorRule()

	getCandidateEntityPrecision(entitydoc, doccandidate)



	print '编辑距离生成候选实体：'
	entitydoc,doccandidate = get_aidayago_CandidateByEditDistance()
	getCandidateEntityPrecision(entitydoc, doccandidate)


	endtime = dt.datetime.now()
	print "runtime:" + str(endtime - starttime)
	print "Candidate entity complete!"

def getCandidateEntityPrecision(entitydoc,doccandidate):
	"""
	计算文档的正确实体覆盖率以及每个实体指称mention生成的候选实体集
	:param entitydoc:链表，存的是文档的id
	:param doccandidate:字典，key为文档id,value 为一个链表；该链表包含两个
			部分，第一个为实体指称mention和它的目标实体，第二个值为一个字典，
			字典Key为实体指称mention，value为该实体指称的候选实体
	:return:
	"""
	rightNum = 0
	totalNum = 0
	canditaNum = 0
	for docId in entitydoc:
		entitydic,targetlist = doccandidate[docId]
		# print  targetlist
		for mention, target in targetlist:
			canditaNum += len(entitydic[mention])

			if target in entitydic[mention]:
				rightNum += 1
			totalNum += 1
	print '覆盖率:' + str(rightNum*1.0 / totalNum)
	print '每个实体生成的候选实体个数：'+ str(canditaNum*1.0 / totalNum)
	pass

if __name__ == '__main__':

	# aidayago_main()
	# tackbp2014_mainG.add_edge('s','s')()
	# aida_ee_201010_main()
	testCandidateEntityPrecision()
	# G = nx.Graph()
	# G.add_nodes_from('ssdasdfasdfasdfwewv')
	# G.add_edge('s','s')
	# G.add_edge('s', 'a')
	# G.add_edge('d', 'a')
	# pr = nx.pagerank(G)
	# print pr['s']
	# nx.draw(G)
	# plt.show()
	# aida_ee_201010_main_Greedy()
	# test1()
	# get_aidayago_Candidate()
	#print groups["-DOCSTART- (1113testa SOCCER)"]
	# aidayago_main()
