#!/usr/bin/env python3
"""Zenodo deposit driver for the CACM preprint + artifact bundle.

Implements FINALIZATION_SPEC §3.2-§3.4:
  Record A — preprint PDF (publication/preprint)
  Record B — artifact bundle ZIP (dataset)
  cross-link via related_identifiers (isSupplementedBy / supplements)

Usage:
  python tools/zenodo_deposit_preprint.py preprint   # creates Record A
  python tools/zenodo_deposit_preprint.py artifact   # creates Record B
  python tools/zenodo_deposit_preprint.py crosslink  # adds cross-refs

Token: ~/.zenodo_token (chmod 600). Real Zenodo (NOT sandbox).
"""
import os, sys, json, pathlib, urllib.request, urllib.error, mimetypes

ZENODO_BASE = "https://zenodo.org/api"
TOKEN_PATH = pathlib.Path.home() / ".zenodo_token"
REPO = pathlib.Path(__file__).resolve().parent.parent

PREPRINT_PDF = REPO / "paper" / "main.pdf"
ARTIFACT_ZIP = REPO / "artifact_bundle_v1.zip"
ARTIFACT_README = REPO / "artifact_bundle" / "README.md"
PREPRINT_TEX = REPO / "paper" / "main.tex"

DOI_A_FILE = REPO / "paper" / "ZENODO_DOI_A.txt"
DOI_B_FILE = REPO / "paper" / "ZENODO_DOI_B.txt"
ID_A_FILE = REPO / "paper" / ".zenodo_id_A.txt"
ID_B_FILE = REPO / "paper" / ".zenodo_id_B.txt"

KEYWORDS = ["LLM security", "formal language theory", "regex",
            "syntactic monoids", "AC0", "defense in depth"]
CREATORS = [{"name": "Lopez, Joseph Robert"}]

def token():
    t = TOKEN_PATH.read_text().strip()
    if not t:
        sys.exit("ERROR: ~/.zenodo_token is empty")
    return t

def req(method, url, *, headers=None, data=None, raw=False):
    h = {"Authorization": f"Bearer {token()}"}
    if headers: h.update(headers)
    body = None
    if data is not None and not raw:
        body = json.dumps(data).encode()
        h.setdefault("Content-Type", "application/json")
    elif raw:
        body = data
    r = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=120) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode()
        except Exception:
            err_body = "<no body>"
        sys.exit(f"HTTP {e.code} on {method} {url}\n{err_body}")

def extract_abstract():
    s = PREPRINT_TEX.read_text()
    a = s.split(r"\begin{abstract}", 1)[1].split(r"\end{abstract}", 1)[0]
    # crude LaTeX strip for plaintext abstract
    import re
    a = re.sub(r"\\emph\{([^}]*)\}", r"<em>\1</em>", a)
    a = re.sub(r"\$([^$]*)\$", r"\1", a)
    a = re.sub(r"\\mathrm\{([^}]*)\}", r"\1", a)
    a = re.sub(r"\\textit\{([^}]*)\}", r"<em>\1</em>", a)
    a = re.sub(r"\{=\}", "=", a)
    a = re.sub(r"\\,", " ", a)
    a = re.sub(r"\\\\", " ", a)
    a = re.sub(r"---", "—", a)
    a = re.sub(r"--", "–", a)
    a = re.sub(r"\\([a-zA-Z]+)", "", a)
    a = re.sub(r"\s+", " ", a).strip()
    return f"<p>{a}</p>"

def title_from_tex():
    s = PREPRINT_TEX.read_text()
    import re
    m = re.search(r"\\title\{[^{]*?\\bfseries\s+([^}]+)\}", s)
    if m: return m.group(1).strip()
    m = re.search(r"\\title\{([^}]+)\}", s)
    if m: return m.group(1).strip()
    return "Algebraic and Computational Limits of LLM Guardrails"

def upload_file(bucket_url, local_path, remote_name):
    data = local_path.read_bytes()
    h = {"Content-Type": "application/octet-stream",
         "Authorization": f"Bearer {token()}"}
    r = urllib.request.Request(f"{bucket_url}/{remote_name}",
                               data=data, headers=h, method="PUT")
    try:
        with urllib.request.urlopen(r, timeout=300) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        sys.exit(f"Upload failed HTTP {e.code}: {e.read().decode()}")

