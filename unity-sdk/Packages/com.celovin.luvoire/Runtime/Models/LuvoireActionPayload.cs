using System;

namespace Luvoire.UnitySdk.Models
{
    [Serializable]
    public sealed class LuvoireActionMetadata
    {
        public bool unity_sdk;
        public string player_action = "";
        public string source = "";
    }

    [Serializable]
    public sealed class LuvoireActionPayload
    {
        public string action_type = "speak";
        public string target = "";
        public string content = "";
        public string location = "";
        public string timestamp = "";
        public LuvoireActionMetadata metadata = new LuvoireActionMetadata();
    }
}
