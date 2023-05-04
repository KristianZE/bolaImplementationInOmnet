package improved5gns.apps;

@namespace(inet);
import inet.applications.contract.IApp;
//
//
//  TCPVideoStreamCliAppV2lite
//
//  1. An adaptation of Navarro Joaquim's code (https://github.com/navarrojoaquin/adaptive-video-tcp-omnet)
//     created on 8 de dez de 2017 by Anderson Andrei da Silva & Patrick Menani Abrah������������������������������������������������������o at University of S������������������������������������������������������o Paulo
//
//  2. Edited and adapted for Omnet++ 5.1 with INET 3.5 by Marcin Bosk at the Technische Universit������t Berlin in January 2019
//
//
// Client for adaptive video streaming over TCP. This client requests a server
// 1s of video with different quality level depending on the buffer ocuppation.
// May be used as a rough model of MPEG-DASH.
//
// The model communicates with the server in sessions. During a session,
// the client opens a single TCP connection to the server, sends several
// requests (always waiting for the complete reply to arrive before
// sending a new request), and closes the connection.
//
// The server app should be ~TCPGenericSrvApp; the model sends ~GenericAppMsg
// messages.
//
// <b>Configuring App</b>
//
// See the parameter list to get an overview of the supported options
//
// The module parameter dataTransferMode should be set the transfer mode in TCP layer.
// You should set dataTransferMode to "object"
//
//   -# use "object", which transmits
//      cMessage objects (and subclasses) over a TCP connection. The same
//      message object sequence that was sent by the client to the
//      sender-side TCP entity will be reproduced on the receiver side.
//      If a client sends a cMessage with length = 1 megabyte, the
//      receiver-side client will receive the same message object (or a clone)
//      after the TCP entities have completed simulating the transmission
//      of 1 megabyte over the connection. This is a different behaviour
//      from TCPVirtualDataSendQueue/RcvQueue.
//      This mode is not implemented in ~TCP_NSC yet.
//
//
// @see ~TCPGenericSrvApp, ~GenericAppMsg, ~TelnetApp
//

simple TCPVideoStreamCliAppV2lite like IApp {
    
    parameters:
        @class(TCPVideoStreamCliAppV2lite);
        // General parameters
        string 			localAddress = default(""); // may be left empty ("")
        int 			localPort = default(-1); // port number to listen on
        string 			connectAddress = default("");  // server address (may be symbolic)
        int 			connectPort = default(1000); // port number to connect to
        string 			dataTransferMode @enum("bytecount","object","bytestream") = default("bytecount");
//        volatile double video_startTime @unit(s) = default(1s); // time first session begins
        double          startTime @unit(s) = default(1s); // time first session begins
        double 			stopTime @unit(s) = default(0s);  // time of finish sending, 0 means infinity
        volatile double idleInterval @unit(s); // time gap between sessions
        volatile int 	requestLength @unit(B) = default(200B); // length of a request
        volatile double reconnectInterval @unit(s) = default(10s);  // if connection breaks, waits this much before trying to reconnect
        volatile int    numRequestsPerSession = default(1);  // number of requests sent per session
        volatile double thinkTime @unit(s); // time gap between requests
        int timeToLive = default(-1); // if not -1, set the TTL (IPv4) or Hop Limit (IPv6) field of sent packets to this value
        int dscp = default(-1); // if not -1, set the DSCP (IPv4/IPv6) field of sent packets to this value
        int tos = default(-1); // if not -1, set the Type Of Service (IPv4) / Traffic Class (IPv6) field of sent packets to this value
        
        // Adaptive Video parameters
        string 			video_resolution = default("240 360 480 720 1080"); // Chosen resolution. Available 240 (as 240p), 360 (as 360p), 480 (as 480p), 720 (as 720p) and 1080 (as 1080p). Based on ITU-T P.1203.1 Table 1-1
        int 			manifest_size @units(byte) = default(100000);
        int 			video_buffer_max_length @unit(s) = default(25s); // buffer max length in seconds
        int 			video_duration @unit(s) = default(300s); // video length in seconds
        int				segment_length @unit(s) = default(3s);  // video segment length in seconds
        string			useFlexibleBitrate = default("flexible"); // should flexible bitrate offset be used. Possible "flexible" or  "non-flexible"
        
        // General statistics
        @display("i=block/app");
        @signal[sentPk](type=cPacket);
        @signal[rcvdPk](type=cPacket);
        @signal[packetReceived](type=inet::Packet);
        @signal[connect](type=long);  // 1 for open, -1 for close
        @statistic[rcvdPk](title="packets received"; source=rcvdPk; record=count,"sum(packetBytes)","vector(packetBytes)"; interpolationmode=none);
        @statistic[sentPk](title="packets sent"; source=sentPk; record=count,"sum(packetBytes)","vector(packetBytes)"; interpolationmode=none);
        @statistic[endToEndDelay](title="end-to-end delay"; source="dataAge(packetReceived)"; unit=s; record=histogram,vector; interpolationmode=none);
        @statistic[numActiveSessions](title="number of active sessions"; source="sum(connect)"; record=max,timeavg,vector; interpolationmode=sample-hold);
        @statistic[numSessions](title="total number of sessions"; source="sum(connect+1)/2"; record=last);
        @signal[positionX](type=double);
        @statistic[positionX](title="position of node on X axis"; source="positionX"; record=last);
        @signal[positionY](type=double);
        @statistic[positionY](title="position of node on Y axis"; source="positionY"; record=last);
        
        // Adaptive Video statistics
        @signal[DASHBufferLength](type="long"); //EDIT! changed from int to long in order for it to cooperate with this version of omnet
        @statistic[DASHBufferLength](title="Video buffer length (in seconds)"; record=vector);
        @signal[DASHVideoBitrate](type="long"); //EDIT! changed from int to long in order for it to cooperate with this version of omnet
        @statistic[DASHVideoBitrate](title="Requested video bitrate"; record=vector);
        @signal[DASHVideoResolution](type="long"); //EDIT! changed from int to long in order for it to cooperate with this version of omnet
        @statistic[DASHVideoResolution](title="Requested video resolution"; record=vector);
        @signal[DASHVideoPlaybackPointer](type="long"); //EDIT! changed from int to long in order for it to cooperate with this version of omnet
        @statistic[DASHVideoPlaybackPointer](title="Video playback pointer"; record=vector);
        @signal[DASHReceivedBytes](type="long"); //Bytes received with each transmission
        @statistic[DASHReceivedBytes](title="Bytes received with last segment"; record=vector);
        @signal[DASHVideoPlaybackStatus](type="bool");
        @statistic[DASHVideoPlaybackStatus](title="Video playback status (playing=1, buffering=0)"; record=vector);
//        @signal[DASHmosScore](type="double");
//        @statistic[DASHmosScore](title="MOS Score calculated after the video finished"; record=vector);
       	@signal[BOLAQualityLevel](type="int"); //EDIT! changed from int to long in order for it to cooperate with this version of omnet
        @statistic[BOLAQualityLevel](title="Requested BOLA quality level (resolution)"; record=vector);
        
    gates:
        input socketIn @labels(TcpCommand/up);
        output socketOut @labels(TcpCommand/down);
}