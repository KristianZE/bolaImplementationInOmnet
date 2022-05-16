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

#include "UdpBasicAppCustom.h"

#include <fstream>

#include "inet/applications/base/ApplicationPacket_m.h"
#include "inet/common/ModuleAccess.h"
#include "inet/common/TagBase_m.h"
#include "inet/common/TimeTag_m.h"
#include "inet/common/lifecycle/ModuleOperations.h"
#include "inet/common/packet/Packet.h"
#include "inet/networklayer/common/FragmentationTag_m.h"
#include "inet/networklayer/common/L3AddressResolver.h"
#include "inet/transportlayer/contract/udp/UdpControlInfo_m.h"

namespace improved5gns{

Define_Module(UdpBasicAppCustom);

UdpBasicAppCustom::~UdpBasicAppCustom()
{
    cancelAndDelete(selfMsg);
}

void UdpBasicAppCustom::initialize(int stage)
{
    ClockUserModuleMixin::initialize(stage);

    if (stage == inet::INITSTAGE_LOCAL) {
        numSent = 0;
        numReceived = 0;
        WATCH(numSent);
        WATCH(numReceived);

        localPort = par("localPort");
        destPort = par("destPort");
        startTime = par("startTime");
        stopTime = par("stopTime");
        packetName = par("packetName");
        dontFragment = par("dontFragment");
        if (stopTime >= inet::CLOCKTIME_ZERO && stopTime < startTime)
            throw inet::cRuntimeError("Invalid startTime/stopTime parameters");
        selfMsg = new inet::ClockEvent("sendTimer");
        ival = par("sendInterval").doubleValue();
    }
}

void UdpBasicAppCustom::finish()
{
    recordScalar("packets sent", numSent);
    recordScalar("packets received", numReceived);
    ApplicationBase::finish();
}

void UdpBasicAppCustom::setSocketOptions()
{
    int timeToLive = par("timeToLive");
    if (timeToLive != -1)
        socket.setTimeToLive(timeToLive);

    int dscp = par("dscp");
    if (dscp != -1)
        socket.setDscp(dscp);

    int tos = par("tos");
    if (tos != -1)
        socket.setTos(tos);

    const char *multicastInterface = par("multicastInterface");
    if (multicastInterface[0]) {
        inet::IInterfaceTable *ift = inet::getModuleFromPar<inet::IInterfaceTable>(par("interfaceTableModule"), this);
        inet::NetworkInterface *ie = ift->findInterfaceByName(multicastInterface);
        if (!ie)
            throw inet::cRuntimeError("Wrong multicastInterface setting: no interface named \"%s\"", multicastInterface);
        socket.setMulticastOutputInterface(ie->getInterfaceId());
    }

    bool receiveBroadcast = par("receiveBroadcast");
    if (receiveBroadcast)
        socket.setBroadcast(true);

    bool joinLocalMulticastGroups = par("joinLocalMulticastGroups");
    if (joinLocalMulticastGroups) {
        inet::MulticastGroupList mgl = inet::getModuleFromPar<inet::IInterfaceTable>(par("interfaceTableModule"), this)->collectMulticastGroups();
        socket.joinLocalMulticastGroups(mgl);
    }
    socket.setCallback(this);
}

inet::L3Address UdpBasicAppCustom::chooseDestAddr()
{
    int k = intrand(destAddresses.size());
    if (destAddresses[k].isUnspecified() || destAddresses[k].isLinkLocal()) {
        inet::L3AddressResolver().tryResolve(destAddressStr[k].c_str(), destAddresses[k]);
    }
    return destAddresses[k];
}

void UdpBasicAppCustom::sendPacket()
{
    std::ostringstream str;
    str << packetName << "-" << numSent;
    inet::Packet *packet = new inet::Packet(str.str().c_str());
    if (dontFragment)
        packet->addTag<inet::FragmentationReq>()->setDontFragment(true);
    const auto& payload = inet::makeShared<inet::ApplicationPacket>();
    payload->setChunkLength(inet::B(par("messageLength")));
    payload->setSequenceNumber(numSent);
    payload->addTag<inet::CreationTimeTag>()->setCreationTime(inet::simTime());
    packet->insertAtBack(payload);
    inet::L3Address destAddr = chooseDestAddr();
    emit(inet::packetSentSignal, packet);
    socket.sendTo(packet, destAddr, destPort);
    numSent++;
}

void UdpBasicAppCustom::processStart()
{
    socket.setOutputGate(gate("socketOut"));
    const char *localAddress = par("localAddress");
    socket.bind(*localAddress ? inet::L3AddressResolver().resolve(localAddress) : inet::L3Address(), localPort);
    setSocketOptions();

    const char *destAddrs = par("destAddresses");
    inet::cStringTokenizer tokenizer(destAddrs);
    const char *token;

    while ((token = tokenizer.nextToken()) != nullptr) {
        destAddressStr.push_back(token);
        inet::L3Address result;
        inet::L3AddressResolver().tryResolve(token, result);
        if (result.isUnspecified())
            EV_ERROR << "cannot resolve destination address: " << token << inet::endl;
        destAddresses.push_back(result);
    }

    if (!destAddresses.empty()) {
        selfMsg->setKind(SEND);
        processSend();
    }
    else {
        if (stopTime >= inet::CLOCKTIME_ZERO) {
            selfMsg->setKind(STOP);
            scheduleClockEventAt(stopTime, selfMsg);
        }
    }
}

void UdpBasicAppCustom::processSend()
{
    std::string currentNumber = std::to_string(getIndex());
    std::string fileName = "configs/UDPconf/";
    fileName += "app";
    fileName += currentNumber;
    fileName += ".txt";
    std::fstream fin;
    fin.open(fileName, std::ios::in);
    std::string flag_s;
    getline(fin, flag_s);
//    EV_INFO << "processSend: Flag - " << flag_s << inet::endl;
    std::string ival_s;
    getline(fin, ival_s);
//    EV_INFO << "processSend: Interval - " << ival_s << inet::endl;
    fin.close(); //close the file object.
    if (ival_s.length() > 0) {
        ival = std::stod(ival_s);
        EV_INFO << "processSend: New interval read from file - " << ival << inet::endl;
    } else {
        EV_WARN << "processSend: Could not read new interval from file. Keeping old interval - " << ival << inet::endl;
    }
    if (flag_s.length() > 0) {
        flag = std::stoi(flag_s);
        EV_INFO << "processSend: New flag read from file - " << flag << inet::endl;
    } else {
        EV_WARN << "processSend: Could not read new flag from file. Keeping old flag - " << flag << inet::endl;
    }

    if (flag) {
        sendPacket();
    }

//    inet::clocktime_t d = par("sendInterval");
    inet::clocktime_t d = inet::ClockTime(ival);
    if (stopTime < inet::CLOCKTIME_ZERO || getClockTime() + d < stopTime) {
        selfMsg->setKind(SEND);
        scheduleClockEventAfter(d, selfMsg);
    }
    else {
        selfMsg->setKind(STOP);
        scheduleClockEventAt(stopTime, selfMsg);
    }
}

void UdpBasicAppCustom::processStop()
{
    socket.close();
}

void UdpBasicAppCustom::handleMessageWhenUp(inet::cMessage *msg)
{
    if (msg->isSelfMessage()) {
        ASSERT(msg == selfMsg);
        switch (selfMsg->getKind()) {
            case START:
                processStart();
                break;

            case SEND:
                processSend();
                break;

            case STOP:
                processStop();
                break;

            default:
                throw inet::cRuntimeError("Invalid kind %d in self message", (int)selfMsg->getKind());
        }
    }
    else
        socket.processMessage(msg);
}

void UdpBasicAppCustom::socketDataArrived(inet::UdpSocket *socket, inet::Packet *packet)
{
    // process incoming packet
    processPacket(packet);
}

void UdpBasicAppCustom::socketErrorArrived(inet::UdpSocket *socket, inet::Indication *indication)
{
    EV_WARN << "Ignoring UDP error report " << indication->getName() << inet::endl;
    delete indication;
}

void UdpBasicAppCustom::socketClosed(inet::UdpSocket *socket)
{
    if (operationalState == State::STOPPING_OPERATION)
        startActiveOperationExtraTimeOrFinish(par("stopOperationExtraTime"));
}

void UdpBasicAppCustom::refreshDisplay() const
{
    ApplicationBase::refreshDisplay();

    char buf[100];
    sprintf(buf, "rcvd: %d pks\nsent: %d pks", numReceived, numSent);
    getDisplayString().setTagArg("t", 0, buf);
}

void UdpBasicAppCustom::processPacket(inet::Packet *pk)
{
    emit(inet::packetReceivedSignal, pk);
    EV_INFO << "Received packet: " << inet::UdpSocket::getReceivedPacketInfo(pk) << inet::endl;
    delete pk;
    numReceived++;
}

void UdpBasicAppCustom::handleStartOperation(inet::LifecycleOperation *operation)
{
    inet::clocktime_t start = std::max(startTime, getClockTime());
    if ((stopTime < inet::CLOCKTIME_ZERO) || (start < stopTime) || (start == stopTime && startTime == stopTime)) {
        selfMsg->setKind(START);
        scheduleClockEventAt(start, selfMsg);
    }
}

void UdpBasicAppCustom::handleStopOperation(inet::LifecycleOperation *operation)
{
    cancelEvent(selfMsg);
    socket.close();
    delayActiveOperationFinish(par("stopOperationTimeout"));
}

void UdpBasicAppCustom::handleCrashOperation(inet::LifecycleOperation *operation)
{
    cancelClockEvent(selfMsg);
    socket.destroy(); // TODO  in real operating systems, program crash detected by OS and OS closes sockets of crashed programs.
}

} // namespace inet

