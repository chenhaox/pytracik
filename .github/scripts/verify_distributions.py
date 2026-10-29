"""Reject releases missing a supported architecture or native runtime library."""

import ast
from pathlib import Path
import sys
import zipfile


def main():
    project = Path(__file__).resolve().parents[2]
    version = ast.literal_eval((project / "trac_ik/version.py").read_text().split("=", 1)[1].strip())
    dist = Path(sys.argv[1])
    expected = {(py, platform) for py in ("cp39", "cp310", "cp311", "cp312", "cp313")
                for platform in ("win_amd64", "manylinux_x86_64", "manylinux_aarch64",
                                 "macosx_x86_64", "macosx_arm64")}
    expected.remove(("cp39", "macosx_arm64"))
    found = set()
    for wheel in sorted(dist.glob("*.whl")):
        name, wheel_version, python, abi, platform = wheel.stem.split("-")
        if name != "pytracik" or wheel_version != version:
            raise RuntimeError(f"Unexpected distribution: {wheel.name}")
        if platform.startswith("manylinux"):
            family = "manylinux_aarch64" if platform.endswith("aarch64") else "manylinux_x86_64"
            required = ("nlopt", "orocos-kdl")
        elif platform.startswith("macosx"):
            family = "macosx_arm64" if platform.endswith("arm64") else "macosx_x86_64"
            required = ("nlopt", "orocos-kdl")
        elif platform == "win_amd64":
            family = platform
            required = ("nlopt.dll",)
        else:
            raise RuntimeError(f"Unexpected platform: {wheel.name}")
        key = (python, family)
        if key not in expected or key in found or abi != python:
            raise RuntimeError(f"Unexpected or duplicate wheel: {wheel.name}")
        with zipfile.ZipFile(wheel) as archive:
            names = [name.lower() for name in archive.namelist()]
            for library in required:
                if not any(library in name and (".so" in name or name.endswith((".dylib", ".dll")))
                           for name in names):
                    raise RuntimeError(f"{wheel.name} is missing bundled {library}")
        found.add(key)
        print(wheel.name)
    missing = expected - found
    if missing:
        raise RuntimeError(f"Missing supported wheels: {sorted(missing)}")
    if not (dist / f"pytracik-{version}.tar.gz").is_file():
        raise RuntimeError("Missing source distribution")
    print(f"Verified {len(found)} wheels and source distribution for {version}.")


if __name__ == "__main__":
    main()
