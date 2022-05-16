//
// Copyright (C) 2000 Institut fuer Telematik, Universitaet Karlsruhe
// Copyright (C) 2004,2011 OpenSim Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Lesser General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Lesser General Public License for more details.
//
// You should have received a copy of the GNU Lesser General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
//

#ifndef __INET_UdpBasicAppCustom_H
#define __INET_UdpBasicAppCustom_H

#include <vector>

#include "inet/applications/base/ApplicationBase.h"
#include "inet/common/clock/ClockUserModuleMixin.h"
#include "inet/transportlayer/contract/udp/UdpSocket.h"

namespace improved5gns {

/**
 * UDP application. See NED for more info.
 */
class INET_API UdpBasicAppCustom : public inet::ClockUserModuleMixin<inet::ApplicationBase>, public inet::UdpSocket::ICallback
{
  protected:
    enum SelfMsgKinds { START = 1, SEND, STOP };

    // parameters
    std::vector<inet::L3Address> destAddresses;
    std::vector<std::string> destAddressStr;
    int localPort = -1, destPort = -1;
    inet::clocktime_t startTime;
    inet::clocktime_t stopTime;
    bool dontFragment = false;
    const char *packetName = nullptr;

    double ival;
    int flag = 1; // On by default

    // state
    inet::UdpSocket socket;
    inet::ClockEvent *selfMsg = nullptr;

    // statistics
    int numSent = 0;
    int numReceived = 0;

  protected:
    virtual int numInitStages() const override { return inet::NUM_INIT_STAGES; }
    virtual void initialize(int stage) override;
    virtual void handleMessageWhenUp(inet::cMessage *msg) override;
    virtual void finish() override;
    virtual void refreshDisplay() const override;

    // chooses random destination address
    virtual inet::L3Address chooseDestAddr();
    virtual void sendPacket();
    virtual void processPacket(inet::Packet *msg);
    virtual void setSocketOptions();

    virtual void processStart();
    virtual void processSend();
    virtual void processStop();

    virtual void handleStartOperation(inet::LifecycleOperation *operation) override;
    virtual void handleStopOperation(inet::LifecycleOperation *operation) override;
    virtual void handleCrashOperation(inet::LifecycleOperation *operation) override;

    virtual void socketDataArrived(inet::UdpSocket *socket, inet::Packet *packet) override;
    virtual void socketErrorArrived(inet::UdpSocket *socket, inet::Indication *indication) override;
    virtual void socketClosed(inet::UdpSocket *socket) override;

  public:
    UdpBasicAppCustom() {}
    ~UdpBasicAppCustom();
};

} // namespace inet

#endif

