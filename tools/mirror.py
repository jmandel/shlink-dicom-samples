"""Build and upload the jmandel/shlink-dicom-samples releases from inventory.json.

    python3 mirror.py manifest <set>    writes repo/manifests/<release>.json and repo/NOTICE.md
    python3 mirror.py upload <set>      uploads the assets of <release> (creating the release)

Assets are named <sha256>.dcm; the manifest maps each to the file names our scripts use.
"""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = "jmandel/shlink-dicom-samples"
RELEASE = {"codec-corpus": "codec-corpus-1", "objects": "objects-1", "slides": "slides-1"}
inv = json.load(open(f"{HERE}/inventory.json"))
idc = json.load(open(f"{HERE}/idc-series.json"))


def describe(r):
    s = r["source"] or ""
    m = re.search(r"amazonaws.com/([0-9a-f-]{36})/", s)
    if m:
        x = idc[m.group(1)]
        lic = x["licence"]
        url = "https://creativecommons.org/licenses/by/4.0/" if "4.0" in lic else "https://creativecommons.org/licenses/by/3.0/"
        coll = x["collection"]
        doi = x["doi"]
        what = f"analysis result {x['analysis']} for collection {coll}" if isinstance(x.get("analysis"), str) and x["analysis"] else f"collection {coll}"
        return dict(licence=f"{lic} ({url})",
                    attribution=f"Data from the NCI Imaging Data Commons (https://imaging.datacommons.cancer.gov), {what}, DOI https://doi.org/{doi}. Licensed under {lic}.",
                    deidentified="De-identified by TCIA/IDC before publication (Patient Identity Removed: YES).")
    if "SC_jpeg_no_color_transform" in s:
        return dict(licence="MIT (pydicom, https://github.com/pydicom/pydicom/blob/main/LICENSE); image from TCIA TCGA (CC BY 3.0)",
                    attribution="pydicom test file (pydicom/pydicom-data). Its image is a tile of a TCGA whole-slide image obtained from The Cancer Imaging Archive, CC BY 3.0.",
                    deidentified="A slide tile with no patient identity; from a de-identified TCIA collection.")
    if "cornerstone3D" in s:
        return dict(licence="MIT (cornerstonejs/cornerstone3D LICENSE)",
                    attribution="cornerstonejs/cornerstone3D dicomImageLoader testImages, made by its make-fixtures.py from ColorImage.dcm: kodim23 from the Kodak True Color suite (released for unrestricted use) in a synthetic Secondary Capture header.",
                    deidentified="Not medical data; no human subject.")
    if "highdicom" in s:
        return dict(licence="MIT (ImagingDataCommons/highdicom LICENSE)", attribution="highdicom test data (data/test_files).", deidentified="Test data with no real patient.")
    if "pylinac" in s:
        return dict(licence="MIT (jrkerns/pylinac LICENSE)", attribution="pylinac documentation file, a synthetic image from pylinac's image generator.", deidentified="Synthetic; no patient.")
    if "dcm2bq" in s:
        return dict(licence="Apache-2.0 (GoogleCloudPlatform/dcm2bq LICENSE)", attribution="dcm2bq test data; the embedded PDF is NationalRad's public sample report.", deidentified="Empty patient module; sample report.")
    raise SystemExit(f"no description for {r['id']}: {s}")


def rows(set_):
    return [r for r in inv if r.get("mirror") and r["set"] == set_]


def manifest(set_):
    rel = RELEASE[set_]
    files = []
    for r in rows(set_):
        files.append(dict(asset=f"{r['sha256']}.dcm", sha256=r["sha256"], size=r["size"], name=r["id"], source=r["source"], **describe(r)))
    os.makedirs(f"{HERE}/repo/manifests", exist_ok=True)
    json.dump(dict(release=rel, files=files), open(f"{HERE}/repo/manifests/{rel}.json", "w"), indent=1)
    notice()
    print(rel, len(files), "files,", len({f['sha256'] for f in files}), "assets,", round(sum(f["size"] for f in files) / 1e6, 1), "MB")


def notice():
    out = ["# NOTICE", "", "Every file in this repository's releases, with where it came from, its licence, the attribution its licence asks for, and its de-identification status. The same facts are in each release's manifest (`manifests/<release>.json`).", ""]
    for rel in sorted(os.listdir(f"{HERE}/repo/manifests")):
        m = json.load(open(f"{HERE}/repo/manifests/{rel}"))
        out += [f"## {m['release']}", "", "| File | SHA-256 | Size | Source | Licence | Attribution | De-identification |", "|---|---|---|---|---|---|---|"]
        for f in m["files"]:
            out.append(f"| {f['name']} | `{f['sha256']}` | {f['size']} | {f['source']} | {f['licence']} | {f['attribution']} | {f['deidentified']} |")
        out.append("")
    open(f"{HERE}/repo/NOTICE.md", "w").write("\n".join(out))


def upload(set_):
    rel = RELEASE[set_]
    m = json.load(open(f"{HERE}/repo/manifests/{rel}.json"))
    have = subprocess.run(["gh", "release", "view", rel, "-R", REPO, "--json", "assets", "--jq", ".assets[].name"], capture_output=True, text=True)
    if have.returncode != 0:
        subprocess.run(["gh", "release", "create", rel, "-R", REPO, "--title", rel, "--notes", f"Sample files for shlink-dicom ({set_}). See manifests/{rel}.json and NOTICE.md in the repository."], check=True)
        done = set()
    else:
        done = set(have.stdout.split())
    paths = {}
    for r in rows(set_):
        paths.setdefault(r["sha256"], r["path"])
    stage = f"{HERE}/stage/{rel}"
    os.makedirs(stage, exist_ok=True)
    todo = []
    for sha, p in paths.items():
        if f"{sha}.dcm" in done:
            continue
        dst = f"{stage}/{sha}.dcm"
        if not os.path.exists(dst):
            os.link(p, dst) if os.stat(p).st_dev == os.stat(stage).st_dev else subprocess.run(["cp", p, dst], check=True)
        todo.append(dst)
    print(rel, len(todo), "to upload,", len(done), "already there")
    for i in range(0, len(todo), 20):
        subprocess.run(["gh", "release", "upload", rel, "-R", REPO, *todo[i:i + 20]], check=True)
        print(f"  {min(i + 20, len(todo))}/{len(todo)}", flush=True)


if __name__ == "__main__":
    {"manifest": manifest, "upload": upload}[sys.argv[1]](sys.argv[2])
