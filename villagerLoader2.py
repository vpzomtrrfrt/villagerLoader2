import vl2, random
#vl2.load("takeout-20160408T184318Z.zip")
#vl2.load("vl2.py")
d = vl2.load("Sdubzskycraft-0.73.zip")
r = d[random.randrange(len(d))]
print(r)
vl2.downloadFile(r)
