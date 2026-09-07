"""
Reflection layer.

This is the piece that makes "3 devices hit the same unknown pattern"
become ONE review request instead of three. Uses the same dependency-free
TF-IDF/cosine approach as the retrieval tool, for the same reason: no
external service call on stage.

Deliberately a flat, greedy single-linkage clustering over a similarity
threshold — not a serious clustering algorithm. At this scale (tens of
detections per mission, not millions) that's the right amount of
engineering, not a shortcut that will bite later.
"""

from typing import List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from state import GroupedReview
from memory.knowledge_base import UnknownCommandDetection

CLUSTER_SIMILARITY_THRESHOLD = 0.55


def cluster_unknowns(detections: List[UnknownCommandDetection],
                      device_id_by_file: dict) -> List[GroupedReview]:
    """Groups UnknownCommandDetections that are probably the same
    underlying unmapped syntax, even across different devices/files."""
    if not detections:
        return []

    texts = [d.raw for d in detections]
    if len(texts) == 1:
        d = detections[0]
        return [GroupedReview(
            representative_raw=d.raw, vendor=d.vendor_fingerprint.value,
            device_ids=[device_id_by_file.get(d.file, d.file)],
            line_refs=[f"{d.file}:{d.line}"],
        )]

    vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
    matrix = vectorizer.fit_transform(texts)
    sims = cosine_similarity(matrix)

    assigned = [False] * len(detections)
    groups: List[GroupedReview] = []

    for i in range(len(detections)):
        if assigned[i]:
            continue
        cluster_idxs = [i]
        assigned[i] = True
        for j in range(i + 1, len(detections)):
            if not assigned[j] and sims[i][j] >= CLUSTER_SIMILARITY_THRESHOLD:
                # only merge within the same vendor family — cross-vendor
                # text similarity is coincidental, not semantic
                if detections[j].vendor_fingerprint == detections[i].vendor_fingerprint:
                    cluster_idxs.append(j)
                    assigned[j] = True

        members = [detections[k] for k in cluster_idxs]
        groups.append(GroupedReview(
            representative_raw=members[0].raw,
            vendor=members[0].vendor_fingerprint.value,
            device_ids=sorted({device_id_by_file.get(m.file, m.file) for m in members}),
            line_refs=[f"{m.file}:{m.line}" for m in members],
        ))

    return groups
