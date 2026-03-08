import ast
import fnmatch
import os
import platform
import subprocess
import sys
import sysconfig

import pybind11
from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import setup


def find_files(path, file_extension, visited=None, found_files=None):
    if found_files is None:
        found_files = []
    if visited is None:
        visited = set()

    path_real = os.path.realpath(path)
    if path_real in visited:
        return found_files
    visited.add(path_real)

    if os.path.isfile(path):
        if fnmatch.fnmatch(path, '*' + file_extension):
            found_files.append(path)
        return found_files

    if os.path.isdir(path):
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.exists(item_path):
                find_files(item_path, file_extension, visited, found_files)
            else:
                print(f'Warning: Path {item_path} does not exist or is a broken symbolic link', file=sys.stderr)
    return found_files


_here = os.path.dirname(os.path.abspath(__file__))

version_file = os.path.join(_here, "trac_ik", "version.py")
with open(version_file, "r") as _f:
    version = ast.literal_eval(_f.read().strip().split("=")[-1].strip())

module_name = "pytracik"
src_dir = os.path.join(_here, "src")
src_files = [
    os.path.relpath(f, _here).replace(os.sep, '/')
    for f in find_files(src_dir, '.cpp')
]

_system = platform.system()

if _system == "Linux":
    python_include = sysconfig.get_paths()["include"]
    python_library = sysconfig.get_config_var('LDLIBRARY')
    python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    if python_library:
        python_lib = os.path.splitext(os.path.basename(python_library))[0].replace('lib', '')
    else:
        python_lib = python_version

    ext_modules = [
        Pybind11Extension(
            module_name,
            src_files,
            include_dirs=[
                pybind11.get_include(),
                python_include,
                "/usr/include/eigen3",
                "/usr/include/orocos/kdl",
                "/usr/include/",
                "/usr/include/boost",
            ],
            libraries=['nlopt', 'orocos-kdl', 'boost_date_time', 'boost_system', 'boost_thread'],
            library_dirs=['/usr/lib/x86_64-linux-gnu', '/usr/lib64'],
            language='c++',
            extra_compile_args=['-std=c++17'],
        ),
    ]
    _packages = ['trac_ik']
    _package_data = {}

elif _system == "Darwin":
    python_library = sysconfig.get_config_var('LIBPL')
    python_lib = f"python{sys.version_info.major}.{sys.version_info.minor}"

    homebrew_prefix = subprocess.check_output(["brew", "--prefix"]).decode().strip()
    kdl_prefix = subprocess.check_output(["brew", "--prefix", "orocos-kdl"]).decode().strip()

    ext_modules = [
        Pybind11Extension(
            module_name,
            src_files,
            include_dirs=[
                pybind11.get_include(),
                f"{homebrew_prefix}/include",
                f"{kdl_prefix}/include",
                f"{homebrew_prefix}/include/eigen3",
            ],
            libraries=['nlopt', 'orocos-kdl', 'boost_date_time', 'boost_thread', python_lib],
            library_dirs=[
                f"{homebrew_prefix}/lib",
                f"{kdl_prefix}/lib",
                python_library,
            ],
            language="c++",
            extra_compile_args=["-std=c++17", "-stdlib=libc++"],
        ),
    ]
    _packages = ['trac_ik']
    _package_data = {}

elif _system == "Windows":
    ldlib = sysconfig.get_config_var("LDLIBRARY") or ""
    libname = (
        os.path.splitext(ldlib)[0]
        if ldlib
        else f"python{sys.version_info.major}{sys.version_info.minor}"
    )
    libdir = (
        sysconfig.get_config_var("LIBDIR")
        or sysconfig.get_config_var("LIBPL")
        or os.path.join(sys.base_prefix, "libs")
    )

    third_party_libraries = ["nlopt", "orocos-kdl", "libboost_date_time-vc143-mt-s-x64-1_79"]
    third_party_library_dirs = [
        r"./dependency/boost_1_79_0/lib",
        r"./dependency/kdl/lib",
        r"./dependency/nlopt/lib",
    ]
    libraries = third_party_libraries + ([libname] if libname else [])
    library_dirs = third_party_library_dirs + ([libdir] if libdir else [])

    ext_modules = [
        Pybind11Extension(
            module_name,
            src_files,
            include_dirs=[
                pybind11.get_include(),
                r".\dependency\eigen-3.4.0",
                r".\dependency\kdl\include",
                r".\dependency\nlopt\include",
                r".\dependency\boost_1_79_0",
            ],
            libraries=libraries,
            library_dirs=library_dirs,
            language='c++',
            extra_compile_args=['/std:c++17'],
        ),
    ]
    _packages = ['trac_ik']
    _package_data = {'': ['nlopt.dll']}

else:
    raise RuntimeError(f"Unsupported platform: {_system}")

setup(
    packages=_packages,
    include_package_data=True,
    package_data=_package_data,
    cmdclass={"build_ext": build_ext},
    ext_modules=ext_modules,
)
