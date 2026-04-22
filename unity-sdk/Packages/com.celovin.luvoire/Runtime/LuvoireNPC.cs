using System;
using Luvoire.UnitySdk.Models;
using UnityEngine;

namespace Luvoire.UnitySdk
{
    public sealed class LuvoireNPC : MonoBehaviour
    {
        [SerializeField] private string baseUrl = "http://localhost:8000";
        [SerializeField] private string bearerToken = "";
        [SerializeField] private string sessionId = "unity-demo";
        [SerializeField] private string agentId = "guide";
        [SerializeField] [TextArea] private string contextJson = "{\"location\":\"Demo Village > Plaza\"}";

        private LuvoireClient client;

        public string SessionId => string.IsNullOrWhiteSpace(sessionId) ? "unity-demo" : sessionId;
        public string AgentId => string.IsNullOrWhiteSpace(agentId) ? "guide" : agentId;

        private void Awake()
        {
            client = new LuvoireClient(baseUrl, bearerToken);
        }

        public void Tick(
            string playerAction,
            Action<LuvoireTickResponse> onCompleted,
            Action<string> onError = null
        )
        {
            EnsureClient();
            var request = new LuvoireTickRequest
            {
                session_id = SessionId,
                agent_id = AgentId,
                player_action = string.IsNullOrWhiteSpace(playerAction) ? "waits" : playerAction,
                context_json = string.IsNullOrWhiteSpace(contextJson) ? "{}" : contextJson,
            };
            StartCoroutine(client.TickAsync(request, onCompleted, onError));
        }

        public void GetMemory(
            Action<LuvoireMemoryResponse> onCompleted,
            Action<string> onError = null
        )
        {
            EnsureClient();
            StartCoroutine(client.GetMemoryAsync(SessionId, AgentId, onCompleted, onError));
        }

        private void EnsureClient()
        {
            if (client == null)
            {
                client = new LuvoireClient(baseUrl, bearerToken);
            }
        }
    }
}
