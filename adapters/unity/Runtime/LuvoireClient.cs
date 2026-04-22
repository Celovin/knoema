using System;
using System.Collections;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

namespace Luvoire.Unity
{
    [Serializable]
    public sealed class LuvoireRequest
    {
        public string session_id = "unity-demo";
        public string agent_id = "npc";
        public string player_action = "";
        public string context_json = "{}";
    }

    [Serializable]
    public sealed class LuvoireResponse
    {
        public string content = "";
        public string emotion = "neutral";
        public string[] branch_flags = Array.Empty<string>();
    }

    public sealed class LuvoireClient
    {
        private readonly LuvoireConfig config;

        public LuvoireClient(LuvoireConfig config)
        {
            this.config = config;
        }

        public IEnumerator SendAsync(
            string agentId,
            string playerAction,
            string contextJson,
            Action<LuvoireResponse> onCompleted,
            Action<string> onError = null
        )
        {
            if (config == null || config.UseLocalFallback || string.IsNullOrWhiteSpace(config.EndpointUrl))
            {
                onCompleted?.Invoke(LocalFallback(agentId, playerAction));
                yield break;
            }

            var request = new LuvoireRequest
            {
                session_id = config.SessionId,
                agent_id = string.IsNullOrWhiteSpace(agentId) ? "npc" : agentId,
                player_action = playerAction == null ? "" : playerAction,
                context_json = string.IsNullOrWhiteSpace(contextJson) ? "{}" : contextJson,
            };
            var body = Encoding.UTF8.GetBytes(JsonUtility.ToJson(request));

            using var http = new UnityWebRequest(config.EndpointUrl, UnityWebRequest.kHttpVerbPOST)
            {
                uploadHandler = new UploadHandlerRaw(body),
                downloadHandler = new DownloadHandlerBuffer(),
            };
            http.SetRequestHeader("Content-Type", "application/json");

            yield return http.SendWebRequest();

            if (HasRequestError(http))
            {
                var error = string.IsNullOrEmpty(http.error) ? "Luvoire request failed." : http.error;
                onError?.Invoke(error);
                onCompleted?.Invoke(LocalFallback(agentId, playerAction));
                yield break;
            }

            var response = JsonUtility.FromJson<LuvoireResponse>(http.downloadHandler.text);
            if (response == null || string.IsNullOrWhiteSpace(response.content))
            {
                onCompleted?.Invoke(LocalFallback(agentId, playerAction));
                yield break;
            }

            onCompleted?.Invoke(response);
        }

        private static bool HasRequestError(UnityWebRequest http)
        {
#if UNITY_2020_2_OR_NEWER
            return http.result != UnityWebRequest.Result.Success;
#else
            return http.isNetworkError || http.isHttpError;
#endif
        }

        private static LuvoireResponse LocalFallback(string agentId, string playerAction)
        {
            var safeAgentId = string.IsNullOrWhiteSpace(agentId) ? "npc" : agentId;
            var safeAction = string.IsNullOrWhiteSpace(playerAction) ? "the current scene" : playerAction;
            return new LuvoireResponse
            {
                content = $"{safeAgentId} remembers '{safeAction}' and responds with a small next step.",
                emotion = "calm",
                branch_flags = new[] { "local_fallback" },
            };
        }
    }
}
