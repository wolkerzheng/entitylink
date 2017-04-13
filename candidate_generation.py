#encoding=utf8
import MySQLdb
import wikipedia
import threading
import Levenshtein
import datetime as dt
import re
########################################################################################

'''
使用mysql内部全文搜索方式(full text)获取候选实体，准确率不高
'''
def getCanByMatch(mention):
	canlist = []
	conn= MySQLdb.connect(host='192.168.140.98',port=3306,user='root',passwd = '**',db ='entitylinkdb')
	cur = conn.cursor()
	mysql = "select entityname from labels  where match(entitystr) against (\""+mention+"\" in natural language mode) limit 5"
	#mysql = "select entityname from labels  where match(entitystr) against (\""+mention+"\" in boolean mode) limit 4"
	cur.execute(mysql)
	resultlist = cur.fetchall()
	for each in resultlist:
		canlist.append(each[0])
	cur.close()
	conn.commit()
	conn.close()
	return canlist

#######################################################################################
'''
通过搜索规则的方式生成候选实体
该方法模仿了我们手动搜索维基百科词条的步骤，当我们搜索某
一个目标实体时，首先键入代表该实体的字符串，这个字符串正如实体消歧任
务中的实体指称，可能是规范的或者不规范的实体表示形式，这些字符串表示
可能是精确的，也可能具有某些歧义。当目标实体和我们搜索的字符串一致时
会直接返回目标实体，这正如直接从 label 数据集获得候选实体。当我们搜索的
字符串具有歧义时我们会被引导到消歧页面，然后从消歧页面选择我们想要查
找的实体，我们从 disambiguation 数据集添加候选实体就是这样的目的。 当我
们以别称或者绰号搜索某个人名时，如果这个绰号没有歧义会被自动重定向到
目标实体。如果有歧义则通过消歧页面选择目标实体。
'''
def getCanByLabels(mention):#通过Labels_en.nt文件获取候选实体
	canlist = []
	conn= MySQLdb.connect(host='192.168.140.98',port=3306,user='root',passwd = '
			      **',db ='entitylinkdb')
	cur = conn.cursor()
	stmt = "select entitystr from labels where entityname = \"" + mention + "\""
	cur.execute(stmt)
	result = cur.fetchall()
	if result:
		for each in result:
			canlist.append(each[0])
	cur.close()
	conn.commit()
	conn.close()
	return canlist

def getCanByRedirect(mention):#通过Redirect_en.nt文件获取候选实体
	canlist = []
	conn= MySQLdb.connect(host='192.168.140.98',port=3306,user='root',passwd = '**',db ='entitylinkdb')
	cur = conn.cursor()
	stmt = "select redirectname from redirect where entityname = \"" + mention + "\""
	cur.execute(stmt)
	result = cur.fetchall()
	if result:
		for each in result:
			canlist.append(each[0])
	cur.close()
	conn.commit()
	conn.close()
	return canlist

def getCanByDisambiguation(mention):#通过Disambiguation_en.nt文件获取候选实体
	canlist = []
	conn= MySQLdb.connect(host='192.168.140.98',port=3306,user='root',passwd = '***',db ='entitylinkdb')
	cur = conn.cursor()
	stmt1 = "select disname  from disambiguation where entityname = \"" + mention + "\""
	cur.execute(stmt1)
	result = cur.fetchall()
	if result:
		for each in result:
			canlist.append(each[0])

	stmt2 = "select disname  from disambiguation where entityname = \"" + mention + "_(disambiguation)" + "\""
	cur.execute(stmt2)
	result = cur.fetchall()
	if result:
		for each in result:
			canlist.append(each[0])
	cur.close()
	conn.commit()
	conn.close()
	return list(set(canlist))


def getCanByRule(mention):
	canlist = []
	labelslist = getCanByLabels(mention)
	redirectlist = getCanByRedirect(mention)
	dislist = getCanByDisambiguation(mention)
	canlist.extend(labelslist)
	canlist.extend(redirectlist)
	canlist.extend(dislist)
	if redirectlist != []:
		for can in redirectlist:
			canlist.extend(getCanByLabels(can))
			canlist.extend(getCanByDisambiguation(can))
	if canlist == []:
		canlist = getCanByMatch(mention)
	if canlist == []:
		canlist = get_can(mention,5)
	return list(set(canlist))

#######################################################################################
'''
通过锚文本先验概率的方法生成候选实体
锚文本指的是一个实体的维基百科页面可以通过其正文中的锚文本跳转到另一个实体的维基百科页面
我们对于所有锚文本中的实体指称 m，统计所有与之共现的实体名
e1,e2,e3,…与 m 的共现次数，我们可以得出条件概率
在uriGivenSf.txt文本中记录了所有在wikipedia article中的先验概率
用先验概率获得实体指称所有可能的目标实体

'''

def getCanByPrior(mention):#通过先验概率获取所有可能的候选实体
	canlist = []
	conn= MySQLdb.connect(host='192.168.140.98',port=3306,user='root',passwd = '***',db ='entitylinkdb')
	cur = conn.cursor()
	stmt = "select entity from popularity where mention = \"" + mention + "\""
	cur.execute(stmt)
	result = cur.fetchall()
	if result:
		for each in result:
			canlist.append(each[0])
	cur.close()
	conn.commit()
	conn.close()
	return canlist


def getCanByPrior1(mention,maxnum):#可设置获取候选实体的最大个数
	canlist = []
	conn= MySQLdb.connect(host='192.168.140.98',port=3306,user='root',passwd = '***',db ='entitylinkdb')
	cur = conn.cursor()
	stmt = "select entity,prob from popularity where mention = \"" + mention + "\""
	cur.execute(stmt)
	result = cur.fetchall()
	if len(result) <= maxnum:
		canlist = [x[0] for x in result]
	else:
		result = sorted(list(result), key=lambda x:float(x[1]),reverse=True)
		canlist = [x[0] for x in result[0:maxnum]]
	for i in canlist:
		if "_(disambiguation)" in i:
			canlist.extend(getCanByDisambiguation(i))
			canlist.remove(i)
	#if result:
	#	for mention,prob in result:
	#		canlist.append([])
	cur.close()
	conn.commit()
	conn.close()
	return canlist

def getCanByPriorRule(mention):#如果在先验概率表中查不到，使用搜索规则的方法和Wikipedia API查找
	canlist = []
	#priorlist = getCanByPrior(mention)
	priorlist = getCanByPrior1(mention,10)
	canlist.extend(priorlist)
	if priorlist == []:
		canlist.extend(getCanByRule(mention))
	if canlist == []:
		canlist = getCanByMatch(mention)
	if canlist == []:
		canlist = get_can(mention,5)
	return canlist


def main():# 测试不同方法目标实体在候选实体集中的覆盖率
	entitydoc,docmention = get_mention()
	totalnumber = 0
	covernumber = 0
	docnumber = 0
	errorlist = []
	totalcan = 0
	nullnumber = 0
	nulllist = []
	for doc in entitydoc:
		tm = 0
		cn = 0
		docnumber += 1
		print docnumber
		mentionlist = docmention[doc]
		for mention,entityname in mentionlist:
			tm += 1
			totalnumber += 1
			result = getCanByRule(mention)
			if result == []:
				nulllist.append(mention)
				nullnumber += 1
			totalcan += len(result)
			if entityname in result:
				cn += 1
				covernumber += 1
			else:
				errorlist.append([mention,entityname])
		print "**********************"
		print "total:" + str(tm)
		print "cover:" + str(cn)
	print totalnumber
	print covernumber
	print float(covernumber)/totalnumber
	print float(totalcan)/totalnumber
	print float(totalcan)/covernumber
	print nullnumber
	print nulllist

def main1():
	entitydoc,docmention = get_mention()
	totalnumber = 0
	covernumber = 0
	docnumber = 0
	errorlist = []
	totalcan = 0
	nullnumber = 0
	nulllist = []
	for doc in entitydoc:
		tm = 0
		cn = 0
		docnumber += 1
		print docnumber
		mentionlist = docmention[doc]
		for mention,entityname in mentionlist:
			tm += 1
			totalnumber += 1
			#result = getCanByRedirect(mention)
			#result = getCanByPrior1(mention,10)
			result = getCanByPriorRule(mention)
			if result == []:
				nulllist.append(mention)
				nullnumber += 1
			totalcan += len(result)
			if entityname in result:
				cn += 1
				covernumber += 1
			else:
				errorlist.append([mention,entityname])
		print "**********************"
		print "total:" + str(tm)
		print "cover:" + str(cn)
	print totalnumber
	print covernumber
	print float(covernumber)/totalnumber

	print float(totalcan)/totalnumber
	print float(totalcan) / covernumber
	print nullnumber
	print nulllist


#######################################################################################
'''
使用wikipedia API 获取候选实体，联网调用返回比较慢，使用多线程
输入任意字符串，返回与字符串相似的维基百科中的实体
'''

def get_can(mention,maxnum):
	resultlist = wikipedia.search(mention,results=maxnum)
	returnlist = []
	for each in resultlist:
		returnlist.append("_".join(each.encode("utf-8").split()))
	return returnlist

def get_mention():
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
			mentionlist.append([mention,entityname])
		docmention[doc] = mentionlist
	cur.close()
	conn.commit()
	conn.close()
	return entitydoc,docmention



def test(entitydoc,docmention):
	totalnumber = 0
	covernumber = 0
	docnumber = 0
	for doc in entitydoc:
		tm = 0
		cn = 0
		docnumber += 1
		print docnumber
		mentionlist = docmention[doc]
		for mention,entityname in mentionlist:
			tm += 1
			totalnumber += 1
			result = get_can(mention,5)
			if entityname in result:
				cn += 1
				covernumber += 1
		print "**********************"
		print "total:" + str(tm)
		print "cover:" + str(cn)
	print totalnumber
	print covernumber

class getentity(threading.Thread):
	def __init__(self,mention,maxnum):
		threading.Thread.__init__(self)
		self.mention = mention
		self.maxnum = maxnum
		self.resultlist = []

	def run(self):
		self.resultlist = get_can(self.mention,self.maxnum)

def test1(entitydoc,docmention,maxnum):
	totalnumber = 0
	covernumber = 0
	docnumber = 0
	for doc in entitydoc:
		docnumber += 1
		mentionlist = docmention[doc]
		threads = []
		entitylist = []
		resultlist = []
		for mention,entityname in mentionlist:
			threads.append(getentity(mention,maxnum))
			entitylist.append(entityname)
	 	for t in threads:
	 		t.start()
	 	for t in threads:
	 		t.join()
	 		resultlist.append(t.resultlist)
	 	tm = 0
	 	cn = 0
	 	for i in range(len(entitylist)):
	 		tm += 1
	 		totalnumber += 1
	 		if entitylist[i] in resultlist[i]:
	 			cn += 1
	 			covernumber += 1
	 	print "***************doc:" + str(docnumber) + "*************"
		print "total:" + str(tm)
		print "cover:" + str(cn)
	print totalnumber
	print covernumber
	print float(covernumber)/totalnumber	

#######################################################################################

'''
编辑距离是衡量字符串相似度的一种方法。一个字符串经过一系列特定
的操作变化为另一个字符串的最少操作数称作编辑距离，特定操作指的是对字
符进行插入、删除、替换操作。
使用编辑距离的方法生成候选实体，dis设置最大距离
'''
#返回与实体指编辑距离小于dis的候选实体列表canList
def getCandidateByEditdistance(mention,dis=6):
    if mention=='': return []
    if mention.isupper():
        stmt="select entityname from labels where left(entitystr,1)=\""+mention[0]+"\""
    else:
        piece=mention.split('_')
        mention='+'+' +'.join(piece)
        stmt="select entityname from labels where match (entitystr) AGAINST (\""+mention+"\"IN BOOLEAN MODE)"
	'''
	首先筛选与候选实体相近的候选实体
	'''
    canList=[]

    conn=MySQLdb.connect(host="192.168.140.98",user="root",passwd="**",db="entitylinkdb")
    cur=conn.cursor()
    cnt=cur.execute(stmt)
    if cnt==0: return []
    res=cur.fetchall()
    if mention.isupper():#若实体指称全为大写
        letterSetM=set([l.lower() for l in list(mention)])
        for r in res:
           letterLs=list(set(r[0].split('_'))-set(['The','the','and','with','to','at','in','a','of']))
           letterSet=set([w[0]  for w in letterLs if w ])
           if  letterSetM.issubset(letterSet):
               canList.append(r[0])
    else:
        #否则直接匹配
        canList=[en[0] for en in res if Levenshtein.distance(re.sub('_\(.*\)|,_.*','',en[0]),mention)<dis]

        
    canList=list(set(canList))
    if cur: cur.close()
    if conn: conn.commit();conn.close()
    return canList

#采用基于编辑距离的方法生成候选实体
#input：mentionList=[mention1,mention2]实体指称列表
#output：dic={mention1:[can1,can2],mention2:[can21,can22]}can1,can2为实体指称mention1的候选实体
def getCandidate(mentionlist):
    dic={}
    startTime=dt.datetime.now()
    for name in mentionlist:
        dic[name]=getCandidateByEditdistance(name,4)#int(len(name)*0.3)
    print "distance=2"
    for item in dic.keys():
        print "mention: "+item+"  candidate count: "+str(len(dic[item]))
        #print "candidate:"+str(dic[item])
    print "---------Time Used---------"
    endTime=dt.datetime.now()
    print 'time used:'+str(endTime-startTime)
    return dic#
#######################################################################################


if __name__ == '__main__':
	# print '规则'
	# main()
	print '先验：'
	main1()
