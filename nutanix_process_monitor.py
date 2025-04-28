#
# Script to collect process metrics from Nutanix nodes over SSH.
# This script requires SSH access to the nodes and the 'ps' command to be available.
# It collects CPU, memory, and virtual size metrics for specified processes.
# Runs indefinitely until interrupted, and saves the collected data to CSV files.
#
# Usage:
# python nutanix_process_monitor.py --processes <process1> <process2> ... --interval <seconds>
# authod: alfaz.ahmed@nutanix.com
#

import argparse
import subprocess
import time
import pandas as pd
from collections import defaultdict
import signal

stop_signal = False

def signal_handler(sig, frame):
    global stop_signal
    print("\nStopping monitoring...")
    stop_signal = True

signal.signal(signal.SIGINT, signal_handler)

def get_node_ips():
    try:
        result = subprocess.run(['/usr/local/nutanix/cluster/bin/svmips'], stdout=subprocess.PIPE, text=True)
        ips = result.stdout.strip().split()
        return ips
    except Exception as e:
        print(f"Failed to get IPs: {e}")
        return []

def ssh_run(ip, command):
    ssh_command = ["ssh", ip, command]
    result = subprocess.run(ssh_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result.stdout

def collect_process_metrics(ip, process_name):
    ps_command = "ps -eo pid,pcpu,pmem,vsz,comm | grep {} | grep -v grep".format(process_name)
    output = ssh_run(ip, ps_command)
    metrics = []

    for line in output.strip().split('\n'):
        if not line.strip():
            continue
        try:
            parts = line.split(None, 4)
            if len(parts) < 5:
                continue
            pid, cpu, mem, vsz, cmd = parts
            if process_name in cmd:
                metrics.append({
                    "timestamp": pd.Timestamp.now(),
                    "node": ip,
                    "pid": int(pid),
                    "cpu%": float(cpu),
                    "mem%": float(mem),
                    "vsz": int(vsz)
                })
        except Exception as e:
            print(f"Error parsing line from {ip}: '{line}' -> {e}")
    return metrics

def main(processes, interval):
    data_storage = defaultdict(list)
    ips = get_node_ips()
    if not ips:
        print("No node IPs found. Exiting.")
        return

    print(f"Monitoring every {interval}s... Press Ctrl+C to stop.")
    while not stop_signal:
        print(f"\n[{pd.Timestamp.now()}] Polling metrics...")
        for proc in processes:
            print(f"\nProcess: {proc}")
            for ip in ips:
                metrics = collect_process_metrics(ip, proc)
                if metrics:
                    for m in metrics:
                        print(f"  Node: {m['node']}, PID: {m['pid']}, CPU%: {m['cpu%']:.2f}, MEM%: {m['mem%']:.2f}, VSZ: {m['vsz']}")
                        data_storage[proc].append(m)
                else:
                    print(f"  No {proc} processes found on {ip}")
        time.sleep(interval)

    print("\nWriting CSV files...")
    for proc_name, records in data_storage.items():
        df = pd.DataFrame(records)
        csv_filename = f"{proc_name}.csv"
        df.to_csv(csv_filename, index=False)
        print(f"Saved: {csv_filename}")
    print("All done.!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor Nutanix cluster processes over SSH.")
    parser.add_argument('--processes', nargs='+', required=True, help='List of process names')
    parser.add_argument('--interval', type=int, default=10, help='Polling interval in seconds')
    args = parser.parse_args()
    main(args.processes, args.interval)

