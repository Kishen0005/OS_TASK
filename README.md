# OS Synchronization Assignment

**AI-Assisted Synchronization Algorithms with Program-Generated HTML Simulation**
Readers-Writers and Dining Philosophers, each solved with semaphores and with monitors.

| | |
|---|---|
| **Name** | [Student Name] |
| **USN** | [USN] |
| **Course** | Operating Systems |
| **Semester / Section** | [Semester / Section] |
| **Instructor** | [Instructor Name] |

---

## 1. Overview

This project implements two classical process-synchronization problems, each in two ways, using real concurrent threads in Python. Every program records the state changes made by its threads during execution and uses that record to generate a standalone HTML simulation that can be replayed in a browser. The HTML is never hand-written for a particular scenario: it is built from the execution trace of the run.

| # | Problem | Technique | File |
|---|---|---|---|
| 1 | Readers-Writers | Semaphores | `rw_semaphore.py` |
| 2 | Readers-Writers | Monitor | `rw_monitor.py` |
| 3 | Dining Philosophers (4) | Semaphores | `dp_semaphore.py` |
| 4 | Dining Philosophers (4) | Monitor | `dp_monitor.py` |
| - | Shared recorder, verifier, HTML generator | - | `common.py` |

## 2. Implementations

### 2.1 Readers-Writers, semaphore based
- **Shared resource:** one integer, `shared["value"]`. Writers update it with a deliberate read-modify-write sequence, so a failure of mutual exclusion would show up as a lost update.
- **Semaphores:** `mutex = Semaphore(1)` protects the `read_count` counter. `wrt = Semaphore(1)` gives writers exclusive access. The first reader acquires `wrt` and the last reader releases it.
- **Policy:** readers preference. Writers can starve if readers keep overlapping.

### 2.2 Readers-Writers, monitor based
- A class `RWMonitor` holds `readers`, `writing` and `waiting_writers` behind one `threading.Condition` (lock plus condition variable).
- Interface: `start_read`, `end_read`, `start_write`, `end_write`. Every wait is a `while` loop around `cond.wait()`.
- **Policy:** writer preference. Readers wait while a writer is active or waiting. Readers can starve if writers keep arriving.

### 2.3 Dining Philosophers (4), semaphore based
- Four forks, each a `Semaphore(1)`. Philosopher *i* uses fork *i* (left) and fork *(i+1) mod 4* (right).
- **Deadlock prevention:** a `room = Semaphore(3)` admits at most three philosophers to the fork-acquisition phase, so a circular wait cannot form.
- **Starvation:** unlikely in practice because of the wake-up order, but not formally guaranteed.

### 2.4 Dining Philosophers (4), monitor based
- A class `DiningMonitor` keeps one state per philosopher (`thinking`, `hungry`, `eating`) under one `Condition`.
- A philosopher eats only if both neighbours are not eating, and both forks are granted atomically. This removes hold-and-wait, so there is no deadlock.
- **Starvation:** possible if a philosopher's neighbours alternate eating.

## 3. Language and requirements

- **Language:** Python 3.8 or newer
- **Libraries:** standard library only (`threading`, `time`, `random`, `json`, `argparse`, `os`). Nothing needs to be installed.
- **Browser:** any modern browser for viewing the simulations.

## 4. Repository structure

```
OS-Synchronization-Assignment/
├── README.md
├── common.py                  # event recorder, trace verifier, HTML generator
├── rw_semaphore.py            # Readers-Writers, semaphores
├── rw_monitor.py              # Readers-Writers, monitor
├── dp_semaphore.py            # Dining Philosophers, semaphores
├── dp_monitor.py              # Dining Philosophers, monitor
├── generated_html/            # simulations produced by the programs
│   ├── readers_writers_semaphore.html
│   ├── readers_writers_monitor.html
│   ├── dining_philosophers_semaphore.html
│   └── dining_philosophers_monitor.html
├── screenshots/               # execution and simulation screenshots
├── ai_prompts/
│   └── prompts.md             # AI prompt log
├── references/
│   └── references.md
└── report/
    └── Assignment_Report.pdf
```

## 5. Build and run

There is no build or compile step. Clone the repository and run the scripts from the project folder.

```bash
git clone https://github.com/<your-username>/OS-Synchronization-Assignment.git
cd OS-Synchronization-Assignment
```

Run any implementation:

```bash
python rw_semaphore.py
python rw_monitor.py
python dp_semaphore.py
python dp_monitor.py
```

On Windows, use `py` in place of `python` if `python` is not recognised.

### Command-line options

| Option | Applies to | Default | Meaning |
|---|---|---|---|
| `--readers N` | Readers-Writers | 4 | number of reader threads |
| `--writers N` | Readers-Writers | 2 | number of writer threads |
| `--rounds N` | Readers-Writers | 3 | read/write attempts per thread |
| `--meals N` | Dining Philosophers | 3 | meals per philosopher |
| `--delay S` | all | 0.3 | base delay in seconds, to make concurrency visible |
| `--out DIR` | all | `generated_html` | output folder |

