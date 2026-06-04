import json

data = json.load(open('C:/tmp/arxiv_feed.json'))

keywords = [
    'metadynamic', 'meta-dynamic', 'enhanced sampling', 'free energy',
    'molecular dynamics', 'force field', 'machine learning force', 'mlff', 'ml force',
    'path integral', 'pimd', 'nuclear quantum', 'quantum tunneling', 'kinetic isotope',
    'ring polymer', 'rpmd', 'collective variable', 'bias potential',
    'plumed', 'opes', 'replica exchange', 'parallel tempering',
    'graph neural network', 'interatomic potential', 'neural network potential',
    'neural force', 'conformational sampling', 'free-energy', 'boltzmann',
    'potential energy surface', 'ab initio md', 'aimd', 'quantum chemistry',
    'transition state', 'reaction rate', 'chemical reaction',
    'coarse grain', 'umbrella sampling', 'thermodynamic integration',
    'gfn', 'equivariant neural', 'message passing neural', 'equivariant gnn',
    'allegro', 'nequip', 'mace', 'physnet', 'schnet', 'painn', 'ani-',
]

# Already-ingested arxiv IDs
existing_ids = {'2502.10461', '2405.16015'}  # from wiki papers

candidates = []
for p in data:
    if p['arxiv_id'] in existing_ids:
        continue
    text = (p['title'] + ' ' + p['abstract']).lower()
    score = sum(1 for kw in keywords if kw in text)
    if score >= 1:
        candidates.append({**p, 'kw_score': score})

candidates.sort(key=lambda x: -x['kw_score'])
print(f'Candidates after keyword filter: {len(candidates)}')
for c in candidates[:20]:
    print(f"  [{c['kw_score']}] {c['title'][:90]}")

json.dump(candidates, open('C:/tmp/arxiv_candidates.json', 'w'), indent=2)
