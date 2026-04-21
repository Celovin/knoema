using System;

namespace Knoema.UnitySdk.Models
{
    [Serializable]
    public sealed class KnoemaTickResponse
    {
        public string session_id = "unity-demo";
        public string agent_id = "guide";
        public int tick;
        public string content = "";
        public string emotion = "neutral";
        public string[] branch_flags = Array.Empty<string>();
        public KnoemaActionPayload action = new KnoemaActionPayload();
    }
}
