package simulator.mesi;

import java.io.IOException;
import java.io.Writer;
import java.util.LinkedList;
import java.util.List;
import java.util.StringTokenizer;

import joptsimple.OptionParser;
import joptsimple.OptionSpec;

public class Knobs {

	public static final OptionSpec<Boolean> Help;
	public static final OptionSpec<Boolean> Xasserts;
	public static final OptionSpec<Integer> AssertPeriod;
	public static final OptionSpec<String> StatsFile;
	public static final OptionSpec<String> ToSimulatorFifo;

	public static final OptionSpec<Integer> Cores;
	public static final OptionSpec<Integer> PinThreads;

	// caches
	public static final OptionSpec<Integer> LineSize;

	public static final OptionSpec<Integer> L1Size;
	public static final OptionSpec<Integer> L1Assoc;

	public static final OptionSpec<Boolean> UseL2;
	public static final OptionSpec<Integer> L2Size;
	public static final OptionSpec<Integer> L2Assoc;

	public static final OptionSpec<Integer> L3Size;
	public static final OptionSpec<Integer> L3Assoc;

	public static final OptionSpec<String> SimulationMode;
	public static final OptionSpec<Boolean> IgnoreStackRefs;
	public static final OptionSpec<Boolean> RemoteAccessesAffectLRU;
	public static final OptionSpec<Boolean> modelOnlyROI;

	public static final OptionSpec<Boolean> ConflictExceptions;

	public static final OptionSpec<Boolean> Pintool;
	public static final OptionSpec<Boolean> Lockstep;
	public static final OptionSpec<Boolean> ReportSites;
	public static final OptionSpec<Boolean> TreatAtomicUpdatesAsRegularAccesses;

	public static final OptionSpec<Boolean> UsePLRU;

	public static final OptionSpec<Boolean> WithPacifistBackends;

	public static final OptionSpec<Boolean> UseAIMCache;
	public static final OptionSpec<Integer> NumAIMLines;
	public static final OptionSpec<Boolean> ClearAIMAtRegionBoundaries;

	public static final OptionParser parser;

	private Knobs() {
	}

	static {
		parser = new OptionParser();
		BooleanParameters = new LinkedList<OptionSpec<Boolean>>();
		StringParameters = new LinkedList<OptionSpec<String>>();
		IntegerParameters = new LinkedList<OptionSpec<Integer>>();
		EnumParameters = new LinkedList<OptionSpec<? extends Enum<?>>>();

		Help = parser.accepts("help", "print this help message").withOptionalArg()
				.ofType(Boolean.class).defaultsTo(false);
		Xasserts = parser.accepts("xasserts", "enable eXpensive assert checks").withOptionalArg()
				.ofType(Boolean.class).defaultsTo(true);
		AssertPeriod = parser.accepts("assert-period", "enable asserts after so many events")
				.withOptionalArg().ofType(Integer.class).defaultsTo(1);
		StatsFile = parser.accepts("stats-file", "stats file to generate").withRequiredArg()
				.defaultsTo("sim-stats.py");
		ToSimulatorFifo = parser
				.accepts("tosim-fifo", "named fifo used to get events from the front-end")
				.withRequiredArg();
		modelOnlyROI = parser.accepts("model-only-roi", "Whether to only simulate the ROI?")
				.withRequiredArg().ofType(Boolean.class).defaultsTo(true);

		// processor parameters
		Cores = registerInt(parser.accepts("cores", "number of cores to simulate").withRequiredArg()
				.ofType(Integer.class).defaultsTo(1));
		PinThreads = registerInt(parser.accepts("pinThreads", "number of Pin threads")
				.withRequiredArg().ofType(Integer.class).defaultsTo(1));

		// cache parameters
		LineSize = registerInt(parser.accepts("line-size", "Line size for all caches")
				.withOptionalArg().ofType(Integer.class).defaultsTo(64));

		L1Size = registerInt(parser.accepts("l1-size", "Size (in bytes) of each private L1 cache")
				.withOptionalArg().ofType(Integer.class).defaultsTo(1 << 15/* 32KB */));
		L1Assoc = registerInt(parser.accepts("l1-assoc", "Associativity of each private L1 cache")
				.withOptionalArg().ofType(Integer.class).defaultsTo(8));

		UseL2 = registerBool(parser.accepts("use-l2", "Model a private L2 for each core")
				.withRequiredArg().ofType(Boolean.class).defaultsTo(true));
		L2Size = registerInt(parser.accepts("l2-size", "Size (in bytes) of the private L2 cache")
				.withOptionalArg().ofType(Integer.class).defaultsTo(1 << 18/* 256KB */));
		L2Assoc = registerInt(parser.accepts("l2-assoc", "Associativity of the private L2 cache")
				.withOptionalArg().ofType(Integer.class).defaultsTo(8));

		L3Size = registerInt(parser.accepts("l3-size", "Size (in bytes) of the shared L3 cache")
				.withOptionalArg().ofType(Integer.class).defaultsTo(1 << 24/* 16MB */));
		L3Assoc = registerInt(parser.accepts("l3-assoc", "Associativity of the shared L3 cache")
				.withOptionalArg().ofType(Integer.class).defaultsTo(16));

		UseAIMCache = registerBool(parser.accepts("use-aim-cache", "Use AIM cache")
				.withRequiredArg().ofType(Boolean.class).defaultsTo(false));
		// XXX: Might need to change this for JUnit test cases
		NumAIMLines = registerInt(parser.accepts("num-aim-lines", "Num AIM lines (set * assoc)")
				.withOptionalArg().ofType(Integer.class).defaultsTo(1 << 15 /* 32K */));
		ClearAIMAtRegionBoundaries = registerBool(parser
				.accepts("clear-aim-region-boundaries", "Clear AIM cache at region boundaries")
				.withRequiredArg().ofType(Boolean.class).defaultsTo(false));

		SimulationMode = registerString(
				parser.accepts("sim-mode", "Simulation mode to use (one of: baseline, viser).")
						.withRequiredArg().defaultsTo("baseline"));

		// optional stuff
		IgnoreStackRefs = registerBool(
				parser.accepts("ignore-stack", "Assume stack references are thread-private.")
						.withOptionalArg().ofType(Boolean.class).defaultsTo(false));
		RemoteAccessesAffectLRU = registerBool(parser
				.accepts("remote-accesses-affect-lru", "Remote accesses update LRU cache state.")
				.withOptionalArg().ofType(Boolean.class).defaultsTo(false));

		ConflictExceptions = registerBool(
				parser.accepts("conflict-exceptions", "Model Conflict Exceptions").withRequiredArg()
						.ofType(Boolean.class).defaultsTo(false));

		Pintool = registerBool(parser.accepts("pintool", "Is the Pintool executing?")
				.withRequiredArg().ofType(Boolean.class).defaultsTo(false));
		Lockstep = registerBool(
				parser.accepts("lockstep", "Execute the backend in lockstep with the " + "Pintool")
						.withRequiredArg().ofType(Boolean.class).defaultsTo(false));
		ReportSites = registerBool(
				parser.accepts("report-sites", "Report the sites involved in a conflict detected.")
						.withRequiredArg().ofType(Boolean.class).defaultsTo(false));
		TreatAtomicUpdatesAsRegularAccesses = registerBool(parser
				.accepts("treat-atomic-updates-as-regular-accesses",
						"Treat atomic updates as regular memory accesses")
				.withRequiredArg().ofType(Boolean.class).defaultsTo(false));
		UsePLRU = registerBool(parser.accepts("use-plru", "Use the PLRU cache replacement policy")
				.withRequiredArg().ofType(Boolean.class).defaultsTo(false));
		WithPacifistBackends = registerBool(
				parser.accepts("with-pacifist-backends", "Running with Pacifist backends")
						.withRequiredArg().ofType(Boolean.class).defaultsTo(false));
	}

