"""Dining Philosophers (4) using a MONITOR (Dijkstra-style): a philosopher eats only if both neighbours are not eating,
then both forks are taken atomically.  No hold-and-wait => no deadlock.  Starvation IS possible (a philosopher whose
neighbours alternate eating may wait indefinitely); tests below the monitor show it is rare with random delays."""
import threading, time, random
from common import TraceRecorder, dp_args, finish

N = 4
class DiningMonitor:
    def __init__(self, rec):
        self.cond = threading.Condition(); self.state = ["thinking"] * N; self.rec = rec
    def _test(self, i):
        l, r = (i - 1) % N, (i + 1) % N
        if self.state[i] == "hungry" and self.state[l] != "eating" and self.state[r] != "eating":
            self.state[i] = "eating"; self.rec.log(f"P{i}", "acquiring")
            self.rec.log(f"F{i}", "held", f"P{i}"); self.rec.log(f"F{r}", "held", f"P{i}")
            self.rec.log(f"P{i}", "eating"); self.cond.notify_all()
    def pickup(self, i):
        with self.cond:
            self.state[i] = "hungry"; self.rec.log(f"P{i}", "hungry"); self._test(i)
            while self.state[i] != "eating": self.cond.wait()
    def putdown(self, i):
        with self.cond:
            self.rec.log(f"P{i}", "releasing"); self.state[i] = "thinking"
            self.rec.log(f"F{i}", "free"); self.rec.log(f"F{(i+1)%N}", "free"); self.rec.log(f"P{i}", "thinking")
            self._test((i - 1) % N); self._test((i + 1) % N)

def main():
    a = dp_args()
    P = [f"P{i}" for i in range(N)]; F = [f"F{i}" for i in range(N)]
    init = {**{p: "thinking" for p in P}, **{f: "free" for f in F}}
    rec = TraceRecorder("Dining Philosophers (4) - Monitor based", "dp", "Monitor: lock + condition variable, state[] + test()",
                        P + F, init, f"{a.meals} meals each")
    mon = DiningMonitor(rec)
    def philosopher(i):
        for _ in range(a.meals):
            time.sleep(random.uniform(0, a.delay)); mon.pickup(i)
            time.sleep(random.uniform(a.delay / 2, a.delay)); mon.putdown(i)
    ts = [threading.Thread(target=philosopher, args=(i,)) for i in range(N)]
    [t.start() for t in ts]; [t.join() for t in ts]
    finish(rec, a.out, "dining_philosophers_monitor")

if __name__ == "__main__": main()
