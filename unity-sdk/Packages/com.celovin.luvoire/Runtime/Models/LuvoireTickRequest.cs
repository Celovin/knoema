using System;

namespace Luvoire.UnitySdk.Models
{
    [Serializable]
    public sealed class LuvoireTickRequest
    {
        public string session_id = "unity-demo";
        public string agent_id = "guide";
        public string player_action = "";
        public string context_json = "{}";
    }
}