	/*
	 * Below is the stuff that automatically allows certain flags ("registered" ones) to appear in
	 * the stats output, without any additional effort.
	 */

	private static final List<OptionSpec<Boolean>> BooleanParameters;
	private static final List<OptionSpec<String>> StringParameters;
	private static final List<OptionSpec<Integer>> IntegerParameters;
	private static final List<OptionSpec<? extends Enum<?>>> EnumParameters;

	private static OptionSpec<String> registerString(OptionSpec<String> o) {
		StringParameters.add(o);
		return o;
	}

	private static OptionSpec<Integer> registerInt(OptionSpec<Integer> o) {
		IntegerParameters.add(o);
		return o;
	}

	private static OptionSpec<Boolean> registerBool(OptionSpec<Boolean> o) {
		BooleanParameters.add(o);
		return o;
	}

	@SuppressWarnings("unused")
	private static <E extends Enum<E>> OptionSpec<E> registerEnum(OptionSpec<E> o) {
		EnumParameters.add(o);
		return o;
	}

	private static String format(String flag) {
		// strip brackets
		String noBrackets = flag.replaceAll("\\[", "").replaceAll("\\]", "");

		// tokenize on dashes
		String result = "";
		StringTokenizer tok = new StringTokenizer(noBrackets, "-");
		while (tok.hasMoreTokens()) {
			String t = tok.nextToken();
			// capitalize each token
			result += (t.substring(0, 1).toUpperCase() + t.substring(1));
		}

		return result;
	}

	public static void dumpRegisteredParams(Writer w) throws IOException {
		for (OptionSpec<Boolean> osb : BooleanParameters) {
			String value = MESISim.Options.valueOf(osb) ? "True" : "False";
			w.write("'" + format(osb.toString()) + "': " + value + ", ");
		}
		for (OptionSpec<String> os : StringParameters) {
			w.write("'" + format(os.toString()) + "': '" + MESISim.Options.valueOf(os) + "', ");
		}
		for (OptionSpec<? extends Enum<?>> os : EnumParameters) {
			w.write("'" + format(os.toString()) + "': '" + MESISim.Options.valueOf(os).toString()
					+ "', ");
		}
		for (OptionSpec<Integer> os : IntegerParameters) {
			if (os == Cores) {
				w.write("'" + format(os.toString()) + "': '" + MESISim.Options.valueOf(os)
						+ "p', ");
			} else if (os == L1Size || os == L2Size || os == L3Size) {
				int kb = MESISim.Options.valueOf(os) / 1024;
				w.write("'" + format(os.toString()) + "': '" + kb + "KB', ");
			} else {
				w.write("'" + format(os.toString()) + "': " + MESISim.Options.valueOf(os) + ", ");
			}
		}
	}

}
