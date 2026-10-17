# shlink-dicom-samples

Copies of the public DICOM sample files that [shlink-dicom](https://github.com/jmandel/shlink-dicom)'s tests and checks use, kept here so the tests still run if a source moves or disappears.

Only files whose source clearly allows redistribution are here: NCI Imaging Data Commons data under CC BY 3.0 or 4.0, and test files that their projects made themselves under MIT or Apache-2.0. Other test files (GDCM, Orthanc, fo-dicom, dcm4che, files attached to issues, CC BY-NC collections) are still fetched from their sources, and a check skips them when they are gone.

## Releases

| Release | What | Used by |
|---|---|---|
| `codec-corpus-1` | Codec test cases: IDC instances chosen for transfer syntax and vendor coverage, and a few project-made test files | `codec-corpus/scripts` |
| `objects-1` | Object-type and display test files (SR, SEG, RT, PDF, presentation states, waveforms, and more) | `web/checks/objects/fetch-samples.py` |
| `slides-1` | Whole-slide images and their annotations from IDC | `web/view/wsi-tools`, `web/checks/share-checks.mjs`, `imaging-sandbox` |

Each asset is named by its SHA-256 (`<sha256>.dcm`) and is downloaded from

    https://github.com/jmandel/shlink-dicom-samples/releases/download/<release>/<sha256>.dcm

`manifests/<release>.json` lists every file: its SHA-256, size, the name the scripts use, its original source URL, licence, attribution text and de-identification status. `NOTICE.md` has the same facts as one table per release.

## How the scripts use it

They look for a file in this mirror first, then at its original source, and check its SHA-256 either way. A file that matches neither is skipped, not used.

## Licences and attribution

Each file keeps its own licence; there is no licence for the collection as a whole. The IDC files are CC BY. When you use them, cite the collection DOI given in the manifest and NOTICE, and the NCI Imaging Data Commons (https://imaging.datacommons.cancer.gov). The project-made test files are under their projects' MIT or Apache-2.0 licences, named per file.

All human data here was de-identified by its publishers (TCIA and IDC) before release. No file comes from a patient's own records.
