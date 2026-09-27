"""Assembly sequence: which step every component belongs to (used for the step images)."""

STEPS = [
    # (number, title, render view, name prefixes)
    (1, "Body: heat-set inserts and detent plunger", "w_34",
     ["body", "inlay_body", "insert_gf", "insert_yrail", "insert_top", "insert_side", "insert_arca", "plunger_y"]),
    (2, "Graflok module, clamp blade and wheel", "w_rear",
     ["graflok_", "screw_gf", "screw_blade", "screw_wheel", "insert_blade"]),
    (3, "Arca plates, top handle and levels", "w_rear",
     ["arca_", "top_handle", "vial_top", "screw_top", "vial_side"]),
    (4, "Vertical guide, bushings and body velvet", "w_34",
     ["rail_y", "screw_yrail", "block_y", "bush_y", "velvet_body"]),
    (5, "Y plate, rise screw and knob", "w_34",
     ["y_plate", "inlay_yplate", "pad_y", "plug_yblock", "screw_yblock", "nut_y_drive", "rod_y", "nut_y_bottom",
      "oring_y", "knob_y", "inlay_knob_y", "insert_xrail", "plunger_x"]),
    (6, "Horizontal guide, bushings and Y plate velvet", "w_34",
     ["rail_x", "screw_xrail", "block_x", "bush_x", "velvet_yplate"]),
    (7, "Lens panel, M65 flange, turret, shift screw and knob", "w_34",
     ["x_plate", "inlay_xplate", "x_turret", "screw_turret", "insert_turret", "flange", "screw_flange",
      "screw_xblock", "stop_pin", "insert_stop", "nut_x", "rod_x", "oring_x", "knob_x", "inlay_knob_x"]),
    (8, "Helicoid and focus ring", "w_34", ["helicoid", "focus_ring", "inlay_focus"]),
    (9, "Adapter ring, board holder, lens board and lens", "w_34",
     ["adapter_ring", "screw_adapter", "insert_holder", "board_holder", "felt_adapter", "felt_board", "holder_latch",
      "screw_latch", "spring_latch", "lensboard", "lens"]),
    (10, "Film back", "w_rear", ["rb_"]),
]


def step_of(name):
    for n, _, _, prefixes in STEPS:
        for p in prefixes:
            if name.startswith(p):
                return n
    raise KeyError(name)
