import os
import tempfile
import unittest

from epuscreeningcompiler.main import build_argparse
from epuscreeningcompiler_gui.form import DIR, DIRLIST, FLAG, build_argv, describe, validate


class FormLogicTests(unittest.TestCase):
    def setUp(self):
        self.fields = describe(build_argparse())
        self.by = {f.dest: f for f in self.fields}

    def test_kinds(self):
        self.assertEqual(self.by["epu_sessions"].kind, DIRLIST)
        self.assertEqual(self.by["output"].kind, DIR)
        self.assertTrue(self.by["output"].required)
        self.assertEqual(self.by["atlas"].kind, DIR)
        self.assertFalse(self.by["atlas"].required)
        self.assertEqual(self.by["onlypng"].kind, FLAG)
        self.assertEqual(self.by["verbose"].kind, FLAG)
        self.assertNotIn("help", self.by)

    def test_argv_and_validate(self):
        with tempfile.TemporaryDirectory() as d:
            values = {"atlas": "", "output": d, "onlypng": True, "verbose": False, "epu_sessions": [d, d]}
            self.assertEqual(validate(self.fields, values), [])
            self.assertEqual(build_argv(self.fields, values), ["--output", d, "--onlypng", d, d])
            # the CLI's own parser accepts what we build
            ns = build_argparse().parse_args(build_argv(self.fields, values))
            self.assertTrue(ns.onlypng)
            self.assertEqual(ns.epu_sessions, [d, d])

    def test_validation_problems(self):
        values = {"atlas": "/nonexistent", "output": "", "onlypng": False, "verbose": False, "epu_sessions": []}
        problems = validate(self.fields, values)
        self.assertEqual(len(problems), 3)


if __name__ == "__main__":
    unittest.main()
