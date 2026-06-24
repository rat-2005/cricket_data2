import math

# ICC ZAD data for Kohli vs Malinga, 2020-01-07, over 16
# The six to fine leg has ZAD = '1,16,6' -> zone=1, angle=16°, distance=6

# ICC coordinate system: 0° = South (behind batter/keeper), angles increase CLOCKWISE
# Fine leg = behind batter, leg side = South-West direction
# Third man = behind batter, off side = South-East direction

# Frontend canvas expects:
#   positive x = RIGHT (off side)
#   negative x = LEFT (leg side)
#   positive y -> mappedY = origin - y -> goes UP (towards bowler)
#   negative y -> mappedY = origin + y -> goes DOWN (behind batter)

# For fine leg at 16°: should be LEFT (leg) and DOWN (behind) -> x negative, y negative
# For third man at 343°: should be RIGHT (off) and DOWN (behind) -> x positive, y negative

# Correct formula: CW rotation from South (0, -1):
# x = -r * sin(α)
# y = -r * cos(α)

test_cases = [
    ("Fine Leg (16°, six off Malinga)", 16, 6),
    ("Third Man area (343°)", 343, 4),
    ("Midwicket area (71°)", 71, 5),
    ("Mid-on area (116°)", 116, 4),
    ("Cover area (251°)", 251, 3),
]

for name, angle, dist in test_cases:
    rad = math.radians(angle)
    r = dist * 50
    
    # Current (WRONG) formula:
    x_wrong = -r * math.sin(rad)
    y_wrong = r * math.cos(rad)  # POSITIVE cos -> goes UP -> WRONG for behind-batter shots!
    
    # Fixed formula:
    x_fixed = -r * math.sin(rad)
    y_fixed = -r * math.cos(rad)  # NEGATIVE cos -> goes DOWN -> CORRECT for behind-batter shots!
    
    print(f"\n{name}:")
    print(f"  WRONG: x={x_wrong:+.1f}, y={y_wrong:+.1f} -> {'LEFT' if x_wrong<0 else 'RIGHT'}, {'UP(bowler)' if y_wrong>0 else 'DOWN(behind)'}")
    print(f"  FIXED: x={x_fixed:+.1f}, y={y_fixed:+.1f} -> {'LEFT' if x_fixed<0 else 'RIGHT'}, {'UP(bowler)' if y_fixed>0 else 'DOWN(behind)'}")
