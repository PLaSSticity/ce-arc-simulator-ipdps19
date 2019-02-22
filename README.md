# Rethinking Support for Region Conflict Exceptions

This repository includes the CE, CE+, and ARC simulators as reported in the IPDPS'19 paper. Please refer to the following paper for more details.

    Swarnendu Biswas, Rui Zhang, Michael D. Bond, and Brandon Lucia. Rethinking Support for Region Conflict Exceptions. IPDPS 2019.

In the following, we give a brief description of the implementation, and list instructions to build and execute the projects.

These instructions have been tested on a Ubuntu 14.04.5 LTS platform. It should also be possible to set the simulators up on newer Ubuntu LTS releases (e.g., 16.04), by taking care of the C++ and Java compiler versions and compatibility with the packages like Intel Pin.

We assume the root of the repository (top-level directory) is given by `$PROJECT_ROOT`.

## Setup the Environment

Create two directories `exp-output` and `exp-products` under $HOME. It is possible to use a different path but you will need to change the environment variables in the implementations.

```Bash
cd; mkdir exp-output exp-products
```

You will need to install the following packages on a Ubuntu 14.04.5 LTS distribution to get the following simulators working.

```Bash
sudo apt install git ant openjdk-7-jdk make gcc g++ libboost-dev libc6-i386 libc6 libgcc1 libstdc++6 build-essential ImageMagick lib32ncurses5 lib32stdc++6 libssl-dev m4 pkg-config libglib2.0-dev libxext-dev libxmu-dev libxml2-dev gcc-multilib g++-multilib python3.5 python3.5-dev python3-pip libblas-dev liblapack-dev libblas-dev liblapack-dev libblas3gf libgfortran3 liblapack3gf gfortran jgraph
```

## CE and ARC

The CE and ARC simulators have been implemented in Java, and share the same directory structure and execution dependencies. The CE simulator source is available at `$PROJECT_ROOT/ce-simulator`, while source for the ARC simulator is available at `$PROJECT_ROOT/arc-simulator`. The CE simulator implements CE/CE+ and the WMM configurations on top of a MESI protocol.

The following instructions should work for both the simulators.

+ Build the source: `ant` or `ant build`

+ Clean the build: `ant clean`

It should be possible to execute the simulators with both Java versions 1.7 and 1.8. You can also setup the projects in Java IDEs like Eclipse for automating the build and for browsing the source.

We assume the path to the CE simulator is denoted by `$MESISIM_ROOT` and the path to the ARC simulator is denoted by `$VISERSIM_ROOT`.

The following are a few simulator configurations that were used for the experiments reported in the IPDPS'19 paper:

+ mesi8 (WMM with 8 cores)
+ ce16 (CE with 16 cores)
+ ce32-64Kaim (CE with 32 cores using a 64K-entry AIM cache)
+ viser8-unopt (Unoptimized basic design of ARC with 8 cores)
+ viser8-selfinvalidationopt (Intermediate ARC design with 8 cores that only includes optimizations to reduce self-invalidations at region boundaries)
+ viser8-32Kaim (Fully optimized ARC design with 8 cores and 32K-entry AIM)
+ viser8-16Kaim (Fully optimized ARC design with 8 cores and 16K-entry AIM)
+ viser32-64Kaim (Fully optimized ARC design with 32 cores and 64K-entry AIM)
+ viser32-idealaim (Fully optimized ARC design with 32 cores and an ideal AIM)

## PARSEC

The simulators execute benchmarks from the PARSEC suite version 3.0-beta-20150206. The PARSEC suite can be downloaded from http://parsec.cs.princeton.edu/.

For our experiments, we have created a new build configuration `gcc-pthreads-hooks` for the relevant PARSEC applications to ensure Pthreads as the parallelization model. Otherwise, applications like `swaptions` use TBB as the default threading model (see `gcc-hooks.bldconf` for `swaptions`).

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

The build configuration files we have used are available in `$PROJECT_ROOT/parsec`. You can avoid the overhead of creating new `.bldconf` files for each application in PARSEC and use the build configurations that are part of PARSEC (for e.g., `gcc.bldconf`), as long as you make sure that the application uses Pthreads as the parallelization model. In that case, you will need to instead make the following changes:

+ Make sure Pthreads is the default parallelization model in `gcc-hooks.bldconf` for relevant PARSEC applications
+ Update the build configuration in `$PROJECT_ROOT/intel-pintool/Viser/makefile.rules`
+ Update the build configuration in `PARSEC_ARGS1` in `$PROJECT_ROOT/sim-framework/src/options/constants.py`

We have also included a couple of helper scripts to fix two issues we faced:
1. `$PROJECT_ROOT/parsec/x264.patch` - Fix a double free error in `x264`
2. `$PROJECT_ROOT/parsec/resolve_pod_issues.h` - Resolve issues with Perl versions (building `ssl` library will possibly require Perl version <= 5.14)

