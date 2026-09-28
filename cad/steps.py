"""Assembly sequence: which step every component belongs to (used for the step images)."""

STEPS = [
    # (number, title, render view, name prefixes)
    (1, "Body: inserts, rise plunger, rise bushings", "w_34",
     ["body", "inlay_body", "insert_gf", "insert_top", "insert_arca", "insert_yway", "plunger_y", "bush_y"]),
    (2, "Graflok module, clamp blade and wheel", "w_rear",
     ["graflok_", "screw_gf", "screw_blade", "screw_wheel", "insert_blade"]),
    (3, "Arca plates, top handle and levels", "w_rear",
     ["arca_", "top_handle", "vial_top", "screw_top", "vial_side", "inlay_handle"]),
    (4, "Vertical ways and body velvet", "w_34",
     ["way_y", "screw_yway", "velvet_body"]),
    (5, "Front standard on the bench: Y plate, lens panel, horizontal ways, shift screw", "w_34",
     ["y_plate", "inlay_yplate", "bush_x", "plunger_x", "velvet_yplate", "x_plate", "inlay_xplate", "x_turret",
      "flange", "screw_flange", "stop_pin", "insert_stop", "nut_x", "insert_xway", "way_x", "screw_xway", "gib_x",
      "grub_gib_x", "inlay_xway", "rod_x", "washer_x_thrust", "oring_x", "knob_x", "inlay_knob_x"]),
    (6, "Front standard into the body, rise screw and knob", "w_34",
     ["y_turret", "nut_y_drive", "insert_yturret", "screw_yturret", "velvet_discs", "gib_y", "grub_gib_y", "rod_y", "nut_y_cap",
      "oring_y", "knob_y", "inlay_knob_y"]),
    (7, "Helicoid and focus ring", "w_34", ["helicoid", "focus_ring", "inlay_focus"]),
    (8, "Adapter ring, board holder, lens board and lens", "w_34",
     ["adapter_ring", "insert_adapter", "screw_adapter", "board_holder", "felt_adapter", "felt_board", "holder_latch",
      "screw_latch", "spring_latch", "lensboard", "lens"]),
    (9, "Film back", "w_rear", ["rb_"]),
]


def step_of(name):
    for n, _, _, prefixes in STEPS:
        for p in prefixes:
            if name.startswith(p):
                return n
    raise KeyError(name)
