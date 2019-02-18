import math
import os


class Constants():
    """Define constants to different project directories and executables."""

    # Paths to various directories
    PIN_ROOT = os.getenv('PIN_ROOT')
    VS_PINTOOL_ROOT = os.getenv('PINTOOL_ROOT')  # the default Viser pintool
    ST_PINTOOL_ROOT = os.getenv('ST_PINTOOL_ROOT')  # the ViserST pintool
    ST_PINTOOL_ROOT = (PIN_ROOT + "/source/tools/ViserST") if (
        ST_PINTOOL_ROOT is None) else ST_PINTOOL_ROOT
    PARSEC_ROOT = os.getenv('PARSEC_ROOT', "")

    MESISIM_ROOT = os.getenv('MESISIM_ROOT')
    VISERSIM_ROOT = os.getenv('VISERSIM_ROOT')
    VISER_EXP = os.getenv('VISER_EXP')
    RCCSISIM_ROOT = os.getenv('RCCSISIM_ROOT', "")

    HTTPD_ROOT = os.getenv('HTTPD_ROOT')
    MYSQLD_ROOT = os.getenv('MYSQLD_ROOT')
    MEMCACHED_ROOT = os.getenv('MEMCACHED_ROOT')

    EXP_OUTPUT = os.getenv('HOME') + "/exp-output/"
    EXP_PRODUCTS = os.getenv('HOME') + "/exp-products/"

    PYTHON_EXEC = "python3"
    BASH_SHEBANG = "#!/bin/bash"
    VISER_EXP_LOCAL = "viser-local"
    VISER_EXP_REMOTE = "viser-remote"

    # Simulator parameters
    CLK_FREQUENCY = 1.6 * math.pow(10, 9)
    ONCHIP_BW = 100  # GB/s
    OFFCHIP_BW = 48  # GB/s
    NUM_BYTES_FLIT = 16
    DATA_LINE_SIZE = 64  # Bytes
    NUM_BYTES_MEM_FLIT = DATA_LINE_SIZE
    RD_MD_BYTES_PER_LINE = 8  # Private caches, 1 bit per byte
    WR_MD_BYTES_PER_LINE = 8  # Private caches, 1 bit per byte

    ARC_VERSION_SIZE = 4  # Bytes

    CONFIG = "config.ini"
    # Named pipes
    FIFO_PREFIX = "fifo."
    FIFO_FRONTEND = FIFO_PREFIX + "frontend"
    FIFO_PERTHREAD = FIFO_PREFIX + "tid"

    # Pintool
    PARSECMGMT = PARSEC_ROOT + "/bin/parsecmgmt -a run -p "
    PARSEC_ARGS1 = "-c gcc-pthreads-hooks -i "
    PARSEC_ARGS3 = ('''-s "''' + PIN_ROOT + "/pin -ifeellucky -injection child -t ")
    PARSEC_ARGS4 = ("/obj-intel64/visersim.so")

    PINBIN = PIN_ROOT + "/pin -ifeellucky -injection child "
    # PIN_ARG = "-t " + PINTOOL_ROOT + "/obj-intel64/visersim.so"

    GUAVA_JAR = "/lib/guava-18.0.jar:"
    JOPTSIMPLE_JAR = "/lib/jopt-simple-5.0.2.jar"

    MESISIM_CLASSPATH = (" -classpath " + MESISIM_ROOT + "/bin/:" + MESISIM_ROOT + GUAVA_JAR +
                         MESISIM_ROOT + JOPTSIMPLE_JAR + " simulator.mesi.MESISim")

    VISERSIM_CLASSPATH = (" -Xmx40g -classpath " + VISERSIM_ROOT + "/bin/:" + VISERSIM_ROOT +
                          GUAVA_JAR + VISERSIM_ROOT + JOPTSIMPLE_JAR + " simulator.viser.ViserSim")

    PAUSESIM_CLASSPATH = (" -Xmx42g -classpath " + VISERSIM_ROOT + "/bin/:" + VISERSIM_ROOT +
                          GUAVA_JAR + VISERSIM_ROOT + JOPTSIMPLE_JAR + " simulator.viser.ViserSim")

    RESTARTSIM_CLASSPATH = (
        " -Xmx60g -classpath " + VISERSIM_ROOT + "/bin/:" + VISERSIM_ROOT + GUAVA_JAR +
        VISERSIM_ROOT + JOPTSIMPLE_JAR + " simulator.viser.ViserSim")

    RCCSISIM_CLASSPATH = (" -Xmx30g -classpath " + RCCSISIM_ROOT + "/bin/:" + RCCSISIM_ROOT +
                          GUAVA_JAR + RCCSISIM_ROOT + JOPTSIMPLE_JAR + " simulator.rccsi.RCCSISim")

    # httpd constants
    HTTPD_PID_FILE = (HTTPD_ROOT + "/logs/httpd.pid") if (HTTPD_ROOT is not None) else None
    HTTPD_START = (HTTPD_ROOT + "/bin/apachectl start") if (HTTPD_ROOT is not None) else None
    HTTPD_STOP = (HTTPD_ROOT + "/bin/apachectl stop") if (HTTPD_ROOT is not None) else None
    HTTP_CLIENT0 = (HTTPD_ROOT + "/trigger-con0.sh") if (HTTPD_ROOT is not None) else None
    HTTP_CLIENT1 = (HTTPD_ROOT + "/trigger-con1.sh") if (HTTPD_ROOT is not None) else None

    HTTPD_DEBUG_START = (HTTPD_ROOT + "/bin/httpd -X -k start") if (
        HTTPD_ROOT is not None) else None
    HTTPD_DEBUG_STOP = (HTTPD_ROOT + "/bin/httpd -X -k stop") if (HTTPD_ROOT is not None) else None

    # mysqld constants
    MEMCACHED_START = (MEMCACHED_ROOT + "/bin/memcached") if (MEMCACHED_ROOT is not None) else None
    MEMCACHED_STOP = ("killall -15 " + MEMCACHED_START) if (MEMCACHED_START is not None) else None
    MEMCACHED_CLIENT0 = (MEMCACHED_ROOT + "/reproduce-pkg/trigger") if (
        MEMCACHED_ROOT is not None) else None
    MEMCACHED_CLIENT1 = (MEMCACHED_ROOT + "/reproduce-pkg/trigger") if (
        MEMCACHED_ROOT is not None) else None

    # memcached constants
    MYSQLD_START = (
        MYSQLD_ROOT + "/bin/mysqld " +
        # "--max_connections=8 --innodb-read-io-threads=1 " +
        "--innodb-read-io-threads=1 --skip-innodb_adaptive_hash_index " +
        "--innodb-lru-scan-depth=256 --innodb-lock-wait-timeout=1073741820 " +
        "--innodb-write-io-threads=1 " + "--basedir=" + MYSQLD_ROOT + " --datadir=" + MYSQLD_ROOT +
        "/data --plugin-dir=" + MYSQLD_ROOT + "/lib/plugin") if (MYSQLD_ROOT is not None) else None
    MYSQLD_CACHED_THREADS = " --thread_cache_size="
    MYSQLD_INNODB_THREADS = " --innodb-thread-concurrency="
    MYSQLD_STOP = (MYSQLD_ROOT + "/support-files/mysql.server stop") if (
        MYSQLD_ROOT is not None) else None
    MYSQL_CLIENT0 = (MYSQLD_ROOT + "/trigger-con0.sh") if (MYSQLD_ROOT is not None) else None
    MYSQL_CLIENT1 = (MYSQLD_ROOT + "/trigger-con1.sh") if (MYSQLD_ROOT is not None) else None

    # OS-level constants
    FILE_SEP = "/"

    # Number of digits after decimal
    PRECISION_DIGITS = 3

    ADD_AIM_McPAT = True

    # Table 8.4 in the primer book shows a total of 5 states in the directory.
    DIR_LINE_SIZE = 3  # In bits

    # This is common across simulators
    LLC_4_LATENCY = 25
    LLC_8_LATENCY = 35
    LLC_16_LATENCY = 40
    LLC_32_LATENCY = 50

    LLC_4_ASSOC = 8
    LLC_8_ASSOC = 16
    LLC_16_ASSOC = 16
    LLC_32_ASSOC = 32

    # Assuming data line of 64 Bytes
    LLC_4_LINES = 131072  # 128K lines
    LLC_8_LINES = 262144  # 256K lines
    LLC_16_LINES = 524288  # 512K lines
    LLC_32_LINES = 1048576  # 1M lines
