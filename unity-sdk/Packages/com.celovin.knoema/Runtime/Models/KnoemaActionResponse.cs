using System;

namespace Knoema.UnitySdk.Models
{
    [Serializable]
    public sealed class KnoemaActionResponse
    {
        public string session_id = "unity-demo";
        public string agent_id = "guide";
        public int tick;
        public bool accepted;
        public KnoemaActionPayload action = new KnoemaActionPayload();
    }
}
