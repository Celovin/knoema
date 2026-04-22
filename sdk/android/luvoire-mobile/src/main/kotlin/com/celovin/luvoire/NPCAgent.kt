package com.celovin.luvoire

class NPCAgent(
    private val agentId: String,
    private val displayName: String,
    private val client: LuvoireClient,
) {
    fun endpoint(): String {
        return client.restUrl("/agents/$agentId")
    }

    fun name(): String {
        return displayName
    }

    fun cachedOrOfflineResponse(input: String): NPCActionResponse {
        val key = "$agentId:$input"
        val cached = client.cachedResponse(key)
        if (cached != null) {
            return cached
        }
        val response = client.offlineResponse(agentId, input)
        client.cacheResponse(key, response)
        return response
    }
}
