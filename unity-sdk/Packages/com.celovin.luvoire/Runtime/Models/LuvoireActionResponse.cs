using System;

namespace Luvoire.UnitySdk.Models
{
    [Serializable]
    public sealed class LuvoireActionResponse
    {
        public string session_id = "unity-demo";
        public string agent_id = "guide";
        public int tick;
        public bool accepted;
        public LuvoireActionPayload action = new LuvoireActionPayload();
    }
}
