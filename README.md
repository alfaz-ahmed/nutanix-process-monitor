# Nutanix Process Monitor

This is a lightweight Python script to monitor specific processes running across a Nutanix cluster.

It:
- Uses `/usr/local/nutanix/cluster/bin/svmips` to get the list of node IPs.
- Connects to each node via SSH.
- Runs `ps` to collect metrics for specified processes.
- Periodically prints live CPU, memory, and VSZ stats.
- Saves results into per-process `.csv` files for later analysis.

---

## 🔧 Requirements

- Python 3.6+
- SSH access (passwordless recommended) from the running node to all cluster nodes.

---

## 🚀 Usage

```bash
~/.venvs/bin/bin/python3 nutanix_process_monitor.py --processes <proc1> <proc2> ... --interval <seconds>
```
Please use venv already shipped with AOS for dependencies as noted above.

