#coding=utf-8
import urllib
import re
'''
处理Labels_en.nt文件存入mysql中
'''
infile = open("../dataset/labels_en.nt")
# outfile = open('../dataset/labels_en.txt', 'w')
line = infile.readline()
num = 0
while line:
	match = re.search("(<http://dbpedia.org/resource/)(.*)(> <http://www.w3.org/2000/01/rdf-schema#label>)",line)
	if match:
		entity = match.group(2)
		entity1 = urllib.unquote(entity).decode('utf-8','ignore').encode('utf-8')
		strtemp = entity1 + '\t' + entity1 + '\n'
		# outfile.write(strtemp)
		if num == 119559 :
			print str(num) + ' ' + strtemp
			print len(str(entity1))
			break
		num += 1
	line = infile.readline()