Examples:

```bash
python rw_semaphore.py --readers 6 --writers 3 --rounds 2 --delay 0.2
python dp_monitor.py --meals 5 --delay 0.1
```

## 6. Generating and viewing the HTML simulation

Running a program is the only step needed to generate its simulation. Each run writes two files to `generated_html/`:

- `<name>.html`: the simulation page
- `<name>.json`: the raw execution trace the page was built from

To view a simulation, open the `.html` file in a browser (double-click it, or right-click it in VS Code and use "Open with Live Server"). Use **Start**, **Pause** and **Reset**, change the speed, drag the slider, or click any event in the timeline to jump to it. Re-running a program overwrites the files, so refresh the browser tab afterwards.

### How the simulation is produced

```
Execute program -> threads synchronize -> state changes logged -> trace saved -> HTML generated -> view in browser
```

1. Each thread calls `TraceRecorder.log(actor, state, detail)` at every state change (waiting, reading, writing, hungry, acquiring, eating and so on). A lock keeps the log in a consistent order.
2. When the threads finish, `verify()` replays the trace and checks mutual exclusion (Readers-Writers) and fork exclusivity with no two neighbours eating together (Dining Philosophers).
3. `finish()` embeds the trace in an HTML/JavaScript template. The page redraws its state from the recorded events, so different runs produce different simulations.

### What each simulation shows

- **Readers-Writers:** reader and writer states, shared-resource status (free, open to readers, locked by a writer), the waiting queue, and the event timeline.
- **Dining Philosophers:** four philosophers and four forks on a table, fork ownership shown by lines to the owner, philosopher states (thinking, hungry, acquiring, eating, releasing), and the event timeline.

## 7. Expected output

Each run prints the number of recorded events and the verification result. The Readers-Writers programs also compare the final shared value with the expected number of writes.

```
final shared value: 6 (expected 6 )
54 events -> generated_html/readers_writers_semaphore.html | trace verified: no violations
```

```
108 events -> generated_html/dining_philosophers_semaphore.html | trace verified: no violations
```

Event counts and interleavings vary from run to run because of thread scheduling and random delays.

## 8. Screenshots

| Simulation | Screenshot |
|---|---|
| Readers-Writers, semaphore | ![RW semaphore](screenshots/readers_writers_semaphore.png) |
| Readers-Writers, monitor | ![RW monitor](screenshots/readers_writers_monitor.png) |
| Dining Philosophers, semaphore | ![DP semaphore](screenshots/dining_philosophers_semaphore.png) |
| Dining Philosophers, monitor | ![DP monitor](screenshots/dining_philosophers_monitor.png) |

## 9. Race conditions, deadlock and starvation

| Concern | How it is handled |
|---|---|
| Race condition | `mutex` protects `read_count`; `wrt` or the monitor lock protects the shared value |
| Mutual exclusion | Checked on every run by `verify()` |
| Deadlock (Dining Philosophers) | Semaphore version limits competitors with `room(3)`; monitor version grants both forks atomically |
| Starvation | Not eliminated. See limitations below |

## 10. Known limitations

- Python's GIL means threads do not run CPU-bound work in parallel. Blocking calls release it, so the synchronization behaviour is still demonstrated correctly.
- None of the four solutions guarantees bounded waiting. Writers can starve in the semaphore Readers-Writers solution, readers can starve in the monitor one, and a philosopher can be passed over repeatedly in the monitor Dining Philosophers solution.
- The semaphore Dining Philosophers solution relies on the wake-up order of Python semaphores, which the language does not specify.
- Delays are random, so a specific interleaving cannot be reproduced exactly.
- Dining Philosophers is fixed at four philosophers.

## 11. AI tools used

- **Tool:** Claude (Anthropic)
- **Use:** design of the four implementations, the shared trace and HTML generator, and drafting of the report
- **Prompt log:** [`ai_prompts/prompts.md`](ai_prompts/prompts.md)
- **Manual changes and testing:** [describe what you modified and tested yourself]

## 12. References and acknowledgements

Full list in [`references/references.md`](references/references.md).

1. Python Software Foundation, "threading: Thread-based parallelism," Python 3 Documentation. https://docs.python.org/3/library/threading.html
2. A. Silberschatz, P. B. Galvin and G. Gagne, *Operating System Concepts*. Wiley.
3. A. B. Downey, *The Little Book of Semaphores*. https://greenteapress.com/wp/semaphores/
4. E. W. Dijkstra, "Cooperating Sequential Processes," 1968.
5. P. J. Courtois, F. Heymans and D. L. Parnas, "Concurrent Control with 'Readers' and 'Writers'," *Communications of the ACM*, 1971.
6. C. A. R. Hoare, "Monitors: An Operating System Structuring Concept," *Communications of the ACM*, 1974.

## 13. Academic integrity

I have personally tested and understood the submitted programs. I have disclosed the AI tool used in developing this assignment, and I can explain the synchronization logic, the generated HTML simulation and the modifications made to the code.
