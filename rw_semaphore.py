"""Readers-Writers (readers-preference) using SEMAPHORES.
Shared resource: shared["value"].  Critical section: the read / read-modify-write of that value.
  mutex = Semaphore(1): protects read_count        wrt = Semaphore(1): exclusive access for writers
(first reader locks wrt, last reader unlocks it).  Starvation: writers can starve if readers keep arriving."""
import threading, time, random
from common import TraceRecorder, rw_args, finish

def main():
    a = rw_args()
    R = [f"R{i+1}" for i in range(a.readers)]; W = [f"W{i+1}" for i in range(a.writers)]
    rec = TraceRecorder("Readers-Writers - Semaphore based", "rw", "Semaphores: mutex(1) + wrt(1)",
                        R + W, {x: "idle" for x in R + W},
                        f"{a.readers} readers, {a.writers} writers, {a.rounds} rounds")
    mutex, wrt = threading.Semaphore(1), threading.Semaphore(1)
    state = {"read_count": 0}; shared = {"value": 0}

    def reader(name):
        for _ in range(a.rounds):
            time.sleep(random.uniform(0, a.delay))          # think
            rec.log(name, "waiting")
            mutex.acquire()                                  # wait(mutex)
            state["read_count"] += 1
            if state["read_count"] == 1: wrt.acquire()       # first reader blocks writers
            mutex.release()                                  # signal(mutex)
            rec.log(name, "reading", f"value={shared['value']}")   # ---- critical section
            time.sleep(random.uniform(a.delay / 2, a.delay))
            rec.log(name, "idle")
            mutex.acquire()
            state["read_count"] -= 1
            if state["read_count"] == 0: wrt.release()       # last reader lets writers in
            mutex.release()

    def writer(name):
        for _ in range(a.rounds):
            time.sleep(random.uniform(0, a.delay))
            rec.log(name, "waiting")
            wrt.acquire()                                    # exclusive access
            v = shared["value"]; rec.log(name, "writing", f"{v}->{v+1}")  # ---- critical section
            time.sleep(random.uniform(a.delay / 2, a.delay))
            shared["value"] = v + 1                          # read-modify-write (racy without wrt)
            rec.log(name, "idle")
            wrt.release()

    ts = [threading.Thread(target=reader, args=(n,)) for n in R] + [threading.Thread(target=writer, args=(n,)) for n in W]
    [t.start() for t in ts]; [t.join() for t in ts]
    print("final shared value:", shared["value"], "(expected", a.writers * a.rounds, ")")
    finish(rec, a.out, "readers_writers_semaphore")

if __name__ == "__main__": main()
