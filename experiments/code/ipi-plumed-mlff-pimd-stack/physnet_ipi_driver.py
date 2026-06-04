#!/usr/bin/env python3
"""
PhysNet i-PI driver — 32-bead PIMD, one socket client per bead.

Each bead is an independent i-PI client. Forces are evaluated by BeadCompute, a
deadlock-free hybrid: it batches all P beads through one GPU pass on the fast
path, but bounds the wait with a timeout so a partial i-PI dispatch sweep falls
back to batching whoever arrived instead of hanging. (An earlier version used a
plain threading.Barrier requiring all P beads before any proceeded; that
deadlocked intermittently because i-PI does not guarantee it dispatches POSDATA
to all P beads before collecting forces.)

i-PI protocol: positions Bohr, forces Ha/Bohr, energy Ha.
PhysNet:       positions Ang,  forces kcal/(mol·Ang).
"""
import argparse
import os
import socket
import struct
import sys
import threading
import time

import numpy as np

# ── Unit conversions ─────────────────────────────────────────────────────────
ANG_PER_BOHR     = 0.52917390
KCAL_PER_HA      = 627.509474
KCAL_PER_HA_BOHR = KCAL_PER_HA / ANG_PER_BOHR   # 1185.82

def bohr_to_ang(x):            return x * ANG_PER_BOHR
def kcal_ang_to_ha_bohr(f):    return f / KCAL_PER_HA_BOHR

# ── i-PI binary protocol ──────────────────────────────────────────────────────
def _recv(sock, n):
    buf = b''
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise EOFError('connection closed')
        buf += chunk
    return buf

def recv_header(sock):
    return _recv(sock, 12).decode('ascii').strip()

def send_header(sock, msg):
    sock.sendall(msg.encode('ascii').ljust(12)[:12])

def recv_posdata(sock):
    _recv(sock, 72)   # cell  — skipped (gas phase)
    _recv(sock, 72)   # icell — skipped
    natoms = struct.unpack('<i', _recv(sock, 4))[0]
    pos = np.frombuffer(_recv(sock, natoms * 3 * 8), dtype='<f8').reshape(natoms, 3)
    return natoms, pos

def send_forceready(sock, energy_ha, forces_ha_bohr):
    natoms = forces_ha_bohr.shape[0]
    send_header(sock, 'FORCEREADY')
    sock.sendall(struct.pack('<d', float(energy_ha)))
    sock.sendall(struct.pack('<i', natoms))
    sock.sendall(forces_ha_bohr.astype('<f8').tobytes())
    sock.sendall(np.zeros(9, dtype='<f8').tobytes())  # virial = 0
    sock.sendall(struct.pack('<i', 0))                 # extras = empty

# ── Hybrid batched / partial-sweep synchronization ─────────────────────────────
class BeadCompute:
    """Deadlock-free force evaluation: batch the fast path, time out the rest.

    FAST PATH — when all P beads' POSDATA arrive within `batch_timeout` (the
    normal case: i-PI dispatches them in one sweep), the first bead to arrive (the
    "leader") runs ONE batched GPU forward pass over all P beads, then distributes
    the forces. This is the throughput path (~8 steps/s for 10-atom FAD).

    SAFETY PATH — i-PI does NOT guarantee it sends POSDATA to all P beads before
    collecting forces from any. On a partial sweep (the race that deadlocked the
    old all-or-nothing threading.Barrier), the leader's wait is BOUNDED by
    batch_timeout: it then batches whatever beads have arrived and returns their
    forces, which unblocks i-PI to dispatch the stragglers. Those form the next
    "generation" and get batched in turn. The wait is always bounded, so no
    dispatch order can deadlock the driver.

    The condition-variable lock is held across the GPU call, which also serializes
    access to the FF's shared TF batch buffers (get_forces_batch mutates
    self._R_batch). This is safe because i-PI collects all P forces of step N
    before dispatching step N+1, so no next-generation bead is waiting to register
    while the leader computes.
    """

    def __init__(self, n_beads, ff, batch_timeout=0.3):
        self.P             = n_beads
        self.ff            = ff
        self.batch_timeout = batch_timeout
        self._cv           = threading.Condition()
        self._pos          = [None] * n_beads
        self._forces       = [None] * n_beads
        self._waiting      = []     # bead indices arrived in the current generation
        self._gen          = 0      # current (open) generation id
        self._results_gen  = -1     # highest generation whose forces are published
        self._calls        = 0      # total bead evals, for the progress log
        self._aborted      = False

    def compute(self, bead_idx, pos_bohr):
        """Returns (energy_ha, forces_ha_bohr) for this bead. Energy unused (NVT)."""
        with self._cv:
            if self._aborted:
                raise threading.BrokenBarrierError
            gen = self._gen
            self._pos[bead_idx] = pos_bohr
            self._waiting.append(bead_idx)
            is_leader = (len(self._waiting) == 1)
            self._cv.notify_all()   # wake the leader so it re-checks the arrival count

            if is_leader:
                # Wait for a full sweep, but never longer than batch_timeout.
                deadline = time.monotonic() + self.batch_timeout
                while len(self._waiting) < self.P and not self._aborted:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        break
                    self._cv.wait(remaining)
                if self._aborted:
                    self._cv.notify_all()
                    raise threading.BrokenBarrierError

                # Batch over whoever has arrived. CRUCIAL: always run a FULL P-sized
                # batch — pad the missing beads with a valid geometry and discard
                # their results. A variable batch size makes PhysNet's TF graph
                # retrace (multi-second), which blows i-PI's socket timeout and makes
                # it drop every client. Padding keeps the shape constant → no retrace.
                members = list(self._waiting)
                ref     = self._pos[members[0]]
                natoms  = ref.shape[0]
                batch   = np.empty((self.P, natoms, 3), dtype=np.float64)
                for b in range(self.P):
                    p = self._pos[b]
                    batch[b] = bohr_to_ang(p if p is not None else ref)
                forces_kcal = self.ff.get_forces_batch(batch, self.ff.numbers)
                for b in members:
                    self._forces[b] = kcal_ang_to_ha_bohr(forces_kcal[b])   # padded slots discarded

                self._calls += len(members)
                prev = self._calls - len(members)
                if prev // (self.P * 100) != self._calls // (self.P * 100):
                    print(f'[driver] ~{self._calls // self.P} MD steps done '
                          f'({self._calls} bead evals)', flush=True)

                # Publish results and open the next generation.
                self._waiting     = []
                self._results_gen = gen
                self._gen        += 1
                self._cv.notify_all()
            else:
                # Follower: block until the leader publishes this generation.
                while self._results_gen < gen and not self._aborted:
                    self._cv.wait()
                if self._aborted:
                    raise threading.BrokenBarrierError

            return 0.0, self._forces[bead_idx]

    def abort(self):
        with self._cv:
            self._aborted = True
            self._cv.notify_all()

