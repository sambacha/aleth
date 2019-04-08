#include "StoreStats.h"



namespace dev {
namespace eth {


StoreKeyStats::StoreKeyStats() = default;


void StoreStats::recordWrite(const u256 &key, u256 originalValue, const u256 &currentValue, const u256 &newValue) {
    auto res = m_changes.insert(std::make_pair(key, StoreKeyStats()));
    auto& stats = res.first->second;
    if (!stats.initialValueSet) {
        stats.initialValueSet = true;
        stats.initialValue = std::move(originalValue);
    }
    stats.newValue = newValue;
    stats.writesCount++;
    if (currentValue != newValue) {
        stats.changesCount++;
    }
}

void StoreStats::recordRead(const u256 &key) {
    auto res = m_changes.insert(std::make_pair(key, StoreKeyStats()));
    auto& stats = res.first->second;
    stats.readsCount++;
}

void StoreStats::recordCreate(const u256 &size) {
    m_createCalls.push_back(size);
}


Json::Value StoreStats::toJson() const {
    uint64_t changesCount = 0;
    uint64_t writesCount = 0;
    uint64_t readsCount = 0;
    uint64_t storageAllocated = 0;
    for (auto& changeKv : m_changes) {
        auto& change = changeKv.second;
        changesCount += change.changesCount;
        writesCount += change.writesCount;
        readsCount += change.readsCount;
        if (change.initialValue == 0 && change.newValue != 0) {
            storageAllocated++;
        } else if (change.initialValue != 0 && change.newValue == 0) {
            storageAllocated--;
        }
    }

    uint64_t creationSize = 0;
    for (const u256& size : m_createCalls) {
        creationSize += size.convert_to<uint64_t>();
    }

    Json::Value result;
    result["changesCount"] = changesCount;
    result["writesCount"] = writesCount;
    result["readsCount"] = readsCount;
    result["storageAllocated"] = storageAllocated;
    result["creationCount"] = m_createCalls.size();
    result["creationSize"] = creationSize;

    return result;
}

}
}
