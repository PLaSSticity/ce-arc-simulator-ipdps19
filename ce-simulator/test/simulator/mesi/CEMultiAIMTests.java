package simulator.mesi;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import org.junit.After;
import org.junit.AfterClass;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;

import simulator.mesi.MESISim.PARSEC_PHASE;
import simulator.mesi.Machine.SimulationMode;

public final class CEMultiAIMTests {

	static Machine<MESILine> machine;

	static final CpuId P0 = new CpuId(0);
	static final CpuId P1 = new CpuId(1);
	static final CpuId P2 = new CpuId(2);
	static final CpuId P3 = new CpuId(3);

	static final ThreadId T0 = new ThreadId(0);
	static final ThreadId T1 = new ThreadId(1);
	static final ThreadId T2 = new ThreadId(2);
	static final ThreadId T3 = new ThreadId(3);

	static final int CORES = 4;
	static final int PINTHREADS = 1;
	static final int LINE_SIZE = 4;

	static final int L1_ASSOC = 2;
	static final int L1_CACHE_SIZE = 16; // 4 blocks, 2 sets

	static final int L2_ASSOC = 2;
	static final int L2_CACHE_SIZE = 16; // 4 blocks, 2 sets

	static final int L3_ASSOC = 4;
	static final int L3_CACHE_SIZE = 64;

	static {
		// This will enable all the assertions like cache inclusivity checks
		assert MESISim.XASSERTS;
		SystemConstants.unsafeSetLineSize(LINE_SIZE);
	}

	static CacheConfiguration<MESILine> l1config = new CacheConfiguration<MESILine>() {
		{
			cacheSize = L1_CACHE_SIZE;
			lineSize = LINE_SIZE;
			assoc = L1_ASSOC;
			level = CacheLevel.L1;
		}
	};

	static CacheConfiguration<MESILine> l2config = new CacheConfiguration<MESILine>() {
		{
			cacheSize = L2_CACHE_SIZE;
			lineSize = LINE_SIZE;
			assoc = L2_ASSOC;
			level = CacheLevel.L2;
		}
	};

	static CacheConfiguration<MESILine> l3config = new CacheConfiguration<MESILine>() {
		{
			cacheSize = L3_CACHE_SIZE;
			lineSize = LINE_SIZE;
			assoc = L3_ASSOC;
			level = CacheLevel.L3;
		}
	};

	/**
	 * @throws java.lang.Exception
	 */
	@BeforeClass
	public static void setUpBeforeClass() throws Exception {
	}

	/**
	 * @throws java.lang.Exception
	 */
	@AfterClass
	public static void tearDownAfterClass() throws Exception {
	}

	/**
	 * @throws java.lang.Exception
	 */
	@Before
	public void setUp() throws Exception {
		Machine.MachineParams<MESILine> params = new Machine.MachineParams<MESILine>() {

			@Override
			SimulationMode simulationMode() {
				return SimulationMode.BASELINE;
			}

			@Override
			int numProcessors() {
				return CORES;
			}

			@Override
			int numPinThreads() {
				return PINTHREADS;
			}

			@Override
			boolean pintool() {
				return false;
			}

			@Override
			CacheConfiguration<MESILine> l1config() {
				return l1config;
			}

			@Override
			boolean useL2() {
				return true;
			}

			@Override
			CacheConfiguration<MESILine> l2config() {
				return l2config;
			}

			@Override
			CacheConfiguration<MESILine> l3config() {
				return l3config;
			}

			LineFactory<MESILine> lineFactory() {
				return new LineFactory<MESILine>() {
					@Override
					public MESILine create(CpuId id, CacheLevel level) {
						return new MESILine(id, level);
					}

					@Override
					public MESILine create(CpuId id, CacheLevel level, LineAddress la) {
						return new MESILine(id, level, la);
					}

					@Override
					public MESILine create(CpuId id, CacheLevel level, MESILine l) {
						assert l.valid() : "Source line should be valid.";
						MESILine tmp = new MESILine(id, level, l.lineAddress());
						tmp.changeStateTo(l.getState());
						tmp.setDirty(l.dirty());
						if (conflictExceptions()) {
							tmp.setLocalReads(l.getLocalReads());
							tmp.setLocalWrites(l.getLocalWrites());
							tmp.setRemoteReads(l.getRemoteReads());
							tmp.setRemoteWrites(l.getRemoteWrites());
						}

						return tmp;
					}
				};
			}

			@Override
			boolean ignoreStackReferences() {
				return false;
			}

			@Override
			boolean remoteAccessesAffectLRU() {
				return false;
			}

			@Override
			boolean conflictExceptions() {
				return true;
			}

			@Override
			boolean printConflictingSites() {
				return false;
			}

			@Override
			boolean reportSites() {
				return false;
			}

			@Override
			boolean treatAtomicUpdatesAsRegularAccesses() {
				return false;
			}

			@Override
			boolean usePLRU() {
				return false;
			}

			@Override
			boolean withPacifistBackends() {
				return false;
			}

			@Override
			boolean useAIMCache() {
				return true; // XXX: Reduce the default AIM cache size before setting this to true
			}

			@Override
			boolean clearAIMCacheAtRegionBoundaries() {
				return false;
			}
		};

		// Not sure how we can override JOpt command line
		MESISim.Options = Knobs.parser.parse("--xassert=true --assert-period=1");
		MESISim.setPhase(PARSEC_PHASE.IN_ROI);
		assertTrue(MESISim.XASSERTS);
		assertEquals(1, MESISim.Options.valueOf(Knobs.AssertPeriod).intValue());

		machine = new Machine<MESILine>(params);
		machine.initializeEpochs();
	}

