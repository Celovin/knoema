using NUnit.Framework;
using UnityEngine;

namespace Luvoire.Unity.Tests
{
    public sealed class LuvoireClientTests
    {
        [Test]
        public void ConfigDefaultsToLocalhostEndpoint()
        {
            var config = ScriptableObject.CreateInstance<LuvoireConfig>();

            Assert.That(config.EndpointUrl, Does.Contain("localhost:8000"));
            Assert.That(config.SessionId, Is.EqualTo("unity-demo"));
            Assert.That(config.UseLocalFallback, Is.True);
        }

        [Test]
        public void ClientTypeIsAvailableForNpcAgents()
        {
            var client = new LuvoireClient(null);

            Assert.That(client, Is.Not.Null);
        }
    }
}
