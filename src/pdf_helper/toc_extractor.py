from typing import List, Optional

import numpy as np
from pydantic import BaseModel
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from .content_parser import PaddleXBoxContent
from .layout_parser import PaddleX17Cls


class TocEntry(BaseModel):
    """
    Represents a table-of-contents (TOC) entry.
    The 'level' field indicates the hierarchy depth (e.g., 1 for top-level section,
    2 for subsection, etc.).
    """

    title: str
    page_number: int
    level: int

    class Config:
        frozen = True


def dynamic_extract_hierarchy(
    content_list: List[PaddleXBoxContent], num_levels: Optional[int] = None
) -> List[TocEntry]:
    """
    Dynamically extracts a TOC hierarchy from a list of content boxes by gathering
    features from all title candidates and clustering them. Instead of mapping to a
    HierarchyLevel enum, the function directly assigns a numeric level (1, 2, etc.)
    to each title.
    """
    # Gather candidate title boxes.
    candidates = []
    features = []  # Each feature vector: [max_font_size, avg_font_size, text_length]
    for box in content_list:
        if box.cls_id == PaddleX17Cls.paragraph_title and box.text is not None:
            title_text = getattr(box.text, "content", None)
            if not title_text:
                continue
            fonts = box.text.fonts
            if not fonts:
                continue
            font_sizes = [font.size for font in fonts]
            max_font = max(font_sizes)
            avg_font = sum(font_sizes) / len(font_sizes)
            text_len = len(title_text)
            candidates.append((box, title_text))
            features.append([max_font, avg_font, text_len])

    if not candidates:
        return []

    features = np.array(features)
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)

    # Decide on number of clusters if not provided.
    if num_levels is None:
        # If very few candidates, use 2 clusters; else default to 3.
        num_levels = 2 if len(candidates) < 5 else 3

    # Run KMeans clustering.
    kmeans = KMeans(n_clusters=num_levels, random_state=42)
    labels = kmeans.fit_predict(features_scaled)

    # Compute average max font size per cluster (using unscaled features)
    cluster_stats = {}
    for label, feat in zip(labels, features):
        # feat[0] is the max font size.
        cluster_stats.setdefault(label, []).append(feat[0])
    cluster_avg = {label: np.mean(sizes) for label, sizes in cluster_stats.items()}

    # Rank clusters: highest average max font size -> level 1, next -> level 2, etc.
    sorted_labels = sorted(cluster_avg.items(), key=lambda x: x[1], reverse=True)
    label_to_numeric_level = {}
    for rank, (label, _) in enumerate(sorted_labels, start=1):
        label_to_numeric_level[label] = rank  # level numbers: 1, 2, ...

    # Build the TOC entries list using numeric levels.
    toc_entries: List[TocEntry] = []
    for (box, title_text), label in zip(candidates, labels):
        numeric_level = label_to_numeric_level[label]
        toc_entries.append(
            TocEntry(title=title_text, page_number=box.page_number, level=numeric_level)
        )

    # Optionally, sort by page number and numeric level.
    toc_entries = sorted(toc_entries, key=lambda t: (t.page_number, t.level))
    return toc_entries
