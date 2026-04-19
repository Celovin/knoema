using Knoema.Unity;
using UnityEngine;
using UnityEngine.UI;

namespace Knoema.Unity.Samples
{
    public sealed class TavernDemo : MonoBehaviour
    {
        [SerializeField] private TavernPlayerController player;
        [SerializeField] private NPCAgent bjorn;
        [SerializeField] private Transform bjornAnchor;
        [SerializeField] private CanvasGroup dialogBox;
        [SerializeField] private InputField input;
        [SerializeField] private Button sendButton;
        [SerializeField] private Text statusLabel;
        [SerializeField] private Text transcript;
        [SerializeField] private float interactionDistance = 64f;

        private void Awake()
        {
            if (sendButton != null)
            {
                sendButton.onClick.AddListener(Send);
            }
        }

        private void Update()
        {
            var nearBjorn = player != null
                && bjornAnchor != null
                && Vector3.Distance(player.transform.position, bjornAnchor.position) <= interactionDistance;

            if (dialogBox != null)
            {
                dialogBox.alpha = nearBjorn ? 1f : 0.25f;
                dialogBox.interactable = nearBjorn;
                dialogBox.blocksRaycasts = nearBjorn;
            }

            if (statusLabel != null)
            {
                statusLabel.text = nearBjorn
                    ? "Bjorn is ready. Type a line and press Send."
                    : "Walk within 64px of Bjorn.";
            }
        }

        private void Send()
        {
            var message = input == null ? "" : input.text;
            if (string.IsNullOrWhiteSpace(message) || bjorn == null)
            {
                return;
            }

            Append($"Player: {message}");
            if (input != null)
            {
                input.text = "";
            }

            bjorn.Interact(
                message,
                response => Append($"Bjorn: {response.content}"),
                error => Append($"Replay-only fallback: {error}")
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
