/*
 * TcpRttListener.h
 *
 *  Created on: Jan 20, 2020
 *      Author: marcin
 */

#ifndef INET_APPLICATIONS_TCPAPP_TCPRTTLISTENER_H_
#define INET_APPLICATIONS_TCPAPP_TCPRTTLISTENER_H_

#include <omnetpp.h>

#include "inet/common/lifecycle/LifecycleOperation.h"

#include <list>

namespace inet {

    class INET_API TcpRttListener : public cListener {
        public:
            std::list<simtime_t> allRtts;
//            std::list<cComponent *> sources;
        public:
            TcpRttListener();
            virtual ~TcpRttListener();

            virtual void receiveSignal(cComponent *source, simsignal_t signalID, const SimTime& t, cObject *details) override;

            simtime_t getMeanRtt(void);
    };

}
#endif /* INET_APPLICATIONS_TCPAPP_TCPRTTLISTENER_H_ */
