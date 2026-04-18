"""
Generate DFD Level 0 — Context Diagram: AI DevOps Commander
Yourdon-DeMarco notation:
  Processes  → circles (bubbles)
  Entities   → rectangles with double left border
  Data flows → labelled directed arrows (no data stores at Level 0)
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, FancyBboxPatch
import numpy as np

# ── Palette ────────────────────────────────────────────────────────────────────
NAVY      = '#000080'
PROC_FILL = '#d6eaf8'
PROC_EDGE = '#1a5276'
ENT_FILL  = '#ebebeb'
ENT_EDGE  = '#2c2c2c'
FLOW_CLR  = '#111111'
LBL_BG    = '#ffffff'
LBL_EDGE  = '#aaaaaa'
TITLE_BG  = '#eef0ff'

FIG_W, FIG_H = 58, 44

# Central process position
PX, PY, PR = 29, 22, 5.0

fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, FIG_W)
ax.set_ylim(0, FIG_H)
ax.axis('off')
fig.patch.set_facecolor('white')
ax.set_facecolor('white')

# ── Title ──────────────────────────────────────────────────────────────────────
ax.text(FIG_W / 2, 43.1,
        'DFD Level 0  —  Context Diagram: AI DevOps Commander',
        ha='center', va='center', fontsize=24, fontweight='bold', color=NAVY,
        bbox=dict(boxstyle='round,pad=0.55', facecolor=TITLE_BG,
                  edgecolor=NAVY, linewidth=2.2),
        zorder=15)

# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def circ_pt(tx, ty):
    """Point on the process-circle boundary facing (tx, ty)."""
    a = np.arctan2(ty - PY, tx - PX)
    return PX + PR * np.cos(a), PY + PR * np.sin(a)


def draw_entity(cx, cy, w, h, lines):
    """
    Yourdon-DeMarco external entity: filled rectangle with double left border.
    lines[0] = entity ID (small italic), lines[1:] = main label.
    """
    x0, y0 = cx - w / 2, cy - h / 2
    # Drop-shadow
    ax.add_patch(Rectangle((x0 + 0.20, y0 - 0.20), w, h,
                            facecolor='#bbbbbb', edgecolor='none', zorder=5))
    # Main box
    ax.add_patch(Rectangle((x0, y0), w, h,
                            facecolor=ENT_FILL, edgecolor=ENT_EDGE,
                            linewidth=2.3, zorder=6))
    # Double left border (inner parallel line)
    ax.plot([x0 + 0.32, x0 + 0.32], [y0 + 0.14, y0 + h - 0.14],
            color=ENT_EDGE, lw=1.7, zorder=7)

    # Entity-ID label (top, small italic)
    ax.text(cx + 0.20, y0 + h - 0.65, lines[0],
            ha='center', va='center', fontsize=11, fontstyle='italic',
            color='#555555', zorder=8)

    # Main label lines
    body = lines[1:]
    n = len(body)
    line_h = min(1.20, (h - 1.4) / max(n, 1))
    for i, ln in enumerate(body):
        yy = cy - 0.25 + (n - 1) * line_h / 2 - i * line_h
        ax.text(cx + 0.20, yy, ln,
                ha='center', va='center', fontsize=13, fontweight='bold',
                color='#111111', zorder=8, multialignment='center')


def draw_process():
    """Central process bubble — Yourdon-DeMarco style."""
    # Soft glow ring
    ax.add_patch(Circle((PX, PY), PR + 0.28,
                         facecolor='#9ec9e8', edgecolor='none',
                         alpha=0.35, zorder=5))
    # Main circle
    ax.add_patch(Circle((PX, PY), PR,
                         facecolor=PROC_FILL, edgecolor=PROC_EDGE,
                         linewidth=3.0, zorder=6))
    ax.text(PX, PY + 1.50, 'Process 0',
            ha='center', va='center', fontsize=18, fontweight='bold',
            color=PROC_EDGE, zorder=7)
    ax.text(PX, PY - 0.10, 'AI DevOps',
            ha='center', va='center', fontsize=15, fontweight='bold',
            color=PROC_EDGE, zorder=7)
    ax.text(PX, PY - 1.70, 'Commander',
            ha='center', va='center', fontsize=15, fontweight='bold',
            color=PROC_EDGE, zorder=7)


def df_arrow(sx, sy, ex, ey, label, rad=0.0, lbl_frac=0.48, lbl_dx=0.0, lbl_dy=0.0):
    """
    Draw a directed data-flow arrow from (sx,sy) to (ex,ey) with a centred label.
    rad   : arc curvature (arc3 connectionstyle)
    lbl_frac : position along arc for label (0=start, 1=end)
    lbl_dx/dy: additional nudge for tight cases
    """
    ax.annotate('', xy=(ex, ey), xytext=(sx, sy),
                arrowprops=dict(
                    arrowstyle='->', color=FLOW_CLR, lw=1.65,
                    mutation_scale=18,
                    connectionstyle=f'arc3,rad={rad}'),
                zorder=9)

    # Midpoint + perpendicular offset proportional to curvature
    mx = sx + lbl_frac * (ex - sx)
    my = sy + lbl_frac * (ey - sy)
    if abs(rad) > 0.005:
        dx, dy = ex - sx, ey - sy
        L = np.hypot(dx, dy) + 1e-9
        # Perpendicular direction (rotated 90° CCW)
        px, py = -dy / L, dx / L
        # Scale offset by chord length so it looks proportional
        mx += rad * px * L * 0.30
        my += rad * py * L * 0.30
    mx += lbl_dx
    my += lbl_dy

    ax.text(mx, my, label,
            ha='center', va='center', fontsize=8.0, color='#111111',
            fontweight='bold', linespacing=1.35,
            bbox=dict(facecolor=LBL_BG, edgecolor=LBL_EDGE,
                      boxstyle='round,pad=0.22', linewidth=0.9, alpha=0.97),
            zorder=12)


# ══════════════════════════════════════════════════════════════════════════════
# EXTERNAL ENTITIES
# ══════════════════════════════════════════════════════════════════════════════

# E1 Developer/Operator — top-left
E1 = dict(cx=7.0,  cy=33.5, w=12.0, h=11.0)
draw_entity(**E1, lines=['E1', 'Developer /\nOperator'])

# E2 LLM Provider — top-right
E2 = dict(cx=51.0, cy=33.5, w=12.0, h=11.0)
draw_entity(**E2, lines=['E2', 'LLM Provider', '(Gemini / OpenAI\n/ Ollama)'])

# E3 Docker Daemon — bottom-right
E3 = dict(cx=51.0, cy=10.5, w=12.0, h=9.0)
draw_entity(**E3, lines=['E3', 'Docker\nDaemon'])

# E4 GitHub — bottom-left
E4 = dict(cx=7.0,  cy=10.5, w=12.0, h=9.0)
draw_entity(**E4, lines=['E4', 'GitHub'])

# E5 Redis/RQ — bottom-centre
E5 = dict(cx=29.0, cy=3.2,  w=14.0, h=4.5)
draw_entity(**E5, lines=['E5', 'Redis / RQ Job Queue'])

# ══════════════════════════════════════════════════════════════════════════════
# CENTRAL PROCESS
# ══════════════════════════════════════════════════════════════════════════════
draw_process()

# ══════════════════════════════════════════════════════════════════════════════
# DATA FLOWS
# Naming convention: DF-XX\n<Short Name>
# Arrows: entity-side fixed point → circ_pt OR circ_pt → entity-side fixed point
# ══════════════════════════════════════════════════════════════════════════════

# ─── Precompute entity edge X / Y coordinates ──────────────────────────────
E1_RX = E1['cx'] + E1['w'] / 2   # 11.7   right edge of E1
E2_LX = E2['cx'] - E2['w'] / 2   # 38.3   left  edge of E2
E3_LX = E3['cx'] - E3['w'] / 2   # 38.3   left  edge of E3
E4_RX = E4['cx'] + E4['w'] / 2   # 11.7   right edge of E4
E5_TY = E5['cy'] + E5['h'] / 2   #  4.4   top   edge of E5

# ── Helper: evenly-spaced vertical slots along an entity's edge ──────────────
def vslots(cy, h, n, padding=0.55):
    """Return n evenly-spaced y-positions along a vertical edge."""
    bot = cy - h / 2 + padding
    top = cy + h / 2 - padding
    return [bot + (top - bot) * (i + 1) / (n + 1) for i in range(n)]

def hslots(cx, w, n, padding=0.7):
    """Return n evenly-spaced x-positions along a horizontal edge."""
    left  = cx - w / 2 + padding
    right = cx + w / 2 - padding
    return [left + (right - left) * (i + 1) / (n + 1) for i in range(n)]


# ════════════════════════════════════════════════════════════════════════════
# E1 ↔ Process  (10 flows)
# Split E1's right edge: upper 4 slots = P→E1 incoming,
#                        lower 6 slots = E1→P outgoing
# Rationale: Process is BELOW-right of E1; outgoing arrows naturally depart
# from the lower portion and incoming arrive at the upper portion.
# ════════════════════════════════════════════════════════════════════════════
e1_slots = vslots(E1['cy'], E1['h'], 10)
# slots[0]=lowest … slots[9]=highest

# E1→P outgoing (DF-01 to DF-06): use slots 0-5 (lower)
e1_out = [
    ('DF-01\nProject Reg.\nRequest',    e1_slots[0], -0.14),
    ('DF-02\nEnv File\nUpload',         e1_slots[1], -0.10),
    ('DF-03\nNL Deploy\nCommand',       e1_slots[2], -0.06),
    ('DF-04\nPlan Approval\nSignal',    e1_slots[3],  0.0),
    ('DF-05\nManual Rollback\nRequest', e1_slots[4],  0.06),
    ('DF-06\nChat Message',             e1_slots[5],  0.10),
]
for lbl, ey, rad in e1_out:
    sx, sy = E1_RX, ey
    ex, ey2 = circ_pt(sx, sy)
    df_arrow(sx, sy, ex, ey2, lbl, rad=rad, lbl_frac=0.42)

# P→E1 incoming (DF-07 to DF-10): use slots 6-9 (upper)
p_e1_in = [
    ('DF-07\nPlan Preview\n+ AI Metadata', e1_slots[6],  0.14),
    ('DF-08\nExecution\nLogs',             e1_slots[7],  0.10),
    ('DF-09\nChat Response',               e1_slots[8],  0.06),
    ('DF-10\nProject Reg.\nResult',        e1_slots[9],  0.02),
]
for lbl, ey, rad in p_e1_in:
    ex_ent, ey_ent = E1_RX, ey
    sx_p, sy_p = circ_pt(ex_ent, ey_ent)
    df_arrow(sx_p, sy_p, ex_ent, ey_ent, lbl, rad=rad, lbl_frac=0.55)


# ════════════════════════════════════════════════════════════════════════════
# E2 ↔ Process  (6 flows)
# Process is BELOW-left of E2.
# P→E2 outgoing (DF-11 to DF-13): lower 3 slots on E2's left edge
# E2→P incoming (DF-14 to DF-16): upper 3 slots on E2's left edge
# ════════════════════════════════════════════════════════════════════════════
e2_slots = vslots(E2['cy'], E2['h'], 6)

p_e2_out = [
    ('DF-11\nCmd Interp.\nRequest',  e2_slots[0], -0.10),
    ('DF-12\nRisk Assess.\nRequest', e2_slots[1], -0.05),
    ('DF-13\nConv. LLM\nRequest',    e2_slots[2],  0.0),
]
for lbl, ey, rad in p_e2_out:
    ex_ent, ey_ent = E2_LX, ey
    sx_p, sy_p = circ_pt(ex_ent, ey_ent)
    df_arrow(sx_p, sy_p, ex_ent, ey_ent, lbl, rad=rad, lbl_frac=0.50)

e2_p_in = [
    ('DF-14\nStructured Cmd\nInterp. Response', e2_slots[3],  0.0),
    ('DF-15\nStructured Risk\nAdvisory Resp.',  e2_slots[4],  0.05),
    ('DF-16\nConv. LLM\nResponse',              e2_slots[5],  0.10),
]
for lbl, ey, rad in e2_p_in:
    sx, sy = E2_LX, ey
    ex, ey2 = circ_pt(sx, sy)
    df_arrow(sx, sy, ex, ey2, lbl, rad=rad, lbl_frac=0.50)


# ════════════════════════════════════════════════════════════════════════════
# E3 ↔ Process  (7 flows)
# Process is ABOVE-left of E3.
# P→E3 outgoing (DF-17 to DF-20): upper 4 slots on E3's left edge
# E3→P incoming (DF-21 to DF-23): lower 3 slots on E3's left edge
# ════════════════════════════════════════════════════════════════════════════
e3_slots = vslots(E3['cy'], E3['h'], 7)

p_e3_out = [
    ('DF-17\nDocker Build\nRequest',      e3_slots[6], -0.12),
    ('DF-18\nContainer Run\nRequest',     e3_slots[5], -0.07),
    ('DF-19\nContainer Stop/\nRemove',    e3_slots[4],  0.0),
    ('DF-20\nHealth Check\nRequest',      e3_slots[3],  0.07),
]
for lbl, ey, rad in p_e3_out:
    ex_ent, ey_ent = E3_LX, ey
    sx_p, sy_p = circ_pt(ex_ent, ey_ent)
    df_arrow(sx_p, sy_p, ex_ent, ey_ent, lbl, rad=rad, lbl_frac=0.50)

e3_p_in = [
    ('DF-21\nBuild Log\nStream',       e3_slots[2],  0.07),
    ('DF-22\nContainer Run\nResult',   e3_slots[1],  0.0),
    ('DF-23\nContainer\nHealth Status',e3_slots[0], -0.07),
]
for lbl, ey, rad in e3_p_in:
    sx, sy = E3_LX, ey
    ex, ey2 = circ_pt(sx, sy)
    df_arrow(sx, sy, ex, ey2, lbl, rad=rad, lbl_frac=0.50)


# ════════════════════════════════════════════════════════════════════════════
# E4 ↔ Process  (2 flows)
# Process is ABOVE-right of E4.
# DF-24 P→E4, DF-25 E4→P
# ════════════════════════════════════════════════════════════════════════════
e4_mid  = E4['cy']
e4_bot_y = e4_mid - 0.60
e4_top_y = e4_mid + 0.60

# P→E4: DF-24
ex_ent, ey_ent = E4_RX, e4_bot_y
sx_p, sy_p = circ_pt(ex_ent, ey_ent)
df_arrow(sx_p, sy_p, ex_ent, ey_ent,
         'DF-24\nRepo Clone\nRequest', rad=-0.20, lbl_frac=0.50)

# E4→P: DF-25
sx, sy = E4_RX, e4_top_y
ex, ey2 = circ_pt(sx, sy)
df_arrow(sx, sy, ex, ey2,
         'DF-25\nCloned Repo\nContents', rad=0.20, lbl_frac=0.50)


# ════════════════════════════════════════════════════════════════════════════
# E5 ↔ Process  (2 flows)
# Process is directly ABOVE E5.
# DF-26 P→E5, DF-27 E5→P
# ════════════════════════════════════════════════════════════════════════════
e5_slots_h = hslots(E5['cx'], E5['w'], 2)

# P→E5: DF-26
ex_ent, ey_ent = e5_slots_h[1], E5_TY
sx_p, sy_p = circ_pt(ex_ent, ey_ent)
df_arrow(sx_p, sy_p, ex_ent, ey_ent,
         'DF-26\nDeploy Job\nEnqueue', rad=-0.22, lbl_frac=0.52)

# E5→P: DF-27
sx, sy = e5_slots_h[0], E5_TY
ex, ey2 = circ_pt(sx, sy)
df_arrow(sx, sy, ex, ey2,
         'DF-27\nJob Execution\nCallback', rad=0.22, lbl_frac=0.52)


# ══════════════════════════════════════════════════════════════════════════════
# LEGEND BOX
# ══════════════════════════════════════════════════════════════════════════════
LX, LY, LW, LH = 1.0, 0.2, 56.0, 4.5

ax.add_patch(FancyBboxPatch((LX, LY), LW, LH,
    boxstyle='round,pad=0.18', linewidth=1.5,
    edgecolor='#888888', facecolor='#f8f8f8', zorder=7))

ax.text(LX + LW / 2, LY + LH - 0.35, 'Legend — Yourdon-DeMarco DFD Notation',
        ha='center', va='top', fontsize=13, fontweight='bold', color=NAVY, zorder=8)

# ── Process circle ─────────────────────────────────────────────────────────
LEG_PX, LEG_PY = LX + 2.5, LY + 1.5
ax.add_patch(Circle((LEG_PX, LEG_PY), 0.70,
                     facecolor=PROC_FILL, edgecolor=PROC_EDGE, lw=2, zorder=8))
ax.text(LEG_PX, LEG_PY, 'Process', ha='center', va='center',
        fontsize=7, fontweight='bold', color=PROC_EDGE, zorder=9)
ax.text(LEG_PX, LY + 0.70, 'Process (circle/bubble)',
        ha='center', va='center', fontsize=9, color='#333333', zorder=8)

# ── Entity rectangle ───────────────────────────────────────────────────────
LEG_EX, LEG_EY = LX + 9.0, LY + 1.5
ax.add_patch(Rectangle((LEG_EX - 1.3, LEG_EY - 0.55), 2.6, 1.10,
    facecolor=ENT_FILL, edgecolor=ENT_EDGE, linewidth=1.8, zorder=8))
ax.plot([LEG_EX - 1.3 + 0.26, LEG_EX - 1.3 + 0.26],
        [LEG_EY - 0.55 + 0.10, LEG_EY + 0.55 - 0.10],
        color=ENT_EDGE, lw=1.3, zorder=9)
ax.text(LEG_EX, LEG_EY, 'Entity', ha='center', va='center',
        fontsize=8, fontweight='bold', color='#111111', zorder=10)
ax.text(LEG_EX, LY + 0.70, 'External Entity (double left border)',
        ha='center', va='center', fontsize=9, color='#333333', zorder=8)

# ── Outgoing data flow arrow ───────────────────────────────────────────────
LEG_A1X, LEG_A1Y = LX + 18.0, LY + 1.5
ax.annotate('', xy=(LEG_A1X + 2.0, LEG_A1Y), xytext=(LEG_A1X, LEG_A1Y),
    arrowprops=dict(arrowstyle='->', color=FLOW_CLR, lw=1.8,
                    mutation_scale=16), zorder=8)
ax.text(LEG_A1X + 1.0, LEG_A1Y + 0.38, 'DF-XX: Flow Name',
        ha='center', va='bottom', fontsize=7.5, fontweight='bold',
        bbox=dict(facecolor=LBL_BG, edgecolor=LBL_EDGE,
                  boxstyle='round,pad=0.15', lw=0.7, alpha=0.95), zorder=9)
ax.text(LEG_A1X + 1.0, LY + 0.70, 'Data Flow (labelled arrow)',
        ha='center', va='center', fontsize=9, color='#333333', zorder=8)

# ── No data-store note ──────────────────────────────────────────────────────
ax.text(LX + LW - 10.5, LY + 1.5,
        'No data stores shown at Level 0\n(Context Diagram — single process view)',
        ha='center', va='center', fontsize=9.5, fontstyle='italic',
        color='#555555', zorder=8,
        bbox=dict(facecolor='#fffbe6', edgecolor='#ccbb44',
                  boxstyle='round,pad=0.25', lw=1.0))

# ── Flow count summary ─────────────────────────────────────────────────────
ax.text(LX + LW - 2.2, LY + 1.5,
        '27 data flows\n5 external entities\n1 central process',
        ha='center', va='center', fontsize=9.5, color='#333333', zorder=8,
        bbox=dict(facecolor='#eef8e8', edgecolor='#66aa55',
                  boxstyle='round,pad=0.25', lw=1.0))


# ══════════════════════════════════════════════════════════════════════════════
# CONNECTOR LINES — entity label bands showing which flows go where
# (subtle bracket annotations on entity boxes)
# ══════════════════════════════════════════════════════════════════════════════

def side_label(x, y, text, ha='left'):
    ax.text(x, y, text, ha=ha, va='center', fontsize=6.5,
            color='#666666', fontstyle='italic', zorder=11)

# E1 bracket annotations
e1_rx_ann = E1_RX + 0.25
side_label(e1_rx_ann, (e1_slots[0] + e1_slots[5]) / 2,
           '→ DF-01…06\n   (to Process)')
side_label(e1_rx_ann, (e1_slots[6] + e1_slots[9]) / 2,
           '← DF-07…10\n   (from Process)')

# E2 bracket annotations
e2_lx_ann = E2_LX - 0.25
side_label(e2_lx_ann, (e2_slots[0] + e2_slots[2]) / 2,
           'DF-11…13 ←\n(from Process)', ha='right')
side_label(e2_lx_ann, (e2_slots[3] + e2_slots[5]) / 2,
           'DF-14…16 →\n(to Process)', ha='right')

# E3 bracket annotations
e3_lx_ann = E3_LX - 0.25
side_label(e3_lx_ann, (e3_slots[0] + e3_slots[2]) / 2,
           'DF-21…23 →\n(to Process)', ha='right')
side_label(e3_lx_ann, (e3_slots[3] + e3_slots[6]) / 2,
           'DF-17…20 ←\n(from Process)', ha='right')


# ══════════════════════════════════════════════════════════════════════════════
# SAVE
# ══════════════════════════════════════════════════════════════════════════════
import os

out = r'c:\Users\psing\Desktop\DevOps Agent\DFD_Level0_Context_Diagram.png'
plt.savefig(out, dpi=150, bbox_inches='tight',
            facecolor='white', edgecolor='none')
print(f"Saved : {out}")
print(f"Size  : {os.path.getsize(out):,} bytes")
