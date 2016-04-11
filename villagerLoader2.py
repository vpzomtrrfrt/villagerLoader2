import vl2, random
#vl2.load("takeout-20160408T184318Z.zip")
#vl2.load("vl2.py")
d = vl2.load("Sdubzskycraft-0.73.zip")
for x in d:
	if vl2.shouldDownloadFile(x, True):
		name = vl2.downloadFile(x)
		if name != None:
			print("Downloaded "+name)
