package com.celovin.luvoire

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class LuvoireClientTest {
    @Test
    fun buildsRestAndWebSocketUrls() {
        val client = LuvoireClient("https://api.example.test", "demo")

        assertEquals("https://api.example.test/agents/alice", client.restUrl("/agents/alice"))
        assertEquals("wss://api.example.test/ws/simulations/demo", client.webSocketUrl("/ws/simulations/demo"))
        assertEquals("Bearer demo", client.headers()["authorization"])
    }

    @Test
    fun npcAgentCachesOfflineResponse() {
        val client = LuvoireClient("http://localhost:8000")
        val agent = NPCAgent("alice", "Alice", client)

        val first = agent.cachedOrOfflineResponse("hello")
        val second = agent.cachedOrOfflineResponse("hello")

        assertTrue(first.isOffline)
        assertEquals(first, second)
    }
}
