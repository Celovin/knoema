using System;
using Knoema.UnitySdk.Models;
using UnityEngine;

namespace Knoema.UnitySdk
{
    public sealed class KnoemaNPC : MonoBehaviour
    {
        [SerializeField] private string baseUrl = "http://localhost:8000";
        [SerializeField] private string bearerToken = "";
        [SerializeField] private string sessionId = "unity-demo";
        [SerializeField] private string agentId = "guide";
        [SerializeField] [TextArea] private string contextJson = "{\"location\":\"Demo Village > Plaza\"}";

        private KnoemaClient client;

        public string SessionId => string.IsNullOrWhiteSpace(sessionId) ? "unity-demo" : sessionId;
        public string AgentId => string.IsNullOrWhiteSpace(agentId) ? "guide" : agentId;

        private void Awake()
        {
            client = new KnoemaClient(baseUrl, bearerToken);
        }

        public void Tick(
            string playerAction,
            Action<KnoemaTickResponse> onCompleted,
            Action<string> onError = null
        )
        {
            EnsureClient();
            var request = new KnoemaTickRequest
            {
                session_id = SessionId,
                agent_id = AgentId,
                player_action = string.IsNullOrWhiteSpace(playerAction) ? "waits" : playerAction,
                context_json = string.IsNullOrWhiteSpace(contextJson) ? "{}" : contextJson,
            };
            StartCoroutine(client.TickAsync(request, onCompleted, onError));
        }

        public void GetMemory(
            Action<KnoemaMemoryResponse> onCompleted,
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
                client = new KnoemaClient(baseUrl, bearerToken);
            }
        }
    }
}
