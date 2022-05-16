//
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

#include "UdpSinkCustom.h"

#include "inet/common/ModuleAccess.h"
#include "inet/common/packet/Packet.h"
#include "inet/networklayer/common/L3AddressResolver.h"
#include "inet/transportlayer/contract/udp/UdpControlInfo_m.h"

#include <tgmath.h>
#include <string>
#include <chrono>
#include <string>
#include <sstream>

namespace improved5gns {

Define_Module(UdpSinkCustom);

UdpSinkCustom::~UdpSinkCustom()
{
    cancelAndDelete(selfMsg);
}

void UdpSinkCustom::initialize(int stage)
{
    ApplicationBase::initialize(stage);

    if (stage == inet::INITSTAGE_LOCAL) {
        numReceived = 0;
        WATCH(numReceived);

        localPort = par("localPort");
        startTime = par("startTime");
        stopTime = par("stopTime");
        if (stopTime >= SIMTIME_ZERO && stopTime < startTime)
            throw inet::cRuntimeError("Invalid startTime/stopTime parameters");
        selfMsg = new inet::cMessage("UdpSinkCustomTimer");

        std::string moduleName = getParentModule()->getFullName();
        std::string currentNumber = std::to_string(getIndex());
        std::string configName = inet::cSimulation::getActiveEnvir()->getConfigEx()->getActiveConfigName();
        std::string runNumber = std::to_string(inet::cSimulation::getActiveEnvir()->getConfigEx()->getActiveRunNumber());
        fileName = "tempBitrateResults/";
        fileName += configName;
        fileName += runNumber;
        fileName += moduleName;
        fileName += "_app";
        fileName += currentNumber;
        fileName += ".csv";
        std::fstream fout;
        fout.open(fileName, std::ios::out | std::ios::trunc);
        fout << "timestamp,bitrate\n";
        fout.close();
    }
}

void UdpSinkCustom::handleMessageWhenUp(inet::cMessage *msg)
{
    if (msg->isSelfMessage()) {
        ASSERT(msg == selfMsg);
        switch (selfMsg->getKind()) {
            case START:
                processStart();
                break;

            case STOP:
                processStop();
                break;

            default:
                throw inet::cRuntimeError("Invalid kind %d in self message", (int)selfMsg->getKind());
        }
    }
    else if (msg->arrivedOn("socketIn"))
        socket.processMessage(msg);
    else
        throw inet::cRuntimeError("Unknown incoming gate: '%s'", msg->getArrivalGate()->getFullName());
}

void UdpSinkCustom::socketDataArrived(inet::UdpSocket *socket, inet::Packet *packet)
{
    bitsReceived += packet->getBitLength();
    inet::simtime_t curTime = inet::simTime();
    lastCheckBits += packet->getBitLength() + 264;

    double downloadTime = ((double) curTime.raw() - (double) lastCheckTime.raw()) / (double) pow(10,12);
    if (downloadTime >= 0.9) {
        double avgBandwidth = (double) lastCheckBits / downloadTime;

        std::fstream fout;
        fout.open(fileName, std::ios::app);
        std::string timeInfo;
        timeInfo = curTime.str();
        timeInfo += ",";
        timeInfo += std::to_string(avgBandwidth / 1000);
        timeInfo += "\n";
        fout << timeInfo;
        fout.close();

        lastCheckTime = inet::simTime();
        lastCheckBits = 0;
    }
    // process incoming packet
    processPacket(packet);
}

void UdpSinkCustom::socketErrorArrived(inet::UdpSocket *socket, inet::Indication *indication)
{
    EV_WARN << "Ignoring UDP error report " << indication->getName() << inet::endl;
    delete indication;
}

void UdpSinkCustom::socketClosed(inet::UdpSocket *socket)
{
    if (operationalState == State::STOPPING_OPERATION)
        startActiveOperationExtraTimeOrFinish(par("stopOperationExtraTime"));
}

void UdpSinkCustom::refreshDisplay() const
{
    ApplicationBase::refreshDisplay();

    char buf[50];
    sprintf(buf, "rcvd: %d pks", numReceived);
    getDisplayString().setTagArg("t", 0, buf);
}

void UdpSinkCustom::finish()
{
    ApplicationBase::finish();
    EV_INFO << getFullPath() << ": received " << numReceived << " packets\n";
}

void UdpSinkCustom::setSocketOptions()
{
    bool receiveBroadcast = par("receiveBroadcast");
    if (receiveBroadcast)
        socket.setBroadcast(true);

    inet::MulticastGroupList mgl = inet::getModuleFromPar<inet::IInterfaceTable>(par("interfaceTableModule"), this)->collectMulticastGroups();
    socket.joinLocalMulticastGroups(mgl);

    // join multicastGroup
    const char *groupAddr = par("multicastGroup");
    multicastGroup = inet::L3AddressResolver().resolve(groupAddr);
    if (!multicastGroup.isUnspecified()) {
        if (!multicastGroup.isMulticast())
            throw inet::cRuntimeError("Wrong multicastGroup setting: not a multicast address: %s", groupAddr);
        socket.joinMulticastGroup(multicastGroup);
    }
    socket.setCallback(this);
}

void UdpSinkCustom::processStart()
{
    socket.setOutputGate(gate("socketOut"));
    socket.bind(localPort);
    setSocketOptions();

    if (stopTime >= SIMTIME_ZERO) {
        selfMsg->setKind(STOP);
        scheduleAt(stopTime, selfMsg);
    }
}

void UdpSinkCustom::processStop()
{
    if (!multicastGroup.isUnspecified())
        socket.leaveMulticastGroup(multicastGroup); // FIXME should be done by socket.close()
    socket.close();
}

void UdpSinkCustom::processPacket(inet::Packet *pk)
{
    EV_INFO << "Received packet: " << inet::UdpSocket::getReceivedPacketInfo(pk) << inet::endl;
    emit(inet::packetReceivedSignal, pk);
    delete pk;

    numReceived++;
}

void UdpSinkCustom::handleStartOperation(inet::LifecycleOperation *operation)
{
    inet::simtime_t start = std::max(startTime, inet::simTime());
    if ((stopTime < SIMTIME_ZERO) || (start < stopTime) || (start == stopTime && startTime == stopTime)) {
        selfMsg->setKind(START);
        scheduleAt(start, selfMsg);
    }
}

void UdpSinkCustom::handleStopOperation(inet::LifecycleOperation *operation)
{
    cancelEvent(selfMsg);
    if (!multicastGroup.isUnspecified())
        socket.leaveMulticastGroup(multicastGroup); // FIXME should be done by socket.close()
    socket.close();
    delayActiveOperationFinish(par("stopOperationTimeout"));
}

void UdpSinkCustom::handleCrashOperation(inet::LifecycleOperation *operation)
{
    cancelEvent(selfMsg);
    if (operation->getRootModule() != getContainingNode(this)) { // closes socket when the application crashed only
        if (!multicastGroup.isUnspecified())
            socket.leaveMulticastGroup(multicastGroup); // FIXME should be done by socket.close()
        socket.destroy(); // TODO  in real operating systems, program crash detected by OS and OS closes sockets of crashed programs.
    }
}

} // namespace inet