# ── Per-bead connection handler ───────────────────────────────────────────────
def bead_loop(bead_idx, sock_path, barrier, verbose):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    # Large socket buffers prevent FORCEREADY send from blocking when i-PI is
    # slow to drain its receive queue (output writes, smotion, Python GC).
    # Without this, a full OS socket buffer can stall a bead's send while the
    # next step's batch is waiting on that same bead. 1 MB per bead.
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024 * 1024)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
    for attempt in range(90):
        try:
            sock.connect(sock_path)
            break
        except (FileNotFoundError, ConnectionRefusedError):
            if attempt == 89:
                barrier.abort()   # unblock other threads waiting at barrier
                raise RuntimeError(f'bead {bead_idx}: could not connect after 90s')
            time.sleep(1.0)
    if verbose:
        print(f'[bead {bead_idx:2d}] connected', flush=True)

    state       = 'NEEDINIT'
    energy_ha   = 0.0
    forces_ha_b = None

    try:
        while True:
            header = recv_header(sock)

            if header == 'STATUS':
                send_header(sock, state)

            elif header == 'INIT':
                struct.unpack('<i', _recv(sock, 4))
                init_len = struct.unpack('<i', _recv(sock, 4))[0]
                if init_len > 0:
                    _recv(sock, init_len)
                state = 'READY'
                if verbose:
                    print(f'[bead {bead_idx:2d}] INIT → READY', flush=True)

            elif header == 'POSDATA':
                natoms, pos_bohr = recv_posdata(sock)
                # Compute this bead's forces independently under the FF lock.
                # No cross-bead wait → i-PI's dispatch order cannot deadlock us.
                energy_ha, forces_ha_b = barrier.compute(bead_idx, pos_bohr)
                state = 'HAVEDATA'

            elif header == 'GETFORCE':
                send_forceready(sock, energy_ha, forces_ha_b)
                state = 'READY'

            elif header == 'FLUSH':
                pass  # server-side flush hint; no reply expected

            else:
                print(f'[bead {bead_idx}] unknown: {header!r}', flush=True)

    except EOFError:
        if verbose:
            print(f'[bead {bead_idx}] EOF', flush=True)
    except OSError:
        # BrokenPipeError / ConnectionResetError on clean i-PI shutdown (ENDRUN closes sockets)
        if verbose:
            print(f'[bead {bead_idx}] socket closed by server', flush=True)
    except threading.BrokenBarrierError:
        print(f'[bead {bead_idx}] barrier broken — another bead failed to connect', flush=True)
    finally:
        sock.close()

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--n-beads',      type=int, default=32)
    ap.add_argument('--socket',       default='/tmp/ipi_physnet')
    ap.add_argument('--physnet-base', default='/repo/experiments/code/opes-pimd-fad-proton-transfer-convergence')
    ap.add_argument('--verbose',      action='store_true')
    args = ap.parse_args()

    os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')
    os.environ.setdefault('TF_ENABLE_ONEDNN_OPTS', '0')
    mlff_dir = '/repo/experiments/code/mlff-pimd-fad-barrier-comparison'
    for d in [args.physnet_base, mlff_dir]:
        if d not in sys.path:
            sys.path.insert(0, d)

    print('[driver] loading PhysNet …', flush=True)
    from force_fields import PhysNetFF
    ff = PhysNetFF(args.physnet_base)
    print('[driver] PhysNet ready  (batched GPU, hybrid sync)', flush=True)

    # Warmup: run one dummy full-size (P=n_beads) batch to compile the TF graph
    # NOW, before i-PI connects. Matches the fast-path batch size so the first
    # real step doesn't pay a graph rebuild (which would trip i-PI's timeout).
    print(f'[driver] warming up TF graph (P={args.n_beads} compile) …', flush=True)
    _dummy = np.zeros((args.n_beads, 10, 3), dtype=np.float64)
    _dummy[:, :, 0] = np.tile(np.arange(10), (args.n_beads, 1)) * 0.1
    ff.get_forces_batch(_dummy, ff.numbers)
    print('[driver] TF graph warmed up — ready for i-PI', flush=True)

    barrier = BeadCompute(args.n_beads, ff)
    threads = []
    for i in range(args.n_beads):
        t = threading.Thread(
            target=bead_loop,
            args=(i, args.socket, barrier, args.verbose),
            daemon=True,
        )
        t.start()
        threads.append(t)
        time.sleep(0.02)

    print(f'[driver] {args.n_beads} bead threads started', flush=True)
    for t in threads:
        t.join()
    print('[driver] done', flush=True)

if __name__ == '__main__':
    main()
