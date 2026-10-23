import argparse,json,urllib.request
p=argparse.ArgumentParser();p.add_argument("file");p.add_argument("--api",default="http://localhost:8080/api");p.add_argument("--token",required=True)
a=p.parse_args();payload=json.load(open(a.file))
req=urllib.request.Request(a.api+"/admin/gis",data=json.dumps(payload).encode(),method="POST",
 headers={"Authorization":"Bearer "+a.token,"Content-Type":"application/json"})
with urllib.request.urlopen(req) as r:print(r.read().decode())
