using System;
using System.Collections;
using System.Text;
using Knoema.UnitySdk.Models;
using UnityEngine.Networking;

namespace Knoema.UnitySdk
{
    public sealed class KnoemaClient
    {
        private readonly string baseUrl;
        private readonly string bearerToken;

        public KnoemaClient(string baseUrl = "http://localhost:8000", string bearerToken = "")
        {
            this.baseUrl = string.IsNullOrWhiteSpace(baseUrl) ? "http://localhost:8000" : baseUrl.TrimEnd('/');
            this.bearerToken = bearerToken ?? "";
        }

        public IEnumerator TickAsync(
            KnoemaTickRequest request,
            Action<KnoemaTickResponse> onCompleted,
            Action<string> onError = null
        )
        {
            yield return SendJson(
                "POST",
                "/simulate/tick",
                request,
                text => onCompleted?.Invoke(UnityEngine.JsonUtility.FromJson<KnoemaTickResponse>(text)),
                onError
            );
        }

        public IEnumerator GetMemoryAsync(
            string sessionId,
            string agentId,
            Action<KnoemaMemoryResponse> onCompleted,
            Action<string> onError = null
        )
        {
            var safeSession = string.IsNullOrWhiteSpace(sessionId) ? "unity-demo" : Uri.EscapeDataString(sessionId);
            var safeAgent = string.IsNullOrWhiteSpace(agentId) ? "guide" : Uri.EscapeDataString(agentId);
            yield return SendJson(
                "GET",
                $"/agent/{safeAgent}/memory?session_id={safeSession}",
                null,
                text => onCompleted?.Invoke(UnityEngine.JsonUtility.FromJson<KnoemaMemoryResponse>(text)),
                onError
            );
        }

        public IEnumerator PostActionAsync(
            string agentId,
            KnoemaActionRequest request,
            Action<KnoemaActionResponse> onCompleted,
            Action<string> onError = null
        )
        {
            var safeAgent = string.IsNullOrWhiteSpace(agentId) ? "guide" : Uri.EscapeDataString(agentId);
            yield return SendJson(
                "POST",
                $"/agent/{safeAgent}/action",
                request,
                text => onCompleted?.Invoke(UnityEngine.JsonUtility.FromJson<KnoemaActionResponse>(text)),
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
                onError?.Invoke(string.IsNullOrWhiteSpace(message) ? "Knoema request failed." : message);
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