	/**
	 * @throws java.lang.Exception
	 */
	@After
	public void tearDown() throws Exception {
	}

	// IMP: AIM associativity is 2 and # lines is 16, and set useAIMCache() to true
	@Test
	public void testAIM1() {
		Processor<MESILine> proc0 = machine.getProc(P0);
		Processor<MESILine> proc1 = machine.getProc(P1);

		machine.testCacheMemoryRead(P0, 80L, 2);
		// A LLC miss means we should fetch the line into the AIM. But an LLC miss is not an AIM
		// miss if there is no metadata.
		assertEquals(0, proc0.stats.pc_aim.pc_ReadMisses.get(), 0);
		assertFalse(proc0.aimcache.junitGetLine(proc0, new DataLineAddress(80L)).hasAIMMD());

		machine.testCacheMemoryWrite(P1, 80L, 2); // LLC hit, this invalidates the line in P0
		assertEquals(0, proc1.stats.pc_aim.pc_WriteMisses.get(), 0);
		assertFalse(proc1.aimcache.junitGetLine(proc1, new DataLineAddress(80L)).hasAIMMD());

		machine.testCacheMemoryWrite(P1, 96L, 2);
		assertEquals(0, proc1.stats.pc_aim.pc_WriteMisses.get(), 0);

		machine.testCacheMemoryRead(P0, 112L, 2);
		assertEquals(0, proc0.stats.pc_aim.pc_ReadMisses.get(), 0);
		// 80L is evicted from AIM but has no metadata.
		assertEquals(0, proc0.stats.pc_aim.pc_LineEvictions.get(), 0);
		// Private caches do not evict any lines
		assertEquals(0, proc0.stats.pc_aim.pc_WriteMisses.get(), 0);
		assertFalse(proc0.aimcache.junitGetLine(proc0, new DataLineAddress(80L)).hasAIMMD());
		assertFalse(proc0.aimcache.junitGetLine(proc0, new DataLineAddress(112L)).hasAIMMD());

		// This is a private cache hit. So 80L is not brought into the AIM.
		machine.testCacheMemoryRead(P1, 80L, 2);
		assertEquals(1, proc1.stats.pc_l1d.pc_ReadHits.get(), 0);
		assertEquals(0, proc1.stats.pc_aim.pc_ReadMisses.get(), 0);
		assertEquals(0, proc1.stats.pc_aim.pc_LineEvictions.get(), 0);

		// System.out.println(proc0.L1cache);
		// System.out.println(proc1.L1cache);

		machine.testCacheMemoryRead(P0, 128L, 2);
		// System.out.println(proc0.L1cache);
		// 80L is not evicted from AIM as 128L is going to a different set. 80L will be evicted
		// from private caches.
		assertEquals(0, proc0.stats.pc_aim.pc_ReadMisses.get(), 0);
		assertEquals(0, proc0.stats.pc_aim.pc_LineEvictions.get(), 0);
		// +1 for fetching, +2 for data + metadata, +1 for return metadata of 112L.
		assertEquals(0, proc0.stats.pc_aim.pc_WriteMisses.get(), 0);

		machine.testCacheMemoryWrite(P0, 64L, 2);
		// 80L will be evicted from LLC, 80L from the AIM (has metadata). Then 112L will be evicted
		// from private caches and will hit in the AIM.
		assertEquals(0, proc0.stats.pc_aim.pc_WriteMisses.get(), 0);
		assertEquals(1, proc0.stats.pc_aim.pc_LineEvictions.get(), 0);
		// +1 for fetch, +2 for data + metadata, +2 for evicting data and metadata of 80L, +1 for
		// requesting metadata of 112L and +1 for metadata of 112L
		assertTrue(proc0.aimcache.junitGetLine(proc0, new DataLineAddress(112L)).hasAIMMD());
		// System.out.println(proc0.L1cache);
	}

