"""Embed job texts and O*NET occupations with an open-source sentence-embedding model.

Outputs (data/interim/)
  onet.parquet             one row per O*NET occupation (code, soc6, title, text)
  emb_family.npy           family text per job class (rows align with jobs.parquet)
  emb_level.npy            title + level paragraph per job class
  emb_family_query.npy     family text with the model's retrieval-query prefix (for matching)
  emb_onet.npy             O*NET occupation texts
"""
import io
import zipfile

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

from common import EMBED_MODEL, INTERIM, ONET_ZIP, ensure_dirs

QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
N_TASKS = 8


def read_onet(name):
    with zipfile.ZipFile(ONET_ZIP) as z:
        path = next(p for p in z.namelist() if p.endswith(f"/{name}"))
        return pd.read_csv(io.BytesIO(z.read(path)), sep="\t", dtype=str)


def onet_docs():
    occ = read_onet("Occupation Data.txt")
    tasks = read_onet("Task Statements.txt")
    tasks = tasks[tasks["Task Type"] == "Core"] if "Task Type" in tasks else tasks
    top = (tasks.groupby("O*NET-SOC Code")["Task"]
           .apply(lambda s: " ".join(s.head(N_TASKS))).rename("tasks"))
    occ = occ.join(top, on="O*NET-SOC Code")
    occ["tasks"] = occ["tasks"].fillna("")
    occ["soc6"] = occ["O*NET-SOC Code"].str[:7].str.replace("-", "")
    occ["text"] = occ["Title"] + ". " + occ["Description"] + " Tasks: " + occ["tasks"]
    return occ.rename(columns={"O*NET-SOC Code": "onet_code", "Title": "title"})[
        ["onet_code", "soc6", "title", "text"]].reset_index(drop=True)


def main():
    ensure_dirs()
    jobs = pd.read_parquet(INTERIM / "jobs.parquet")
    onet = onet_docs()
    onet.to_parquet(INTERIM / "onet.parquet", index=False)

    model = SentenceTransformer(EMBED_MODEL, device="cpu")
    model.max_seq_length = 512
    enc = lambda texts: model.encode(list(texts), batch_size=16, normalize_embeddings=True,
                                     show_progress_bar=False)

    fam = jobs["series"] + ". " + jobs["family_text"]
    fam_unique = fam.drop_duplicates()
    fam_vec = dict(zip(fam_unique, enc(fam_unique)))
    np.save(INTERIM / "emb_family.npy", np.stack([fam_vec[f] for f in fam]))

    famq_vec = dict(zip(fam_unique, enc(QUERY_PREFIX + fam_unique)))
    np.save(INTERIM / "emb_family_query.npy", np.stack([famq_vec[f] for f in fam]))

    np.save(INTERIM / "emb_level.npy", enc(jobs["class_title"] + ". " + jobs["level_text"]))
    np.save(INTERIM / "emb_onet.npy", enc(onet["text"]))
    print(f"embedded {len(fam_unique)} job families, {len(jobs)} job classes, {len(onet)} O*NET occupations "
          f"with {EMBED_MODEL}")


if __name__ == "__main__":
    main()
