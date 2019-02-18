package simulator.mesi;

public class Event {
	final EventType type;
	final EventType semantics;
	final ThreadId tid;
	long addr;
	byte memOpSize;
	boolean stackRef;
	long value;
	int insnCount;
	int siteIndex;

	Event(EventType typ, EventType semantics, byte tid) {
		this.type = typ;
		this.semantics = semantics;
		this.tid = new ThreadId(tid);
	}

	@Override
	public String toString() {
		return "type=" + type + " semantics=" + semantics + " tid=" + tid + " addr=" + addr
				+ " memOpSize=" + memOpSize + " stackRef=" + stackRef + " value=" + value
				+ " inscount=" + insnCount + " siteIndex=" + siteIndex;
	}
}
