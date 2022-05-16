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

#include "TcpSimpleSshAppV2lite.h"

#include "inet/applications/tcpapp/GenericAppMsg_m.h"
#include "inet/common/ModuleAccess.h"
#include "inet/common/lifecycle/NodeStatus.h"
#include "inet/common/lifecycle/ModuleOperations.h"
#include "inet/common/packet/Packet.h"
#include "inet/common/TimeTag_m.h"

#include <tgmath.h>

#include <fstream>

#include <omnetpp.h>

#include <list>

namespace inet {

#define MSGKIND_CONNECT    0
#define MSGKIND_SEND       1
#define MSGKIND_CLOSE      2

Define_Module(TcpSimpleSshAppV2lite);


TcpSimpleSshAppV2lite::~TcpSimpleSshAppV2lite()
{
    cancelAndDelete(timeoutMsg);
}

void TcpSimpleSshAppV2lite::checkedScheduleAt(simtime_t t, cMessage *msg)
{
    if (stopTime < SIMTIME_ZERO || t < stopTime)
        scheduleAt(t, msg);
}

void TcpSimpleSshAppV2lite::initialize(int stage)
{
    TcpAppBase::initialize(stage);

    if (stage == INITSTAGE_LOCAL) {
        numCharsToType = numLinesToType = 0;
        WATCH(numCharsToType);
        WATCH(numLinesToType);

        rttSignal = registerSignal("roundTripTime");
        mosValueSignal = registerSignal("mosValue");
        simtime_t startTime = par("startTime");
        stopTime = par("stopTime");
        if (stopTime >= SIMTIME_ZERO && stopTime < startTime)
            throw cRuntimeError("Invalid startTime/stopTime parameters");
        timeoutMsg = new cMessage("timer");
        sendTime = 0;
        finalRTT = 0;
    }


}

void TcpSimpleSshAppV2lite::handleStartOperation(LifecycleOperation *operation)
{
    simtime_t now = simTime();
    simtime_t startTime = par("startTime");
    simtime_t start = std::max(startTime, now);
    if (timeoutMsg && ((stopTime < SIMTIME_ZERO) || (start < stopTime) || (start == stopTime && startTime == stopTime))) {
        timeoutMsg->setKind(MSGKIND_CONNECT);
        scheduleAt(start, timeoutMsg);
    }
}

void TcpSimpleSshAppV2lite::handleStopOperation(LifecycleOperation *operation)
{
    cancelEvent(timeoutMsg);
    if (socket.isOpen()) {
        TcpAppBase::close();
        delayActiveOperationFinish(par("stopOperationTimeout"));
    }
}

void TcpSimpleSshAppV2lite::handleCrashOperation(LifecycleOperation *operation)
{
    cancelEvent(timeoutMsg);
    if (operation->getRootModule() != getContainingNode(this))
        socket.destroy();
}

void TcpSimpleSshAppV2lite::handleTimer(cMessage *msg)
{
    switch (msg->getKind()) {
        case MSGKIND_CONNECT:
            EV_INFO << "user fires up telnet program\n";
            TcpAppBase::connect();
            listener = new TcpRttListener();
            EV << "TcpSimpleSshApp: Parent module = " << getParentModule()->getFullName() << "\n";
            getParentModule()->subscribe("rtt", listener);
            break;
//        We'll mimic the sha1 ETM 40 bytes tcp segment payload per keystroke https://www.trisul.org/blog/analysing-ssh/post.html
        case MSGKIND_SEND:
            if (numCharsToType > 0) {
                // user types a character and expects it to be echoed
                if (socket.getState() != 6) {// change here to eliminate LOCALLY_CLOSED socket state error
                    EV_INFO << "user types one character, " << numCharsToType - 1 << " more to go\n";
                    sendGenericAppMsg(40, 40);
                    numCharsToType--;
                }
                checkedScheduleAt(simTime() + par("keyPressDelay"), timeoutMsg);
            }
            else {
                if (socket.getState() != 6) {
                    EV_INFO << "user hits Enter key\n";
                    // Note: reply length must be at least 2, otherwise we'll think
                    // it's an echo when it comes back!
                    int tempReqRepLength = 10 + 1 + par("commandOutputLength").intValue();
                    int padLen = 0;
                    if (16 - (tempReqRepLength % 16) < 4) {
                        padLen = 32 - (tempReqRepLength % 16);
                    } else {
                        padLen = 16 - (tempReqRepLength % 16);
                    }
                    sendGenericAppMsg(40, tempReqRepLength + padLen);
                    sendTime = simTime();
                    numCharsToType = par("commandLength");
                }

                // Note: no checkedScheduleAt(), because user only starts typing next command
                // when output from previous one has arrived (see socketDataArrived())
            }
            break;

        case MSGKIND_CLOSE:
            EV_INFO << "user exits ssh program\n";
            TcpAppBase::close();
            break;
    }
}

void TcpSimpleSshAppV2lite::sendGenericAppMsg(int numBytes, int expectedReplyBytes)
{
    EV_INFO << "sending " << numBytes << " bytes, expecting " << expectedReplyBytes << endl;

    const auto& payload = makeShared<GenericAppMsg>();
    Packet *packet = new Packet("data");
    payload->addTag<CreationTimeTag>()->setCreationTime(simTime());
    payload->setChunkLength(B(numBytes));
    payload->setExpectedReplyLength(B(expectedReplyBytes));
    payload->setServerClose(false);
    packet->insertAtBack(payload);

    sendPacket(packet);
}

void TcpSimpleSshAppV2lite::socketEstablished(TcpSocket *socket)
{
    TcpAppBase::socketEstablished(socket);

    // schedule first sending
    numLinesToType = par("numCommands");
    EV_INFO << "user will type " << numLinesToType << " commands\n";
    numCharsToType = par("commandLength");
    timeoutMsg->setKind(numLinesToType > 0 ? MSGKIND_SEND : MSGKIND_CLOSE);
    checkedScheduleAt(simTime() + par("thinkTime"), timeoutMsg);
}

void TcpSimpleSshAppV2lite::socketDataArrived(TcpSocket *socket, Packet *msg, bool urgent)
{
    int64_t len = msg->getByteLength();
    EV << "SSH Client received data: " << msg << ", with length: " << len << "; CurTime: " << simTime() << "\n";
    EV << "SSH Client received data with creation time: " << msg->getCreationTime() << "\n";
    if (len == 40) {
        // this is an echo, ignore
        EV_INFO << "received echo\n";
    }
    else {
        // output from last typed command arrived.
        EV_INFO << "received output of command typed\n";
//        simtime_t currentTime = simTime();
//        simtime_t endToEndTime = currentTime - sendTime;
//        double precision = (double) endToEndTime.getScaleExp();
//        double decreaseExp = precision;// + 3.0;
//        double rtt = (double) endToEndTime.raw() * pow(10, decreaseExp);
//        emit(rttSignal, rtt);
//        finalRTT = rtt;
        simtime_t meanRtt = listener->getMeanRtt();
        double precision = (double) meanRtt.getScaleExp();
        finalRTT = (double) meanRtt.raw() * pow(10, precision);
        emit(rttSignal, finalRTT);
        getParentModule()->unsubscribe("rtt", listener);
//        delete(listener);
        // If user has finished working, she closes the connection, otherwise
        // starts typing again after a delay
        numLinesToType--;

        if (numLinesToType == 0) {
            EV_INFO << "user has no more commands to type\n";
            if (timeoutMsg->isScheduled())
                cancelEvent(timeoutMsg);
            timeoutMsg->setKind(MSGKIND_CLOSE);
            checkedScheduleAt(simTime() + par("thinkTime"), timeoutMsg);
        }
        else {
            EV_INFO << "user looks at output, then starts typing next command\n";
            if (!timeoutMsg->isScheduled()) {
                timeoutMsg->setKind(MSGKIND_SEND);
                checkedScheduleAt(simTime() + par("thinkTime"), timeoutMsg);
            }
        }
    }

    TcpAppBase::socketDataArrived(socket, msg, urgent);


//    delete(msg);
}

void TcpSimpleSshAppV2lite::socketClosed(TcpSocket *socket)
{
    TcpAppBase::socketClosed(socket);
    double meanRtt = finalRTT*1000; // In miliseconds

    if (meanRtt == 0) {
        meanRtt = 10000;
    }

//    std::string command = "python3 sshMOScalcFiles/code/sshMOS.py ";
//    std::string moduleName = getParentModule()->getFullName();
//    std::string configName = cSimulation::getActiveEnvir()->getConfigEx()->getActiveConfigName();
//    std::string runNumber = std::to_string(cSimulation::getActiveEnvir()->getConfigEx()->getActiveRunNumber());
//    std::string filename = "sshMOScalcFiles/tempResults/";
//    filename += moduleName;
//    filename += configName;
//    filename += runNumber;
//    filename += ".txt";
//    command += std::to_string(meanRtt);
//    command += " ";
//    command += filename;
//    std::system(command.c_str());
//
//    // Fetch the MOS value from the text file where it has just been saved
//    std::fstream fin;
//    EV << "File to open: " << filename << "\n";
//    fin.open(filename, std::ios::in);
//    double mosValue = 1;
//    std::string value;
//    if (fin.is_open()) {
//        if (getline(fin, value)) {
//            mosValue = std::stod(value);
//            EV << "Received MOS value: " << mosValue << "\n";
//        }
//    }
//    fin.close();
//    std::remove(filename.c_str());
//
//    emit(mosValueSignal, mosValue);

    cancelEvent(timeoutMsg);
    if (operationalState == TcpAppBase::State::OPERATING) {
        // start another session after a delay
        timeoutMsg->setKind(MSGKIND_CONNECT);
        checkedScheduleAt(simTime() + par("idleInterval"), timeoutMsg);
    }
    else if (operationalState == TcpAppBase::State::STOPPING_OPERATION) {
        if (!this->socket.isOpen())
            startActiveOperationExtraTimeOrFinish(par("stopOperationExtraTime"));
    }
}

void TcpSimpleSshAppV2lite::socketFailure(TcpSocket *socket, int code)
{
    TcpAppBase::socketFailure(socket, code);

    // reconnect after a delay
    cancelEvent(timeoutMsg);
    timeoutMsg->setKind(MSGKIND_CONNECT);
    checkedScheduleAt(simTime() + par("reconnectInterval"), timeoutMsg);
}

} // namespace inet

