import vl2, json, argparse
parser = argparse.ArgumentParser(description="A Minecraft modpack downloader")
parser.add_argument('source', nargs="?")
args = parser.parse_args()
src = None
cfgFile = vl2._datadir+"/config.json"
try:
	config = json.load(open(cfgFile, 'r'))
except FileNotFoundError:
	config = {}
if args.source == None:
	if "source" in config:
		src = config["source"]
else:
	src = args.source
if src == None:
	print("You must specify a pack source.")
else:
	save = True
	if "://" in src:
		to = vl2.OpenableURL(src)
	else:
		to = vl2.OpenableFile(src)
		save = False
	d = vl2.load(to)
	config["source"] = src
	vl2._mkparents(cfgFile)
	json.dump(config, open(cfgFile, 'w'))
	for x in d:
		if vl2.shouldDownloadFile(x, True):
			name = vl2.downloadFile(x)
			if name != None:
				print("Downloaded "+name)
