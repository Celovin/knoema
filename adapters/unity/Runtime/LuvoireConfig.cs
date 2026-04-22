using UnityEngine;

namespace Luvoire.Unity
{
    [CreateAssetMenu(fileName = "LuvoireConfig", menuName = "Luvoire/Config")]
    public sealed class LuvoireConfig : ScriptableObject
    {
        [SerializeField] private string endpointUrl = "http://localhost:8000/interact";
        [SerializeField] private string sessionId = "unity-demo";
        [SerializeField] private bool useLocalFallback = true;

        public string EndpointUrl => endpointUrl;
        public string SessionId => string.IsNullOrWhiteSpace(sessionId) ? "unity-demo" : sessionId;
        public bool UseLocalFallback => useLocalFallback;
    }
}
