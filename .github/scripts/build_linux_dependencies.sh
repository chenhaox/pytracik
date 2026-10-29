#!/usr/bin/env bash
set -euo pipefail

# manylinux_2_28 uses AlmaLinux 8 on both x86_64 and aarch64. Build native
# dependencies from source so ARM does not depend on EPEL KDL availability.
dnf install -y dnf-plugins-core epel-release
dnf config-manager --set-enabled powertools
dnf install -y boost-devel eigen3-devel cmake gcc-c++ curl tar gzip

build_root=$(mktemp -d /tmp/pytracik-dependencies.XXXXXX)
export CMAKE_POLICY_VERSION_MINIMUM=3.5

curl --fail --location --retry 3 \
  https://github.com/orocos/orocos_kinematics_dynamics/archive/refs/tags/v1.5.1.tar.gz \
  -o "$build_root/kdl.tar.gz"
tar -xzf "$build_root/kdl.tar.gz" -C "$build_root"
cmake -S "$build_root/orocos_kinematics_dynamics-1.5.1/orocos_kdl" \
  -B "$build_root/kdl-build" \
  -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr/local \
  -DCMAKE_INSTALL_LIBDIR=lib64 -DENABLE_TESTS=OFF -DENABLE_EXAMPLES=OFF
cmake --build "$build_root/kdl-build" --parallel 2
cmake --install "$build_root/kdl-build"

curl --fail --location --retry 3 \
  https://github.com/stevengj/nlopt/archive/refs/tags/v2.7.1.tar.gz \
  -o "$build_root/nlopt.tar.gz"
tar -xzf "$build_root/nlopt.tar.gz" -C "$build_root"
cmake -S "$build_root/nlopt-2.7.1" -B "$build_root/nlopt-build" \
  -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr/local \
  -DCMAKE_INSTALL_LIBDIR=lib64 -DBUILD_SHARED_LIBS=ON \
  -DNLOPT_PYTHON=OFF -DNLOPT_OCTAVE=OFF -DNLOPT_MATLAB=OFF \
  -DNLOPT_GUILE=OFF -DNLOPT_SWIG=OFF
cmake --build "$build_root/nlopt-build" --parallel 2
cmake --install "$build_root/nlopt-build"

printf '%s\n' /usr/local/lib64 /usr/local/lib > /etc/ld.so.conf.d/pytracik.conf
ldconfig
