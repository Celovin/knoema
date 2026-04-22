using System;

namespace Luvoire.UnitySdk.Models
{
    [Serializable]
    public sealed class LuvoireMemoryResponse
    {
        public string session_id = "unity-demo";
        public string agent_id = "guide";
        public LuvoireMemoryItem[] memories = Array.Empty<LuvoireMemoryItem>();
    }
}
