using UnityEngine;

namespace Knoema.Unity
{
    [CreateAssetMenu(fileName = "KnoemaConfig", menuName = "Knoema/Config")]
    public sealed class KnoemaConfig : ScriptableObject
    {
        [SerializeField] private string endpointUrl = "http://localhost:8000/interact";
        [SerializeField] private string sessionId = "unity-demo";
        [SerializeField] private bool useLocalFallback = true;

        public string EndpointUrl => endpointUrl;
        public string SessionId => string.IsNullOrWhiteSpace(sessionId) ? "unity-demo" : sessionId;
        public bool UseLocalFallback => useLocalFallback;
    }
}
