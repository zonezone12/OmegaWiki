"""Generate fad_init.xyz for i-PI initialization."""
import numpy as np

# FAD C2h geometry (Angstrom) — same as make_fad() in train.py
positions = np.array([
    [ 0.990,  0.000, 0.000],  # H1
    [-0.423,  1.272, 0.000],  # C1
    [ 0.285,  2.253, 0.000],  # O1
    [ 0.000,  0.000, 0.000],  # O2
    [-1.520,  1.217, 0.000],  # H2
    [ 2.015,  2.254, 0.000],  # H3
    [ 3.427,  0.982, 0.000],  # C2
    [ 2.720,  0.000, 0.000],  # O3
    [ 3.005,  2.254, 0.000],  # O4
    [ 4.524,  1.037, 0.000],  # H4
])
symbols = ['H', 'C', 'O', 'O', 'H', 'H', 'C', 'O', 'O', 'H']

with open('fad_init.xyz', 'w') as f:
    f.write(f'{len(symbols)}\n')
    # Large cell (non-periodic) — 50 Ang box
    f.write('# CELL(abcABC): 50.0 50.0 50.0 90.0 90.0 90.0 cell{angstrom}\n')
    for sym, pos in zip(symbols, positions):
        f.write(f'{sym:4s}  {pos[0]:12.6f}  {pos[1]:12.6f}  {pos[2]:12.6f}\n')
print("Written: fad_init.xyz")
