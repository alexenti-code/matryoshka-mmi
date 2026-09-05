"""PMI executor v0.6.0 — tick-clock tests (stdlib unittest, temp HOME sandbox).

Isolation: HOME is pointed at a temp dir BEFORE (re)importing mmi_mcp,
because storage paths are computed at import time. The real ~/.matryoshka
is never touched.
"""
import importlib
import math
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mmi_mcp


def fresh(env_extra=None):
    """Re-import the server under a sandbox HOME with the given env."""
    tmp = tempfile.mkdtemp(prefix="pmi-test-")
    for k in ("MMI_CLOCK", "MMI_TAU_TICKS", "MMI_INJECT_TOP",
              "MMI_TAU_SCALE", "MMI_NO_UPDATE_CHECK"):
        os.environ.pop(k, None)
    os.environ["HOME"] = tmp
    os.environ["MMI_NO_UPDATE_CHECK"] = "1"
    for k, v in (env_extra or {}).items():
        os.environ[k] = v
    importlib.reload(mmi_mcp)
    return tmp


class TickClock(unittest.TestCase):
    def test_three_ticks_advance(self):
        fresh({"MMI_CLOCK": "ticks"})
        self.assertEqual(mmi_mcp.tick_now(), 0)
        for i in range(3):
            mmi_mcp.call_tool("matryoshka_write", {"content": f"fact {i}"})
        # one lived tick per storing act: the stand counts, not the model
        self.assertEqual(mmi_mcp.tick_now(), 3)
        recs = mmi_mcp.act_read()
        self.assertEqual([r["record_tick"] for r in recs], [0, 1, 2])

    def test_manual_tick_deprecated_in_ticks_mode(self):
        fresh({"MMI_CLOCK": "ticks"})
        mmi_mcp.call_tool("matryoshka_write", {"content": "x"})
        before = mmi_mcp.tick_now()
        out = mmi_mcp.call_tool("matryoshka_tick", {"note": "model tries"})
        self.assertTrue(out.get("deprecated"))
        self.assertEqual(mmi_mcp.tick_now(), before)

    def test_tick_aging(self):
        fresh({"MMI_CLOCK": "ticks"})
        mmi_mcp.call_tool("matryoshka_write",
                          {"content": "old", "layer": "beat"})
        for i in range(10):  # advance 10 lived ticks
            mmi_mcp.call_tool("matryoshka_write", {"content": f"filler {i}"})
        got = mmi_mcp.act_read(mode="ids", ids=[1])[0]["weight"]
        tau = mmi_mcp.tau_ticks()["beat"]  # default 10
        # 1 (the write itself) + 10 fillers = 11 lived ticks elapsed
        self.assertAlmostEqual(got, round(math.exp(-11 / tau), 4))

    def test_repeat_doubles(self):
        fresh({"MMI_CLOCK": "ticks",
               "MMI_TAU_TICKS": "100000,100000,100000,100000,100000"})
        mmi_mcp.call_tool("matryoshka_write", {"content": "keep me"})
        mmi_mcp.call_tool("matryoshka_repeat", {"id": 1})
        got = mmi_mcp.act_read(mode="ids", ids=[1])[0]["weight"]
        self.assertAlmostEqual(got, 2.0, places=3)

    def test_wall_mode_regression(self):
        fresh({})  # default clock is wall
        st = mmi_mcp.call_tool("matryoshka_status", {})
        self.assertEqual(st["clock"], "wall")
        mmi_mcp.call_tool("matryoshka_write", {"content": "fresh"})
        got = mmi_mcp.act_read(mode="ids", ids=[1])[0]["weight"]
        self.assertAlmostEqual(got, 1.0, places=3)
        # wall weight ignores record_tick: an ancient wall stamp still decays
        # by the calendar even with a fresh tick counter
        recs = mmi_mcp._load(mmi_mcp.PHI)
        recs[0]["record_time"] = "2000-01-01T00:00:00+00:00"
        mmi_mcp._rewrite(mmi_mcp.PHI, recs)
        got2 = mmi_mcp.act_read(mode="ids", ids=[1])[0]["weight"]
        self.assertLess(got2, 0.01)

    def test_connect_reconcile_refs(self):
        fresh({"MMI_CLOCK": "ticks"})
        a = mmi_mcp.call_tool("matryoshka_write", {"content": "fact A"})
        b = mmi_mcp.call_tool("matryoshka_write", {"content": "fact B"})
        before = [dict(r) for r in mmi_mcp._load(mmi_mcp.PHI)
                  if r.get("act") == "WRITE"]
        c = mmi_mcp.call_tool("matryoshka_connect",
                              {"refs": [a["id"], b["id"]],
                               "summary": "A and B belong together"})
        self.assertEqual(c["act"], "CONNECT")
        self.assertEqual(c["refs"], [a["id"], b["id"]])
        r = mmi_mcp.call_tool("matryoshka_reconcile",
                              {"note": "clock gap noticed",
                               "refs": [a["id"]]})
        self.assertEqual(r["act"], "RECONCILE")
        self.assertEqual(r["layer"], "project")
        # sources untouched: the linked WRITE records are byte-identical
        after = [dict(r) for r in mmi_mcp._load(mmi_mcp.PHI)
                 if r.get("act") == "WRITE"]
        self.assertEqual(before, after)
        st = mmi_mcp.call_tool("matryoshka_status", {})
        self.assertEqual(st["acts"].get("CONNECT"), 1)
        self.assertEqual(st["acts"].get("RECONCILE"), 1)
        self.assertEqual(st["acts"].get("WRITE"), 2)

    def test_top_n_by_weight_only(self):
        fresh({"MMI_CLOCK": "ticks",
               "MMI_TAU_TICKS": "100000,100000,100000,100000,100000"})
        mmi_mcp.call_tool("matryoshka_write", {"content": "aaa weakest"})
        mmi_mcp.call_tool("matryoshka_write", {"content": "bbb strongest"})
        mmi_mcp.call_tool("matryoshka_write", {"content": "ccc middle"})
        mmi_mcp.call_tool("matryoshka_repeat", {"id": 2})
        mmi_mcp.call_tool("matryoshka_repeat", {"id": 2})
        mmi_mcp.call_tool("matryoshka_repeat", {"id": 3})
        top = mmi_mcp.inject_top(2)
        # ranking is by weight only: id 2 (2 repeats) > id 3 (1) > id 1 (0)
        self.assertEqual([r["id"] for r in top], [2, 3])
        block = mmi_mcp.pmi_block(2)
        self.assertTrue(block.startswith("<<PMI>>"))
        self.assertIn("bbb strongest", block)
        self.assertNotIn("aaa weakest", block)


if __name__ == "__main__":
    unittest.main()
