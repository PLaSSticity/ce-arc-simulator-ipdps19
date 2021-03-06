package simulator.viser;

import java.util.ArrayList;
import java.util.Deque;
import java.util.Iterator;
import java.util.LinkedList;
import java.util.List;

import simulator.viser.Processor.ExecutionPhase;

class AIMResponse<Line extends ViserLine> {
	/** The level of the cache hierarchy where the hit occurred */
	public CacheLevel whereHit;

	@Override
	public String toString() {
		return whereHit.toString();
	}
}

// This class just simulates an AIM cache structure, without actually storing the values. It would
// require 132 bytes to actually store all the metadata for 8 cores + 4 bytes version. Instead we
// just want to model the hit/miss ratio, so we store tags.
public final class AIMCache<Line extends ViserLine> {
	private final int assoc = 4; // XXX: Might need to change this for JUnit test cases
	// this corresponds to the data line size, and not the actual capacity that
	// should also include the metadata
	private final int lineSize = 64;
	private final int numLines; // Total lines (set * assoc)

	private int numSets;
	/** log_2(line size) */
	private short lineOffsetBits;
	/** mask used to clear out the tag bits */
	private long indexMask;

	List<Deque<Line>> sets;
	private LineFactory<Line> lineFactory;

	private CacheLevel levelInHierarchy = CacheLevel.L3;

	public HierarchicalCache<Line> l3cache;
	public Processor<Line> processor;

	/** Return the cache index for the given address */
	protected int index(long address) {
		return (int) ((address >> lineOffsetBits) & indexMask);
	}

	public AIMCache(HierarchicalCache<Line> llc, LineFactory<Line> factory,
			Processor<Line> processor) {
		assert BitTwiddle.isPowerOf2(assoc);
		assert BitTwiddle.isPowerOf2(lineSize);

		this.l3cache = llc;
		this.lineFactory = factory;
		this.processor = processor;

		this.numLines = ViserSim.Options.valueOf(Knobs.NumAIMLines);
		this.numSets = numLines / assoc;
		assert BitTwiddle.isPowerOf2(numSets);

		indexMask = numSets - 1;
		lineOffsetBits = (short) BitTwiddle.floorLog2(lineSize);

		sets = new ArrayList<Deque<Line>>(numSets);

		for (int i = 0; i < numSets; i++) {
			Deque<Line> set = new LinkedList<Line>();
			for (int j = 0; j < assoc; j++) {
				// the processor is always P0.
				assert this.processor.id.get() == 0;
				Line line = lineFactory.create(this.processor, this.levelInHierarchy);
				set.add(line);
			}
			sets.add(set);
		}
	}

	private int getAIMLineSize(Processor<Line> proc) {
		int lineSize = 0;
		switch (proc.params.numProcessors()) {
			case 1: { // Primarily for unit tests
				lineSize = 20;
				break;
			}
			case 2: { // Primarily for unit tests
				lineSize = 36;
				break;
			}
			case 4: {
				lineSize = 60;
				break;
			}
			case 8: {
				lineSize = 100;
				break;
			}
			case 16: {
				lineSize = 172;
				break;
			}
			case 32: {
				lineSize = 308;
				break;
			}
			default: {
				throw new RuntimeException("Unknown number of cores");
			}
		}
		return lineSize;
	}

	/**
	 * Just get the corresponding line. The check for presence of metadata is already performed in
	 * the caller.
	 */
	// This method should not be there. It should be replaced by request().
	// SB: I think this is overaccounting. The method should actually be replaced by request()
	public Line getLine(Processor<Line> proc, Line line, boolean read) {
		Deque<Line> set = sets.get(index(line.lineAddress().get()));
		// search this cache
		for (Iterator<Line> it = set.iterator(); it.hasNext();) {
			Line l = it.next();
			if (l.lineAddress() != null) {
				if (l.lineAddress().equals(line.lineAddress())) {
					assert l.id().equals(processor.id);
					assert !l.isPrivateCacheLine();
					// if (read) {
					// proc.stats.pc_aim.pc_ReadHits.incr();
					// } else {
					// proc.stats.pc_aim.pc_WriteHits.incr();
					// }
					return l;
				}
			}
		}

		// if (read) {
		// proc.stats.pc_aim.pc_ReadMisses.incr();
		// } else {
		// proc.stats.pc_aim.pc_WriteMisses.incr();
		// }
		return null;
	}

