#!/usr/bin/env python
"""
PhysNet i-PI force server — implements i-PI driver socket protocol.

Listens for P=32 concurrent bead connections from i-PI, batches all bead
positions into a single PhysNet GPU forward pass, returns forces.

Usage:
    python physnet_server.py [--port 31415] [--beads 32] [--host 0.0.0.0]

i-PI driver protocol (per connection):
    i-PI sends:  STATUS    → server responds: READY / HAVEDATA / NEEDINIT
    i-PI sends:  POSDATA   → server reads cell + positions, responds: HAVEDATA
    i-PI sends:  GETFORCE  → server responds with energy + forces + virial
    i-PI sends:  EXIT      → server closes connection

Unit conventions (i-PI atomic units):
    positions : Bohr
    forces    : Hartree / Bohr
    energy    : Hartree
"""
import argparse
import socket
import struct
import sys
import os
import threading
import numpy as np

# Unit conversions
BOHR_TO_ANG   = 0.529177210903
ANG_TO_BOHR   = 1.0 / BOHR_TO_ANG
KCAL_TO_HA    = 1.0 / 627.509474         # kcal/mol → Hartree
# kcal/mol/Ang → Hartree/Bohr
FORCE_CONV    = KCAL_TO_HA * ANG_TO_BOHR  # = 1.0 / (627.509474 * 0.529177) = 0.001593601

# Atom order: H1(0) C1(1) O1(2) O2(3) H2(4) H3(5) C2(6) O3(7) O4(8) H4(9)
FAD_NUMBERS = np.array([1, 6, 8, 8, 1, 1, 6, 8, 8, 1])
FAD_MASSES  = np.array([1, 12, 16, 16, 1, 1, 12, 16, 16, 1], dtype=float)


def recv_all(sock, n):
    """Receive exactly n bytes, blocking until available."""
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise ConnectionResetError("i-PI connection closed unexpectedly")
        data += chunk
    return data


def send_header(sock, msg):
    """Send 12-byte padded header string."""
    sock.sendall(msg.ljust(12).encode())


class BatchForceServer:
    """
    Manages P concurrent bead connections with synchronized batch evaluation.

    All P beads must send POSDATA before any bead's GETFORCE is answered.
    Uses threading.Barrier to synchronize; bead 0 performs the batch PhysNet call.
    """

    def __init__(self, ff, n_beads, host, port):
        self.ff      = ff
        self.P       = n_beads
        self.host    = host
        self.port    = port
        self._positions = [None] * n_beads   # (N, 3) Angstrom per bead
        self._forces    = [None] * n_beads   # (N, 3) Hartree/Bohr per bead
        self._energies  = [0.0]  * n_beads   # Hartree per bead (dummy OK for NVT)
        self._posdata_barrier = threading.Barrier(n_beads)
        self._getforce_barrier = threading.Barrier(n_beads)

    def _handle_bead(self, bead_idx, conn):
        """Protocol loop for one bead connection."""
        print(f"[server] bead {bead_idx:2d} connected")
        try:
            while True:
                header = recv_all(conn, 12).decode(errors='replace').strip()

                if header == 'STATUS':
                    send_header(conn, 'READY')

                elif header == 'POSDATA':
                    # cell: 9 float64 (row-major, Bohr)
                    cell = np.frombuffer(recv_all(conn, 72), dtype=np.float64).reshape(3, 3)
                    natoms = struct.unpack('i', recv_all(conn, 4))[0]
                    pos_bohr = np.frombuffer(recv_all(conn, 24 * natoms), dtype=np.float64).reshape(natoms, 3)
                    self._positions[bead_idx] = pos_bohr * BOHR_TO_ANG
                    send_header(conn, 'HAVEDATA')

                    # ── synchronize: wait until ALL beads have sent POSDATA ──
                    self._posdata_barrier.wait()

                    # Bead 0 batches all positions and evaluates PhysNet
                    if bead_idx == 0:
                        all_pos = np.stack(self._positions, axis=0)   # (P, N, 3) Ang
                        all_f_kcal = self.ff.get_forces_batch(all_pos, FAD_NUMBERS)  # (P, N, 3)
                        for i in range(self.P):
                            self._forces[i] = all_f_kcal[i] * FORCE_CONV   # Hartree/Bohr

                    # ── wait until bead 0 finishes batch eval ──
                    self._getforce_barrier.wait()

                elif header == 'GETFORCE':
                    forces  = self._forces[bead_idx]   # (N, 3) Hartree/Bohr
                    energy  = self._energies[bead_idx]  # Hartree (0.0 for NVT)
                    virial  = np.zeros((3, 3))           # Not needed for NVT
                    natoms  = forces.shape[0]
                    extras  = b""

                    buf  = struct.pack('d', energy)
                    buf += struct.pack('i', natoms)
                    buf += forces.flatten().astype(np.float64).tobytes()
                    buf += virial.flatten().astype(np.float64).tobytes()
                    buf += struct.pack('i', len(extras))
                    if extras:
                        buf += extras
                    conn.sendall(buf)

                elif header in ('EXIT', 'END'):
                    print(f"[server] bead {bead_idx:2d} received {header} — closing")
                    break

                else:
                    print(f"[server] bead {bead_idx:2d} unexpected header: {header!r}")

        except (ConnectionResetError, BrokenPipeError) as e:
            print(f"[server] bead {bead_idx:2d} disconnected: {e}")
        finally:
            conn.close()

    def run(self):
        """Accept P connections and spawn one thread per bead."""
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((self.host, self.port))
        srv.listen(self.P + 2)
        print(f"[server] PhysNet force server listening on {self.host}:{self.port} (P={self.P} beads)")

        threads = []
        for i in range(self.P):
            conn, addr = srv.accept()
            t = threading.Thread(target=self._handle_bead, args=(i, conn), daemon=True)
            t.start()
            threads.append(t)
            print(f"[server] accepted bead {i} from {addr}")

        print(f"[server] all {self.P} beads connected — running")
        for t in threads:
            t.join()
        print("[server] all beads done, shutting down")
        srv.close()


def main():
    ap = argparse.ArgumentParser(description="PhysNet i-PI force server")
    ap.add_argument("--port",  type=int, default=31415)
    ap.add_argument("--host",  default="0.0.0.0")
    ap.add_argument("--beads", type=int, default=32)
    ap.add_argument("--physnet-base", default="../opes-pimd-fad-proton-transfer-convergence")
    args = ap.parse_args()

    # Load PhysNetFF
    mlff_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mlff-pimd-fad-barrier-comparison"))
    if mlff_dir not in sys.path:
        sys.path.insert(0, mlff_dir)
    from force_fields import load_ff

    # Build a minimal config dict for load_ff
    physnet_base = os.path.abspath(os.path.join(os.path.dirname(__file__), args.physnet_base))
    cfg = {"model": {"physnet_base": os.path.relpath(physnet_base, mlff_dir)}}
    print(f"[server] loading PhysNet from {physnet_base}")
    ff = load_ff("physnet", cfg)
    print(f"[server] PhysNet ready — starting batch server")

    server = BatchForceServer(ff, n_beads=args.beads, host=args.host, port=args.port)
    server.run()


if __name__ == "__main__":
    main()
