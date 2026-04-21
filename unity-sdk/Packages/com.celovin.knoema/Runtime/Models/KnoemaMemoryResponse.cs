using System;

namespace Knoema.UnitySdk.Models
{
    [Serializable]
    public sealed class KnoemaMemoryResponse
    {
        public string session_id = "unity-demo";
        public string agent_id = "guide";
        public KnoemaMemoryItem[] memories = Array.Empty<KnoemaMemoryItem>();
    }
}