	// IMP: AIM associativity is 2 and # lines is 16, and set useAIMCache() to true
	@Test
	public void testAIM2() {
		Processor<MESILine> proc0 = machine.getProc(P0);
		Processor<MESILine> proc1 = machine.getProc(P1);

		machine.testCacheMemoryRead(P0, 80L, 2);
		machine.testCacheMemoryRead(P0, 64L, 2);
		machine.testCacheMemoryRead(P0, 96L, 2);
		assertTrue(proc0.L2cache.outOfCache);
		machine.testCacheMemoryRead(P0, 48L, 2);

		// Evict 80L from L3 and AIM
		machine.testCacheMemoryRead(P0, 112L, 2);
		assertEquals(1, proc0.stats.pc_aim.pc_LineEvictions.get(), 0);
		assertTrue(proc0.aimcache.junitGetLine(proc0, new DataLineAddress(96L)).hasAIMMD());
		assertTrue(proc0.aimcache.junitGetLine(proc0, new DataLineAddress(64L)).hasAIMMD());
		assertFalse(proc0.aimcache.junitGetLine(proc0, new DataLineAddress(48L)).hasAIMMD());

		// Bring in 80L from memory. AIM MD bit should be set.
		machine.testCacheMemoryWrite(P1, 80L, 2);
		assertTrue(proc1.aimcache.junitGetLine(proc1, new DataLineAddress(80L)).hasAIMMD());
	}

	// IMP: AIM associativity is 2 and # lines is 16, and set useAIMCache() to true
	@Test
	public void testAIM3() {
		Processor<MESILine> proc0 = machine.getProc(P0);
		Processor<MESILine> proc1 = machine.getProc(P1);

		machine.testCacheMemoryRead(P0, 80L, 2);
		machine.testCacheMemoryRead(P0, 64L, 2);
		machine.testCacheMemoryRead(P0, 96L, 2);
		machine.testCacheMemoryRead(P0, 48L, 2);

		// Evict 80L from L3 and AIM
		machine.testCacheMemoryRead(P0, 112L, 2);
		assertEquals(1, proc0.stats.pc_aim.pc_LineEvictions.get(), 0);
		assertTrue(proc0.aimcache.junitGetLine(proc0, new DataLineAddress(96L)).hasAIMMD());
		assertTrue(proc0.aimcache.junitGetLine(proc0, new DataLineAddress(64L)).hasAIMMD());
		assertFalse(proc0.aimcache.junitGetLine(proc0, new DataLineAddress(48L)).hasAIMMD());

		machine.processSyncOp(P0, T0, EventType.LOCK_ACQUIRE, EventType.REG_END);

		// Bring in 80L from memory. AIM MD bit should be set.
		machine.testCacheMemoryWrite(P1, 80L, 2);
		assertFalse(proc1.aimcache.junitGetLine(proc1, new DataLineAddress(80L)).hasAIMMD());
	}

	// IMP: AIM associativity is 2 and # lines is 16, and set useAIMCache() to true
	@Test
	public void testAIM4() {
		Processor<MESILine> proc0 = machine.getProc(P0);
		Processor<MESILine> proc1 = machine.getProc(P1);

		machine.testCacheMemoryRead(P0, 80L, 2);
		machine.testCacheMemoryRead(P0, 64L, 2);
		machine.testCacheMemoryRead(P0, 96L, 2);
		machine.testCacheMemoryRead(P0, 48L, 2);

		// Evict 80L from L3 and AIM
		machine.testCacheMemoryRead(P0, 112L, 2);
		assertEquals(1, proc0.stats.pc_aim.pc_LineEvictions.get(), 0);
		assertTrue(proc0.aimcache.junitGetLine(proc0, new DataLineAddress(96L)).hasAIMMD());
		assertTrue(proc0.aimcache.junitGetLine(proc0, new DataLineAddress(64L)).hasAIMMD());
		assertFalse(proc0.aimcache.junitGetLine(proc0, new DataLineAddress(48L)).hasAIMMD());

		machine.processSyncOp(P1, T1, EventType.LOCK_ACQUIRE, EventType.REG_END);

		// Bring in 80L from memory. AIM MD bit should be set.
		machine.testCacheMemoryWrite(P1, 80L, 2);
		assertTrue(proc1.aimcache.junitGetLine(proc1, new DataLineAddress(80L)).hasAIMMD());
	}

}
