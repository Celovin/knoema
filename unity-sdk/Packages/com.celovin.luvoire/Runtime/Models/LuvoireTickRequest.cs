using System;

namespace Knoema.UnitySdk.Models
{
    [Serializable]
    public sealed class KnoemaTickRequest
    {
        public string session_id = "unity-demo";
        public string agent_id = "guide";
        public string player_action = "";
        public string context_json = "{}";
    }
}
