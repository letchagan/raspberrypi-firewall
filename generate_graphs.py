import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os

OUTPUT = '/home/pi/idps/logs/'
os.makedirs(OUTPUT, exist_ok=True)

# ── Style ──────────────────────────────────────────────────────────────────
plt.rcParams.update({
    'figure.facecolor': '#0a0e1a',
    'axes.facecolor': '#0d1f35',
    'axes.edgecolor': '#1a3a5c',
    'axes.labelcolor': '#cdd9e8',
    'xtick.color': '#7a9bbf',
    'ytick.color': '#7a9bbf',
    'text.color': '#cdd9e8',
    'grid.color': '#1a3a5c',
    'grid.linestyle': '--',
    'grid.alpha': 0.5,
    'font.family': 'DejaVu Sans',
})

# ── Graph 1: Detection Accuracy by Attack Category ─────────────────────────
fig, ax = plt.subplots(figsize=(10, 5))
categories = ['Malicious\nUser Agent', 'Attack\nResponse', 'Port\nScan', 'DoS\nAttack', 'Brute\nForce', 'SQL\nInjection', 'Web\nAttack XSS', 'Overall']
our_system = [100, 100, 78, 95, 92, 89, 87, 99.80]
enterprise  = [98,  97,  96, 98, 95, 94, 93, 96.00]

x = np.arange(len(categories))
w = 0.35

bars1 = ax.bar(x - w/2, our_system, w, label='Our IDPS (Raspberry Pi)', color='#00e5ff', alpha=0.85, zorder=3)
bars2 = ax.bar(x + w/2, enterprise,  w, label='Enterprise IDPS',         color='#ff6d00', alpha=0.85, zorder=3)

ax.set_ylabel('Detection Rate (%)', fontsize=11)
ax.set_title('Detection Accuracy by Attack Category', fontsize=13, fontweight='bold', pad=15)
ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=9)
ax.set_ylim(0, 115)
ax.legend(loc='lower right', fontsize=9)
ax.grid(axis='y', zorder=0)
ax.axhline(y=94, color='#ffd600', linestyle='--', alpha=0.5, label='94% threshold')

for bar in bars1:
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+1,
            f'{bar.get_height():.0f}%', ha='center', va='bottom', fontsize=7.5, color='#00e5ff')
for bar in bars2:
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+1,
            f'{bar.get_height():.0f}%', ha='center', va='bottom', fontsize=7.5, color='#ff6d00')

plt.tight_layout()
plt.savefig(OUTPUT+'fig3_detection_accuracy.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ Graph 1 saved: fig3_detection_accuracy.png")

# ── Graph 2: Response Time Comparison ──────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 5))
systems  = ['Our IDPS\n(Pi 4)', 'Cisco\nFirepower', 'Palo Alto\nNetworks', 'Fortinet\nFortiGate', 'Snort\n(Basic)']
avg_times = [255, 310, 280, 340, 420]
colors    = ['#00e5ff', '#ff6d00', '#ff6d00', '#ff6d00', '#7a9bbf']

bars = ax.bar(systems, avg_times, color=colors, alpha=0.85, zorder=3, width=0.5)
ax.set_ylabel('Average Response Time (ms)', fontsize=11)
ax.set_title('Threat Response Time: Our IDPS vs Competitors', fontsize=13, fontweight='bold', pad=15)
ax.set_ylim(0, 520)
ax.grid(axis='y', zorder=0)
ax.axhline(y=300, color='#ffd600', linestyle='--', alpha=0.6, label='300ms target')
ax.legend(fontsize=9)

for bar in bars:
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+8,
            f'{bar.get_height()}ms', ha='center', va='bottom', fontsize=10, fontweight='bold',
            color='#00e5ff' if bar.get_height()==255 else '#cdd9e8')

plt.tight_layout()
plt.savefig(OUTPUT+'fig4_response_time.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ Graph 2 saved: fig4_response_time.png")

# ── Graph 3: Cost vs Performance ───────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 6))
systems2 = ['Our IDPS', 'Snort Basic', 'IPFire', 'Cisco\nFirepower', 'Palo Alto\nNetworks']
costs    = [120, 300, 200, 9000, 12000]
accuracy = [99.80, 78.4, 61.3, 97.0, 98.0]
sizes    = [200, 150, 150, 300, 300]
clrs     = ['#00e5ff', '#7a9bbf', '#7a9bbf', '#ff6d00', '#ff1744']

scatter = ax.scatter(costs, accuracy, s=sizes, c=clrs, alpha=0.85, zorder=3, edgecolors='white', linewidths=0.5)

labels = ['Our IDPS\n$120', 'Snort\n$300', 'IPFire\n$200', 'Cisco FP\n$9,000', 'Palo Alto\n$12,000']
offsets = [(50, -3), (80, 1), (80, -3), (-1200, 1), (-1500, -3)]
for i, (x, y) in enumerate(zip(costs, accuracy)):
    ax.annotate(labels[i], (x, y), xytext=(x+offsets[i][0], y+offsets[i][1]),
                fontsize=8, color=clrs[i], ha='left')

ax.set_xlabel('Hardware Cost (USD)', fontsize=11)
ax.set_ylabel('Detection Accuracy (%)', fontsize=11)
ax.set_title('Cost vs Detection Accuracy Comparison', fontsize=13, fontweight='bold', pad=15)
ax.set_xlim(-500, 14000)
ax.set_ylim(50, 105)
ax.grid(zorder=0)

plt.tight_layout()
plt.savefig(OUTPUT+'fig5_cost_vs_performance.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ Graph 3 saved: fig5_cost_vs_performance.png")

# ── Graph 4: False Positive Rate ───────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 5))
systems3  = ['Our IDPS\n(Real Test)', 'Our IDPS\n(Paper Est.)', 'Snort', 'IPFire', 'Enterprise\nIDPS']
fp_rates  = [0.00, 2.1, 8.7, 5.2, 1.5]
clrs2     = ['#00e676', '#00e5ff', '#ff6d00', '#ff6d00', '#ffd600']

bars3 = ax.bar(systems3, fp_rates, color=clrs2, alpha=0.85, zorder=3, width=0.5)
ax.set_ylabel('False Positive Rate (%)', fontsize=11)
ax.set_title('False Positive Rate Comparison', fontsize=13, fontweight='bold', pad=15)
ax.set_ylim(0, 12)
ax.grid(axis='y', zorder=0)

for bar in bars3:
    val = bar.get_height()
    ax.text(bar.get_x()+bar.get_width()/2, val+0.2,
            f'{val:.2f}%', ha='center', va='bottom', fontsize=10, fontweight='bold',
            color='#00e676' if val==0.00 else '#cdd9e8')

plt.tight_layout()
plt.savefig(OUTPUT+'fig6_false_positive.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ Graph 4 saved: fig6_false_positive.png")

print("\n🎉 All graphs generated successfully!")
print(f"Saved to: {OUTPUT}")
