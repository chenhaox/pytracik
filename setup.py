""" 

Author: Hao Chen (chen960216@gmail.com)
Created: 20230911osaka

"""


def get_package_version(package_name: str) -> str:
    # Construct the path to the __init__.py file of the specified package
    package_path = f'{package_name}/__init__.py'

    # Create a module object from the package's __init__.py file
    spec = importlib.util.spec_from_file_location(package_name, package_path)
    package_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(package_module)

    # Access the __version__ attribute from the module
    version = getattr(package_module, '__version__', None)

    if version is not None:
        return version
    else:
        raise f"Version not found for {package_name}"

def requirements_from_file(file_name):
    return open(file_name).read().splitlines()

if __name__ == '__main__':
    import os
    import importlib.util
    from setuptools import setup

    # load version from file
    version_file = os.path.join(os.path.dirname(__file__), "pytracik/version.py")
    with open(version_file, "r") as f:
        # use eval to get a clean string of version from file
        version = eval(f.read().strip().split("=")[-1])

    setup(
        name="pytracik",
        version=version,
        description="TracIK Python Bindings",
        author="Hao Chen",
        author_email="chen960216@gmail.com",
        license="MIT Software License",
        url="https://github.com/chenhaox/pytracik",
        keywords="robotics inverse kinematics",
        platforms=['Windows', 'Linux Ubuntu'],
        install_requires=requirements_from_file('requirements.txt')
    )
