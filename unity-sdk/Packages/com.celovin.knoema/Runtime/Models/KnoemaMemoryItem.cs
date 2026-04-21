using System;

namespace Knoema.UnitySdk.Models
{
    [Serializable]
    public sealed class KnoemaMemoryItem
    {
        public string id = "";
        public string agent_id = "";
        public string timestamp = "";
        public string content = "";
        public string memory_type = "";
        public float importance;
    }
}