	/**
	 * This is just for lookup. This does not bring in or evict lines, and neither does it add
	 * costs. This method is specialized to avoid duplicate accounting.
	 */
	private MemoryResponse<Line> getLineFromLLCOrMemoryAIM(Processor<Line> proc, Line l,
			boolean read) {
		assert l.valid();
		MemoryResponse<Line> resp = new MemoryResponse<Line>();

		// Get the corresponding line from memory or LLC
		Line llcLine = proc.L3cache.getLine(l);
		if (llcLine == null) { // Line not in LLC, get from memory
			llcLine = proc.machine.memory.get(l.lineAddress().get());
			assert !llcLine.isLineDeferred();
			resp.whereHit = CacheLevel.MEMORY;
		} else {
			resp.whereHit = CacheLevel.L3;
		}

		// We should not call aimcache.getLine(this, l, read) from here, since AIMCache request()
		// already checks for AIM hits/misses.

		assert llcLine != null && llcLine.valid();
		assert llcLine.id().get() == 0;
		resp.lineHit = llcLine;
		return resp;
	}

	/** Just get the corresponding line */
	Line junitGetLine(Processor<Line> proc, LineAddress addr) {
		Deque<Line> set = sets.get(index(addr.get()));
		// search this cache
		for (Iterator<Line> it = set.iterator(); it.hasNext();) {
			Line line = it.next();
			if (line.lineAddress() != null) {
				if (line.lineAddress().equals(addr)) {
					assert line.id().equals(processor.id);
					assert !line.isPrivateCacheLine();
					return line;
				}
			}
		}
		return null;
	}

	/** The check for presence of metadata has already been performed in the caller. */
	public AIMResponse<Line> request(Processor<Line> proc, final Line incomingLine, boolean read,
			ExecutionPhase phase) {
		assert proc.params.useAIMCache();

		Deque<Line> set = sets.get(index(incomingLine.lineAddress().get()));
		assert set.size() == assoc;
		incomingLine.changeStateTo(ViserState.VISER_VALID);
		AIMResponse<Line> ret = new AIMResponse<Line>();

		proc.updateAIMEnergy(read);

		// search this cache
		for (Iterator<Line> it = set.iterator(); it.hasNext();) {
			Line line = it.next();

			if (line.lineAddress() != null
					&& line.lineAddress().equals(incomingLine.lineAddress())) {
				ret.whereHit = this.levelInHierarchy;
				assert line.id().equals(processor.id);
				assert !line.isPrivateCacheLine();
				line.setAIMMD(incomingLine.hasAIMMD());

				if (read) {
					proc.stats.pc_aim.pc_ReadHits.incr();
				} else {
					proc.stats.pc_aim.pc_WriteHits.incr();
				}
				return ret;
			}
		}

		// Check if the line has non-zero metadata for at least one core. It is an AIM miss only if
		// so. L1/L2 and the LLC is not inclusive for Viser. Since this is an LLC hit, we expect a
		// fetch from LLC should hold over here as well. But there could the following scenario: LLC
		// line is fetched into L2, L2 line is evicted, and that causes the current
		// LLC line to get evicted. This happens at least for canneal and dedup
		MemoryResponse<Line> sharedResp = getLineFromLLCOrMemoryAIM(proc, incomingLine, read);
		assert sharedResp.lineHit != null;
		boolean miss = sharedResp.lineHit
				.hasAIMMD() /* proc.needToCheckAIMCache(sharedResp.lineHit) */;
		Line aimLine = lineFactory.create(this.processor, this.levelInHierarchy,
				incomingLine.lineAddress());
		aimLine.setAIMMD(incomingLine.hasAIMMD());

		if (miss) {
			// if we made it here, we missed in the AIM
			ret.whereHit = CacheLevel.MEMORY;
			if (read) {
				proc.stats.pc_aim.pc_ReadMisses.incr();
			} else {
				proc.stats.pc_aim.pc_WriteMisses.incr();
			}

			// Choose a line for eviction, ideally prefer lines that have no metadata set
			Line toEvict = getVictimLineNoRegionBoundaryClearance(proc, incomingLine);
			assert toEvict.id() == proc.id;
			if (toEvict.valid() /* && proc.needToCheckAIMCache(toEvict) */) {
				Line llcLine = proc.L3cache.getLine(toEvict);
				assert llcLine != null; // FIXME: When can this assertion fail?
				if (llcLine != null && llcLine.hasAIMMD()) {
					proc.stats.pc_aim.pc_LineEvictions.incr();
					proc.stats.pc_aim.pc_DirtyLineEvictions.incr();
					updateOnChipNetworkMessageAIM(proc, phase);
				}
			}
			set.remove(toEvict);
			set.addFirst(aimLine);
		} else { // Otherwise it is a LLC hit, and we do not need to access metadata lines
			if (read) {
				proc.stats.pc_aim.pc_ReadHits.incr();
			} else {
				proc.stats.pc_aim.pc_WriteHits.incr();
			}
			ret.whereHit = CacheLevel.L3;
		}

		return ret;
	}

