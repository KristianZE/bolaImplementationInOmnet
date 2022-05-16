/*
 *  TCPLiveVideoStreamCliAppLite.h
 *
 *  1. An adaptation of Navarro Joaquim's code (https://github.com/navarrojoaquin/adaptive-video-tcp-omnet)
 *     created on 8 de dez de 2017 by Anderson Andrei da Silva & Patrick Menani Abrahao at University of Sao Paulo
 *
 *  2. Edited and adapted for Omnet++ 5.5.1 with INET 4.2.0 by Marcin Bosk at the Technische Universität Berlin in February 2020
 *
 */

#ifndef TCPVIDEOSTREAMCLIAPP_H_
#define TCPVIDEOSTREAMCLIAPP_H_

#include <omnetpp.h>
#include <omnetpp/csimulation.h>
#include <algorithm>
#include <list>
#include <fstream>
#include <iostream>
#include <cstdlib>
#include <cstdio>
#include <random>
#include <string>
#include "inet/common/INETDefs.h"
#include "inet/applications/tcpapp/TcpBasicClientApp.h"

namespace inet {

class TCPLiveVideoStreamCliAppLite: public TcpBasicClientApp {

protected:

    // Adaptive Video (AV) and other parameters
    std::vector<int> video_resolution;
    int video_buffer_max_length;
    int video_duration;
    int segment_length;                     // M: Video is downloaded segment-wise, this is the segments length
    int numRequestsToSend;                  // requests to send in this session. Each request = 1s of video
    int video_buffer;                       // current length of the buffer in seconds
    int video_buffer_min_rebuffering = 2; // if video_buffer < video_buffer_min_rebuffering then a rebuffering event occurs
    int manifest_size;

    int num_curr_requests = 0;

    std::string videoType;
    double delayThreshold;
    double speedupRate;

    simtime_t refVidStartTime;

    simtime_t startTime;
    simtime_t stopTime;
    cMessage *timeoutMsg;

    // Statistics collection variables
    int video_current_quality_index;        // requested quality
    bool video_is_playing;
    int video_playback_pointer;
    int received_bytes;
    long msgsRcvd;
    long msgsSent;
    long bytesRcvd;
    long bytesSent;

    std::string nodeIdentifier;

    // Signals for statistics collection
    simsignal_t DASH_buffer_length_signal;
    simsignal_t DASH_video_bitrate_signal;
    simsignal_t DASH_video_resolution_signal;
    simsignal_t DASH_video_is_playing_signal;
    simsignal_t DASH_playback_pointer;
    simsignal_t DASH_received_bytes;
//    simsignal_t DASHmosScoreSignal;
    simsignal_t DASH_live_delay_signal;
    simsignal_t DASH_estimated_bitrate_signal;

    static simsignal_t rcvdPkSignal;
    static simsignal_t sentPkSignal;

    static simsignal_t positionX;
    static simsignal_t positionY;

    // Flags to avoid multiple quality switches when the buffer is at full capacity
    bool can_switch = true;
    int switch_timeout = 1;
    int switch_timer = switch_timeout;

    // Other flags and guards
    std::list<long> requestedReplyLengths;
    std::list<simtime_t> requestTimes;
    long cumulatedReceivedBytes;
    bool manifestAlreadySent = false;
    bool video_is_buffering = true;
    unsigned long uniqueIdentifier;

//    std::list<double> segmentByteSize;
//    std::list<double> segmentDownloadTime;
    std::list<double> segmentDownloadBitrate;

    //
    std::string useFlexibleFlag;

    // Enhanced switch algorithm (estimate available bit rate before switching to higher quality level)
//    int packetTimeArrayLength = 5;
//    simtime_t packetTime[5];
//    int packetTimePointer = 0;
//    simtime_t tLastPacketRequested;

    // Lists with collected statistics with timestamps used for MOS calculation
//    std::list<std::pair<simtime_t, bool>> videoPlaying;
//    std::list<std::pair<simtime_t, double>> bufferLength;
//    std::list<std::pair<simtime_t, double>> videoBitrate;
//    std::list<std::pair<simtime_t, int>> videoResolution;
//    std::list<std::pair<simtime_t, double>> playbackPointer;
//    std::list<std::pair<simtime_t, double>> receivedBytes;

    // Utility functions declarations
    /** Utility: sends a request to the server */
    virtual void sendRequest() override;

    /** Utility: cancel msgTimer and if d is smaller than stopTime, then schedule it to d,
     * otherwise delete msgTimer */

    virtual void rescheduleAfterOrDeleteTimer(simtime_t d, short int msgKind) override;

    /** Utility: calculate the MOS score based on collected data after the video finished */
//    void prepareCSV();
//    double calculateMOS();
    void nextVidSetup();

    void scheduleVideoPlayEvent();
    int generateRandomNumberFromRange(int min, int max);
    int generateRandomizedBitrate(int minBitrate, int maxBitrate);
    int getVideoBitrate(int resolution);
//    std::string getVResString(int resolution);
    double calculateEWMA(std::list<double> list, double alpha);
    int getMaxBitrate(int resolution);

public:
    TCPLiveVideoStreamCliAppLite();
    virtual ~TCPLiveVideoStreamCliAppLite();

protected:
    /** Redefined . */
    virtual void initialize(int stage) override;

    /** Redefined. */
    virtual void handleTimer(cMessage *msg) override;

    /** Redefined. */
    virtual void socketEstablished(TcpSocket *socket) override;

    /** Redefined. */
    virtual void socketDataArrived(TcpSocket *socket, Packet *msg, bool urgent) override;

    /** Redefined to start another session after a delay (currently not used). */
    virtual void socketClosed(TcpSocket *socket) override;

    /** Redefined to reconnect after a delay. */
    virtual void socketFailure(TcpSocket *socket, int code) override;

    virtual void refreshDisplay() const override;

};
} //namespace inet
#endif




