using UnityEditor;
using UnityEngine;

namespace Knoema.UnitySdk.Editor
{
    public sealed class KnoemaSettingsWindow : EditorWindow
    {
        private string baseUrl = "http://localhost:8000";
        private string sessionId = "unity-demo";
        private string agentId = "guide";

        [MenuItem("Tools/Knoema/Settings")]
        public static void Open()
        {
            GetWindow<KnoemaSettingsWindow>("Knoema");
        }

        private void OnGUI()
        {
            EditorGUILayout.LabelField("Knoema Unity SDK", EditorStyles.boldLabel);
            baseUrl = EditorGUILayout.TextField("API Base URL", baseUrl);
            sessionId = EditorGUILayout.TextField("Session ID", sessionId);
            agentId = EditorGUILayout.TextField("Agent ID", agentId);

            EditorGUILayout.Space();
            EditorGUILayout.HelpBox(
                "Add KnoemaNPC to an NPC GameObject, then copy these values into the component.",
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
