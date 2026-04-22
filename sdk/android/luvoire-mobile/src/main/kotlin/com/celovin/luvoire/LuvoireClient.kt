package com.celovin.knoema

data class NPCActionResponse(
    val agentId: String,
    val actionType: String,
    val content: String,
    val isOffline: Boolean = false,
)

data class AgentSnapshot(
    val agentId: String,
    val displayName: String,
    val location: String,
    val summary: String,
)

class KnoemaClient(
    private val baseUrl: String,
    private val token: String? = null,
) {
    private val cache = mutableMapOf<String, NPCActionResponse>()

    fun restUrl(path: String): String {
        return baseUrl.trimEnd('/') + "/" + path.trimStart('/')
    }

    fun webSocketUrl(path: String = "/ws/simulations/default"): String {
        val scheme = if (baseUrl.startsWith("https://")) "wss://" else "ws://"
        val host = baseUrl.removePrefix("https://").removePrefix("http://").trimEnd('/')
        return scheme + host + "/" + path.trimStart('/')
    }

    fun headers(): Map<String, String> {
        val baseHeaders = mutableMapOf("accept" to "application/json")
        if (token != null) {
            baseHeaders["authorization"] = "Bearer $token"
        }
        return baseHeaders
    }

    fun cacheResponse(key: String, response: NPCActionResponse) {
        cache[key] = response
    }

    fun cachedResponse(key: String): NPCActionResponse? {
        return cache[key]
    }

    fun offlineResponse(agentId: String, input: String): NPCActionResponse {
        return NPCActionResponse(
            agentId = agentId,
            actionType = "speak",
            content = "Offline response for $input",
            isOffline = true,
        )
    }
}
