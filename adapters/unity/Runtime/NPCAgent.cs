using System;
using UnityEngine;

namespace Luvoire.Unity
{
    public sealed class NPCAgent : MonoBehaviour
    {
        [SerializeField] private LuvoireConfig config;
        [SerializeField] private string agentId = "guide";
        [SerializeField] [TextArea] private string contextJson = "{\"location\":\"sample scene\"}";

        private LuvoireClient client;

        public string AgentId => string.IsNullOrWhiteSpace(agentId) ? "guide" : agentId;

        private void Awake()
        {
            client = new LuvoireClient(config);
        }

        public void Interact(
            string playerAction,
            Action<LuvoireResponse> onCompleted,
            Action<string> onError = null
        )
        {
            if (client == null)
            {
                client = new LuvoireClient(config);
            }
            StartCoroutine(client.SendAsync(AgentId, playerAction, contextJson, onCompleted, onError));
        }
    }
}
