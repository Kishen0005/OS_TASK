"""Dining Philosophers (4) using SEMAPHORES.  Forks: fork[i] = Semaphore(1); fork i is left of P_i, fork (i+1)%4 is right.
Deadlock prevention: 'room' = Semaphore(3) lets at most N-1 philosophers compete for forks, so the circular wait
(all 4 holding their left fork) can never form.  Starvation: Python semaphores wake waiters roughly FIFO, which in
practice avoids starvation here, but it is not formally guaranteed."""
import threading, time, random
from common import TraceRecorder, dp_args, finish

N = 4
def main():
    a = dp_args()
    P = [f"P{i}" for i in range(N)]; F = [f"F{i}" for i in range(N)]
    init = {**{p: "thinking" for p in P}, **{f: "free" for f in F}}
    rec = TraceRecorder("Dining Philosophers (4) - Semaphore based", "dp", "fork semaphores + room(N-1) semaphore",
                        P + F, init, f"{a.meals} meals each")
    fork = [threading.Semaphore(1) for _ in range(N)]; room = threading.Semaphore(N - 1)

    def philosopher(i):
        l, r = i, (i + 1) % N
        for _ in range(a.meals):
            time.sleep(random.uniform(0, a.delay))                 # thinking
            rec.log(P[i], "hungry"); room.acquire()               # entry control (deadlock avoidance)
            rec.log(P[i], "acquiring")
            fork[l].acquire(); rec.log(F[l], "held", P[i])
            time.sleep(random.uniform(0, a.delay / 4))             # widen the window for deadlock if unprotected
            fork[r].acquire(); rec.log(F[r], "held", P[i])
            rec.log(P[i], "eating"); time.sleep(random.uniform(a.delay / 2, a.delay))
            rec.log(P[i], "releasing")
            rec.log(F[l], "free"); fork[l].release()
            rec.log(F[r], "free"); fork[r].release()
            room.release(); rec.log(P[i], "thinking")

    ts = [threading.Thread(target=philosopher, args=(i,)) for i in range(N)]
    [t.start() for t in ts]; [t.join() for t in ts]
    finish(rec, a.out, "dining_philosophers_semaphore")

if __name__ == "__main__": main()
