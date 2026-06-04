import json
data = json.load(open('C:/tmp/arxiv_candidates.json'))
for i, p in enumerate(data):
    arxiv_id = p['arxiv_id']
    title = p['title']
    abstract = p['abstract'][:500]
    kw = p['kw_score']
    print(f"--- Paper {i+1} [kw={kw}] ---")
    print(f"ID: {arxiv_id}")
    print(f"Title: {title}")
    print(f"Abstract: {abstract}")
    print()
