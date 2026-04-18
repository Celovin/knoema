using Knoema.Unity;
using UnityEngine;
using UnityEngine.UI;

namespace Knoema.Unity.Samples
{
    public sealed class BasicNPCDemo : MonoBehaviour
    {
        [SerializeField] private NPCAgent npc;
        [SerializeField] private InputField input;
        [SerializeField] private Button sendButton;
        [SerializeField] private Text transcript;

        private void Awake()
        {
            if (sendButton != null)
            {
                sendButton.onClick.AddListener(Send);
            }
        }

        private void Send()
        {
            var message = input == null ? "" : input.text;
            if (string.IsNullOrWhiteSpace(message) || npc == null)
            {
                return;
            }

            Append($"Player: {message}");
            if (input != null)
            {
                input.text = "";
            }

            npc.Interact(
                message,
                response => Append($"NPC: {response.content}"),
                error => Append($"Knoema fallback used: {error}")
            );
        }

        private void Append(string line)
        {
            if (transcript == null)
            {
                return;
            }

            transcript.text = string.IsNullOrEmpty(transcript.text)
                ? line
                : $"{transcript.text}\n{line}";
        }
    }
}
