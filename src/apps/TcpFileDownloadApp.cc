//
// Copyright (C) 2004 Andras Varga
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
// along with this program; if not, see <http://www.gnu.org/licenses/>.
//

#include "TcpFileDownloadApp.h"

#include "inet/applications/tcpapp/GenericAppMsg_m.h"
#include "inet/common/ModuleAccess.h"
#include "inet/common/lifecycle/ModuleOperations.h"
#include "inet/common/packet/Packet.h"
#include "inet/common/TimeTag_m.h"

#include <tgmath.h>

namespace inet {

#define MSGKIND_CONNECT    0
#define MSGKIND_SEND       1

Define_Module(TcpFileDownloadApp);

TcpFileDownloadApp::~TcpFileDownloadApp()
{
    cancelAndDelete(timeoutMsg);
}

void TcpFileDownloadApp::initialize(int stage)
{
    TcpAppBase::initialize(stage);
    if (stage == INITSTAGE_LOCAL) {
        numRequestsToSend = 0;
        earlySend = false;    // TBD make it parameter
        WATCH(numRequestsToSend);
        WATCH(earlySend);

        mosScoreSignal = registerSignal("mosScore");
        downloadTimeSignal = registerSignal("downloadTime");
        averageDownloadThroughputSignal = registerSignal("averageDownloadThroughput");

        startTime = par("startTime");
        stopTime = par("stopTime");
        if (stopTime >= SIMTIME_ZERO && stopTime < startTime)
            throw cRuntimeError("Invalid startTime/stopTime parameters");
        timeoutMsg = new cMessage("timer");
    }
}

void TcpFileDownloadApp::handleStartOperation(LifecycleOperation *operation)
{
    simtime_t now = simTime();
    simtime_t start = std::max(startTime, now);
    if (timeoutMsg && ((stopTime < SIMTIME_ZERO) || (start < stopTime) || (start == stopTime && startTime == stopTime))) {
        timeoutMsg->setKind(MSGKIND_CONNECT);
        scheduleAt(start, timeoutMsg);
    }
}

void TcpFileDownloadApp::handleStopOperation(LifecycleOperation *operation)
{
    cancelEvent(timeoutMsg);
    if (socket.getState() == TcpSocket::CONNECTED || socket.getState() == TcpSocket::CONNECTING || socket.getState() == TcpSocket::PEER_CLOSED)
        close();
}

void TcpFileDownloadApp::handleCrashOperation(LifecycleOperation *operation)
{
    cancelEvent(timeoutMsg);
    if (operation->getRootModule() != getContainingNode(this))
        socket.destroy();
}

void TcpFileDownloadApp::sendRequest()
{
    long requestLength = par("requestLength");
    replyLength = par("replyLength");
    if (requestLength < 1)
        requestLength = 1;
    if (replyLength < 1)
        replyLength = 1;

    const auto& payload = makeShared<GenericAppMsg>();
    Packet *packet = new Packet("data");
    payload->addTag<CreationTimeTag>()->setCreationTime(simTime());
    payload->setChunkLength(B(requestLength));
    payload->setExpectedReplyLength(B(replyLength));
    payload->setServerClose(false);
    packet->insertAtBack(payload);

    EV_INFO << "sending request with " << requestLength << " bytes, expected reply length " << replyLength << " bytes,"
            << "remaining " << numRequestsToSend - 1 << " request\n";

    downloadBegin = simTime();
    bitsReceived = 0;
    sendPacket(packet);
}

void TcpFileDownloadApp::handleTimer(cMessage *msg)
{
    switch (msg->getKind()) {
        case MSGKIND_CONNECT:
            connect();    // active OPEN

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

void TcpFileDownloadApp::socketEstablished(TcpSocket *socket)
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

void TcpFileDownloadApp::rescheduleOrDeleteTimer(simtime_t d, short int msgKind)
{
    cancelEvent(timeoutMsg);

    if (stopTime < SIMTIME_ZERO || d < stopTime) {
        timeoutMsg->setKind(msgKind);
        scheduleAt(d, timeoutMsg);
    }
    else {
        delete timeoutMsg;
        timeoutMsg = nullptr;
    }
}

void TcpFileDownloadApp::socketDataArrived(TcpSocket *socket, Packet *msg, bool urgent)
{
    bitsReceived += msg->getBitLength();
    TcpAppBase::socketDataArrived(socket, msg, urgent);



    if (bitsReceived >= replyLength*8) {
        simtime_t curTime = simTime();
        double downloadTime = ((double) curTime.raw() - (double) downloadBegin.raw()) / (double) pow(10,12);
        double avgBandwidth = (double) bitsReceived / downloadTime;
        double bwkbps = avgBandwidth / 1000;
//        double mos = -1.68 * log(downloadTime) + 9.61;
//        double mos = a * log10(b * bandwidth)
//        double a = 1.1667;
//        double b = 0.07197;
//        double mos = a * log10(b * bwkbps);
        double tempMos = -1.68 * log(downloadTime) + 9.61;
        double mos = std::max(1.0, std::min(tempMos, 5.0));


        emit(mosScoreSignal, mos);
        emit(downloadTimeSignal, downloadTime);
        emit(averageDownloadThroughputSignal, avgBandwidth);
        bitsReceived = 0;
    }

    if (numRequestsToSend > 0) {
        EV_INFO << "reply arrived\n";

        if (timeoutMsg) {
            simtime_t d = simTime() + par("thinkTime");
            rescheduleOrDeleteTimer(d, MSGKIND_SEND);
        }
    }
    else if (socket->getState() != TcpSocket::LOCALLY_CLOSED) {
        EV_INFO << "reply to last request arrived, closing session\n";
        close();
    }
}

void TcpFileDownloadApp::close()
{
    TcpAppBase::close();
    cancelEvent(timeoutMsg);
}

void TcpFileDownloadApp::socketClosed(TcpSocket *socket)
{
    TcpAppBase::socketClosed(socket);

    // start another session after a delay
    if (timeoutMsg) {
        simtime_t d = simTime() + par("idleInterval");
        rescheduleOrDeleteTimer(d, MSGKIND_CONNECT);
    }
}

void TcpFileDownloadApp::socketFailure(TcpSocket *socket, int code)
{
    TcpAppBase::socketFailure(socket, code);

    // reconnect after a delay
    if (timeoutMsg) {
        simtime_t d = simTime() + par("reconnectInterval");
        rescheduleOrDeleteTimer(d, MSGKIND_CONNECT);
    }
}

} // namespace inet

