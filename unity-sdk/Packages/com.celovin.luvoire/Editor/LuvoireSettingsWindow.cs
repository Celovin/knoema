using UnityEditor;
using UnityEngine;

namespace Luvoire.UnitySdk.Editor
{
    public sealed class LuvoireSettingsWindow : EditorWindow
    {
        private string baseUrl = "http://localhost:8000";
        private string sessionId = "unity-demo";
        private string agentId = "guide";

        [MenuItem("Tools/Luvoire/Settings")]
        public static void Open()
        {
            GetWindow<LuvoireSettingsWindow>("Luvoire");
        }

        private void OnGUI()
        {
            EditorGUILayout.LabelField("Luvoire Unity SDK", EditorStyles.boldLabel);
            baseUrl = EditorGUILayout.TextField("API Base URL", baseUrl);
            sessionId = EditorGUILayout.TextField("Session ID", sessionId);
            agentId = EditorGUILayout.TextField("Agent ID", agentId);

            EditorGUILayout.Space();
            EditorGUILayout.HelpBox(
                "Add LuvoireNPC to an NPC GameObject, then copy these values into the component.",
                MessageType.Info
            );

            if (GUILayout.Button("Copy curl smoke command"))
            {
                var command = "curl -X POST " + baseUrl.TrimEnd('/') +
                    "/simulate/tick -H \"Content-Type: application/json\" -d " +
                    "'{\"session_id\":\"" + sessionId + "\",\"agent_id\":\"" + agentId +
                    "\",\"player_action\":\"hello\",\"context_json\":\"{\\\"location\\\":\\\"Demo Village > Plaza\\\"}\"}'";
                EditorGUIUtility.systemCopyBuffer = command;
            }
        }
    }
}
