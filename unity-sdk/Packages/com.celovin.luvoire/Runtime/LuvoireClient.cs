using System;
using System.Collections;
using System.Text;
using Luvoire.UnitySdk.Models;
using UnityEngine.Networking;

namespace Luvoire.UnitySdk
{
    public sealed class LuvoireClient
    {
        private readonly string baseUrl;
        private readonly string bearerToken;

        public LuvoireClient(string baseUrl = "http://localhost:8000", string bearerToken = "")
        {
            this.baseUrl = string.IsNullOrWhiteSpace(baseUrl) ? "http://localhost:8000" : baseUrl.TrimEnd('/');
            this.bearerToken = bearerToken ?? "";
        }

        public IEnumerator TickAsync(
            LuvoireTickRequest request,
            Action<LuvoireTickResponse> onCompleted,
            Action<string> onError = null
        )
        {
            yield return SendJson(
                "POST",
                "/simulate/tick",
                request,
                text => onCompleted?.Invoke(UnityEngine.JsonUtility.FromJson<LuvoireTickResponse>(text)),
                onError
            );
        }

        public IEnumerator GetMemoryAsync(
            string sessionId,
            string agentId,
            Action<LuvoireMemoryResponse> onCompleted,
            Action<string> onError = null
        )
        {
            var safeSession = string.IsNullOrWhiteSpace(sessionId) ? "unity-demo" : Uri.EscapeDataString(sessionId);
            var safeAgent = string.IsNullOrWhiteSpace(agentId) ? "guide" : Uri.EscapeDataString(agentId);
            yield return SendJson(
                "GET",
                $"/agent/{safeAgent}/memory?session_id={safeSession}",
                null,
                text => onCompleted?.Invoke(UnityEngine.JsonUtility.FromJson<LuvoireMemoryResponse>(text)),
                onError
            );
        }

        public IEnumerator PostActionAsync(
            string agentId,
            LuvoireActionRequest request,
            Action<LuvoireActionResponse> onCompleted,
            Action<string> onError = null
        )
        {
            var safeAgent = string.IsNullOrWhiteSpace(agentId) ? "guide" : Uri.EscapeDataString(agentId);
            yield return SendJson(
                "POST",
                $"/agent/{safeAgent}/action",
                request,
                text => onCompleted?.Invoke(UnityEngine.JsonUtility.FromJson<LuvoireActionResponse>(text)),
                onError
            );
        }

        private IEnumerator SendJson(
            string method,
            string path,
            object payload,
            Action<string> onCompleted,
            Action<string> onError
        )
        {
            var body = payload == null ? Array.Empty<byte>() : Encoding.UTF8.GetBytes(UnityEngine.JsonUtility.ToJson(payload));
            using var http = new UnityWebRequest(baseUrl + path, method)
            {
                uploadHandler = payload == null ? null : new UploadHandlerRaw(body),
                downloadHandler = new DownloadHandlerBuffer(),
            };
            http.SetRequestHeader("Accept", "application/json");
            if (payload != null)
            {
                http.SetRequestHeader("Content-Type", "application/json");
            }
            if (!string.IsNullOrWhiteSpace(bearerToken))
            {
                http.SetRequestHeader("Authorization", "Bearer " + bearerToken);
            }

            yield return http.SendWebRequest();

            if (HasRequestError(http))
            {
                var message = string.IsNullOrWhiteSpace(http.error) ? http.downloadHandler.text : http.error;
                onError?.Invoke(string.IsNullOrWhiteSpace(message) ? "Luvoire request failed." : message);
                yield break;
            }

            onCompleted?.Invoke(http.downloadHandler.text);
        }

        private static bool HasRequestError(UnityWebRequest http)
        {
#if UNITY_2020_2_OR_NEWER
            return http.result != UnityWebRequest.Result.Success;
#else
            return http.isNetworkError || http.isHttpError;
#endif
        }
    }
}