def deposit_preprint():
    print("=== Record A: preprint ===")
    status, dep = req("POST", f"{ZENODO_BASE}/deposit/depositions", data={})
    print(f"  created id={dep['id']}")
    bucket = dep["links"]["bucket"]
    upload_file(bucket, PREPRINT_PDF, "main.pdf")
    print(f"  uploaded {PREPRINT_PDF.name}")
    title = title_from_tex()
    abstract = extract_abstract()
    metadata = {
        "metadata": {
            "title": title,
            "upload_type": "publication",
            "publication_type": "preprint",
            "description": abstract,
            "creators": CREATORS,
            "keywords": KEYWORDS,
            "license": "cc-by-4.0",
            "access_right": "open",
        }
    }
    req("PUT", dep["links"]["self"], data=metadata)
    print(f"  metadata set; title=\"{title}\"")
    status, pub = req("POST", dep["links"]["publish"])
    doi = pub.get("doi") or pub["metadata"]["doi"]
    print(f"  PUBLISHED — DOI={doi}")
    DOI_A_FILE.write_text(doi + "\n")
    ID_A_FILE.write_text(str(pub["id"]) + "\n")
    print(f"  saved → {DOI_A_FILE.name}, {ID_A_FILE.name}")

def deposit_artifact():
    print("=== Record B: artifact bundle ===")
    title = title_from_tex()
    status, dep = req("POST", f"{ZENODO_BASE}/deposit/depositions", data={})
    print(f"  created id={dep['id']}")
    bucket = dep["links"]["bucket"]
    upload_file(bucket, ARTIFACT_ZIP, "artifact_bundle_v1.zip")
    print(f"  uploaded {ARTIFACT_ZIP.name}")
    desc = "<pre>" + ARTIFACT_README.read_text().replace("<", "&lt;").replace(">", "&gt;") + "</pre>"
    metadata = {
        "metadata": {
            "title": f"Artifacts for \"{title}\"",
            "upload_type": "dataset",
            "description": desc,
            "creators": CREATORS,
            "keywords": KEYWORDS,
            "license": "cc-by-4.0",
            "access_right": "open",
        }
    }
    req("PUT", dep["links"]["self"], data=metadata)
    print(f"  metadata set")
    status, pub = req("POST", dep["links"]["publish"])
    doi = pub.get("doi") or pub["metadata"]["doi"]
    print(f"  PUBLISHED — DOI={doi}")
    DOI_B_FILE.write_text(doi + "\n")
    ID_B_FILE.write_text(str(pub["id"]) + "\n")
    print(f"  saved → {DOI_B_FILE.name}, {ID_B_FILE.name}")

def crosslink_one(record_id, peer_doi, relation, label):
    """newversion → edit → set related_identifiers → publish."""
    print(f"  [{label}] newversion of id={record_id} → add {relation} {peer_doi}")
    status, nv = req("POST", f"{ZENODO_BASE}/deposit/depositions/{record_id}/actions/newversion")
    new_url = nv["links"]["latest_draft"]
    # GET draft
    status, draft = req("GET", new_url)
    new_id = draft["id"]
    print(f"    new draft id={new_id}")
    # Modify metadata
    md = draft["metadata"]
    md.setdefault("related_identifiers", [])
    if not any(r.get("identifier") == peer_doi for r in md["related_identifiers"]):
        md["related_identifiers"].append({
            "identifier": peer_doi,
            "relation": relation,
            "scheme": "doi",
        })
    req("PUT", draft["links"]["self"], data={"metadata": md})
    status, pub = req("POST", draft["links"]["publish"])
    doi = pub.get("doi") or pub["metadata"]["doi"]
    print(f"    published — DOI={doi}")
    return new_id, doi

def crosslink():
    print("=== Cross-link records ===")
    doi_a = DOI_A_FILE.read_text().strip()
    doi_b = DOI_B_FILE.read_text().strip()
    id_a = int(ID_A_FILE.read_text().strip())
    id_b = int(ID_B_FILE.read_text().strip())
    new_a_id, new_a_doi = crosslink_one(id_a, doi_b, "isSupplementedBy", "A→B")
    new_b_id, new_b_doi = crosslink_one(id_b, doi_a, "supplements", "B→A")
    if new_a_doi != doi_a:
        print(f"  Record A DOI changed: {doi_a} → {new_a_doi}")
        DOI_A_FILE.write_text(new_a_doi + "\n")
        ID_A_FILE.write_text(str(new_a_id) + "\n")
    if new_b_doi != doi_b:
        print(f"  Record B DOI changed: {doi_b} → {new_b_doi}")
        DOI_B_FILE.write_text(new_b_doi + "\n")
        ID_B_FILE.write_text(str(new_b_id) + "\n")

def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("preprint", "artifact", "crosslink"):
        sys.exit("usage: zenodo_deposit_preprint.py {preprint|artifact|crosslink}")
    {
        "preprint":  deposit_preprint,
        "artifact":  deposit_artifact,
        "crosslink": crosslink,
    }[sys.argv[1]]()

if __name__ == "__main__":
    main()
