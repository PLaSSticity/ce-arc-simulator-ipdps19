package simulator.viser;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import org.junit.After;
import org.junit.AfterClass;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;

import simulator.viser.Machine.SimulationMode;
import simulator.viser.Processor.ExecutionPhase;
import simulator.viser.ViserSim.PARSEC_PHASE;

public final class UniProcessorTests {

	static Machine<ViserLine> machine;
	static final CpuId P0 = new CpuId(0);
	static final ThreadId T0 = new ThreadId((byte) 0);

	static final int CORES = 1;
	static final int LINE_SIZE = 4;

	// 2 sets each with 2 lines for a total of 4 lines, each of size 4 bytes
	static final int L1_ASSOC = 2;
	static final int L1_CACHE_SIZE = 16;

	static final int L2_ASSOC = 2;
	static final int L2_CACHE_SIZE = 16; // 4 blocks, 2 sets

	// 4 sets each with 4 lines for a total of 16 lines, each of size 4 bytes
	static final int L3_ASSOC = 4;
	static final int L3_CACHE_SIZE = 64;

	static {
		// This will enable all the assertions like cache inclusivity checks
		assert ViserSim.XASSERTS;
		SystemConstants.unsafeSetLineSize(LINE_SIZE);
	}

	static CacheConfiguration<ViserLine> l1config = new CacheConfiguration<ViserLine>() {
		{
			cacheSize = L1_CACHE_SIZE;
			lineSize = LINE_SIZE;
			assoc = L1_ASSOC;
			level = CacheLevel.L1;
		}
	};

	static CacheConfiguration<ViserLine> l2config = new CacheConfiguration<ViserLine>() {
		{
			cacheSize = L2_CACHE_SIZE;
			lineSize = LINE_SIZE;
			assoc = L2_ASSOC;
			level = CacheLevel.L2;
		}
	};

