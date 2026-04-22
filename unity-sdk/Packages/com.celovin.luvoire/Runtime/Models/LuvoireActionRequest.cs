using System;

namespace Luvoire.UnitySdk.Models
{
    [Serializable]
    public sealed class LuvoireActionRequest
    {
        public string session_id = "unity-demo";
        public string action_type = "speak";
        public string target = "";
        public string content = "";
        public string location = "";
        public string metadata_json = "{}";
        public string context_json = "{}";
    }
}
