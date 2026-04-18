using System;
using UnityEngine;

namespace Knoema.Unity
{
    public sealed class NPCAgent : MonoBehaviour
    {
        [SerializeField] private KnoemaConfig config;
        [SerializeField] private string agentId = "guide";
        [SerializeField] [TextArea] private string contextJson = "{\"location\":\"sample scene\"}";

        private KnoemaClient client;

        public string AgentId => string.IsNullOrWhiteSpace(agentId) ? "guide" : agentId;

        private void Awake()
        {
            client = new KnoemaClient(config);
        }

        public void Interact(
            string playerAction,
            Action<KnoemaResponse> onCompleted,
            Action<string> onError = null
        )
        {
            if (client == null)
            {
                client = new KnoemaClient(config);
            }
            StartCoroutine(client.SendAsync(AgentId, playerAction, contextJson, onCompleted, onError));
        }
    }
}
