"""Readers-Writers (writer-preference) using a MONITOR (class = lock + condition variable).
Monitor state: readers, writing, waiting_writers.  Readers wait while a writer is active OR waiting,
so writers cannot starve (readers might, if writers arrive continuously)."""
import threading, time, random
from common import TraceRecorder, rw_args, finish

class RWMonitor:
    def __init__(self, rec):
        self.cond = threading.Condition()       # monitor lock + condition variable
        self.readers = 0; self.writing = False; self.waiting_writers = 0; self.rec = rec
    def start_read(self, n, val):
        with self.cond:
            self.rec.log(n, "waiting")
            while self.writing or self.waiting_writers > 0: self.cond.wait()
            self.readers += 1; self.rec.log(n, "reading", f"value={val()}")
    def end_read(self, n):
        with self.cond:
            self.readers -= 1; self.rec.log(n, "idle")
            if self.readers == 0: self.cond.notify_all()
    def start_write(self, n, val):
        with self.cond:
            self.rec.log(n, "waiting"); self.waiting_writers += 1
            while self.writing or self.readers > 0: self.cond.wait()
            self.waiting_writers -= 1; self.writing = True; self.rec.log(n, "writing", f"{val()}->{val()+1}")
    def end_write(self, n):
        with self.cond:
            self.writing = False; self.rec.log(n, "idle"); self.cond.notify_all()

def main():
    a = rw_args()
    R = [f"R{i+1}" for i in range(a.readers)]; W = [f"W{i+1}" for i in range(a.writers)]
    rec = TraceRecorder("Readers-Writers - Monitor based", "rw", "Monitor: lock + condition variable (writer preference)",
                        R + W, {x: "idle" for x in R + W}, f"{a.readers} readers, {a.writers} writers, {a.rounds} rounds")
    mon = RWMonitor(rec); shared = {"value": 0}; val = lambda: shared["value"]

    def reader(n):
        for _ in range(a.rounds):
            time.sleep(random.uniform(0, a.delay)); mon.start_read(n, val)
            time.sleep(random.uniform(a.delay / 2, a.delay)); mon.end_read(n)
    def writer(n):
        for _ in range(a.rounds):
            time.sleep(random.uniform(0, a.delay)); mon.start_write(n, val)
            v = shared["value"]; time.sleep(random.uniform(a.delay / 2, a.delay)); shared["value"] = v + 1
            mon.end_write(n)

    ts = [threading.Thread(target=reader, args=(n,)) for n in R] + [threading.Thread(target=writer, args=(n,)) for n in W]
    [t.start() for t in ts]; [t.join() for t in ts]
    print("final shared value:", shared["value"], "(expected", a.writers * a.rounds, ")")
    finish(rec, a.out, "readers_writers_monitor")

if __name__ == "__main__": main()