We assume that the path to the PARSEC suite is denoted by `$PARSEC_ROOT`.

## Intel Pintool

The implementation uses Intel Pin version 2.14 to generate a serialized event trace of relevant application events (for e.g., shared-memory read and write). The Intel Pintool is implemented in C++ and depends on the Boost library version > 1.58. The Pintool source is available at `$PROJECT_ROOT/intel-pintool`.

You can find more information about Intel Pin from https://software.intel.com/en-us/articles/pin-a-dynamic-binary-instrumentation-tool. Intel Pin v2.14 for GNU/Linux can be downloaded from https://software.intel.com/sites/landingpage/pintool/downloads/pin-2.14-71313-gcc.4.4.7-linux.tar.gz. After downloading and extracting Pin, you need to copy `$PROJECT_ROOT/intel-pintool/Viser` to `$PIN_ROOT/source/tools/`. You can use the following instructions to build the Pintool:

```Bash
cd; tar xvzf pin-2.14-71313-gcc.4.4.7-linux.tar.gz; mv pin-2.14-71313-gcc.4.4.7-linux intel-pin; cd intel-pin/source/tools
cp -r $PROJECT_ROOT/intel-pintool/Viser .
cd ..; make
```

We assume that the path to the extracted source is denoted by `$PIN_ROOT`.

## Helper Framework

This is a helper project written in Python >= 3.5 to automate different steps with evaluation (e.g., executing PARSEC applications with the Pintool and one or more configurations of the CE/ARC simulators, and plot graphs comparing performance). We assume that the path to the source is denoted by `$VISER_EXP`.

The framework depends on a few Python packages, and a few third applications like `jgraph` (https://web.eecs.utk.edu/~plank/plank/jgraph/jgraph.html) and `McPAT` (https://github.com/HewlettPackard/mcpat).

```Bash
sudo python3.5 -m pip install --upgrade numpy scipy django

cd; git clone https://github.com/HewlettPackard/mcpat.git; cd mcpat; make;
```

In addition, the framework assumes that the following environment variables are defined (for e.g., in `$HOME/.bashrc`).

```Bash
export PIN_ROOT=<path to Intel Pin on your setup>
export PINTOOL_ROOT=$PIN_ROOT/source/tools/Viser
export PARSEC_ROOT=<path to PARSEC on your setup>
# $PROJECT_ROOT is the path where you have cloned this repository
export MESISIM_ROOT=$PROJECT_ROOT/ce-simulator
export VISERSIM_ROOT=$PROJECT_ROOT/arc-simulator
export VISER_EXP=$PROJECT_ROOT/sim-framework
export MCPAT_ROOT=$HOME/mcpat
PATH=$VISER_EXP:$PATH
```

## Examples

Here are some short-running experiments  with PARSEC benchmarks to test whether your setup is working.

```Bash
arc --tools=pintool,mesi8 --tasks=build,run,result --workload=test --bench=blackscholes,x264 --pinThreads=8 --core=8 --outputDir=8core-experiments --trials=1 --assert=False --xassert=False --printOnly=False --roiOnly=True --project=viser --lockstep=False --generateEnergyStats=True --verbose=1
```

The experiment output is

Here are some examples to run the simulators with PARSEC benchmarks.

```Bash
arc --tools=pintool,mesi8,ce8,ce8-32Kaim,viser8-unopt,viser8-selfinvalidationopt,viser8-32Kaim,viser8-16Kaim,viser8-idealaim --tasks=sync,build,run --workload=simmedium --bench=blackscholes,bodytrack,canneal,dedup,ferret,fluidanimate,raytrace,streamcluster,swaptions,vips,x264 --pinThreads=8 --core=8 --outputDir=8core-experiments --trials=1 --assert=False --xassert=False --printOnly=False --roiOnly=True --project=viser --lockstep=False --generateEnergyStats=True --verbose=1
```

The time taken and memory required to execute these experiments depend on the number of simultaneous configurations that are run, along with the input size of the PARSEC applications.

```Bash
arc --tools=pintool,mesi32,ce32,ce32-64Kaim,viser32-32Kaim,viser32-64Kaim,viser32-idealaim --tasks=result --workload=simmedium --bench=blackscholes,bodytrack,canneal,dedup,ferret,fluidanimate,raytrace,streamcluster,swaptions,vips,x264 --pinThreads=32 --core=32 --outputDir=32core-experiments --trials=1 --assert=False --xassert=False --printOnly=False --roiOnly=True --project=viser --lockstep=False --generateEnergyStats=True --verbose=1
```

## Questions

Feel free to post issues or contact with any questions.
