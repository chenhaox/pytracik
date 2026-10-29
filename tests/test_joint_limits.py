"""Native IK regressions for bounded joint normalization (GitHub issue #13).

Run with: python -m unittest discover -s tests -v
"""

import itertools
import math
import unittest

import numpy as np

# Load the packaged NLopt DLL directory on Windows before the native module.
import trac_ik  # noqa: F401
import pytracik


LOWER = np.array([-1.0472, -1.5708])
UPPER = np.array([1.0472, 3.4907])
EPS = 1e-7
MODES = ("Speed", "Distance", "Manip1", "Manip2")
XML = """<robot name="two_revolute_boundary">
<link name="base"/><link name="link1"/><link name="link2"/><link name="tip"/>
<joint name="joint1" type="revolute">
 <parent link="base"/><child link="link1"/><axis xyz="0 0 1"/>
 <limit lower="-1.0472" upper="1.0472" effort="1" velocity="1"/>
</joint>
<joint name="joint2" type="revolute">
 <parent link="link1"/><child link="link2"/><origin xyz="1 0 0"/>
 <axis xyz="0 0 1"/>
 <limit lower="-1.5708" upper="3.4907" effort="1" velocity="1"/>
</joint>
<joint name="tool" type="fixed">
 <parent link="link2"/><child link="tip"/><origin xyz="1 0 0"/>
</joint></robot>"""

# Two independent DOFs keep both native solvers active (NLopt requires >= 2).
MIXED_XML = """<robot name="spin_and_slide">
<link name="base"/><link name="spin_link"/><link name="tip"/>
<joint name="spin" type="continuous">
 <parent link="base"/><child link="spin_link"/><axis xyz="0 0 1"/>
</joint>
<joint name="slide" type="prismatic">
 <parent link="spin_link"/><child link="tip"/><axis xyz="0 0 1"/>
 <limit lower="-0.123456789" upper="0.987654321" effort="1" velocity="1"/>
</joint></robot>"""


def pose(q):
    """Independent analytical FK for the synthetic planar two-link chain."""
    angle = float(q[0] + q[1])
    return [math.cos(q[0]) + math.cos(angle),
            math.sin(q[0]) + math.sin(angle), 0.0,
            0.0, 0.0, math.sin(angle / 2), math.cos(angle / 2)]


def make_solver(mode="Speed", xml=XML):
    return pytracik.TRAC_IK("base", "tip", xml, 0.05, EPS,
                          getattr(pytracik.SolveType, mode))


class JointLimitTests(unittest.TestCase):
    def assert_valid(self, solver, raw, target):
        self.assertGreaterEqual(raw[0], 0, "reachable pose returned failure")
        q = np.asarray(raw[1:])
        self.assertTrue(np.all(np.isfinite(q)))
        lower = np.asarray(pytracik.get_joint_lower_bounds(solver))
        upper = np.asarray(pytracik.get_joint_upper_bounds(solver))
        self.assertTrue(np.all(q >= lower), (q, lower))
        self.assertTrue(np.all(q <= upper), (q, upper))
        actual = np.asarray(pose(q))
        np.testing.assert_allclose(actual[:3], target[:3], atol=2 * EPS, rtol=0)
        # q and -q describe the same quaternion rotation.
        target_rot = np.asarray(target[3:])
        if np.dot(actual[3:], target_rot) < 0:
            target_rot = -target_rot
        np.testing.assert_allclose(actual[3:], target_rot, atol=EPS, rtol=0)

    def test_urdf_limits_keep_double_precision(self):
        solver = make_solver()
        np.testing.assert_array_equal(pytracik.get_joint_lower_bounds(solver), LOWER)
        np.testing.assert_array_equal(pytracik.get_joint_upper_bounds(solver), UPPER)

    def test_issue_13_original_boundary_seed(self):
        target = pose(LOWER)
        for mode in MODES:
            with self.subTest(mode=mode):
                solver = make_solver(mode)
                raw = pytracik.ik(solver, LOWER.copy(), *target)
                self.assert_valid(solver, raw, target)

    def test_boundary_seeds_and_neighboring_floats(self):
        for mode in MODES:
            solver = make_solver(mode)
            for sides in itertools.product((0, 1), repeat=2):
                boundary = np.where(sides, UPPER, LOWER)
                for direction in (None, -np.inf, np.inf):
                    with self.subTest(mode=mode, sides=sides, direction=direction):
                        seed = (boundary.copy() if direction is None else
                                np.nextafter(boundary, direction))
                        target = pose(boundary)
                        raw = pytracik.ik(solver, seed, *target)
                        self.assert_valid(solver, raw, target)

    def test_equivalent_seed_wraps_into_limits(self):
        for mode in MODES:
            for sides in itertools.product((0, 1), repeat=2):
                boundary = np.where(sides, UPPER, LOWER)
                target = pose(boundary)
                for turns in (-2, -1, 1, 2):
                    with self.subTest(mode=mode, sides=sides, turns=turns):
                        solver = make_solver(mode)
                        seed = boundary + turns * 2 * math.pi
                        raw = pytracik.ik(solver, seed, *target)
                        self.assert_valid(solver, raw, target)

    def test_pose_outside_joint_range_is_not_success(self):
        # These full poses have no equivalent configuration within the limits.
        for mode in MODES:
            for q in (np.array([UPPER[0] + 0.2, 0.0]),
                      np.array([LOWER[0] - 0.2, 0.0])):
                with self.subTest(mode=mode, q=q):
                    solver = make_solver(mode)
                    raw = pytracik.ik(solver, q, *pose(q))
                    self.assertLess(raw[0], 0, raw)

    def test_prismatic_limits_are_enforced(self):
        for mode in MODES:
            solver = make_solver(mode, MIXED_XML)
            for value in (-0.123456789, 0.987654321):
                with self.subTest(mode=mode, value=value):
                    raw = pytracik.ik(solver, np.array([0.0, value]),
                                      0.0, 0.0, value, 0.0, 0.0, 0.0, 1.0)
                    self.assertGreaterEqual(raw[0], 0, raw)
                    self.assertGreaterEqual(raw[2], -0.123456789)
                    self.assertLessEqual(raw[2], 0.987654321)
                    self.assertAlmostEqual(raw[2], value, delta=EPS)
            # KDL's early pose success must not bypass a prismatic limit.
            raw = pytracik.ik(solver, np.array([0.0, 1.2]),
                              0.0, 0.0, 1.2, 0.0, 0.0, 0.0, 1.0)
            self.assertLess(raw[0], 0, raw)

    def test_continuous_joint_keeps_unbounded_seed(self):
        angle = 10 * math.pi + 0.3
        for mode in MODES:
            with self.subTest(mode=mode):
                solver = make_solver(mode, MIXED_XML)
                raw = pytracik.ik(solver, np.array([angle, 0.0]), 0.0, 0.0, 0.0,
                                  0.0, 0.0, math.sin(angle / 2), math.cos(angle / 2))
                self.assertGreaterEqual(raw[0], 0, raw)
                self.assertAlmostEqual(raw[1], angle, delta=EPS)


if __name__ == "__main__":
    unittest.main()
