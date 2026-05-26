import subprocess
import time
import json
import os
import statistics
from datetime import datetime

RESULTS = {
    'timestamp': str(datetime.now()),
    'tests': [],
    'summary': {}
}

LOG = '/var/log/suricata/eve.json'

def get_alert_count():
    try:
        with open(LOG) as f:
            return sum(1 for line in f if '"event_type":"alert"' in line)
    except:
        return 0

def get_blocked_count():
    try:
        result = subprocess.getoutput('nft list set ip blocklist blocked_ips 2>/dev/null | grep -c "\\."')
        return int(result.strip()) if result.strip().isdigit() else 0
    except:
        return 0

def measure_response_time(attack_cmd):
    before = get_alert_count()
    start = time.time()
    os.system(attack_cmd + ' > /dev/null 2>&1')
    # Wait for Suricata to process
    for _ in range(30):
        time.sleep(0.1)
        after = get_alert_count()
        if after > before:
            response_ms = (time.time() - start) * 1000
            return response_ms, True
    return 3000, False  # Timeout

def run_test(name, cmd, expected_detection=True):
    print(f"\n{'='*50}")
    print(f"TEST: {name}")
    print(f"CMD : {cmd}")
    print(f"{'='*50}")

    times = []
    detected = 0
    trials = 5

    for i in range(trials):
        print(f"  Trial {i+1}/{trials}...", end=' ', flush=True)
        ms, det = measure_response_time(cmd)
        if det:
            detected += 1
            times.append(ms)
            print(f"✅ Detected in {ms:.0f}ms")
        else:
            print(f"❌ Not detected")
        time.sleep(1)

    detection_rate = (detected / trials) * 100
    avg_time = statistics.mean(times) if times else 0
    min_time = min(times) if times else 0
    max_time = max(times) if times else 0

    result = {
        'test': name,
        'trials': trials,
        'detected': detected,
        'detection_rate': detection_rate,
        'avg_response_ms': round(avg_time, 1),
        'min_response_ms': round(min_time, 1),
        'max_response_ms': round(max_time, 1),
    }

    RESULTS['tests'].append(result)

    print(f"\n  Detection Rate : {detection_rate:.0f}%")
    print(f"  Avg Response   : {avg_time:.0f}ms")
    print(f"  Min/Max        : {min_time:.0f}ms / {max_time:.0f}ms")
    return result

def measure_throughput():
    print(f"\n{'='*50}")
    print("TEST: Network Throughput Overhead")
    print(f"{'='*50}")

    # Baseline without IDPS inspection
    print("  Measuring baseline ping latency...")
    baseline = []
    for _ in range(20):
        result = subprocess.getoutput('ping -c 1 -W 1 8.8.8.8 2>/dev/null | grep time=')
        if 'time=' in result:
            ms = float(result.split('time=')[1].split(' ')[0])
            baseline.append(ms)
        time.sleep(0.2)

    avg_latency = statistics.mean(baseline) if baseline else 0
    print(f"  Average latency: {avg_latency:.1f}ms")

    RESULTS['summary']['avg_latency_ms'] = round(avg_latency, 1)
    return avg_latency

def measure_false_positives():
    print(f"\n{'='*50}")
    print("TEST: False Positive Rate (Normal Traffic)")
    print(f"{'='*50}")

    before = get_alert_count()
    print("  Generating normal traffic for 30 seconds...")

    # Generate normal traffic
    normal_cmds = [
        'curl -s https://www.google.com > /dev/null',
        'curl -s https://github.com > /dev/null',
        'ping -c 3 8.8.8.8 > /dev/null',
        'curl -s https://httpbin.org/get > /dev/null',
    ]

    start = time.time()
    fp_count = 0
    total_requests = 0

    while time.time() - start < 30:
        for cmd in normal_cmds:
            os.system(cmd + ' 2>/dev/null')
            total_requests += 1
            time.sleep(0.5)

    after = get_alert_count()
    fp_count = max(0, after - before)
    fp_rate = (fp_count / max(1, total_requests)) * 100

    print(f"  Normal requests sent : {total_requests}")
    print(f"  False alerts         : {fp_count}")
    print(f"  False positive rate  : {fp_rate:.2f}%")

    RESULTS['summary']['false_positive_rate'] = round(fp_rate, 2)
    RESULTS['summary']['total_normal_requests'] = total_requests
    RESULTS['summary']['false_alerts'] = fp_count
    return fp_rate

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*50)
    print("  IDPS BENCHMARK — Phase 7 Testing")
    print(f"  Started: {datetime.now()}")
    print("="*50)

    # Test 1 — Malicious User Agent
    run_test(
        "Malicious User Agent (BlackSun)",
        "curl -4 --interface usb0 -s -A 'BlackSun' http://testmynids.org/uid/index.html"
    )

    # Test 2 — Attack Response Detection
    run_test(
        "Attack Response Detection",
        "curl -4 --interface usb0 -s http://testmynids.org/uid/index.html"
    )

    # Test 3 — Port Scan Detection
    run_test(
        "Port Scan Detection (Nmap)",
        "sudo nmap -sS --max-rate 100 192.168.50.1 -p 1-100"
    )

    # Test 4 — Throughput
    measure_throughput()

    # Test 5 — False Positives
    measure_false_positives()

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'='*50}")
    print("  BENCHMARK COMPLETE — RESULTS SUMMARY")
    print(f"{'='*50}")

    total_tests = len(RESULTS['tests'])
    avg_detection = sum(t['detection_rate'] for t in RESULTS['tests']) / total_tests
    avg_response = sum(t['avg_response_ms'] for t in RESULTS['tests'] if t['avg_response_ms'] > 0) / total_tests

    RESULTS['summary']['avg_detection_rate'] = round(avg_detection, 1)
    RESULTS['summary']['avg_response_ms'] = round(avg_response, 1)

    print(f"\n  Average Detection Rate : {avg_detection:.1f}%")
    print(f"  Average Response Time  : {avg_response:.0f}ms")
    print(f"  False Positive Rate    : {RESULTS['summary'].get('false_positive_rate', 0):.2f}%")
    print(f"  Avg Network Latency    : {RESULTS['summary'].get('avg_latency_ms', 0):.1f}ms")
    print(f"\n  Blocked IPs Total      : {get_blocked_count()}")

    # Save results
    with open('/home/pi/idps/logs/benchmark_results.json', 'w') as f:
        json.dump(RESULTS, f, indent=2)

    print(f"\n  Results saved to: /home/pi/idps/logs/benchmark_results.json")
    print(f"  Completed: {datetime.now()}")
    print("="*50)
