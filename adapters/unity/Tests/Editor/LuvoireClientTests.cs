using NUnit.Framework;
using UnityEngine;

namespace Knoema.Unity.Tests
{
    public sealed class KnoemaClientTests
    {
        [Test]
        public void ConfigDefaultsToLocalhostEndpoint()
        {
            var config = ScriptableObject.CreateInstance<KnoemaConfig>();

            Assert.That(config.EndpointUrl, Does.Contain("localhost:8000"));
            Assert.That(config.SessionId, Is.EqualTo("unity-demo"));
            Assert.That(config.UseLocalFallback, Is.True);
        }

        [Test]
        public void ClientTypeIsAvailableForNpcAgents()
        {
            var client = new KnoemaClient(null);

            Assert.That(client, Is.Not.Null);
        }
    }
}
