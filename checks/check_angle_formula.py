import math

# ICC Zone data from Kohli's T20 WC innings
# Zone: (typical_angle, expected_field_position, expected_canvas_direction)
zones = [
    (1,  25, "Third Man",     "lower-right (behind, off-side)"),
    (2,  52, "Point",         "right (square, off-side)"),
    (3, 132, "Cover",         "upper-right (forward, off-side)"),
    (4, 155, "Mid Off",       "upper-right (forward, near straight)"),
    (5, 205, "Mid On",        "upper-left (forward, near straight)"),
    (6, 243, "Mid Wicket",    "upper-left (forward, on-side)"),
    (7, 290, "Square Leg",    "left (square, on-side)"),
    (8, 335, "Fine Leg",      "lower-left (behind, on-side)"),
]

print("=== Formula: x = sin(a), y = cos(a) (current) ===")
for zone, angle, name, expected in zones:
    a = math.radians(angle)
    x = math.sin(a)
    y = math.cos(a)
    lr = "right" if x > 0.3 else ("left" if x < -0.3 else "center")
    ud = "up" if y > 0.3 else ("down" if y < -0.3 else "level")
    match = "✓" if (("right" in expected and lr == "right") or ("left" in expected and lr == "left")) and \
                   (("upper" in expected and ud == "up") or ("lower" in expected and ud == "down") or ("square" in expected.lower() and ud == "level")) else "✗"
    print(f"  Zone {zone} ({name:15s}): x={x:+.2f} y={y:+.2f} → {lr:6s}, {ud:5s}  expected: {expected:40s} {match}")

print()
print("=== Formula: x = sin(a), y = -cos(a) (alternative) ===")
for zone, angle, name, expected in zones:
    a = math.radians(angle)
    x = math.sin(a)
    y = -math.cos(a)
    lr = "right" if x > 0.3 else ("left" if x < -0.3 else "center")
    ud = "up" if y > 0.3 else ("down" if y < -0.3 else "level")
    match = "✓" if (("right" in expected and lr == "right") or ("left" in expected and lr == "left")) and \
                   (("upper" in expected and ud == "up") or ("lower" in expected and ud == "down") or ("square" in expected.lower() and ud == "level")) else "✗"
    print(f"  Zone {zone} ({name:15s}): x={x:+.2f} y={y:+.2f} → {lr:6s}, {ud:5s}  expected: {expected:40s} {match}")