	private void updateOnChipNetworkMessageAIM(Processor<Line> proc, ExecutionPhase phase) {
		int lineSize = getAIMLineSize(proc);
		proc.updateTrafficForOneNetworkMessage(1, lineSize, phase);
	}

	public interface LineVisitor<Line> {
		public void visit(Line l);
	}

	/**
	 * Calls the given visitor function once on each line in this cache. Lines are traversed in no
	 * particular order.
	 */
	public void visitAllLines(LineVisitor<Line> lv) {
		for (Deque<Line> set : sets) {
			for (Line l : set) {
				lv.visit(l);
			}
		}
	}

	/** Verify that each line is indexed into the proper set. */
	public void verifyIndices() {
		for (int i = 0; i < sets.size(); i++) {
			Deque<Line> set = sets.get(i);
			for (Line l : set) {
				if (l.lineAddress() != null) {
					assert index(l.lineAddress().get()) == i;
				}
			}
		}
	}

	@Override
	public String toString() {
		StringBuilder s = new StringBuilder();
		if (this.levelInHierarchy.compareTo(this.processor.llc()) < 0) {
			s.append(this.processor + "\n");
		}
		s.append("aimcache=" + this.levelInHierarchy + System.getProperty("line.separator"));
		for (Deque<Line> set : sets) {
			for (Line l : set) {
				s.append(l.toString() + "\n");
			}
			s.append(System.getProperty("line.separator"));
		}

		return s.toString();
	}

	/**
	 * Intelligently select a victim line for eviction, based on metadata staleness. Otherwise, just
	 * fallback to LRU.
	 */
	private Line getVictimLineNoRegionBoundaryClearance(Processor<Line> proc, Line incoming) {
		assert !proc.params.clearAIMCacheAtRegionBoundaries();
		Deque<Line> set = sets.get(index(incoming.lineAddress().get()));
		Line remove = set.getLast(); // LRU
		if (remove.lineAddress() == null) {
			return remove;
		}

		for (Iterator<Line> it = set.iterator(); it.hasNext();) {
			Line l = it.next();
			if (l.lineAddress() != null) {
				assert l.id().equals(processor.id);
				assert !l.isPrivateCacheLine();

				Line llcLine = proc.L3cache.getLine(l);
				// We may not evict AIM lines when evicting LLC lines that have no valid metadata.
				if (llcLine != null) {
					if (!llcLine.hasAIMMD()) {
						remove = l;
						break;
					}
				} else {
					remove = l;
					break;
				}

			} else {
				remove = l;
				break;
			}
		}
		return remove;
	}

