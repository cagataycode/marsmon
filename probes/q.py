import sys, json, urllib.request
BASE="https://mars.nasa.gov/rss/api/?feed=raw_images&category=mars2020&feedtype=json&num={num}&page={page}&order=sol+desc"
def get(extra="", num=1, page=0):
    url=BASE.format(num=num,page=page)+extra
    with urllib.request.urlopen(url, timeout=40) as r:
        raw=r.read()
    try: return json.loads(raw)
    except Exception: return {"_err": raw[:120]}
if __name__=="__main__":
    for q in sys.argv[1:]:
        d=get(q)
        if "_err" in d: print(f"{q:55s} ERR {d['_err']!r}"); continue
        im=d.get("images") or [{}]
        print(f"{q:55s} total={d.get('total_results')} first={im[0].get('camera',{}).get('instrument')} sol={im[0].get('sol')}")
