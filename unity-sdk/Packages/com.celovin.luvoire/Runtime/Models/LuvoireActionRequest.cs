using System;

namespace Knoema.UnitySdk.Models
{
    [Serializable]
    public sealed class KnoemaActionRequest
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
