# Inventory of fetched sample data for the shlink-dicom-samples mirror: every file, its set,
# source, licence and whether it may be redistributed. Writes inventory.json and prints totals.
import json, glob, os, re, collections
REPO = os.path.expanduser("~/hobby/shlink-dicom")
CC = os.path.join(REPO, "codec-corpus")
out = []

def decide(lic: str, kind: str = "") -> str:
    l = (lic or "").lower()
    if "nc" in re.findall(r"by-([a-z]+)", l) or "-nc" in l or "noncommercial" in l: return "no"
    if re.search(r"cc by [34]\.0|cc0|\bmit\b|apache-2\.0|bsd", l) and "no explicit" not in l and "no licence file" not in l: return "yes"
    if re.search(r"ms-pl|mpl|gpl", l): return "ask"
    return "no"

# codec corpus: fetched kinds only (generated/repair/strip are made by our scripts from these).
for f in sorted(glob.glob(f"{CC}/formats/*/cases.json")):
    fmt = f.split("/")[-2]
    for c in json.load(open(f))["cases"]:
        s = c.get("source", {}); k = s.get("kind")
        if k in ("generated", "repair", "strip"): continue
        path = f"{CC}/formats/{fmt}/samples/{c['id']}.dcm"
        if k == "local":
            lic, d, url = "Josh Mandel's own data", "no", None
        elif k == "pydicom":
            lic, url = "MIT (pydicom / pydicom-data test files)", f"pydicom.data.get_testdata_file('{s.get('name')}')"
            d = "yes"
        else:
            lic = s.get("license") or s.get("licence") or "?"
            url = s.get("url")
            d = decide(lic)
        out.append(dict(set="codec-corpus", id=f"{fmt}/{c['id']}", path=path, size=c.get("size", 0), kind=k, source=url or s.get("origin"), licence=lic, decision=d))

# object and display test set
m = json.load(open(f"{REPO}/web/checks/objects/samples.json"))
for c in m["cases"]:
    for fd in c.get("fileDetails", []):
        if "path" not in fd: continue
        lic = fd.get("licence", "?")
        d = decide(lic)
        if fd["source"].startswith("pydicom"): d = "yes"
        if "gdcm" in fd["source"] and "sourceforge" in fd["source"]: d = "no"  # gdcmData has no licence file
        out.append(dict(set="objects", id=f"{c['id']}/{fd['path']}", path=f"{m['dataRoot']}/{c['id']}/{fd['path']}", size=fd.get("sizeBytes", 0), kind="", source=fd["source"], licence=lic, decision=d))

# whole-slide inputs (IDC)
SL = "/media/barracuda/shlink-dicom-slides/dl"
lic_of = {"29368d94": "CC BY 4.0 (IDC cptac_brca)", "321c7412": "CC BY 4.0 (IDC cptac_luad)", "4a6b5ed5": "CC BY 4.0 (IDC cptac_luad)",
          "5928613e": "CC BY 4.0 (IDC cptac_ov)", "b67a9aee": "CC BY 4.0 (IDC htan_ohsu)", "76cce1d6": "CC BY 4.0 (IDC htan_wustl)"}
for d in sorted(os.listdir(SL)):
    for root, _, files in os.walk(f"{SL}/{d}"):
        for fn in files:
            p = f"{root}/{fn}"
            sid = d[:8] if d != "study-26f5b0cf" else root.split("/")[-1].split("-", 1)[1][:8]
            lic = lic_of.get(sid, "CC BY 3.0/4.0 (IDC tcga_luad)")
            out.append(dict(set="slides", id=p[len(SL) + 1:], path=p, size=os.path.getsize(p), kind="idc", source=f"https://idc-open-data.s3.amazonaws.com/{d if d != 'study-26f5b0cf' else root.split('/')[-1].split('-',1)[1]}/{fn}", licence=lic, decision="yes"))

json.dump(out, open("/media/barracuda/mirror/inventory.json", "w"), indent=1)
tot = collections.defaultdict(lambda: [0, 0])
bylic = collections.defaultdict(lambda: [0, 0])
for r in out:
    exists = os.path.exists(r["path"])
    tot[(r["set"], r["decision"])][0] += 1; tot[(r["set"], r["decision"])][1] += r["size"]
    if r["decision"] != "yes": bylic[(r["set"], r["decision"], r["licence"][:70])][0] += 1; bylic[(r["set"], r["decision"], r["licence"][:70])][1] += r["size"]
for k, v in sorted(tot.items()): print(f"{k[0]:13} {k[1]:4} {v[0]:6} files {v[1]/1e6:9.1f} MB")
print()
for k, v in sorted(bylic.items(), key=lambda x: (x[0][0], x[0][1], -x[1][1])): print(f"{k[0]:13} {k[1]:4} {v[0]:4} {v[1]/1e6:7.1f} MB  {k[2]}")
print("missing locally:", sum(not os.path.exists(r["path"]) for r in out))
