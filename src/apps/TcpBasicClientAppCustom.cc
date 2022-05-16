//
// Copyright (C) 2004 OpenSim Ltd.
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

#include "TcpBasicClientAppCustom.h"

#include <sstream>
#include <fstream>

#include "inet/applications/tcpapp/GenericAppMsg_m.h"
#include "inet/common/ModuleAccess.h"
#include "inet/common/TimeTag_m.h"
#include "inet/common/lifecycle/ModuleOperations.h"
#include "inet/common/packet/Packet.h"

namespace inet {

#define MSGKIND_CONNECT    0
#define MSGKIND_SEND       1

Define_Module(TcpBasicClientAppCustom);

TcpBasicClientAppCustom::~TcpBasicClientAppCustom()
{
    cancelAndDelete(timeoutMsg);
}

void TcpBasicClientAppCustom::initialize(int stage)
{
    TcpAppBase::initialize(stage);
    if (stage == INITSTAGE_LOCAL) {
        numRequestsToSend = 0;
        earlySend = false; // TODO make it parameter
        WATCH(numRequestsToSend);
        WATCH(earlySend);

        startTime = par("startTime");
        stopTime = par("stopTime");
        if (stopTime >= SIMTIME_ZERO && stopTime < startTime)
            throw cRuntimeError("Invalid startTime/stopTime parameters");
        timeoutMsg = new cMessage("timer");

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
        fout << "timestamp,bitrate,mos\n";
        fout.close();

        lastCheckTime = simTime();
        lastCheckBits = 0;
        lastMos = 0;

    }
}

void TcpBasicClientAppCustom::handleStartOperation(LifecycleOperation *operation)
{
    simtime_t now = simTime();
    simtime_t start = std::max(startTime, now);
    if (timeoutMsg && ((stopTime < SIMTIME_ZERO) || (start < stopTime) || (start == stopTime && startTime == stopTime))) {
        timeoutMsg->setKind(MSGKIND_CONNECT);
        scheduleAt(start, timeoutMsg);
    }
}

void TcpBasicClientAppCustom::handleStopOperation(LifecycleOperation *operation)
{
    cancelEvent(timeoutMsg);
    if (socket.getState() == TcpSocket::CONNECTED || socket.getState() == TcpSocket::CONNECTING || socket.getState() == TcpSocket::PEER_CLOSED)
        close();
}

void TcpBasicClientAppCustom::handleCrashOperation(LifecycleOperation *operation)
{
    cancelEvent(timeoutMsg);
    if (operation->getRootModule() != getContainingNode(this))
        socket.destroy();
}

void TcpBasicClientAppCustom::sendRequest()
{
    long requestLength = par("requestLength");
    replyLength = par("replyLength");
    if (requestLength < 1)
        requestLength = 1;
    if (replyLength < 1)
        replyLength = 1;

    const auto& payload = makeShared<GenericAppMsg>();
    Packet *packet = new Packet("data");
    payload->setChunkLength(B(requestLength));
    payload->setExpectedReplyLength(B(replyLength));
    payload->setServerClose(false);
    payload->addTag<CreationTimeTag>()->setCreationTime(simTime());
    packet->insertAtBack(payload);

    EV_INFO << "sending request with " << requestLength << " bytes, expected reply length " << replyLength << " bytes,"
            << "remaining " << numRequestsToSend - 1 << " request\n";

    downloadBegin = simTime();
    bitsReceived = 0;

    sendPacket(packet);
}

void TcpBasicClientAppCustom::handleTimer(cMessage *msg)
{
    std::string currentNumber = std::to_string(getIndex());
    std::string fileName = "configs/TCPconf/";
    fileName += "app";
    fileName += currentNumber;
    fileName += ".txt";
    std::fstream fin;
    fin.open(fileName, std::ios::in);
    std::string flag_s;
    getline(fin, flag_s);
    if (flag_s.length() > 0) {
        flag = std::stoi(flag_s);
        EV_INFO << "handleTimer: New flag read from file - " << flag << inet::endl;
    } else {
        EV_WARN << "handleTimer: Could not read new flag from file. Keeping old flag - " << flag << inet::endl;
    }
    fin.close(); //close the file object.
    switch (msg->getKind()) {
        case MSGKIND_CONNECT:
            if (flag) {
                connect(); // active OPEN
            } else {
                if (timeoutMsg) {
                    simtime_t d = par("idleInterval");
                    rescheduleAfterOrDeleteTimer(d, MSGKIND_CONNECT);
                }
            }

            // significance of earlySend: if true, data will be sent already
            // in the ACK of SYN, otherwise only in a separate packet (but still
            // immediately)
            if (earlySend)
                sendRequest();
            break;

        case MSGKIND_SEND:
            sendRequest();
            numRequestsToSend--;
            // no scheduleAt(): next request will be sent when reply to this one
            // arrives (see socketDataArrived())
            break;

        default:
            throw cRuntimeError("Invalid timer msg: kind=%d", msg->getKind());
    }
}

void TcpBasicClientAppCustom::socketEstablished(TcpSocket *socket)
{
    TcpAppBase::socketEstablished(socket);

    // determine number of requests in this session
    numRequestsToSend = par("numRequestsPerSession");
    if (numRequestsToSend < 1)
        numRequestsToSend = 1;

    // perform first request if not already done (next one will be sent when reply arrives)
    if (!earlySend)
        sendRequest();

    numRequestsToSend--;
}

void TcpBasicClientAppCustom::rescheduleAfterOrDeleteTimer(simtime_t d, short int msgKind)
{
    if (stopTime < SIMTIME_ZERO || d < stopTime) {
        timeoutMsg->setKind(msgKind);
        rescheduleAfter(d, timeoutMsg);
    }
    else {
        cancelAndDelete(timeoutMsg);
        timeoutMsg = nullptr;
    }
}

void TcpBasicClientAppCustom::socketDataArrived(TcpSocket *socket, Packet *msg, bool urgent)
{
    bitsReceived += msg->getBitLength();
    if (bitsReceived >= replyLength*8) {
        simtime_t curTime = simTime();
        double downloadTime = ((double) curTime.raw() - (double) downloadBegin.raw()) / (double) pow(10,12);
        double avgBandwidth = (double) bitsReceived / downloadTime;
        double bwkbps = avgBandwidth / 1000;
        double tempMos = -1.68 * log(downloadTime) + 9.61;
        lastMos = std::max(1.0, std::min(tempMos, 5.0));
        bitsReceived = 0;
    }

    simtime_t curTime = simTime();
    lastCheckBits += msg->getBitLength() + 320;

    double downloadTime = ((double) curTime.raw() - (double) lastCheckTime.raw()) / (double) pow(10,12);
    if (downloadTime >= 0.9) {
        double avgBandwidth = (double) lastCheckBits / downloadTime;

        std::fstream fout;
        fout.open(fileName, std::ios::app);
        std::string timeInfo;
        timeInfo = curTime.str();
        timeInfo += ",";
        timeInfo += std::to_string(avgBandwidth / 1000);
        timeInfo += ",";
        timeInfo += std::to_string(lastMos);
        timeInfo += "\n";
        fout << timeInfo;
        fout.close();

        lastCheckTime = inet::simTime();
        lastCheckBits = 0;
    }

    TcpAppBase::socketDataArrived(socket, msg, urgent);

    if (numRequestsToSend > 0) {
        EV_INFO << "reply arrived\n";

        if (timeoutMsg) {
            simtime_t d = par("thinkTime");
            rescheduleAfterOrDeleteTimer(d, MSGKIND_SEND);
        }
    }
    else if (socket->getState() != TcpSocket::LOCALLY_CLOSED) {
        EV_INFO << "reply to last request arrived, closing session\n";
        close();
    }
}

void TcpBasicClientAppCustom::close()
{
    TcpAppBase::close();
    cancelEvent(timeoutMsg);
}

void TcpBasicClientAppCustom::socketClosed(TcpSocket *socket)
{
    TcpAppBase::socketClosed(socket);

    // start another session after a delay
    if (timeoutMsg) {
        simtime_t d = par("idleInterval");
        rescheduleAfterOrDeleteTimer(d, MSGKIND_CONNECT);
    }
}

void TcpBasicClientAppCustom::socketFailure(TcpSocket *socket, int code)
{
    TcpAppBase::socketFailure(socket, code);

    // reconnect after a delay
    if (timeoutMsg) {
        simtime_t d = par("reconnectInterval");
        rescheduleAfterOrDeleteTimer(d, MSGKIND_CONNECT);
    }
}

} // namespace inet