	/**
	 * Here we are not choosing a candidate line for eviction. Instead, we will evict toEvict if it
	 * is present.
	 */
	public void evictLine(Processor<Line> proc, Line toEvict, ExecutionPhase phase) {
		Deque<Line> set = sets.get(index(toEvict.lineAddress().get()));
		boolean removed = false;
		for (Iterator<Line> it = set.iterator(); it.hasNext();) {
			Line l = it.next();
			if (l.lineAddress() != null && l.lineAddress().equals(toEvict.lineAddress())) {
				assert l.id().equals(processor.id);
				assert !l.isPrivateCacheLine();

				it.remove();
				if (l.valid() && /* proc.needToCheckAIMCache(toEvict) */
						toEvict.hasAIMMD()) {
					proc.stats.pc_aim.pc_LineEvictions.incr();
					proc.stats.pc_aim.pc_DirtyLineEvictions.incr();
					updateOnChipNetworkMessageAIM(proc, phase);
				}
				removed = true;
			}
		}
		if (removed) {
			set.addLast(lineFactory.create(processor, levelInHierarchy));
		}
		assert set.size() == assoc;
	}

	// This method is called from a LLC miss. If there is a LLC miss, then we do not consider that
	// to be an AIM miss if the llc line does not have metadata.
	public void addLineFromLLCMiss(Processor<Line> proc, Line memLine, boolean read,
			ExecutionPhase phase) {
		LineAddress la = memLine.lineAddress();
		Deque<Line> set = sets.get(index(la.get()));
		Line toEvict = null;
		if (!proc.params.clearAIMCacheAtRegionBoundaries()) {
			toEvict = getVictimLineNoRegionBoundaryClearance(proc, memLine);
		} else {
			toEvict = set.getLast(); // LRU
		}
		boolean found = set.remove(toEvict);
		assert found;
		if (toEvict.lineAddress() != null && /* proc.needToCheckAIMCache(toEvict) */
				memLine.hasAIMMD()) {
			proc.stats.pc_aim.pc_LineEvictions.incr();
			proc.stats.pc_aim.pc_DirtyLineEvictions.incr();
			updateOnChipNetworkMessageAIM(proc, phase);
		}

		// NB: add the incoming line *after* the eviction handler runs
		Line copy = lineFactory.create(processor, levelInHierarchy, memLine.lineAddress());
		copy.changeStateTo(ViserState.VISER_VALID);
		copy.setAIMMD(memLine.hasAIMMD());
		set.addFirst(copy);

		if (memLine.hasAIMMD()) {
			if (read) {
				proc.stats.pc_aim.pc_ReadMisses.incr();
			} else {
				proc.stats.pc_aim.pc_WriteMisses.incr();
			}
		}
	}

	// Add blindly without checking for duplicates. This must be because of an AIM miss.
	public void addLineWithoutCheckingForDuplicates(Processor<Line> proc, Line line, boolean read,
			boolean hasMD, ExecutionPhase phase) {
		LineAddress la = line.lineAddress();
		Deque<Line> set = sets.get(index(la.get()));
		Line toEvict = null;
		if (!proc.params.clearAIMCacheAtRegionBoundaries()) {
			toEvict = getVictimLineNoRegionBoundaryClearance(proc, line);
		} else {
			toEvict = set.getLast(); // LRU
		}
		boolean found = set.remove(toEvict);
		assert found;
		if (toEvict.lineAddress() != null /* && proc.needToCheckAIMCache(toEvict) */ ) {
			Line llcLine = proc.L3cache.getLine(toEvict);
			assert llcLine != null; // FIXME: When can this assertion fail?
			if (llcLine != null && llcLine.hasAIMMD()) {
				proc.stats.pc_aim.pc_LineEvictions.incr();
				proc.stats.pc_aim.pc_DirtyLineEvictions.incr();
				updateOnChipNetworkMessageAIM(proc, phase);
			}
		}

		// NB: add the incoming line *after* the eviction handler runs
		Line copy = lineFactory.create(processor, levelInHierarchy, line.lineAddress());
		copy.changeStateTo(ViserState.VISER_VALID);
		copy.setAIMMD(hasMD);
		set.addFirst(copy);

		if (hasMD) {
			if (read) {
				proc.stats.pc_aim.pc_ReadMisses.incr();
			} else {
				proc.stats.pc_aim.pc_WriteMisses.incr();
			}
		}
	}

