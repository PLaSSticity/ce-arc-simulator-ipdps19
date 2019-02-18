# Rethinking Support for Region Conflict Exceptions

This repository includes the CE, CE+, and ARC simulators as reported in the IPDPS'19 paper. Please refer to the following paper for more details.

    Swarnendu Biswas, Rui Zhang, Michael D. Bond, and Brandon Lucia. Rethinking Support for Region Conflict Exceptions. IPDPS 2019.

In the following, we give a brief description of the implementation, and list instructions to build and execute the projects.

These instructions have been tested on a Ubuntu 14.04.5 LTS platform. It should also be possible to set the simulators up on newer LTS releases, by taking care of the C++ and Java compiler versions.

We assume the root of the repository (top-level directory) is given by `$PROJECT_ROOT`.

## CE and ARC

The CE and ARC simulators have been implemented in Java, and share the same directory structure and execution dependencies. The CE simulator source is available at `$PROJECT_ROOT/ce-simulator`, while source for the ARC simulator is available at `$PROJECT_ROOT/arc-simulator`. The CE simulator implements CE/CE+ and the WMM configurations on top of a MESI protocol.

The following instructions should work for both the simulators.

+ Build the source: `ant` or `ant build`

+ Clean the build: `ant clean`

It should be possible to execute the simulators with both Java versions 1.7 and 1.8. You can also setup the projects in Java IDEs like Eclipse for automating the build and for browsing the source.

We assume the path to the CE simulator is denoted by `$MESISIM_ROOT` and the path to the ARC simulator is denoted by `$VISERSIM_ROOT`.

## PARSEC

The simulators execute benchmarks from the PARSEC suite version 3.0-beta-20150206. The PARSEC suite can be downloaded from http://parsec.cs.princeton.edu/. We assume that the path to the PARSEC suite is denoted by `$PARSEC_ROOT`.

For our experiments, we have created a new build configuration `gcc-pthreads-hooks` for the relevant PARSEC applications to ensure Pthreads as the parallelization model.

The following shows the contents of `gcc-pthreads-hooks.bldconf` file for the `blackscholes` application in PARSEC.

```Bash
#!/bin/bash

# Environment to use for configure script and Makefile
build_env="version=pthreads"

# Whether the build system supports only in-place compilation.
# If TRUE, then all sources will be copied to the build directory before we
# start building the package. Required for older build systems which don't
# support VPATH.
build_inplace="TRUE"

# Arguments to pass to the configure script, if it exists
build_conf=""

# Package dependencies
build_deps="hooks"
```

You can avoid the overhead of creating new `.bldconf` files for each application in PARSEC and use the build configurations that are part of PARSEC (for e.g., `gcc.bldconf`), as long as you make sure that the application uses Pthreads as the parallelization model. In that case, you will need to instead make the following changes:

+ Update the build configuration in `$PROJECT_ROOT/intel-pintool/Viser/makefile.rules`
+ Update the build configuration in `PARSEC_ARGS1` in `$PROJECT_ROOT/sim-framework/src/options/constants.py`

## Intel Pintool

The implementation uses Intel Pin version 2.14 to generate a serialized event trace of relevant application events (for e.g., shared-memory read and write). The Intel Pintool is implemented in C++ and depends on the Boost library version > 1.58. The Pintool source is available at `$PROJECT_ROOT/intel-pintool`.

Intel Pin can be downloaded from https://software.intel.com/en-us/articles/pin-a-dynamic-binary-instrumentation-tool. We assume that the path to the extracted source is denoted by `$PIN_ROOT`. After extracting Intel Pin, copy `$PROJECT_ROOT/intel-pintool/Viser` to `$PIN_ROOT/source/tools/`.

## Simulator Framework

This is a helper project written in Python to automate different steps with evaluation (e.g., executing PARSEC applications with the Pintool and one or more configurations of the CE/ARC simulators, and plot graphs comparing performance). We assume that the path to the source is denoted by `$VISER_EXP`.

The framework depends on a few Python packages, and a few third applications like `jgraph` (https://web.eecs.utk.edu/~plank/plank/jgraph/jgraph.html) and `McPAT` (https://github.com/HewlettPackard/mcpat).

In addition, the framework assumes that the following environment variables are defined (for e.g., in `$HOME/.bashrc`).

```Bash
export PIN_ROOT=<path to Intel Pin on your setup>
export PINTOOL_ROOT=$PIN_ROOT/source/tools/Viser
export PARSEC_ROOT=<path to PARSEC on your setup>
# $PROJECT_ROOT is the path where you have cloned this repository
export MESISIM_ROOT=$PROJECT_ROOT/ce-simulator
export VISERSIM_ROOT=$PROJECT_ROOT/arc-simulator
export VISER_EXP=$PROJECT_ROOT/sim-framework
```

## Examples

Here are some examples to run the simulators with PARSEC benchmarks.

```Bash
```