	static CacheConfiguration<ViserLine> l3config = new CacheConfiguration<ViserLine>() {
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
		Machine.MachineParams<ViserLine> params = new Machine.MachineParams<ViserLine>() {

			@Override
			SimulationMode simulationMode() {
				return SimulationMode.VISER;
			}

			@Override
			int numProcessors() {
				return CORES;
			}

			@Override
			boolean pintool() {
				return false;
			}

			@Override
			CacheConfiguration<ViserLine> l1config() {
				return l1config;
			}

			@Override
			boolean useL2() {
				return true;
			}

			@Override
			CacheConfiguration<ViserLine> l2config() {
				return l2config;
			}

			@Override
			CacheConfiguration<ViserLine> l3config() {
				return l3config;
			}

			LineFactory<ViserLine> lineFactory() {
				return new LineFactory<ViserLine>() {
					@Override
					public ViserLine create(Processor<ViserLine> proc, CacheLevel level) {
						ViserLine line = new ViserLine(proc, level);
						line.setEpoch(proc.id, proc.getCurrentEpoch());
						return line;
					}

					@Override
					public ViserLine create(Processor<ViserLine> proc, CacheLevel level,
							LineAddress la) {
						ViserLine line = new ViserLine(proc, level, la);
						line.setEpoch(proc.id, proc.getCurrentEpoch());
						return line;
					}

					@Override
					public ViserLine create(Processor<ViserLine> proc, CacheLevel level,
							ViserLine l) {
						if (!l.valid()) {
							throw new RuntimeException("Source line should be VALID.");
						}
						ViserLine tmp = new ViserLine(proc, level, l.lineAddress());
						tmp.changeStateTo(l.getState());
						tmp.setVersion(l.getVersion());
						tmp.copyAllValues(l);
						tmp.setLastWriters(l.getLastWriters());
						tmp.setLockOwnerID(l.getLockOwnerID());
						// We do not update deferred owner id from here.
						if (level.compareTo(proc.llc()) < 0) { // private line
							CpuId cid = proc.id;
							tmp.orWriteEncoding(cid, l.getWriteEncoding(cid));
							tmp.orReadEncoding(cid, l.getReadEncoding(cid));
							tmp.updateWriteSiteInfo(cid, l.getWriteEncoding(cid),
									l.getWriteSiteInfo(cid), l.getWriteLastSiteInfo(cid));
							tmp.updateReadSiteInfo(cid, l.getReadEncoding(cid),
									l.getReadSiteInfo(cid), l.getReadLastSiteInfo(cid));
							tmp.setEpoch(proc.id, proc.getCurrentEpoch());
						} else {
							for (int i = 0; i < proc.params.numProcessors(); i++) {
								CpuId cpuId = new CpuId(i);
								PerCoreLineMetadata tmpMd = l.getPerCoreMetadata(cpuId);
								// We do not bother with epoch here, since it should be taken care
								// of automatically
								// later
								PerCoreLineMetadata md = new PerCoreLineMetadata(tmpMd.epoch,
										tmpMd.writeEncoding, tmpMd.readEncoding,
										tmpMd.writeSiteInfo, tmpMd.readSiteInfo,
										tmpMd.writeLastSiteInfo, tmpMd.readLastSiteInfo);
								tmp.setPerCoreMetadata(cpuId, md);
							}
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
			boolean writebackInMemory() {
				return false;
			}

			@Override
			boolean alwaysInvalidateReadOnlyLines() {
				return false;
			}

			@Override
			boolean invalidateWrittenLinesOnlyAfterVersionCheck() {
				return true;
			}

			@Override
			boolean updateWrittenLinesDuringVersionCheck() {
				return false;
			}

			@Override
			boolean invalidateUntouchedLinesOptimization() {
				return false;
			}

			@Override
			boolean useSpecialInvalidState() {
				return true;
			}

			@Override
			boolean useBloomFilter() {
				return true;
			}

			// XXX: Reduce the default AIM cache size before setting this to true
			@Override
			boolean useAIMCache() {
				return true;
			}

			@Override
			boolean deferWriteBacks() {
				return true;
			}

			@Override
			boolean areDeferredWriteBacksPrecise() {
				return false;
			}

			@Override
			boolean skipValidatingReadLines() {
				return true;
			}

			@Override
			boolean ignoreFetchingDeferredLinesDuringReadValidation() {
				return false;
			}

			@Override
			boolean clearAIMCacheAtRegionBoundaries() {
				return false;
			}

			@Override
			boolean ignoreFetchingReadBits() {
				return false;
			}

			@Override
			boolean validateL1ReadsAlongWithL2() {
				return true;
			}

			@Override
			boolean ignoreFetchingWriteBits() {
				return false;
			}

			@Override
			int numPinThreads() {
				return 0;
			}

			@Override
			boolean lockstep() {
				return false;
			}

			@Override
			boolean siteTracking() {
				return false;
			}

			@Override
			boolean printConflictingSites() {
				return false;
			}

			@Override
			boolean treatAtomicUpdatesAsRegularAccesses() {
				return false;
			}

			@Override
			boolean evictCleanLineFirst() {
				return false;
			}

			@Override
			boolean usePLRU() {
				return false;
			}

			@Override
			boolean isHttpd() {
				return false;
			}

			@Override
			boolean treatAtomicUpdatesAsRegionBoundaries() {
				return false;
			}
		};

		// Not sure how we can override JOpt command line
		ViserSim.Options = Knobs.parser.parse("--xassert=true --assert-period=1");
		ViserSim.setPARSECPhase(PARSEC_PHASE.IN_ROI);
		assertTrue(ViserSim.XASSERTS);
		assertEquals(1, ViserSim.Options.valueOf(Knobs.AssertPeriod).intValue());

		machine = new Machine<ViserLine>(params);
		machine.initializeEpochs();
	}

	/**
	 * @throws java.lang.Exception
	 */
	@After
	public void tearDown() throws Exception {
	}

	@Test
	public void testReadL1Eviction() {
		Processor<ViserLine> proc = machine.getProc(P0);

		// Miss in L1/L2 cache, miss in LLC
		machine.testCacheMemoryRead(P0, 80L, 2, 10, T0);
		machine.testCacheMemoryRead(P0, 64L, 2, 20, T0);
		assertEquals(0, proc.stats.pc_l1d.pc_ReadHits.get(), 0);
		assertEquals(2, proc.stats.pc_l1d.pc_ReadMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l2d.pc_ReadHits.get(), 0);
		assertEquals(2, proc.stats.pc_l2d.pc_ReadMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_ReadHits.get(), 0);
		assertEquals(2, proc.stats.pc_l3d.pc_ReadMisses.get(), 0);
		// System.out.println(proc.L1cache);

		// Hit in L1 cache, will change MRU status in L1
		machine.testCacheMemoryRead(P0, 82L, 2, 30, T0);
		assert proc.L1cache.getLine(new DataByteAddress(80L).lineAddress())
				.getState() == ViserState.VISER_VALID;
		assertEquals(1, proc.stats.pc_l1d.pc_ReadHits.get(), 0);
		assertEquals(2, proc.stats.pc_l1d.pc_ReadMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l2d.pc_ReadHits.get(), 0);
		assertEquals(2, proc.stats.pc_l2d.pc_ReadMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_ReadHits.get(), 0);
		assertEquals(2, proc.stats.pc_l3d.pc_ReadMisses.get(), 0);
		// System.out.println(proc.L1cache);

		machine.testCacheMemoryRead(P0, 96L, 2, 0, T0);
		assertEquals(1, proc.stats.pc_l1d.pc_ReadHits.get(), 0);
		assertEquals(3, proc.stats.pc_l1d.pc_ReadMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l1d.pc_LineEvictions.get(), 0);
		assertEquals(3, proc.stats.pc_l2d.pc_ReadMisses.get(), 0);
		// System.out.println(proc.L1cache);

		// Miss in L1/L2 cache, miss in LLC, evicts line 64L to LLC
		machine.testCacheMemoryRead(P0, 72L, 2, 99, T0);
		assertEquals(1, proc.stats.pc_l1d.pc_ReadHits.get(), 0);
		assertEquals(4, proc.stats.pc_l1d.pc_ReadMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l1d.pc_LineEvictions.get(), 0);
		assertEquals(4, proc.stats.pc_l2d.pc_ReadMisses.get(), 0);
		assertEquals(4, proc.stats.pc_l3d.pc_ReadMisses.get(), 0);
		System.out.println(proc.L1cache);
	}

	@Test
	public void testReadAfterWrite() {
		Processor<ViserLine> proc = machine.getProc(P0);

		machine.testCacheMemoryWrite(P0, 80L, 2, 10, T0);
		machine.testCacheMemoryRead(P0, 80L, 2, 10, T0);
		assertEquals(0L,
				proc.L1cache.getLine((new DataByteAddress(80L)).lineAddress()).getReadEncoding(P0));
		machine.testCacheMemoryRead(P0, 82L, 2, 20, T0);
		assert proc.L1cache.getLine((new DataByteAddress(80L)).lineAddress())
				.getReadEncoding(P0) > 0L;
		machine.testCacheMemoryWrite(P0, 82L, 2, 10, T0);
		System.out.println(proc.L1cache);
		System.out.println(proc.L1cache.getLine((new DataByteAddress(80L)).lineAddress())
				.getPerCoreMetadata(P0));
	}

	@Test
	public void testWriteAfterRead() {
		Processor<ViserLine> proc = machine.getProc(P0);

		machine.testCacheMemoryRead(P0, 80L, 2, 0, T0);
		machine.testCacheMemoryWrite(P0, 80L, 2, 100, T0);
		machine.testProcessRegionBoundary(P0, T0, EventType.LOCK_ACQUIRE);
		assertEquals(0, proc.stats.pc_PreciseConflicts.get(), 0);
	}

	@Test
	public void testReadRegionEnd() {
		Processor<ViserLine> proc = machine.getProc(P0);

		// Miss in L1/L2 cache, miss in LLC
		machine.testCacheMemoryRead(P0, 80L, 2, 10, T0);
		machine.testCacheMemoryRead(P0, 64L, 2, 20, T0);
		System.out.println(proc.L1cache);

		machine.testProcessRegionBoundary(P0, T0, EventType.LOCK_ACQUIRE);
		System.out.println(proc.L1cache);

		machine.printEpochMap();
	}

	@Test
	public void testWriteL1Eviction() {
		Processor<ViserLine> proc = machine.getProc(P0);

		machine.testCacheMemoryWrite(P0, 80L, 2, 6, T0);
		machine.testCacheMemoryWrite(P0, 66L, 2, 23, T0);
		assertEquals(2, proc.stats.pc_l1d.pc_WriteMisses.get(), 0);
		assertEquals(2, proc.stats.pc_l2d.pc_WriteMisses.get(), 0);
		assertEquals(2, proc.stats.pc_l3d.pc_WriteMisses.get(), 0);
		System.out.println(proc.L1cache);

		machine.testCacheMemoryWrite(P0, 96L, 2, 29, T0);
		assertEquals(3, proc.stats.pc_l1d.pc_WriteMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l1d.pc_LineEvictions.get(), 0);
		assertEquals(3, proc.stats.pc_l2d.pc_WriteMisses.get(), 0);
		assertEquals(1, proc.stats.pc_l2d.pc_LineEvictions.get(), 0);
		assertEquals(3, proc.stats.pc_l3d.pc_WriteMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_LineEvictions.get(), 0);
		System.out.println(proc.L3cache.getLine((new DataByteAddress(80L)).lineAddress())
				.getPerCoreMetadata(P0));
		System.out.println(proc.L1cache);

		machine.testCacheMemoryWrite(P0, 112L, 2, 99, T0);
		assertEquals(4, proc.stats.pc_l1d.pc_WriteMisses.get(), 0);
		assertEquals(4, proc.stats.pc_l2d.pc_WriteMisses.get(), 0);
		assertEquals(2, proc.stats.pc_l2d.pc_LineEvictions.get(), 0);
		assertEquals(4, proc.stats.pc_l3d.pc_WriteMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_LineEvictions.get(), 0);
		System.out.println(proc.L3cache.getLine((new DataByteAddress(64L)).lineAddress())
				.getPerCoreMetadata(P0));
		System.out.println(proc.L1cache);
	}

	@Test
	public void testWriteRegionEnd() {
		Processor<ViserLine> proc = machine.getProc(P0);

		machine.testCacheMemoryWrite(P0, 80L, 2, 6, T0);
		machine.testCacheMemoryWrite(P0, 64L, 2, 23, T0);
		System.out.println(proc.L1cache);

		machine.testProcessRegionBoundary(P0, T0, EventType.LOCK_ACQUIRE);
		System.out.println(proc.L1cache);

		machine.testProcessRegionBoundary(P0, T0, EventType.LOCK_ACQUIRE);
		System.out.println(proc.L1cache);
	}

	@Test
	public void testWriteReadNoConflict() {
		// Processor<ViserLine> proc0 = machine.getProc(P0);

		machine.testCacheMemoryWrite(P0, 80L, 2, 80, T0);
		machine.testCacheMemoryWrite(P0, 64L, 2, 64, T0);
		machine.testCacheMemoryWrite(P0, 96L, 2, 96, T0);
		machine.testCacheMemoryWrite(P0, 112L, 2, 112, T0);
		// System.out.println(proc0.L1cache);

		machine.testCacheMemoryWrite(P0, 128L, 2, 128, T0);

		// machine.dumpMachineMemory();

		machine.testProcessRegionBoundary(P0, T0, EventType.LOCK_ACQUIRE);

		machine.testCacheMemoryRead(P0, 80L, 2, 3, T0);
		// System.out.println(proc0.L1cache);
	}

	@Test
	public void testLLCHit() {
		Processor<ViserLine> proc = machine.getProc(P0);

		// bring 0d into the cache
		machine.testCacheMemoryRead(P0, 0, 1, 20, T0);
		assertEquals(1, proc.stats.pc_l1d.pc_ReadMisses.get(), 0);
		// System.out.println(proc.L1cache);

		// fetch 16d and 32d which map to set 0; this evicts 0d to the L3
		for (int i = 1; i <= L1_ASSOC; i++) {
			machine.testCacheMemoryRead(P0, L1_CACHE_SIZE * i, 1, i, T0);
			assertEquals(1 + i, proc.stats.pc_l1d.pc_ReadMisses.get(), 0);
		}
		System.out.println(proc.L1cache);
		System.out.println(proc.L3cache.getLine((new DataByteAddress(0L)).lineAddress())
				.getPerCoreMetadata(P0));

		// fetch 0d again, from the L3. This is a hit.
		machine.testCacheMemoryRead(P0, 2, 1, 10, T0);
		assertEquals(1, proc.stats.pc_l3d.pc_ReadHits.get(), 0);
		System.out.println(proc.L1cache);
	}

	@Test
	public void testCrossLineRead() {
		Processor<ViserLine> proc = machine.getProc(P0);

		// this crosses a line boundary
		machine.testCacheMemoryRead(P0, 0, 8, 0, T0);
		assertEquals(0, proc.stats.pc_l1d.pc_ReadHits.get(), 0);
		assertEquals(2, proc.stats.pc_l1d.pc_ReadMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l1d.pc_LineEvictions.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_ReadHits.get(), 0);
		assertEquals(2, proc.stats.pc_l3d.pc_ReadMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_LineEvictions.get(), 0);
		System.out.println(proc.L1cache);

		machine.testCacheMemoryRead(P0, 8, 4, 0, T0);
		assertEquals(0, proc.stats.pc_l1d.pc_ReadHits.get(), 0);
		assertEquals(3, proc.stats.pc_l1d.pc_ReadMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l1d.pc_LineEvictions.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_ReadHits.get(), 0);
		assertEquals(3, proc.stats.pc_l3d.pc_ReadMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_LineEvictions.get(), 0);
		System.out.println(proc.L1cache);

		machine.testCacheMemoryRead(P0, 2, 2, 0, T0);
		assertEquals(1, proc.stats.pc_l1d.pc_ReadHits.get(), 0);
		assertEquals(3, proc.stats.pc_l1d.pc_ReadMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l1d.pc_LineEvictions.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_ReadHits.get(), 0);
		assertEquals(3, proc.stats.pc_l3d.pc_ReadMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_LineEvictions.get(), 0);
		System.out.println(proc.L1cache);

		machine.testCacheMemoryRead(P0, 6, 4, 0, T0);
		assertEquals(3, proc.stats.pc_l1d.pc_ReadHits.get(), 0);
		assertEquals(3, proc.stats.pc_l1d.pc_ReadMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l1d.pc_LineEvictions.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_ReadHits.get(), 0);
		assertEquals(3, proc.stats.pc_l3d.pc_ReadMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_LineEvictions.get(), 0);
		System.out.println(proc.L1cache);
	}

	@Test
	public void testCrossLineWrite() {
		Processor<ViserLine> proc = machine.getProc(P0);

		// this crosses a data line boundary, so it definitely crosses a md line boundary
		machine.testCacheMemoryWrite(P0, 0, 8, 0, T0);
		assertEquals(0, proc.stats.pc_l1d.pc_WriteHits.get(), 0);
		assertEquals(2, proc.stats.pc_l1d.pc_WriteMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l1d.pc_LineEvictions.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_WriteHits.get(), 0);
		assertEquals(2, proc.stats.pc_l3d.pc_WriteMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_LineEvictions.get(), 0);
		System.out.println(proc.L1cache);

		machine.testCacheMemoryWrite(P0, 8, 4, 0, T0);
		assertEquals(0, proc.stats.pc_l1d.pc_WriteHits.get(), 0);
		assertEquals(3, proc.stats.pc_l1d.pc_WriteMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l1d.pc_LineEvictions.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_WriteHits.get(), 0);
		assertEquals(3, proc.stats.pc_l3d.pc_WriteMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_LineEvictions.get(), 0);
		System.out.println(proc.L1cache);

		machine.testCacheMemoryWrite(P0, 2, 2, 0, T0);
		assertEquals(1, proc.stats.pc_l1d.pc_WriteHits.get(), 0);
		assertEquals(3, proc.stats.pc_l1d.pc_WriteMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l1d.pc_LineEvictions.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_WriteHits.get(), 0);
		assertEquals(3, proc.stats.pc_l3d.pc_WriteMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_LineEvictions.get(), 0);
		System.out.println(proc.L1cache);

		machine.testCacheMemoryWrite(P0, 6, 4, 0, T0);
		assertEquals(3, proc.stats.pc_l1d.pc_WriteHits.get(), 0);
		assertEquals(3, proc.stats.pc_l1d.pc_WriteMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l1d.pc_LineEvictions.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_WriteHits.get(), 0);
		assertEquals(3, proc.stats.pc_l3d.pc_WriteMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_LineEvictions.get(), 0);
		System.out.println(proc.L1cache);
	}

	@Test
	public void testReadWrite() {
		Processor<ViserLine> proc = machine.getProc(P0);

		machine.testCacheMemoryRead(P0, 4, 2, 0, T0);
		assertEquals(0, proc.stats.pc_l1d.pc_ReadHits.get(), 0);
		assertEquals(1, proc.stats.pc_l1d.pc_ReadMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l1d.pc_LineEvictions.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_ReadHits.get(), 0);
		assertEquals(1, proc.stats.pc_l3d.pc_ReadMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_LineEvictions.get(), 0);
		System.out.println(proc.L1cache);

		// This is a hit in the private cache
		machine.testCacheMemoryWrite(P0, 4, 2, 0, T0);
		assertEquals(1, proc.stats.pc_l1d.pc_WriteHits.get(), 0);
		assertEquals(0, proc.stats.pc_l1d.pc_WriteMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l1d.pc_LineEvictions.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_WriteHits.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_WriteMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_LineEvictions.get(), 0);
		System.out.println(proc.L1cache);
	}

	@Test
	public void testEviction() {
		Processor<ViserLine> proc = machine.getProc(P0);

		machine.testCacheMemoryRead(P0, 48, 1, 1, T0);
		machine.testCacheMemoryRead(P0, 12, 2, 2, T0);
		assertEquals(2, proc.stats.pc_l1d.pc_ReadMisses.get(), 0);
		assertEquals(2, proc.stats.pc_l3d.pc_ReadMisses.get(), 0);
		// System.out.println(proc.L1cache);
		// 48L and 12L are in different L3 sets, but they are in the same L1, L2, and AIM sets

		machine.testCacheMemoryRead(P0, 28, 2, 3, T0);
		assertEquals(3, proc.stats.pc_l1d.pc_ReadMisses.get(), 0);
		assertEquals(3, proc.stats.pc_l2d.pc_ReadMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l2d.pc_LineEvictions.get(), 0);
		assertEquals(3, proc.stats.pc_l3d.pc_ReadMisses.get(), 0);
		// System.out.println(proc.L1cache);

		machine.testCacheMemoryRead(P0, 60, 2, 4, T0);
		assertEquals(4, proc.stats.pc_l1d.pc_ReadMisses.get(), 0);
		assertEquals(4, proc.stats.pc_l2d.pc_ReadMisses.get(), 0);
		assertEquals(1, proc.stats.pc_l2d.pc_LineEvictions.get(), 0);
		assertEquals(4, proc.stats.pc_l3d.pc_ReadMisses.get(), 0);
		// System.out.println(proc.L1cache);

		machine.testCacheMemoryRead(P0, 76, 2, 0, T0);
		assertEquals(5, proc.stats.pc_l1d.pc_ReadMisses.get(), 0);
		assertEquals(5, proc.stats.pc_l2d.pc_ReadMisses.get(), 0);
		assertEquals(2, proc.stats.pc_l2d.pc_LineEvictions.get(), 0);
		assertEquals(5, proc.stats.pc_l3d.pc_ReadMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_LineEvictions.get(), 0);
		System.out.println(proc.L1cache);

		// machine.dumpMachineMemory();
	}

	@Test
	public void testReadWriteEviction() {
		Processor<ViserLine> proc = machine.getProc(P0);

		machine.testCacheMemoryRead(P0, 64, 2, 0, T0);
		assertEquals(0, proc.stats.pc_l1d.pc_ReadHits.get(), 0);
		assertEquals(1, proc.stats.pc_l1d.pc_ReadMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l1d.pc_LineEvictions.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_ReadHits.get(), 0);
		assertEquals(1, proc.stats.pc_l3d.pc_ReadMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_LineEvictions.get(), 0);

		machine.testCacheMemoryRead(P0, 80, 2, 0, T0);
		assertEquals(0, proc.stats.pc_l1d.pc_ReadHits.get(), 0);
		assertEquals(2, proc.stats.pc_l1d.pc_ReadMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l1d.pc_LineEvictions.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_ReadHits.get(), 0);
		assertEquals(2, proc.stats.pc_l3d.pc_ReadMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_LineEvictions.get(), 0);

		machine.testCacheMemoryWrite(P0, 64, 2, 0, T0);
		assertEquals(1, proc.stats.pc_l1d.pc_WriteHits.get(), 0);
		assertEquals(0, proc.stats.pc_l1d.pc_WriteMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l1d.pc_LineEvictions.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_WriteHits.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_WriteMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_LineEvictions.get(), 0);

		machine.testCacheMemoryRead(P0, 96, 2, 0, T0);
		assertEquals(0, proc.stats.pc_l1d.pc_ReadHits.get(), 0);
		assertEquals(3, proc.stats.pc_l1d.pc_ReadMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l1d.pc_LineEvictions.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_ReadHits.get(), 0);
		assertEquals(3, proc.stats.pc_l3d.pc_ReadMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_LineEvictions.get(), 0);

		machine.testCacheMemoryRead(P0, 112, 2, 0, T0);
		assertEquals(0, proc.stats.pc_l1d.pc_ReadHits.get(), 0);
		assertEquals(4, proc.stats.pc_l1d.pc_ReadMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l1d.pc_LineEvictions.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_ReadHits.get(), 0);
		assertEquals(4, proc.stats.pc_l3d.pc_ReadMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_LineEvictions.get(), 0);

		machine.testCacheMemoryWrite(P0, 128, 2, 0, T0);
		assertEquals(1, proc.stats.pc_l1d.pc_WriteHits.get(), 0);
		assertEquals(1, proc.stats.pc_l1d.pc_WriteMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l1d.pc_LineEvictions.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_WriteHits.get(), 0);
		assertEquals(1, proc.stats.pc_l3d.pc_WriteMisses.get(), 0);
		assertEquals(1, proc.stats.pc_l3d.pc_LineEvictions.get(), 0);

		machine.testCacheMemoryWrite(P0, 80, 2, 0, T0); // Should be a LLC miss
		assertEquals(1, proc.stats.pc_l1d.pc_WriteHits.get(), 0);
		assertEquals(2, proc.stats.pc_l1d.pc_WriteMisses.get(), 0);
		assertEquals(0, proc.stats.pc_l1d.pc_LineEvictions.get(), 0);
		assertEquals(0, proc.stats.pc_l3d.pc_WriteHits.get(), 0);
		assertEquals(2, proc.stats.pc_l3d.pc_WriteMisses.get(), 0);
		assertEquals(2, proc.stats.pc_l3d.pc_LineEvictions.get(), 0);
	}

	@Test
	public void testCleanup() {
		Processor<ViserLine> proc = machine.getProc(P0);

		machine.testCacheMemoryWrite(P0, 80L, 2, 6, T0);
		machine.testCacheMemoryWrite(P0, 64L, 2, 23, T0);
		System.out.println(proc.L1cache);

		machine.testProcessRegionBoundary(P0, T0, EventType.LOCK_ACQUIRE);
		System.out.println(proc.L1cache);

		machine.testCacheMemoryWrite(P0, 64L, 2, 25, T0);
		machine.testCacheMemoryWrite(P0, 80L, 2, 7, T0);
		System.out.println(proc.L1cache);
	}

	@Test
	public void testValidation() {
		Processor<ViserLine> proc = machine.getProc(P0);

		machine.testCacheMemoryRead(P0, 80L, 2, 6, T0);
		machine.testCacheMemoryWrite(P0, 64L, 2, 23, T0);
		System.out.println(proc.L1cache);

		machine.testProcessRegionBoundary(P0, T0, EventType.LOCK_ACQUIRE);
		// assertEquals(0, proc.stats.pc_FailedVersionChecks.get());
		System.out.println(proc.L1cache);
	}

	@Test
	public void testAccessEncoding() {
		Processor<ViserLine> proc = machine.getProc(P0);
		DataByteAddress dba = new DataByteAddress(40L);
		long enc = proc.getEncodingForAccess(
				new DataAccess(MemoryAccessType.MEMORY_READ, dba, 1, 0, P0, T0, -1, -1));
		assertEquals(enc, 1);
		enc = proc.getEncodingForAccess(
				new DataAccess(MemoryAccessType.MEMORY_READ, dba, 2, 0, P0, T0, -1, -1));
		assertEquals(enc, 3);
		enc = proc.getEncodingForAccess(
				new DataAccess(MemoryAccessType.MEMORY_READ, dba, 3, 0, P0, T0, -1, -1));
		assertEquals(enc, 7);
		enc = proc.getEncodingForAccess(
				new DataAccess(MemoryAccessType.MEMORY_READ, dba, 4, 0, P0, T0, -1, -1));
		assertEquals(enc, 15);
	}

	@Test
	public void testBitCount() {
		assertEquals(0, Long.bitCount(0L));
		assertEquals(1, Long.bitCount(1L));
		assertEquals(1, Long.bitCount(2L));
		assertEquals(1, Long.bitCount(16L));
		assertEquals(3, Long.bitCount(7L));
		assertEquals(4, Long.bitCount(15L));
	}

	@Test
	public void testDirtyBit() {
		Processor<ViserLine> proc = machine.getProc(P0);
		machine.testCacheMemoryWrite(P0, 64L, 2, 64, T0);
		machine.testCacheMemoryWrite(P0, 80L, 2, 80, T0);
		machine.testCacheMemoryWrite(P0, 96L, 2, 96, T0);
		machine.testCacheMemoryWrite(P0, 112L, 2, 112, T0);
		machine.testCacheMemoryWrite(P0, 128L, 2, 128, T0);
		System.out.println(proc.L1cache);
		machine.dumpMachineMemory();
	}

	@Test
	public void testTentativeInvalidState() {
		Processor<ViserLine> proc = machine.getProc(P0);
		machine.testCacheMemoryWrite(P0, 64L, 2, 64, T0);
		machine.testProcessRegionBoundary(P0, T0, EventType.LOCK_ACQUIRE);
		System.out.println(proc.L1cache);
		machine.testProcessRegionBoundary(P0, T0, EventType.LOCK_RELEASE);
		System.out.println(proc.L1cache);
		machine.testCacheMemoryRead(P0, 64L, 2, 64, T0);
		assertEquals(1, proc.stats.pc_l1d.pc_ReadHits.get(), 0);
	}

	@Test
	public void testBloomFilter() {
		Processor<ViserLine> proc = machine.getProc(P0);
		machine.testCacheMemoryWrite(P0, 64L, 2, 64, T0);
		machine.testCacheMemoryWrite(P0, 80L, 2, 80, T0);
		machine.testCacheMemoryWrite(P0, 96L, 2, 96, T0);
		machine.testCacheMemoryWrite(P0, 112L, 2, 96, T0);
		System.out.println(proc.bf);
		machine.testProcessRegionBoundary(P0, T0, EventType.LOCK_RELEASE);
		System.out.println(proc.bf);
	}

	@Test
	public void testNumFlits() {
		Processor<ViserLine> proc = machine.getProc(P0);

		proc.updateTrafficForOneNetworkMessage(1, SystemConstants.BLOOM_FILTER_LLC_MESSAGE,
				ExecutionPhase.REGION_BODY);
		// proc.updateFlitsCountForOneNetworkMessage(MemorySystemConstants.BLOOM_FILTER_LLC_MESSAGE);

		assertEquals(4, proc.stats.pc_OnChipNetworkMessageSize4BytesFlits.get(), 0);
		assertEquals(2, proc.stats.pc_OnChipNetworkMessageSize8BytesFlits.get(), 0);
		assertEquals(1, proc.stats.pc_OnChipNetworkMessageSize16BytesFlits.get(), 0);
		assertEquals(1, proc.stats.pc_OnChipNetworkMessageSize32BytesFlits.get(), 0);
	}

	@Test
	public void testClearingOfReadMetadata() {
		Processor<ViserLine> proc = machine.getProc(P0);
		machine.testCacheMemoryRead(P0, 64L, 2, 64, T0);
		machine.testCacheMemoryWrite(P0, 64L, 2, 64, T0);
		ViserLine l1Line = proc.L1cache.getLine(new DataLineAddress(64L));
		assertEquals(3, l1Line.getReadEncoding(P0));
		assertEquals(3, l1Line.getWriteEncoding(P0));

		machine.testCacheMemoryRead(P0, 80L, 2, 80, T0);
		machine.testCacheMemoryRead(P0, 96L, 2, 96, T0);
		// This will evict 64L to the LLC, dirty bit must be set

		ViserLine l3Line = proc.L3cache.getLine(new DataLineAddress(64L));
		assertEquals(true, l3Line.dirty());
		assertEquals(0, l3Line.getReadEncoding(P0));
		assertEquals(3, l3Line.getWriteEncoding(P0));
	}

	/**
	 * Test that the owner core is properly set, and that the LLC fetches the updated values during
	 * eviction.
	 */
	@Test
	public void testDeferWriteBack() {
		Processor<ViserLine> proc = machine.getProc(P0);
		machine.testCacheMemoryWrite(P0, 64L, 2, 640, T0);
		machine.testProcessRegionBoundary(P0, T0, EventType.LOCK_RELEASE);
		machine.testCacheMemoryRead(P0, 80L, 2, 80, T0);
		machine.testCacheMemoryRead(P0, 96L, 2, 96, T0);
		// There is no eviction from L1, since L2 actually recalls the L1 line
		assertEquals(1, proc.stats.pc_l2d.pc_LineEvictions.get(), 0);
		System.out.println(proc.L1cache);
	}

	@Test
	public void testLockAccesses1() {
		Processor<ViserLine> proc = machine.getProc(P0);
		machine.cacheRead(P0, 80L, 2, 11, T0, 0, 0, MemoryAccessType.LOCK_ACQ_READ);
		// System.out.println(proc.L1cache);

		machine.cacheWrite(P0, 80L, 2, 11, T0, 0, 0, MemoryAccessType.LOCK_ACQ_WRITE);
		System.out.println(proc.L1cache);
		assertEquals(3, proc.stats.pc_OnChipNetworkMessages.get(), 0);

		machine.cacheWrite(P0, 80L, 2, 11, T0, 0, 0, MemoryAccessType.LOCK_REL_WRITE);
		System.out.println(proc.L1cache);
		assertEquals(3, proc.stats.pc_OnChipNetworkMessages.get(), 0);
	}

	@Test
	public void testLockAccesses2() {
		Processor<ViserLine> proc = machine.getProc(P0);
		machine.cacheRead(P0, 80L, 2, 11, T0, 0, 0, MemoryAccessType.LOCK_ACQ_READ);
		machine.cacheWrite(P0, 80L, 2, 11, T0, 0, 0, MemoryAccessType.LOCK_ACQ_WRITE);
		assertEquals(3, proc.stats.pc_OnChipNetworkMessages.get(), 0);

		// Evict the lock line
		machine.testCacheMemoryWrite(P0, 64L, 2, 640, T0);
		assertEquals(6, proc.stats.pc_OnChipNetworkMessages.get(), 0);
		machine.testCacheMemoryRead(P0, 96L, 2, 96, T0);
		assertEquals(10, proc.stats.pc_OnChipNetworkMessages.get(), 0);

		machine.cacheWrite(P0, 80L, 2, 11, T0, 0, 0, MemoryAccessType.LOCK_REL_WRITE);
		// There is actually no need to evict 64L
		assertEquals(11, proc.stats.pc_OnChipNetworkMessages.get(), 0);
	}

	// IMP: AIM associativity is 2 and # lines is 16, and set useAIMCache() to true
	@Test
	public void testMemoryAccesses1() {
		Processor<ViserLine> proc = machine.getProc(P0);

		machine.testCacheMemoryRead(P0, 80L, 2, 11, T0);
		assertEquals(0, proc.stats.pc_aim.pc_ReadMisses.get(), 0);

		machine.testCacheMemoryWrite(P0, 80L, 2, 11, T0);
		assertEquals(0, proc.stats.pc_aim.pc_WriteMisses.get(), 0);

		machine.testCacheMemoryWrite(P0, 64L, 2, 11, T0);
		assertEquals(0, proc.stats.pc_aim.pc_WriteMisses.get(), 0);

		machine.testCacheMemoryWrite(P0, 96L, 2, 11, T0);
		// System.out.println(proc.L1cache);
		// This causes 80L to be evicted from AIM but is not counted since it has no metadata. 80L
		// is then evicted from private cache, not evicted from the L3 yet since L3's associativity
		// is four. That causes 64L to be evicted from AIM but that also has no metadata. So the AIM
		// now contains 96L and 80L.
		assertEquals(0, proc.stats.pc_aim.pc_LineEvictions.get(), 0);
		assertEquals(0, proc.stats.pc_aim.pc_WriteMisses.get(), 0);

		machine.testCacheMemoryWrite(P0, 112L, 2, 0, T0);
		// System.out.println(proc.L1cache);
		assertEquals(0, proc.stats.pc_aim.pc_ReadMisses.get(), 0);
		// 112L fits in an L3 set, so a NULL line is evicted from LLC. Private caches
		// evict 64L which causes 96L to evict from the AIM, but 96L has no metadata yet.
		assertEquals(1, proc.stats.pc_aim.pc_WriteMisses.get(), 0);
		assertEquals(0, proc.stats.pc_aim.pc_LineEvictions.get(), 0);

		// Now both the AIM lines 64L and 80L have valid metadata.

		// Read another line to cause AIM eviction of 64L
		machine.testCacheMemoryRead(P0, 48L, 2, 55, T0);
		assertEquals(1, proc.stats.pc_aim.pc_LineEvictions.get(), 0);
		// +3 for fetching new line and +2 for eviction
		System.out.println(proc.L1cache);

		machine.testCacheMemoryRead(P0, 96L, 2, 3, T0);
		System.out.println(proc.L1cache);
		assertEquals(2, proc.stats.pc_aim.pc_LineEvictions.get(), 0);
	}

	// IMP: AIM associativity is 2 and # lines is 16, and set useAIMCache() to true
	@Test
	public void testAIMAccesses1() {
		Processor<ViserLine> proc = machine.getProc(P0);

		machine.cacheRead(P0, 80L, 2, 11, T0, 0, 0, MemoryAccessType.MEMORY_READ);
		// A LLC miss means we should fetch the line into the AIM.
		assertEquals(0, proc.stats.pc_aim.pc_ReadMisses.get(), 0);

		machine.cacheWrite(P0, 96L, 2, 11, T0, 0, 0, MemoryAccessType.MEMORY_WRITE);
		assertEquals(0, proc.stats.pc_aim.pc_WriteMisses.get(), 0);

		machine.cacheWrite(P0, 64L, 2, 1, T0, 0, 0, MemoryAccessType.MEMORY_WRITE);
		// 96L is evicted from AIM, but it does not have metadata
		assertEquals(0, proc.stats.pc_aim.pc_WriteMisses.get(), 0);
		machine.cacheRead(P0, 112L, 2, 9, T0, 0, 0, MemoryAccessType.MEMORY_READ);
		// 64L is evicted from private cache and is in the AIM.
		assertEquals(0, proc.stats.pc_aim.pc_ReadMisses.get(), 0);
	}

	/**
	 * The lines to be validated at region end are already present in the LLC/AIM. IMP: AIM
	 * associativity is 2 and # lines is 16, and set useAIMCache() to true
	 */
	@Test
	public void testMemoryAccessesAtRegionEnd1() {
		// Processor<ViserLine> proc = machine.getProc(P0);

		machine.testCacheMemoryWrite(P0, 80L, 2, 6, T0);
		machine.testCacheMemoryWrite(P0, 64L, 2, 23, T0);

		machine.testProcessRegionBoundary(P0, T0, EventType.LOCK_ACQUIRE);
	}

	/**
	 * The lines to be validated at region end have been evicted from the AIM, since it is smaller
	 * than the LLC.
	 */
	@Test
	public void testMemoryAccessesAtRegionEnd2() {
		Processor<ViserLine> proc = machine.getProc(P0);

		machine.testCacheMemoryWrite(P0, 80L, 2, 6, T0);
		machine.testCacheMemoryWrite(P0, 64L, 2, 23, T0);

		machine.testCacheMemoryWrite(P0, 96L, 2, 6, T0);
		machine.testCacheMemoryWrite(P0, 112L, 2, 23, T0);
		machine.testCacheMemoryWrite(P0, 128L, 2, 23, T0);
		// +3 for data line and +2 for AIM line eviction

		System.out.println(proc.L1cache);

		machine.testProcessRegionBoundary(P0, T0, EventType.LOCK_ACQUIRE);
		// This is not correct since the evicted lines are no longer in the private cache as well
		// assertEquals(20, proc.stats.pc_Memory64BytesAccesses.get(), 0);
	}

	// IMP: AIM associativity is 2 and # lines is 16, and set useAIMCache() to true
	@Test
	public void testAIM1() {
		Processor<ViserLine> proc = machine.getProc(P0);

		machine.testCacheMemoryRead(P0, 80L, 2, 0, T0);
		// A LLC miss means we should fetch the line into the AIM. But an LLC miss is not an AIM
		// miss if it does not have metadata.
		assertFalse(proc.aimcache.junitGetLine(proc, new DataLineAddress(80L)).hasAIMMD());
		assertEquals(0, proc.stats.pc_aim.pc_ReadMisses.get(), 0);

		machine.testCacheMemoryWrite(P0, 80L, 2, 0, T0); // LLC hit
		assertEquals(0, proc.stats.pc_aim.pc_WriteMisses.get(), 0);

		machine.testCacheMemoryWrite(P0, 96L, 2, 0, T0);
		assertEquals(0, proc.stats.pc_aim.pc_WriteMisses.get(), 0);

		machine.testCacheMemoryRead(P0, 112L, 2, 0, T0);
		assertEquals(0, proc.stats.pc_aim.pc_ReadMisses.get(), 0);
		// Evicts 96L from AIM, then private caches evict 80L, which is written back to the AIM
		// evicting 96L. Both do not have metadata.
		assertEquals(0, proc.stats.pc_aim.pc_LineEvictions.get(), 0);
		// +1 for fetch request, +2 for incoming data + metadata, +1 for first AIM eviction, +1 for
		// second AIM eviction
		assertEquals(0, proc.stats.pc_aim.pc_WriteMisses.get(), 0);
		assertTrue(proc.aimcache.junitGetLine(proc, new DataLineAddress(80L)).hasAIMMD());
		assertFalse(proc.aimcache.junitGetLine(proc, new DataLineAddress(112L)).hasAIMMD());

		machine.testCacheMemoryRead(P0, 80L, 2, 0, T0); // This should be a LLC hit and an AIM hit
		assertEquals(0, proc.stats.pc_aim.pc_ReadMisses.get(), 0);
		assertEquals(0, proc.stats.pc_aim.pc_LineEvictions.get(), 0);
		// 96L is evicted from the private caches to the AIM, so the AIM line should now have valid
		// metadata
		assertTrue(proc.aimcache.junitGetLine(proc, new DataLineAddress(96L)).hasAIMMD());

		machine.testCacheMemoryRead(P0, 128L, 2, 0, T0);
		// System.out.println(proc.L1cache);
		// 96L is not evicted from AIM as 128L is going to a different set. 112L will be evicted
		// from private caches and will cause 80L to evict from AIM.
		assertEquals(0, proc.stats.pc_aim.pc_ReadMisses.get(), 0);
		assertEquals(1, proc.stats.pc_aim.pc_LineEvictions.get(), 0);
		// +1 for fetching, +2 for data + metadata, +1 to request metadata for 112L and +1 for
		// return metadata of 112L. We are ignoring the cost of 96L. Check with ARC.
		// 112L misses in the AIM
		assertEquals(2, proc.stats.pc_aim.pc_WriteMisses.get(), 0);
		assertTrue(proc.aimcache.junitGetLine(proc, new DataLineAddress(96L)).hasAIMMD());
		assertTrue(proc.aimcache.junitGetLine(proc, new DataLineAddress(112L)).hasAIMMD());
		assertFalse(proc.aimcache.junitGetLine(proc, new DataLineAddress(128L)).hasAIMMD());
		// System.out.println(proc.L1cache);

		machine.testCacheMemoryWrite(P0, 64L, 2, 0, T0);
		// 96L is evicted from AIM while fetching 64L in the LLC. Then 80L is evicted from private
		// caches. It evicts 64L from the AIM since it has no metadata.
		// System.out.println(proc.L1cache);
		assertEquals(3, proc.stats.pc_aim.pc_WriteMisses.get(), 0);
		assertEquals(2, proc.stats.pc_aim.pc_LineEvictions.get(), 0);
		// +1 for fetch, +2 for data + metadata, +2 for evicting data and metadata of 80L, +1 for
		// metadata of 64L
	}

	// IMP: AIM associativity is 2 and # lines is 16, and set useAIMCache() to true
	@Test
	public void testAIM2() {
		Processor<ViserLine> proc = machine.getProc(P0);

		machine.testCacheMemoryRead(P0, 80L, 2, 0, T0);
		// A LLC miss means we should fetch the line into the AIM. But an LLC miss is not an AIM
		// miss if it does not have metadata.
		assertFalse(proc.aimcache.junitGetLine(proc, new DataLineAddress(80L)).hasAIMMD());
		machine.testCacheMemoryRead(P0, 96L, 2, 0, T0);
		machine.testCacheMemoryRead(P0, 64L, 2, 0, T0);
		assertTrue(proc.aimcache.junitGetLine(proc, new DataLineAddress(80L)).hasAIMMD());
		machine.testCacheMemoryRead(P0, 112L, 2, 0, T0);

		// Evict 80L from LLC
		machine.testCacheMemoryRead(P0, 128L, 2, 0, T0);
		assertEquals(1, proc.stats.pc_l3d.pc_LineEvictions.get(), 0);
		assertEquals(0, proc.stats.pc_aim.pc_ReadMisses.get(), 0);

		// Now bring in 80L from memory. The AIM md bit in the LLC line should be set. Since
		// the md bit is set, so therefore this is an AIM miss.
		machine.testCacheMemoryRead(P0, 80L, 2, 0, T0);
		assertTrue(proc.aimcache.junitGetLine(proc, new DataLineAddress(80L)).hasAIMMD());
		assertEquals(1, proc.stats.pc_aim.pc_ReadMisses.get(), 0);
	}

	// IMP: AIM associativity is 2 and # lines is 16, and set useAIMCache() to true
	@Test
	public void testAIM3() {
		Processor<ViserLine> proc = machine.getProc(P0);

		machine.testCacheMemoryRead(P0, 80L, 2, 0, T0);
		machine.testCacheMemoryRead(P0, 64L, 2, 0, T0);
		machine.testCacheMemoryRead(P0, 96L, 2, 0, T0);
		machine.testCacheMemoryRead(P0, 48L, 2, 0, T0);

		// Evict 80L from L3 and AIM
		machine.testCacheMemoryRead(P0, 112L, 2, 0, T0);
		assertEquals(1, proc.stats.pc_aim.pc_LineEvictions.get(), 0);
		assertTrue(proc.aimcache.junitGetLine(proc, new DataLineAddress(96L)).hasAIMMD());
		assertTrue(proc.aimcache.junitGetLine(proc, new DataLineAddress(64L)).hasAIMMD());
		assertFalse(proc.aimcache.junitGetLine(proc, new DataLineAddress(48L)).hasAIMMD());

		// Bring in 80L from memory. AIM MD bit should be set.
		machine.testCacheMemoryWrite(P0, 80L, 2, 0, T0);
		assertTrue(proc.aimcache.junitGetLine(proc, new DataLineAddress(80L)).hasAIMMD());
	}

	// IMP: AIM associativity is 2 and # lines is 16, and set useAIMCache() to true
	@Test
	public void testAIM4() {
		Processor<ViserLine> proc = machine.getProc(P0);

		machine.testCacheMemoryRead(P0, 80L, 2, 0, T0);
		machine.testCacheMemoryRead(P0, 64L, 2, 0, T0);
		machine.testCacheMemoryRead(P0, 96L, 2, 0, T0);
		machine.testCacheMemoryRead(P0, 48L, 2, 0, T0);

		// Evict 80L from L3 and AIM
		machine.testCacheMemoryRead(P0, 112L, 2, 0, T0);
		assertEquals(1, proc.stats.pc_aim.pc_LineEvictions.get(), 0);
		assertTrue(proc.aimcache.junitGetLine(proc, new DataLineAddress(96L)).hasAIMMD());
		assertTrue(proc.aimcache.junitGetLine(proc, new DataLineAddress(64L)).hasAIMMD());
		assertFalse(proc.aimcache.junitGetLine(proc, new DataLineAddress(48L)).hasAIMMD());

		machine.testProcessRegionBoundary(P0, T0, EventType.LOCK_ACQUIRE);

		// Bring in 80L from memory. AIM MD bit should be set.
		machine.testCacheMemoryWrite(P0, 80L, 2, 0, T0);
		assertFalse(proc.aimcache.junitGetLine(proc, new DataLineAddress(80L)).hasAIMMD());
	}

}