	// Add only after checking for duplicates
	public void addLineIfNotPresent(Processor<Line> proc, Line privLine, boolean read,
			boolean hasMD, ExecutionPhase phase) {
		LineAddress la = privLine.lineAddress();
		Deque<Line> set = sets.get(index(la.get()));
		for (Line l : set) {
			if (l.lineAddress() != null && l.lineAddress().equals(la)) {
				// Line is already present, so need not add
				if (hasMD) {
					l.setAIMMD(hasMD);
					if (read) {
						proc.stats.pc_aim.pc_ReadHits.incr();
					} else {
						proc.stats.pc_aim.pc_WriteHits.incr();
					}
				}
				return;
			}
		}
		// Line is not present, so add
		addLineWithoutCheckingForDuplicates(proc, privLine, read, hasMD, phase);
	}

	// I had issues with ConcurrentModificationException. So I get around the problem by creating
	// a copy and selectively copying over lines.
	void clearAIMCache(Processor<Line> proc) {
		List<Deque<Line>> tmpSets = new ArrayList<Deque<Line>>(numSets);
		for (int i = 0; i < numSets; i++) {
			tmpSets.add(new LinkedList<Line>());
		}

		int i = 0;
		while (i < numSets) {
			Deque<Line> origSet = sets.get(i);
			Deque<Line> newSet = tmpSets.get(i);
			assert newSet.size() == 0;

			for (Line origLine : origSet) {
				assert origLine.id().equals(processor.id);
				assert !origLine.isPrivateCacheLine();

				if (origLine.lineAddress() == null) {
					newSet.addLast(lineFactory.create(processor, levelInHierarchy));
				} else {
					boolean valid = false;
					// An AIM line has to be present in the LLC.
					Line llcLine = proc.L3cache.getLine(origLine);
					assert llcLine != null;
					for (int j = 0; j < proc.params.numProcessors(); j++) {
						CpuId cpuId = new CpuId(j);
						if (llcLine.hasReadOffsets(cpuId) || llcLine.hasWrittenOffsets(cpuId)) {
							valid = true;
							break;
						}
					}

					if (valid) {
						Line copy = lineFactory.create(processor, levelInHierarchy,
								origLine.lineAddress());
						newSet.addLast(copy);
					} else {
						newSet.addLast(lineFactory.create(processor, levelInHierarchy));
					}

				}
			}

			assert newSet.size() == origSet.size();
			assert newSet.size() == assoc;
			i++;
		}

		// Reset the cache
		sets = tmpSets;
	}

	void clearAIMCache2(Processor<Line> proc) {
		Iterator<Deque<Line>> setIt = sets.iterator();
		while (setIt.hasNext()) {
			Deque<Line> deq = setIt.next();
			Iterator<Line> deqIt = deq.iterator();
			int numLinesRemoved = 0;
			while (deqIt.hasNext()) {
				Line aimLine = deqIt.next();
				assert aimLine.id().equals(new CpuId(0));

				if (aimLine.lineAddress() == null) {
					continue;
				}

				boolean valid = false;
				Line llcLine = proc.L3cache.getLine(aimLine);
				assert llcLine != null;
				for (int i = 0; i < proc.params.numProcessors(); i++) {
					CpuId cpuId = new CpuId(i);
					Processor<Line> p = proc.machine.getProc(cpuId);
					PerCoreLineMetadata md = llcLine.getPerCoreMetadata(cpuId);
					assert md != null;
					assert md.epoch.getRegionId() <= p.getCurrentEpoch().getRegionId();
					if (llcLine.hasReadOffsets(cpuId) || llcLine.hasWrittenOffsets(cpuId)) {
						valid = true;
						break;
					}
				}

				if (!valid) {
					deqIt.remove();
					numLinesRemoved++;
				}
			}
			for (int i = 0; i < numLinesRemoved; i++) {
				deq.addLast(lineFactory.create(processor, levelInHierarchy));
			}
			assert deq.size() == assoc;
		}
	}
}
