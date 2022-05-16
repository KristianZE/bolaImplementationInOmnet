//
// Copyright (C) 2004 OpenSim Ltd.
// Copyright (C) 2000 Institut fuer Telematik, Universitaet Karlsruhe
//
// This program is free software; you can redistribute it and/or
// modify it under the terms of the GNU Lesser General Public License
// as published by the Free Software Foundation; either version 2
// of the License, or (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Lesser General Public License for more details.
//
// You should have received a copy of the GNU Lesser General Public License
// along with this program; if not, write to the Free Software
// Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
//

#ifndef __INET_UdpSinkCustom_H
#define __INET_UdpSinkCustom_H

#include <fstream>

#include "inet/applications/base/ApplicationBase.h"
#include "inet/transportlayer/contract/udp/UdpSocket.h"

namespace improved5gns {

/**
 * Consumes and prints packets received from the Udp module. See NED for more info.
 */
class INET_API UdpSinkCustom : public inet::ApplicationBase, public inet::UdpSocket::ICallback
{
  protected:
    enum SelfMsgKinds { START = 1, STOP };

    inet::UdpSocket socket;
    int localPort = -1;
    inet::L3Address multicastGroup;
    inet::simtime_t startTime;
    inet::simtime_t stopTime;
    inet::cMessage *selfMsg = nullptr;
    int numReceived = 0;

    int64_t bitsReceived;
    inet::simtime_t downloadBegin;

    int64_t lastCheckBits;
    inet::simtime_t lastCheckTime;
    std::string fileName;

  public:
    UdpSinkCustom() {}
    virtual ~UdpSinkCustom();

  protected:
    virtual void processPacket(inet::Packet *msg);
    virtual void setSocketOptions();

  protected:
    virtual int numInitStages() const override { return inet::NUM_INIT_STAGES; }
    virtual void initialize(int stage) override;
    virtual void handleMessageWhenUp(inet::cMessage *msg) override;
    virtual void finish() override;
    virtual void refreshDisplay() const override;

    virtual void socketDataArrived(inet::UdpSocket *socket, inet::Packet *packet) override;
    virtual void socketErrorArrived(inet::UdpSocket *socket, inet::Indication *indication) override;
    virtual void socketClosed(inet::UdpSocket *socket) override;

    virtual void processStart();
    virtual void processStop();

    virtual void handleStartOperation(inet::LifecycleOperation *operation) override;
    virtual void handleStopOperation(inet::LifecycleOperation *operation) override;
    virtual void handleCrashOperation(inet::LifecycleOperation *operation) override;
};

} // namespace inet

#endif

