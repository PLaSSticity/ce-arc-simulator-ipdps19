#ifndef VISER_HPP_
#define VISER_HPP_

#include <iostream>
#include <cstring>
#include <map>
#include <string>
#include <cassert>
#include <queue>
#include <pthread.h>
#include <list>

#include "pin.H"
#include "event.hpp"

using namespace std;

const uint32_t MAX_CIRCULAR_BUFFER_SIZE = 100000;

// Use the lock to protect updates to this map
static std::map<THREADID, pthread_t> s_threadMap;
// static PIN_LOCK s_threadMapLock;

VOID initSimulator();
VOID handleMkfifoError(string fifoName, int ret);

// Instrumentation callbacks
extern VOID initInstrCallback();
extern VOID initAnalysisCallback();
// extern VOID instrumentInstruction(INS ins, VOID* v);
extern VOID instrumentImage(IMG img, VOID *v);
extern VOID instrumentTrace(TRACE trace, VOID *V);

// Thread-local data
class thread_local_data_t {
public:
  EventType m_eventType;
  THREADID m_tid;
  ADDRINT m_addr; // Effective address
  ADDRINT m_memOpSize;
  BOOL m_stackRef;
  int ignoredFuncs;    // Stack counters for ignored functions
  int activeAcqs;      // The number of currently active acquires
  int16_t lastSrcFile; // index of the last/ most recent source file
  int16_t lastLine;    // the last/ most recent number

  thread_local_data_t() {
    m_eventType = INVALID;
    m_tid = -1;
    m_addr = 0;
    m_stackRef = false;
    m_memOpSize = 0;
    ignoredFuncs = 0;
    activeAcqs = 0;
    lastSrcFile = 0;
    lastLine = 0;
  }
};

#endif // VISER_HPP_
