using System;

namespace Luvoire.UnitySdk.Models
{
    [Serializable]
    public sealed class LuvoireMemoryItem
    {
        public string id = "";
        public string agent_id = "";
        public string timestamp = "";
        public string content = "";
        public string memory_type = "";
        public float importance;
    }
}
