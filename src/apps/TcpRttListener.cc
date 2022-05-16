/*
 * TcpRttListener.cc
 *
 *  Created on: Jan 20, 2020
 *      Author: marcin
 */


#include "TcpRttListener.h"

namespace inet {

    TcpRttListener::TcpRttListener() {
        EV << "TcpRttListener: Initializing TCP RTT listener\n";
    }

    TcpRttListener::~TcpRttListener() {
    }

    void TcpRttListener::receiveSignal(cComponent *source, simsignal_t signalID, const SimTime& t, cObject *details) {
        allRtts.push_back(t);
//        sources.push_back(source);
        EV << "TcpRttListener: Received RTT = " << t << "\n";
        EV << "TcpRttListener: Details = " << details << "\n";
        EV << "TcpRttListener: Source = " << source->getFullName() << "\n";
        EV << "TcpRttListener: Signal ID = " << signalID << "\n";

    }

    simtime_t TcpRttListener::getMeanRtt(void) {

        simtime_t sumRtts = 0;
        int numRtts = 0;
        for (simtime_t rtt : allRtts) {
            EV << "getMeanRtt - RTT[" << numRtts << "] = " << rtt << "\n";
            sumRtts += rtt;
            numRtts += 1;
        }

        if (numRtts > 0) {
            simtime_t meanRtt = sumRtts/numRtts;
            EV << "TcpRttListener: Mean RTT = " << meanRtt << "\n";
            return meanRtt;
        } else {
            simtime_t meanRtt = 0;
            return meanRtt;
        }
    }

}
