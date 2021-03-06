import zipfile, json, sys, os, hashlib, traceback
if sys.version_info < (3,0):
	# python 2
	from cStringIO import StringIO as BytesIO
	from zipfile import BadZipfile as BadZipFile
	from urllib2 import urlopen, Request
else:
	from io import BytesIO
	from zipfile import BadZipFile as BadZipFile
	from urllib.request import urlopen, Request
_datadir = ".villagerLoader2"
_luf = _datadir+"/lastUpdated.json"
class Openable():
	def open(self):
		return self.open_fn("")[0]
	def open_fn(self, fn):
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
	def open_fn(self, fn):
		return (urlopen(Request(self.url, headers={'User-Agent': "Not Chrome"})), fn or ("mods/" + os.path.basename(self.url)))
	def getStateData(self):
		return self.url
class OpenableCurseFile(Openable):
	def __init__(self, projectID, fileID):
		self.project = projectID
		self.file = fileID
	def open_fn(self, fn):
		h = urlopen(Request("https://addons-ecs.forgesvc.net/api/v2/addon/"+str(self.project) + "/file/" + str(self.file)))
		info = json.load(h)
		h.close()
		tr = urlopen(Request(info["downloadUrl"], headers={"User-Agent": "Not Chrome"}))
		return (tr, "mods/" + info["fileName"])
	def getStateData(self):
		return str(self.project)+"/"+str(self.file)
	def getTmpName(self):
		return str(self.project)+"/"+str(self.file)
def _readString(h):
	tr = h.read()
	if type(tr) == bytes:
		tr = tr.decode('utf-8')
	return tr
def _hash(s):
	hsh = hashlib.md5()
	s = repr(s).encode('utf-8')
	hsh.update(s)
	tr = hsh.hexdigest()
	return tr
def _mkparents(path):
	directory = "/".join(path.split("/")[:-1])
	try:
		os.makedirs(directory)
	except OSError:
		# it exists already
		pass
def _autofillData(data):
	if not "id" in data:
		data["id"] = data["name"]
	data["id"] = str(data["id"])
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
						ta["id"] = x["id"]
					tr.append(ta)
		except json.decoder.JSONDecodeError:
			h = to.open()
			l = h.readlines()
			h.close()
			for L in l:
				sp = L.decode('utf-8').strip().split("][")
				if len(sp) == 3:
					ta = {}
					ta["id"] = sp[0]
					ta["name"] = sp[1]
					ta["file"] = OpenableURL(sp[2])
					tr.append(ta)
				else:
					print("Wrong number of parameters in VL file")
	return tr
def downloadFile(data):
	try:
		if "name" in data:
			h = data["file"].open()
		else:
			h, data["name"] = data["file"].open_fn("")
		if data["name"] == "":
			print("Can't find filename")
		else:
			_autofillData(data)
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
	except KeyboardInterrupt:
		print()
		print("Exiting due to Ctrl-C")
		exit()
	except:
		traceback.print_exc()
		if "name" in data:
			name = data["name"]
		elif hasattr(data["file"], "getTmpName"):
			name = data["file"].getTmpName()
		else:
			print(data)
			name = "something"
		print("Failed to download "+name)
def shouldDownloadFile(data, delete=False):
	try:
		j = json.load(open(_luf, 'r'))
		_autofillData(data)
		if data["id"] in j:
			ld = j[data["id"]]
			hsh = _hash(data["file"].getStateData())
			if ("name" in data and data["name"] != ld["file"]) or hsh != ld["hash"]:
				if delete:
					os.remove(ld["file"])
					j.pop(data["id"])
					json.dump(j, open(_luf, 'w'))
					print("Removed "+ld["file"])
				return True
			else:
				return False
		else:
			return True
	except FileNotFoundError:
		print("didn't find JSON")
		return True
def handleRemovedFiles(dl):
	ids = []
	try:
		j = json.load(open(_luf, 'r'))
	except FileNotFoundError:
		j = {}
	for data in dl:
		_autofillData(data)
		ids.append(data["id"])
	for key in list(j.keys()):
		if not key in ids:
			info = j.pop(key)
			os.remove(info["file"])
			json.dump(j, open(_luf, 'w'))
			print("Removed "+info["file"])
