"""

"""
import pybind11
from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import setup
import os
import logging
import sys
import sysconfig

logging.basicConfig(
    level=logging.INFO,
    format='\033[32m[%(asctime)s] [%(levelname)s] %(message)s\033[0m',
)
logger = logging.getLogger('logger')

version_file = os.path.join(os.path.dirname(__file__), "trac_ik/version.py")

logger.info("version file: %s", version_file)

import os


def find_files_by_ext(dir_path: str, ext_filters: list | str) -> list:
    if isinstance(ext_filters, str):
        ext_filters = [ext_filters]
    ext_filters = [ext if ext.startswith('.') else f'.{ext}' for ext in ext_filters]

    matched_files = []
    for root, _, files in os.walk(os.path.abspath(dir_path)):
        for file in files:
            if os.path.splitext(file)[1] in ext_filters:
                matched_files.append(os.path.join(root, file))

    return matched_files


if __name__ == "__main__":
    with open(version_file, "r") as f:
        version = eval(f.read().strip().split("=")[-1])
        logger.info(f"version: {version}")

    modul_name = "pytracik"
    src_dir='./src'
    logger.info("src_dir: %s", src_dir)
    src_files = find_files_by_ext(src_dir, ".cpp")
    setup_dir = os.path.dirname(os.path.abspath(__file__))
    src_files = [
        os.path.relpath(f, setup_dir).replace(os.sep, '/')
        if os.path.isabs(f) else f
        for f in src_files
    ]
    logger.info("src_files: %s", "\n".join(src_files))
    header_files = find_files_by_ext(src_dir, ".h")
    logger.info("header_files: %s", "\n".join(header_files))

    python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    logger.info("python_version: %s", python_version)

    python_library = sysconfig.get_config_var('LIBPL')
    logger.info("python_library: %s", python_library)

    trac_ik_module = [
        Pybind11Extension(
            modul_name,
            src_files,
            include_dirs=[
                pybind11.get_include(),
                "/opt/homebrew/include",
                "/opt/homebrew/Cellar/orocos-kdl/1.5.3_1/include",
                "/opt/homebrew/include/eigen3"
            ],
            libraries=[
                'nlopt',
                'orocos-kdl',
                'boost_date_time',
                'boost_thread',
                'python3.12',
            ],
            library_dirs=[
                "/opt/homebrew/lib",
                "/opt/homebrew/Cellar/orocos-kdl/1.5.3_1/lib/",
                python_library,
            ],
            language="c++",
            extra_compile_args=["-std=c++17", "-stdlib=libc++"],
        )
    ]

    setup(
        name=modul_name,
        version=version,
        packages=["trac_ik"],
        include_package_data=True,
        cmdclass={"build_ext": build_ext},
        ext_modules=trac_ik_module,
    )
