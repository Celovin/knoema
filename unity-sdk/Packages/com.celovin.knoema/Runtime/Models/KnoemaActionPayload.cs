using System;

namespace Knoema.UnitySdk.Models
{
    [Serializable]
    public sealed class KnoemaActionMetadata
    {
        public bool unity_sdk;
        public string player_action = "";
        public string source = "";
    }

    [Serializable]
    public sealed class KnoemaActionPayload
    {
        public string action_type = "speak";
        public string target = "";
        public string content = "";
        public string location = "";
        public string timestamp = "";
        public KnoemaActionMetadata metadata = new KnoemaActionMetadata();
    }
}
