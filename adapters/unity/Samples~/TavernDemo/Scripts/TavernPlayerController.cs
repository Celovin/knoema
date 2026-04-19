using UnityEngine;

namespace Knoema.Unity.Samples
{
    public sealed class TavernPlayerController : MonoBehaviour
    {
        [SerializeField] private float moveSpeed = 4.0f;

        private void Update()
        {
            var input = new Vector3(
                Input.GetAxisRaw("Horizontal"),
                0.0f,
                Input.GetAxisRaw("Vertical")
            );
            if (input.sqrMagnitude > 1.0f)
            {
                input.Normalize();
            }

            transform.position += input * (moveSpeed * Time.deltaTime);
        }
    }
}
