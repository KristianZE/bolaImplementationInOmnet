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
// along with this program.  If not, see http://www.gnu.org/licenses/.
//

#include "inet/applications/voip/SimpleVoipPacket_m.h"
#include "SimpleVoipPacketSerializer.h"
#include "inet/common/packet/serializer/ChunkSerializerRegistry.h"

namespace inet {

Register_Serializer(SimpleVoipPacket, SimpleVoipPacketSerializer);

void SimpleVoipPacketSerializer::serialize(MemoryOutputStream& stream, const Ptr<const Chunk>& chunk) const
{
    auto startPosition = stream.getLength();
    const auto& simpleVoipPacket = staticPtrCast<const SimpleVoipPacket>(chunk);
    stream.writeUint32Be(B(simpleVoipPacket->getChunkLength()).get());
//    stream.writeUint32Be(simpleVoipPacket->getSequenceNumber());
    int64_t remainders = B(simpleVoipPacket->getChunkLength() - (stream.getLength() - startPosition)).get();
    if (remainders < 0)
        throw cRuntimeError("SimpleVoipPacket length = %d smaller than required %d bytes", (int)B(simpleVoipPacket->getChunkLength()).get(), (int)B(stream.getLength() - startPosition).get());
    stream.writeByteRepeatedly('?', remainders);
}

const Ptr<Chunk> SimpleVoipPacketSerializer::deserialize(MemoryInputStream& stream) const
{
    auto startPosition = stream.getPosition();
    auto simpleVoipPacket = makeShared<SimpleVoipPacket>();
    B dataLength = B(stream.readUint32Be());
//    simpleVoipPacket->setSequenceNumber(stream.readUint32Be());
    B remainders = dataLength - (stream.getPosition() - startPosition);
    ASSERT(remainders >= B(0));
    stream.readByteRepeatedly('?', B(remainders).get());
    return simpleVoipPacket;
}

} // namespace inet

