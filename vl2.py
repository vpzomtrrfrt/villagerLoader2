import zipfile, json, sys, os, hashlib
if sys.version_info < (3,0):
	# python 2
	from cStringIO import StringIO as BytesIO
	from zipfile import BadZipfile as BadZipFile
	from urllib2 import urlopen
else:
	from io import BytesIO
	from zipfile import BadZipFile as BadZipFile
	from urllib.request import urlopen
_datadir = ".villagerLoader2"
_luf = _datadir+"/lastUpdated.json"
class Openable():
	def open(self):
		return self.open("")
	def open(self, fn):
		return (self.open(), fn)
	def getStateData(self):
		return str(random.random())
class OpenableZip(Openable):
	def __init__(self, zf, zi):
		self.file = zf
		self.info = zi
	def open(self):
		return self.file.open(self.info)
	def getStateData(self):
		return _hash(self.open().read())
class OpenableFile(Openable):
	def __init__(self, filename):
		self.filename = filename
	def open(self):
		return open(self.filename, 'rb')
class OpenableURL(Openable):
	def __init__(self, url):
		self.url = url
	def open(self):
		return urlopen(self.url)
	def getStateData(self):
		return self.url
class OpenableCurseFile(Openable):
	def __init__(self, projectID, fileID):
		self.project = projectID
		self.file = fileID
	def open(self, fn):
		h = urlopen("http://minecraft.curseforge.com/projects/"+str(self.project))
		h.close()
		base = h.geturl()
		if "?" in base:
			base = base[:base.rfind("?")]
		print(base)
		tr = urlopen(base+"/files/"+str(self.file)+"/download")
		return (tr, "mods/"+tr.geturl().split("/")[-1])
	def getStateData(self):
		return str(self.project)+"/"+str(self.file)
def _readString(h):
	tr = h.read()
	if type(tr) == bytes:
		tr = tr.decode('utf-8')
	return tr
def _hash(s):
	hsh = hashlib.md5()
	if type(s) == str:
		s = s.encode('utf-8')
	hsh.update(s)
	return hsh.hexdigest()
def _mkparents(path):
	directory = "/".join(path.split("/")[:-1])
	try:
		os.makedirs(directory)
	except FileExistsError:
		# it exists already
		pass
def load(to):
	if type(to) == str:
		to = OpenableFile(to)
	tr = []
	try:
		z = zipfile.ZipFile(BytesIO(to.open().read()))
		# it's a zip file
		files = z.infolist()
		for f in files:
			if f.filename[:8] == "manifest":
				print("Found manifest: "+f.filename)
				tr += load(OpenableZip(z, f))
			elif f.filename[-1] == "/":
				# not a file
				pass
			elif f.filename[:10] == "overrides/":
				ta = {}
				ta["name"] = f.filename[10:]
				ta["file"] = OpenableZip(z, f)
				tr.append(ta)
			else:
				print("Unexpected file: "+f.filename)
	except BadZipFile:
		# not a zip file
		try:
			s = _readString(to.open())
			j = json.loads(s)
			# it's a json file
			if type(j) != list:
				if "files" in j:
					j = j["files"]
				else:
					j = []
					print("could not find files")
			for x in j:
				ta = {}
				if "url" in x:
					ta["file"] = OpenableURL(x["url"])
				elif "projectID" in x and "fileID" in x:
					# CurseForge mod
					ta["id"] = x["projectID"]
					ta["file"] = OpenableCurseFile(ta["id"], x["fileID"])
				else:
					print("Don't know how to download")
				if "file" in ta:
					if "name" in x:
						ta["name"] = x["name"]
					if "id" in x:
						ta["id"] = ta["id"]
					tr.append(ta)
		except json.decoder.JSONDecodeError:
			h = to.open()
			print(h.read())
	return tr
def downloadFile(data):
	if "name" in data:
		h = data["file"].open()
	else:
		h, data["name"] = data["file"].open("")
	if data["name"] == "":
		print("Can't find filename")
	else:
		if not "id" in data:
			data["id"] = data["name"]
		_mkparents(data["name"])
		out = open(data["name"], 'wb')
		out.write(h.read())
		out.close()
		ts = {
			"file": data["name"],
			"hash": _hash(data["file"].getStateData())
		}
		try:
			j = json.load(open(_luf, 'r'))
		except FileNotFoundError:
			j = {}
		j[data["id"]] = ts
		_mkparents(_luf)
		json.dump(j, open(_luf, "w"))
		return data["name"]
