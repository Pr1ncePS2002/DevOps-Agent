"""
Generate a high-quality PNG Use Case Diagram for AI DevOps Commander.
Fixes applied:
  1. LLM Provider connected to UC-03, UC-04, and UC-12
  2. Redis/RQ Worker connected to UC-06 and UC-07
  3. UC-07 <<include>> UC-14 added (Dockerfile auto-generated at build time)
  4. Developer/Operator connected to all 8 required use cases
  5. Docker Daemon connected to UC-07, UC-09, UC-10, UC-11
  6. Proper UML actor notation (stick figure for human actor)
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Ellipse, FancyBboxPatch
import numpy as np

# ── Palette ───────────────────────────────────────────────────────────────────
NAVY        = '#000080'
UC_FILL     = '#cce8f4'
UC_EDGE     = '#1a5276'
ACTOR_FILL  = '#dde8ff'
SYS_FILL    = '#f0f4ff'
CLUSTER_FILL= '#ffffff'
ASSOC_CLR   = '#333333'
ARROW_CLR   = '#222222'
LABEL_BG    = '#ffffff'

FIG_W, FIG_H = 34, 26

fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, FIG_W)
ax.set_ylim(-2.5, FIG_H)
ax.axis('off')
fig.patch.set_facecolor('white')
ax.set_facecolor('white')

# ── Title ─────────────────────────────────────────────────────────────────────
ax.text(16.5, 25.4,
        'Use Case Diagram  —  AI DevOps Commander',
        ha='center', va='center', fontsize=21, fontweight='bold', color=NAVY,
        bbox=dict(boxstyle='round,pad=0.55', facecolor='#eef0ff',
                  edgecolor=NAVY, linewidth=2.2))

# ── Helpers ───────────────────────────────────────────────────────────────────
def ellipse_edge(cx, cy, ew, eh, tx, ty):
    """Point on ellipse boundary (cx,cy,ew,eh) in direction of (tx,ty)."""
    dx, dy = tx - cx, ty - cy
    ang = np.arctan2(dy, dx)
    return cx + (ew / 2) * np.cos(ang), cy + (eh / 2) * np.sin(ang)

def draw_cluster(label, x, y, w, h):
    r = FancyBboxPatch((x, y), w, h,
        boxstyle='round,pad=0.15', linewidth=1.6,
        edgecolor='#778899', linestyle=(0, (6, 4)),
        facecolor=CLUSTER_FILL, alpha=0.55, zorder=1)
    ax.add_patch(r)
    ax.text(x + w / 2, y + h - 0.15, label,
            ha='center', va='top', fontsize=11.5,
            color='#445566', fontstyle='italic', fontweight='bold', zorder=2)

def draw_usecase(cx, cy, label, ew, eh):
    e = Ellipse((cx, cy), width=ew, height=eh,
                facecolor=UC_FILL, edgecolor=UC_EDGE,
                linewidth=2.0, zorder=5)
    ax.add_patch(e)
    fs = 8.2 if label.count('\n') >= 2 else 9.5
    ax.text(cx, cy, label, ha='center', va='center',
            fontsize=fs, fontweight='bold', color='#000000',
            multialignment='center', zorder=6)

def draw_human_actor(cx, cy, label):
    R = 0.42
    head = plt.Circle((cx, cy + 2.1 + R), R,
                       facecolor=ACTOR_FILL, edgecolor=NAVY, lw=2.8, zorder=7)
    ax.add_patch(head)
    top_b, bot_b = cy + 2.1, cy + 1.05
    ax.plot([cx, cx], [top_b, bot_b],        color=NAVY, lw=2.8, zorder=7)
    ax.plot([cx - 0.6, cx + 0.6], [top_b - 0.38, top_b - 0.38],
            color=NAVY, lw=2.8, zorder=7)
    ax.plot([cx, cx - 0.55], [bot_b, cy],   color=NAVY, lw=2.8, zorder=7)
    ax.plot([cx, cx + 0.55], [bot_b, cy],   color=NAVY, lw=2.8, zorder=7)
    ax.text(cx, cy - 0.45, label, ha='center', va='top',
            fontsize=11, fontweight='bold', color=NAVY,
            multialignment='center', zorder=7)

def draw_system_actor(cx, cy, label):
    w, h = 4.0, 1.6
    # outer double-border effect
    ax.add_patch(FancyBboxPatch((cx - w/2 - 0.1, cy - h/2 - 0.1), w + 0.2, h + 0.2,
        boxstyle='round,pad=0.06', linewidth=3.0,
        edgecolor=NAVY, facecolor=ACTOR_FILL, zorder=7))
    ax.add_patch(FancyBboxPatch((cx - w/2, cy - h/2), w, h,
        boxstyle='round,pad=0.06', linewidth=1.5,
        edgecolor=NAVY, facecolor='#eef2ff', zorder=8))
    ax.text(cx, cy + 0.2, label, ha='center', va='center',
            fontsize=10, fontweight='bold', color=NAVY,
            multialignment='center', zorder=9)
    ax.text(cx, cy - 0.45, '<<actor>>', ha='center', va='center',
            fontsize=8.5, color='#556677', style='italic', zorder=9)

def assoc_line(x1, y1, x2, y2, alpha=0.65):
    ax.plot([x1, x2], [y1, y2], color=ASSOC_CLR, lw=1.5, alpha=alpha, zorder=3)

def dashed_arrow(src, dst, label, rad=0.0, lx=0.0, ly=0.0):
    """Draw a dashed arrow between two use cases with a stereotype label.

    rad  : arc curvature (matplotlib arc3 convention)
    lx/ly: extra nudge applied to the label only, to avoid nearby overlap
    """
    sx, sy = uc_pos[src][:2]
    dx, dy = uc_pos[dst][:2]
    sew, seh = uc_pos[src][3], uc_pos[src][4]   # index 3=ew, 4=eh (index 2 is label)
    dew, deh = uc_pos[dst][3], uc_pos[dst][4]
    ex1, ey1 = ellipse_edge(sx, sy, sew, seh, dx, dy)
    ex2, ey2 = ellipse_edge(dx, dy, dew, deh, sx, sy)
    ax.annotate('', xy=(ex2, ey2), xytext=(ex1, ey1),
        arrowprops=dict(
            arrowstyle='-|>', color=ARROW_CLR, lw=1.7,
            linestyle=(0, (6, 3)), mutation_scale=14,
            connectionstyle=f'arc3,rad={rad}'),
        zorder=4)
    # Label at true arc midpoint.
    # matplotlib arc3 control point = (mid_x + rad*dy_chord, mid_y - rad*dx_chord)
    # Quadratic Bezier midpoint (t=0.5) = midpoint + 0.5 * (control - midpoint)
    #                                    = (mid_x + 0.5*rad*dy, mid_y - 0.5*rad*dx)
    dx_chord = ex2 - ex1
    dy_chord = ey2 - ey1
    mx = (ex1 + ex2) / 2 + 0.5 * rad * dy_chord + lx
    my = (ey1 + ey2) / 2 - 0.5 * rad * dx_chord + ly
    ax.text(mx, my, label, ha='center', va='center', fontsize=9,
            color='#222222', style='italic',
            bbox=dict(facecolor=LABEL_BG, edgecolor='#cccccc',
                      boxstyle='round,pad=0.18', linewidth=0.8, alpha=0.95),
            zorder=8)

# ── System boundary ───────────────────────────────────────────────────────────
ax.add_patch(FancyBboxPatch((4.0, 0.5), 22.5, 24.0,
    boxstyle='round,pad=0.4', linewidth=2.8,
    edgecolor=NAVY, linestyle='--',
    facecolor=SYS_FILL, alpha=0.35, zorder=0))
ax.text(15.25, 24.3, 'AI DevOps Commander Platform',
        ha='center', va='center', fontsize=13, color=NAVY,
        fontstyle='italic', fontweight='bold', zorder=1)

# ── Clusters ──────────────────────────────────────────────────────────────────
draw_cluster('Registration & Setup',  4.5, 17.8, 21.5, 6.2)
draw_cluster('Command & Planning',    4.5,  9.2, 21.5, 8.1)
draw_cluster('Execution & Ops',       4.5,  0.8, 21.5, 7.9)

# ── Use cases  (cx, cy, label, ellipse_w, ellipse_h) ─────────────────────────
uc_pos = {
    # Registration
    'UC01': (10.0, 22.8, 'UC-01  Register Project',          5.0, 1.05),
    'UC02': (10.0, 20.5, 'UC-02  Upload Environment File',   5.2, 1.05),
    'UC13': (20.5, 22.8, 'UC-13  Clone GitHub Repository',   5.2, 1.05),
    'UC14': (20.5, 20.5, 'UC-14  Auto-Generate Dockerfile',  5.2, 1.05),
    # Planning
    'UC03': ( 9.5, 16.2, 'UC-03  Parse Natural\nLanguage Command',  5.2, 1.2),
    'UC04': (20.5, 16.2, 'UC-04  Assess\nDeployment Risk',          5.0, 1.2),
    'UC05': ( 9.5, 13.8, 'UC-05  Preview Deployment Plan',          5.2, 1.05),
    'UC06': (15.5, 11.5, 'UC-06  Approve Deployment Plan',          5.2, 1.05),
    'UC12': ( 9.5, 10.5, 'UC-12  Conduct Multi-Turn\nDevOps Chat',  5.4, 1.2),
    # Execution
    'UC07': (11.0,  7.2, 'UC-07  Execute Deployment\nPipeline',     5.4, 1.2),
    'UC08': ( 7.2,  5.5, 'UC-08  Stream Execution Logs',            4.8, 1.05),
    'UC09': (11.0,  3.8, 'UC-09  Monitor Deployment Health',        5.4, 1.05),
    'UC10': (20.5,  5.5, 'UC-10  Automatic Rollback',               5.0, 1.05),
    'UC11': (11.0,  2.0, 'UC-11  Manual Rollback',                  4.8, 1.05),
}

for key, (cx, cy, lbl, ew, eh) in uc_pos.items():
    draw_usecase(cx, cy, lbl, ew, eh)

# ── Actors ────────────────────────────────────────────────────────────────────
#  Human actor: Developer/Operator — left side, centred vertically
DEV_CX, DEV_CY = 1.3, 10.5
draw_human_actor(DEV_CX, DEV_CY, 'Developer /\nOperator')

# System actors — right side
draw_system_actor(30.5, 22.0, 'GitHub')
draw_system_actor(30.5, 14.5, 'LLM Provider\n(Gemini / OpenAI / Ollama)')
draw_system_actor(30.5,  6.0, 'Docker Daemon')
draw_system_actor(30.5,  1.8, 'Redis / RQ Worker')

# ── Association lines ─────────────────────────────────────────────────────────
# Developer → use cases  (from right edge of stick figure area)
dev_rx = DEV_CX + 0.65   # right extremity of arms/legs spread
for uc_key in ['UC01', 'UC02', 'UC03', 'UC05', 'UC06', 'UC08', 'UC11', 'UC12']:
    cx, cy, _, ew, eh = uc_pos[uc_key]
    ex, ey = ellipse_edge(cx, cy, ew, eh, dev_rx, DEV_CY + 1.3)
    assoc_line(dev_rx, DEV_CY + 1.3, ex, ey)

# LLM Provider → UC-03, UC-04, UC-12
LLM_LX = 30.5 - 2.1   # left edge of LLM actor box
for uc_key in ['UC03', 'UC04', 'UC12']:
    cx, cy, _, ew, eh = uc_pos[uc_key]
    ex, ey = ellipse_edge(cx, cy, ew, eh, LLM_LX, 14.5)
    assoc_line(LLM_LX, 14.5, ex, ey)

# Docker Daemon → UC-07, UC-09, UC-10, UC-11
DOCK_LX = 30.5 - 2.1
for uc_key in ['UC07', 'UC09', 'UC10', 'UC11']:
    cx, cy, _, ew, eh = uc_pos[uc_key]
    ex, ey = ellipse_edge(cx, cy, ew, eh, DOCK_LX, 6.0)
    assoc_line(DOCK_LX, 6.0, ex, ey)

# GitHub → UC-13
GH_LX = 30.5 - 2.1
cx, cy, _, ew, eh = uc_pos['UC13']
ex, ey = ellipse_edge(cx, cy, ew, eh, GH_LX, 22.0)
assoc_line(GH_LX, 22.0, ex, ey)

# Redis / RQ → UC-06, UC-07
RD_LX = 30.5 - 2.1
for uc_key in ['UC06', 'UC07']:
    cx, cy, _, ew, eh = uc_pos[uc_key]
    ex, ey = ellipse_edge(cx, cy, ew, eh, RD_LX, 1.8)
    assoc_line(RD_LX, 1.8, ex, ey)

# ── <<include>> relationships ───────────────────────────────────────────────────
dashed_arrow('UC01', 'UC13', '<<include>>', rad=-0.12)
dashed_arrow('UC01', 'UC14', '<<include>>', rad=0.18)
dashed_arrow('UC03', 'UC04', '<<include>>', rad=-0.08)
dashed_arrow('UC07', 'UC14', '<<include>>', rad=0.35)   # cross-cluster arc
dashed_arrow('UC09', 'UC10', '<<include>>', rad=-0.15)
dashed_arrow('UC12', 'UC03', '<<include>>', rad=0.22)

# ── <<extend>> relationships ────────────────────────────────────────────────────
dashed_arrow('UC10', 'UC06', '<<extend>>',  rad=-0.28)
dashed_arrow('UC11', 'UC06', '<<extend>>',  rad=0.28)

# ── Legend ────────────────────────────────────────────────────────────────────
LX, LY, LW, LH = 4.5, -2.3, 21.5, 1.7
ax.add_patch(FancyBboxPatch((LX, LY), LW, LH,
    boxstyle='round,pad=0.15', linewidth=1.4,
    edgecolor='#aaaaaa', facecolor='#f9f9f9', zorder=7))

ax.text(LX + LW / 2, LY + LH - 0.2, 'Legend',
        ha='center', va='top', fontsize=11.5,
        fontweight='bold', color=NAVY, zorder=8)

# Association symbol
ax.plot([LX + 0.5, LX + 2.0], [LY + 0.6, LY + 0.6],
        color=ASSOC_CLR, lw=2.0, zorder=8)
ax.text(LX + 2.15, LY + 0.6,
        'Association — Actor ↔ Use Case',
        va='center', fontsize=9.5, zorder=8)

# Include symbol
ax.annotate('', xy=(LX + 9.0, LY + 0.6), xytext=(LX + 7.5, LY + 0.6),
    arrowprops=dict(arrowstyle='-|>', color=ARROW_CLR, lw=1.7,
                    linestyle=(0, (5, 3)), mutation_scale=11), zorder=8)
ax.text(LX + 9.15, LY + 0.6,
        '<<include>> — Mandatory dependency',
        va='center', fontsize=9.5, zorder=8)

# Extend symbol
ax.annotate('', xy=(LX + 16.5, LY + 0.6), xytext=(LX + 15.0, LY + 0.6),
    arrowprops=dict(arrowstyle='-|>', color=ARROW_CLR, lw=1.7,
                    linestyle=(0, (5, 3)), mutation_scale=11), zorder=8)
ax.text(LX + 16.65, LY + 0.6,
        '<<extend>> — Conditional behavior',
        va='center', fontsize=9.5, zorder=8)

# Use case oval in legend
ax.add_patch(Ellipse((LX + 20.2, LY + 0.6), width=2.1, height=0.7,
    facecolor=UC_FILL, edgecolor=UC_EDGE, linewidth=1.6, zorder=8))
ax.text(LX + 20.2, LY + 0.6, 'Use Case',
        ha='center', va='center', fontsize=8.5, fontweight='bold', zorder=9)

# ── Save ──────────────────────────────────────────────────────────────────────
out = r'c:\Users\psing\Desktop\DevOps Agent\UseCase_Diagram.png'
plt.savefig(out, dpi=160, bbox_inches='tight',
            facecolor='white', edgecolor='none')
print(f"Saved: {out}")
import os
print(f"Size:  {os.path.getsize(out):,} bytes")
