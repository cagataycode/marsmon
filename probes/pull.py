import sys, json, time
sys.path.insert(0, sys.argv[0].rsplit('/',1)[0])
from q import get
cam, out = sys.argv[1], sys.argv[2]
maxpages = int(sys.argv[3]) if len(sys.argv)>3 else 10**6
rows=[]; page=0
while page<maxpages:
    d=get(f"&search=%7C{cam}", num=100, page=page)
    ims=d.get("images") or []
    if not ims: break
    for im in ims:
        rows.append({k:im.get(k) for k in ("imageid","sol","date_taken_mars","date_taken_utc","date_received","sample_type","site","drive")}
                    | {"inst":im["camera"]["instrument"],"dim":im["extended"].get("dimension"),"mastAz":im["extended"].get("mastAz"),"mastEl":im["extended"].get("mastEl"),"url":im["image_files"].get("full_res"),"large":im["image_files"].get("large")})
    page+=1; time.sleep(0.2)
json.dump(rows, open(out,"w"))
print(cam, len(rows), "rows,", page, "pages")
